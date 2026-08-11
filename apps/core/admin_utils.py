"""Mixins для Unfold admin."""

from __future__ import annotations

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from apps.core.admin_site_content_widgets import apply_readable_widget


class SingletonModelAdminMixin:
    def has_add_permission(self, request) -> bool:
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        opts = self.model._meta
        return HttpResponseRedirect(
            reverse(f"admin:{opts.app_label}_{opts.model_name}_change", args=[obj.pk])
        )


class ReadableUnfoldFieldsMixin:
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if formfield is not None:
            apply_readable_widget(formfield.widget)
        return formfield


class TinyMCEAdminMixin:
    tinymce_fields: tuple[str, ...] = ()

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name in self.tinymce_fields:
            from tinymce.widgets import TinyMCE

            kwargs["widget"] = TinyMCE()
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class ImagePreviewMixin:
    def get_image_preview(self, obj, field_name: str = "image", height: int = 80):
        image = getattr(obj, field_name, None)
        if not image:
            return "—"
        try:
            url = image.url
        except ValueError:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="max-height:{}px;border-radius:4px">',
            url,
            height,
        )
