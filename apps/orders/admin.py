from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "article",
        "name",
        "size_label",
        "unit_price",
        "vat_rate",
        "price_includes_vat",
        "quantity",
        "line_total",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "number",
        "customer_name",
        "phone",
        "status",
        "payment_status",
        "total",
        "created_at",
    )
    list_filter = ("status", "payment_status")
    search_fields = ("number", "customer_name", "phone", "email")
    readonly_fields = ("access_token",)
    inlines = [OrderItemInline]
