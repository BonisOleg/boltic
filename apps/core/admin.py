from django import forms
from django.contrib import admin

from .models import SiteSettings

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


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    form = SiteSettingsForm
    list_display = ("site_name", "phone", "email", "color_primary")
    fieldsets = (
        (
            "Загальне",
            {
                "fields": (
                    "site_name",
                    "phone",
                    "email",
                    "address",
                    "order_hours",
                    "processing_hours",
                    "social_json",
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

    def has_add_permission(self, request) -> bool:
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
