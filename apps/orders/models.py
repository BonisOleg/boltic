import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import ProductSKU


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "Нове"
        PAID = "paid", "Оплачене"
        PROCESSING = "processing", "В обробці"
        SHIPPED = "shipped", "Відправлене"
        DONE = "done", "Виконане"
        CANCELED = "canceled", "Скасоване"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Очікує"
        PAID = "paid", "Оплачено"
        FAILED = "failed", "Помилка"

    number = models.CharField("Номер", max_length=32, unique=True, db_index=True)
    access_token = models.UUIDField(
        "Токен доступу",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
        verbose_name="Користувач",
    )
    status = models.CharField(
        "Статус", max_length=16, choices=Status.choices, default=Status.NEW
    )
    payment_status = models.CharField(
        "Оплата",
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    customer_name = models.CharField("Імʼя", max_length=255)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email", blank=True)
    shipping_method = models.CharField("Доставка", max_length=128, blank=True)
    shipping_address = models.TextField("Адреса", blank=True)
    comment = models.TextField("Коментар", blank=True)
    total = models.DecimalField("Сума", max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self) -> str:
        return self.number


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Замовлення",
    )
    sku = models.ForeignKey(
        ProductSKU,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="SKU",
    )
    article = models.CharField("Артикул", max_length=64)
    name = models.CharField("Назва", max_length=255)
    size_label = models.CharField("Розмір", max_length=64)
    unit_price = models.DecimalField("Ціна/шт", max_digits=12, decimal_places=2)
    vat_rate = models.DecimalField("ПДВ %", max_digits=5, decimal_places=2, default=20)
    price_includes_vat = models.BooleanField("З ПДВ", default=True)
    quantity = models.PositiveIntegerField("Кількість")
    line_total = models.DecimalField("Сума рядка", max_digits=12, decimal_places=2)

    class Meta:
        verbose_name = "Позиція замовлення"
        verbose_name_plural = "Позиції замовлення"

    def __str__(self) -> str:
        return f"{self.article} × {self.quantity}"
