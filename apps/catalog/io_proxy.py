"""Proxy-модель для окремої admin-сторінки імпорту/експорту."""

from apps.catalog.models.product import ProductSKU


class CatalogImportExport(ProductSKU):
    class Meta:
        proxy = True
        verbose_name = "Імпорт / експорт"
        verbose_name_plural = "Імпорт / експорт"
