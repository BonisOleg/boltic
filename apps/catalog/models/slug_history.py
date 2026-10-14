from __future__ import annotations

from django.db import models


class ProductSlugHistory(models.Model):
    """Історія старих slug товарної групи для 301-редіректів."""

    old_slug = models.SlugField(
        "Старий slug",
        max_length=255,
        unique=True,
        allow_unicode=True,
    )
    product = models.ForeignKey(
        "catalog.ProductGroup",
        on_delete=models.CASCADE,
        related_name="slug_history",
        verbose_name="Товарна група",
    )
    created_at = models.DateTimeField("Створено", auto_now_add=True)

    class Meta:
        verbose_name = "Історія slug товару"
        verbose_name_plural = "Історія slug товарів"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.old_slug} → {self.product_id}"


def record_slug_change(*, product: models.Model, old_slug: str) -> None:
    """Записати старий slug; якщо новий slug уже в історії — видалити запис (без циклів)."""
    new_slug = product.slug
    if not old_slug or old_slug == new_slug:
        return
    ProductSlugHistory.objects.filter(old_slug=new_slug).delete()
    ProductSlugHistory.objects.update_or_create(
        old_slug=old_slug,
        defaults={"product": product},
    )


def lookup_product_by_old_slug(slug: str):
    """Повернути активну ProductGroup за записом історії або None."""
    from apps.catalog.models import ProductGroup

    hist = (
        ProductSlugHistory.objects.filter(old_slug=slug, product__is_active=True)
        .select_related("product")
        .first()
    )
    return hist.product if hist else None


def resolve_product_slug(slug: str) -> str | None:
    """Поточний slug: якщо slug актуальний або є в історії; інакше None."""
    from apps.catalog.models import ProductGroup

    if ProductGroup.objects.filter(slug=slug, is_active=True).exists():
        return slug
    product = lookup_product_by_old_slug(slug)
    return product.slug if product else None
