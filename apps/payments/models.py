from django.db import models

from apps.orders.models import Order


class PaymentTransaction(models.Model):
    class Provider(models.TextChoices):
        LIQPAY = "liqpay", "LiqPay"

    class Status(models.TextChoices):
        CREATED = "created", "Створено"
        REDIRECTED = "redirected", "Перенаправлено"
        SUCCESS = "success", "Успіх"
        FAILURE = "failure", "Помилка"
        REFUNDED = "refunded", "Повернення"

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Замовлення",
    )
    provider = models.CharField(
        "Провайдер",
        max_length=16,
        choices=Provider.choices,
        default=Provider.LIQPAY,
    )
    status = models.CharField(
        "Статус",
        max_length=16,
        choices=Status.choices,
        default=Status.CREATED,
    )
    amount = models.DecimalField("Сума", max_digits=12, decimal_places=2)
    currency = models.CharField("Валюта", max_length=3, default="UAH")
    external_id = models.CharField(
        "External ID", max_length=128, blank=True, db_index=True
    )
    raw_request = models.JSONField("Request", default=dict, blank=True)
    raw_response = models.JSONField("Response", default=dict, blank=True)
    idempotency_key = models.CharField(
        "Idempotency key",
        max_length=128,
        blank=True,
        null=True,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Платіжна транзакція"
        verbose_name_plural = "Платіжні транзакції"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["order", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.provider} · {self.order.number} · {self.status}"
