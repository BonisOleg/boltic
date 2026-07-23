from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("group", "user", "rating", "is_published", "created_at")
    list_filter = ("is_published", "rating")
    search_fields = ("body", "group__name", "user__username")
