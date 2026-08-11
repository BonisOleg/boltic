from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Review


@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ("group", "user", "rating", "is_published", "created_at")
    list_filter = ("is_published", "rating")
    list_filter_submit = True
    search_fields = ("body", "group__name", "user__username")
