from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.catalog.models import ProductSKU


class Cart(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts",
        verbose_name="Користувач",
    )
    session_key = models.CharField(
        "Session key", max_length=64, blank=True, db_index=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Кошик"
        verbose_name_plural = "Кошики"

    def __str__(self) -> str:
        owner = self.user_id or self.session_key or "?"
        return f"Cart #{self.pk} ({owner})"

    def clean(self) -> None:
        if not self.user_id and not self.session_key:
            raise ValidationError("Потрібен user або session_key.")


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Кошик",
    )
    sku = models.ForeignKey(
        ProductSKU,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="SKU",
    )
    quantity = models.PositiveIntegerField("Кількість", default=1)

    class Meta:
        verbose_name = "Позиція кошика"
        verbose_name_plural = "Позиції кошика"
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "sku"],
                name="cart_cartitem_cart_sku_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sku.article} × {self.quantity}"

    def clean(self) -> None:
        if not self.sku_id:
            return
        min_party = self.sku.min_party
        if self.quantity < min_party:
            raise ValidationError(
                {"quantity": f"Мін. партія: {min_party}."}
            )
        if self.quantity % min_party != 0:
            raise ValidationError(
                {"quantity": f"Кількість має бути кратна {min_party}."}
            )
        stock_qty = self.sku.stock_qty
        if stock_qty is not None and self.quantity > stock_qty:
            raise ValidationError(
                {"quantity": f"Доступно лише {stock_qty} шт."}
            )


class WishlistItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name="Користувач",
    )
    sku = models.ForeignKey(
        ProductSKU,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
        verbose_name="SKU",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Бажане"
        verbose_name_plural = "Бажане"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "sku"],
                name="cart_wishlist_user_sku_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} · {self.sku.article}"
