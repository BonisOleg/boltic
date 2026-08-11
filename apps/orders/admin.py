from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Order, OrderItem


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
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
class OrderAdmin(ModelAdmin):
    list_display = (
        "number",
        "customer_name",
        "phone",
        "shipping_method",
        "status",
        "payment_status",
        "total",
        "created_at",
    )
    list_filter = ("status", "payment_status", "shipping_method")
    list_filter_submit = True
    search_fields = (
        "number",
        "customer_name",
        "phone",
        "email",
        "np_city",
        "np_warehouse",
    )
    readonly_fields = ("access_token", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "number",
                    "access_token",
                    "user",
                    "status",
                    "payment_status",
                    "total",
                )
            },
        ),
        (
            "Клієнт",
            {"fields": ("customer_name", "phone", "email", "comment")},
        ),
        (
            "Доставка",
            {
                "fields": (
                    "shipping_method",
                    "shipping_address",
                    "np_delivery_type",
                    "np_city",
                    "np_city_ref",
                    "np_warehouse",
                    "np_warehouse_ref",
                )
            },
        ),
        ("Службове", {"fields": ("created_at", "updated_at")}),
    )
    inlines = [OrderItemInline]
