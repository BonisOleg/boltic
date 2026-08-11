"""CMS section form + change view (один шаблон для всіх секцій)."""

from __future__ import annotations

from django import forms
from django.contrib import messages
from django.core.cache import cache
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from unfold.widgets import UnfoldAdminFileFieldWidget, UnfoldBooleanWidget

from apps.core.admin_contact_branches import build_contact_branch_formset
from apps.core.admin_guidelines import get_text_limit_hint
from apps.core.admin_hero_slides import build_hero_slide_formset
from apps.core.admin_site_content_widgets import (
    CmsAdminTextareaWidget,
    CmsAdminTextInputWidget,
)
from apps.core.block_defaults import (
    INLINE_KEYS,
    MULTILINE_KEYS,
    block_content_type,
    block_default,
    block_label,
    is_visibility_key,
)
from apps.core.models import SITE_BLOCKS_CACHE_KEY, SiteBlock, SiteSettings
from apps.core.site_content_registry import ContentSection, get_section


def ensure_block(page: str, key: str) -> SiteBlock:
    ctype = block_content_type(page, key)
    defaults = {
        "label": block_label(page, key),
        "content_type": ctype,
        "text_html": block_default(page, key),
        "is_active": True,
    }
    if ctype == "url":
        defaults["link_url"] = block_default(page, key)
        defaults["text_html"] = ""
    obj, created = SiteBlock.objects.get_or_create(
        page=page, key=key, defaults=defaults
    )
    if created:
        return obj
    if not obj.label:
        obj.label = block_label(page, key)
        obj.save(update_fields=["label"])
    return obj


def load_section_blocks(section: ContentSection) -> dict[str, SiteBlock]:
    return {key: ensure_block(page, key) for page, key in section.blocks}


class SitePageContentForm(forms.Form):
    def __init__(self, section: ContentSection, blocks: dict[str, SiteBlock], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.section = section
        self.blocks = blocks

        if section.visibility_key:
            vis = blocks.get(section.visibility_key)
            self.fields["section_visible"] = forms.BooleanField(
                label="Показувати секцію на сайті",
                required=False,
                initial=(vis.text_html if vis else "1") not in {"0", "false", "False", ""},
                widget=UnfoldBooleanWidget(),
            )

        for page, key in section.blocks:
            if section.visibility_key and key == section.visibility_key:
                continue
            block = blocks[key]
            label = block.label or block_label(page, key)
            prefix = f"block__{page}__{key}"

            if is_visibility_key(key):
                self.fields[f"{prefix}__visible"] = forms.BooleanField(
                    label=label,
                    required=False,
                    initial=block.text_html not in {"0", "false", "False", ""},
                    widget=UnfoldBooleanWidget(),
                )
                continue

            ctype = block.content_type or block_content_type(page, key)
            if ctype == "image":
                self.fields[f"{prefix}__image"] = forms.ImageField(
                    label=label,
                    required=False,
                    widget=UnfoldAdminFileFieldWidget(),
                )
            elif ctype == "url":
                self.fields[f"{prefix}__link_url"] = forms.CharField(
                    label=f"{label} — URL",
                    required=False,
                    initial=block.link_url,
                    widget=CmsAdminTextInputWidget(),
                )
                self.fields[f"{prefix}__link_label"] = forms.CharField(
                    label=f"{label} — текст",
                    required=False,
                    initial=block.link_label,
                    widget=CmsAdminTextInputWidget(),
                )
            elif key in INLINE_KEYS:
                field = forms.CharField(
                    label=label,
                    required=False,
                    initial=block.text_html,
                    widget=CmsAdminTextInputWidget(),
                )
                hint = get_text_limit_hint(key)
                if hint:
                    field.help_text = hint
                self.fields[f"{prefix}__text_html"] = field
            else:
                rows = 4 if key in MULTILINE_KEYS else 2
                self.fields[f"{prefix}__text_html"] = forms.CharField(
                    label=label,
                    required=False,
                    initial=block.text_html,
                    widget=CmsAdminTextareaWidget(attrs={"rows": rows}),
                )

    def save(self) -> None:
        section = self.section
        cleaned = self.cleaned_data

        if section.visibility_key:
            vis = self.blocks[section.visibility_key]
            vis.text_html = "1" if cleaned.get("section_visible") else "0"
            vis.save(update_fields=["text_html"])

        for page, key in section.blocks:
            if section.visibility_key and key == section.visibility_key:
                continue
            block = self.blocks[key]
            prefix = f"block__{page}__{key}"

            if is_visibility_key(key):
                block.text_html = "1" if cleaned.get(f"{prefix}__visible") else "0"
                block.save(update_fields=["text_html"])
                continue

            ctype = block.content_type or block_content_type(page, key)
            if ctype == "image":
                image = cleaned.get(f"{prefix}__image")
                if image:
                    block.image = image
                    block.save(update_fields=["image"])
            elif ctype == "url":
                block.link_url = cleaned.get(f"{prefix}__link_url") or ""
                block.link_label = cleaned.get(f"{prefix}__link_label") or ""
                block.save(update_fields=["link_url", "link_label"])
            else:
                block.text_html = cleaned.get(f"{prefix}__text_html") or ""
                block.save(update_fields=["text_html"])

        cache.delete(SITE_BLOCKS_CACHE_KEY)


def _grouped_fields(form: SitePageContentForm, section: ContentSection) -> list[dict]:
    groups = []
    if section.visibility_key and "section_visible" in form.fields:
        groups.append({"title": "Видимість", "fields": [form["section_visible"]]})

    for group in section.field_groups:
        fields = []
        for key in group.keys:
            if section.visibility_key and key == section.visibility_key:
                continue
            page = section.page_slug
            prefix = f"block__{page}__{key}"
            for suffix in (
                "__visible",
                "__text_html",
                "__image",
                "__link_url",
                "__link_label",
            ):
                name = f"{prefix}{suffix}"
                if name in form.fields:
                    fields.append(form[name])
        if fields:
            groups.append({"title": group.title, "fields": fields})
    return groups


def site_content_section_view(
    request: HttpRequest,
    page_slug: str,
    section_slug: str,
    *,
    model_admin,
) -> HttpResponse:
    section = get_section(page_slug, section_slug)
    if section is None:
        raise Http404
    SiteSettings.get_solo()
    blocks = load_section_blocks(section)
    # index by key only (page fixed per section)
    blocks_by_key = {key: blocks[key] for _page, key in section.blocks}

    hero_formset = None
    branches_formset = None
    is_hero = section.slug == "hero"
    is_contacts = section.slug == "contacts"

    if request.method == "POST":
        form = SitePageContentForm(section, blocks_by_key, data=request.POST, files=request.FILES)
        if is_hero:
            hero_formset = build_hero_slide_formset(data=request.POST, files=request.FILES)
        if is_contacts:
            branches_formset = build_contact_branch_formset(
                data=request.POST, files=request.FILES
            )
        valid = form.is_valid()
        if hero_formset is not None:
            valid = valid and hero_formset.is_valid()
        if branches_formset is not None:
            valid = valid and branches_formset.is_valid()
        if valid:
            form.save()
            if hero_formset:
                hero_formset.save()
            if branches_formset:
                branches_formset.save()
            messages.success(request, "Збережено")
            opts = model_admin.model._meta
            return redirect(
                reverse(
                    f"admin:{opts.app_label}_{opts.model_name}_change",
                    args=[1],
                )
            )
        messages.error(request, "Не збережено — виправте помилки у формі.")
    else:
        form = SitePageContentForm(section, blocks_by_key)
        if is_hero:
            hero_formset = build_hero_slide_formset()
        if is_contacts:
            branches_formset = build_contact_branch_formset()

    media = form.media
    if hero_formset is not None:
        media = media + hero_formset.media
    if branches_formset is not None:
        media = media + branches_formset.media

    context = {
        **model_admin.admin_site.each_context(request),
        "title": section.title,
        "section": section,
        "form": form,
        "field_groups": _grouped_fields(form, section),
        "hero_formset": hero_formset,
        "branches_formset": branches_formset,
        "opts": model_admin.model._meta,
        "has_view_permission": True,
        "media": media,
    }
    return render(request, "admin/core/site_content_page.html", context)
