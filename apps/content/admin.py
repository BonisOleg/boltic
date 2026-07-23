from django.contrib import admin

from .models import ContactBranch, HomeBlock, NewsPost, Promotion, StaticPage


@admin.register(HomeBlock)
class HomeBlockAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "is_active", "sort_order")
    list_filter = ("is_active",)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "starts_at", "ends_at")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("groups",)


@admin.register(NewsPost)
class NewsPostAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published", "published_at")
    list_filter = ("is_published",)
    prepopulated_fields = {"slug": ("title",)}


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(ContactBranch)
class ContactBranchAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "is_active", "sort_order")
    list_filter = ("is_active",)
