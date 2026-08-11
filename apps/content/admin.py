from django.contrib import admin
from unfold.admin import ModelAdmin

from apps.core.admin_utils import TinyMCEAdminMixin
from .models import ContactBranch, NewsPost, Promotion, StaticPage


@admin.register(Promotion)
class PromotionAdmin(TinyMCEAdminMixin, ModelAdmin):
    list_display = ("title", "slug", "is_published", "starts_at", "ends_at")
    list_filter = ("is_published",)
    list_filter_submit = True
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("groups",)
    tinymce_fields = ("body",)


@admin.register(NewsPost)
class NewsPostAdmin(TinyMCEAdminMixin, ModelAdmin):
    list_display = ("title", "slug", "is_published", "published_at")
    list_filter = ("is_published",)
    list_filter_submit = True
    prepopulated_fields = {"slug": ("title",)}
    tinymce_fields = ("body",)


@admin.register(StaticPage)
class StaticPageAdmin(TinyMCEAdminMixin, ModelAdmin):
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    tinymce_fields = ("body",)
    search_fields = ("title", "slug")


@admin.register(ContactBranch)
class ContactBranchAdmin(ModelAdmin):
    list_display = ("name", "phone", "is_active", "sort_order")
    list_filter = ("is_active",)
    list_filter_submit = True
