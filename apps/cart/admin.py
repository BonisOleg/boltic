from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Cart, CartItem, WishlistItem


class CartItemInline(TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ("id", "user", "session_key", "updated_at")
    search_fields = ("session_key", "user__username")
    inlines = [CartItemInline]


@admin.register(WishlistItem)
class WishlistItemAdmin(ModelAdmin):
    list_display = ("user", "sku", "created_at")
    search_fields = ("user__username", "sku__article")
