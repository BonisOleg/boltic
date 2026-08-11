from django import forms
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from apps.core.admin_guidelines import get_image_hint
from apps.core.admin_site_content_proxies import register_site_content_section_admins
from apps.core.admin_utils import (
    ReadableUnfoldFieldsMixin,
    SingletonModelAdminMixin,
)
from apps.core.models import SiteSettings

COLOR_FIELDS = [
    "color_primary",
    "color_primary_dark",
    "color_secondary",
    "color_accent",
    "color_bg",
    "color_surface",
    "color_text",
    "color_text_muted",
    "color_header_bg",
    "color_header_top_bg",
    "color_header_top_text",
    "color_logo_bg",
    "color_catalog_btn",
    "color_catalog_btn_text",
    "color_link",
    "color_success",
    "color_danger",
    "color_border",
]


class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in COLOR_FIELDS:
            if name in self.fields:
                self.fields[name].widget = forms.TextInput(
                    attrs={"type": "color", "style": "width:4rem;height:2.2rem;padding:0"}
                )
        if "logo" in self.fields:
            self.fields["logo"].help_text = get_image_hint("brand")
        if "favicon" in self.fields:
            self.fields["favicon"].help_text = "ICO або PNG 32×32 / 48×48"


@admin.register(SiteSettings)
class SiteSettingsAdmin(
    ReadableUnfoldFieldsMixin, SingletonModelAdminMixin, ModelAdmin
):
    form = SiteSettingsForm
    list_display = ("site_name", "phone", "email", "color_primary")
    readonly_fields = ("logo_preview", "favicon_preview")
    fieldsets = (
        (
            "Загальне",
            {
                "fields": (
                    "site_name",
                    "phone",
                    "email",
                    "orders_email",
                    "address",
                    "order_hours",
                    "processing_hours",
                    "social_json",
                    "meta_description",
                )
            },
        ),
        (
            "Доставка",
            {
                "fields": (
                    "pickup_enabled",
                    "pickup_description",
                )
            },
        ),
        (
            "Бренд",
            {
                "fields": (
                    "logo",
                    "logo_preview",
                    "favicon",
                    "favicon_preview",
                )
            },
        ),
        (
            "Кольори теми",
            {
                "description": "Змінюйте палітру сайту. Primary — основний зелений.",
                "fields": COLOR_FIELDS,
            },
        ),
    )

    @admin.display(description="Превʼю логотипу")
    def logo_preview(self, obj):
        if obj and obj.logo:
            return format_html(
                '<img src="{}" alt="" style="max-height:64px">', obj.logo.url
            )
        return "—"

    @admin.display(description="Превʼю favicon")
    def favicon_preview(self, obj):
        if obj and obj.favicon:
            return format_html(
                '<img src="{}" alt="" style="max-height:32px">', obj.favicon.url
            )
        return "—"


register_site_content_section_admins()
