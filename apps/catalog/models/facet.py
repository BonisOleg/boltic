from django.db import models
from django.utils.text import slugify

from .product import ProductSKU


class FacetAttribute(models.Model):
    """Атрибут фільтра (?material=…&diametr=…)."""

    code = models.SlugField("Код", max_length=64, unique=True)
    name = models.CharField("Назва", max_length=128)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Атрибут фільтра"
        verbose_name_plural = "Атрибути фільтрів"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class FacetValue(models.Model):
    attribute = models.ForeignKey(
        FacetAttribute,
        on_delete=models.CASCADE,
        related_name="values",
        verbose_name="Атрибут",
    )
    value = models.CharField("Значення", max_length=128)
    slug = models.SlugField("Slug", max_length=128, allow_unicode=True)
    sort_order = models.PositiveIntegerField("Порядок", default=0)

    class Meta:
        verbose_name = "Значення фільтра"
        verbose_name_plural = "Значення фільтрів"
        ordering = ["sort_order", "value"]
        constraints = [
            models.UniqueConstraint(
                fields=["attribute", "slug"],
                name="catalog_facetvalue_attr_slug_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.attribute.code}={self.value}"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(self.value, allow_unicode=True)
        super().save(*args, **kwargs)


class SKUFacet(models.Model):
    sku = models.ForeignKey(
        ProductSKU,
        on_delete=models.CASCADE,
        related_name="facets",
        verbose_name="SKU",
    )
    value = models.ForeignKey(
        FacetValue,
        on_delete=models.CASCADE,
        related_name="sku_links",
        verbose_name="Значення",
    )

    class Meta:
        verbose_name = "Facet SKU"
        verbose_name_plural = "Facets SKU"
        constraints = [
            models.UniqueConstraint(
                fields=["sku", "value"],
                name="catalog_skufacet_sku_value_uniq",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.sku.article} → {self.value}"
