"""HeroSlide ModelFormSet для CMS-секції hero."""

from __future__ import annotations

from django import forms
from django.forms import BaseModelFormSet, modelformset_factory

from apps.core.admin_guidelines import get_image_hint
from apps.core.admin_site_content_widgets import (
    CmsAdminTextareaWidget,
    CmsAdminTextInputWidget,
)
from apps.core.hero_slides import ensure_default_hero_slides
from apps.core.models import HeroSlide


class HeroSlideForm(forms.ModelForm):
    class Meta:
        model = HeroSlide
        fields = (
            "image",
            "title",
            "body",
            "cta_label",
            "cta_url",
            "alt_text",
            "sort_order",
            "is_active",
        )
        widgets = {
            "title": CmsAdminTextInputWidget(),
            "body": CmsAdminTextareaWidget(attrs={"rows": 3}),
            "cta_label": CmsAdminTextInputWidget(),
            "cta_url": CmsAdminTextInputWidget(),
            "alt_text": CmsAdminTextInputWidget(),
            "sort_order": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["image"].help_text = get_image_hint("hero")
        self.fields["is_active"].widget.attrs.setdefault("class", "")

    def clean(self):
        cleaned = super().clean()
        image = cleaned.get("image")
        title = (cleaned.get("title") or "").strip()
        body = (cleaned.get("body") or "").strip()
        cta = (cleaned.get("cta_label") or "").strip()
        has_image = bool(image) or bool(self.instance and self.instance.pk and self.instance.image)
        has_content = bool(has_image or title or body or cta)
        if not has_content and self.empty_permitted:
            return cleaned
        return cleaned


class HeroSlideBaseFormSet(BaseModelFormSet):
    def clean(self):
        super().clean()
        order = 0
        for form in self.forms:
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue
            image = form.cleaned_data.get("image")
            title = (form.cleaned_data.get("title") or "").strip()
            body = (form.cleaned_data.get("body") or "").strip()
            if not image and not title and not body and not form.cleaned_data.get(
                "cta_label"
            ):
                continue
            form.cleaned_data["sort_order"] = order
            form.instance.sort_order = order
            order += 1


def build_hero_slide_formset(data=None, files=None):
    ensure_default_hero_slides()
    FormSet = modelformset_factory(
        HeroSlide,
        form=HeroSlideForm,
        formset=HeroSlideBaseFormSet,
        extra=1,
        can_delete=True,
    )
    queryset = HeroSlide.objects.order_by("sort_order", "pk")
    return FormSet(data=data, files=files, queryset=queryset, prefix="hero_slides")
