from django.contrib import admin

from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
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
    search_fields = ("order__number", "external_id")
    readonly_fields = ("raw_request", "raw_response", "created_at", "updated_at")
