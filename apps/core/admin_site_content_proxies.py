"""Динамічна реєстрація proxy ModelAdmin для CMS-секцій."""

from __future__ import annotations

from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core import cms_proxies
from apps.core.admin_site_content import site_content_section_view
from apps.core.admin_utils import SingletonModelAdminMixin

_SECTION_MODELS = (
    (cms_proxies.HomeHeroSettings, "home", "hero"),
    (cms_proxies.HomeAdvantagesSettings, "home", "advantages"),
    (cms_proxies.HomeCatalogSettings, "home", "catalog"),
    (cms_proxies.HomePromoSettings, "home", "promo"),
    (cms_proxies.HomeTopsSettings, "home", "tops"),
    (cms_proxies.HomeNewsSettings, "home", "news"),
    (cms_proxies.HomeSeoSettings, "home", "seo"),
    (cms_proxies.HomeServicesSettings, "home", "services"),
    (cms_proxies.SiteHeaderSettings, "site", "header"),
    (cms_proxies.SiteFooterSettings, "site", "footer"),
    (cms_proxies.ContactsPageSettings, "contacts", "contacts"),
)


class SiteContentSectionAdmin(SingletonModelAdminMixin, ModelAdmin):
    page_slug: str = ""
    section_slug: str = ""

    def change_view(self, request, object_id, form_url="", extra_context=None):
        return site_content_section_view(
            request,
            self.page_slug,
            self.section_slug,
            model_admin=self,
        )


def register_site_content_section_admins() -> None:
    for model, page_slug, section_slug in _SECTION_MODELS:
        if model in admin.site._registry:
            continue

        admin_class = type(
            f"{model.__name__}Admin",
            (SiteContentSectionAdmin,),
            {
                "page_slug": page_slug,
                "section_slug": section_slug,
            },
        )
        admin.site.register(model, admin_class)
