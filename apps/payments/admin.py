from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(ModelAdmin):
    list_display = (
        "id",
        "order",
        "provider",
        "status",
        "amount",
        "currency",
        "external_id",
        "created_at",
    )
    list_filter = ("provider", "status")
    list_filter_submit = True
    search_fields = ("order__number", "external_id")
    readonly_fields = ("raw_request", "raw_response", "created_at", "updated_at")
