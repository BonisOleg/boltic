"""Експорт повного дампу каталогу."""

from __future__ import annotations

from typing import Any, Iterable

from apps.catalog.io_formats import write_file
from apps.catalog.io_schema import FULL_DUMP_FIELDS
from apps.catalog.models import ProductSKU


def sku_to_row(sku: ProductSKU) -> dict[str, Any]:
    group = sku.group
    category = group.category
    parent = category.parent if category else None
    brand = group.brand
    return {
        "article": sku.article,
        "name": sku.name,
        "size_label": sku.size_label,
        "diameter": sku.diameter,
        "length": sku.length,
        "thread_pitch": sku.thread_pitch,
        "strength_class": sku.strength_class,
        "min_party": sku.min_party,
        "stock_status": sku.stock_status,
        "stock_qty": sku.stock_qty,
        "price": sku.price,
        "price_includes_vat": sku.price_includes_vat,
        "vat_rate": sku.vat_rate,
        "party_price": sku.party_price,
        "is_active": sku.is_active,
        "group_name": group.name,
        "group_slug": group.slug,
        "group_standard": group.standard,
        "group_material": group.material,
        "group_coating": group.coating,
        "group_industry": group.industry,
        "group_short_description": group.short_description,
        "group_description": group.description,
        "group_is_top": group.is_top,
        "group_is_promo": group.is_promo,
        "group_is_active": group.is_active,
        "group_seo_title": group.seo_title,
        "group_seo_description": group.seo_description,
        "brand_slug": brand.slug if brand else "",
        "brand_name": brand.name if brand else "",
        "category_l1_slug": parent.slug if parent else "",
        "category_l1_name": parent.name if parent else "",
        "category_l2_slug": category.slug if category else "",
        "category_l2_name": category.name if category else "",
        "barcode": "",
    }


def iter_export_rows(queryset: Iterable[ProductSKU] | None = None) -> list[dict[str, Any]]:
    if queryset is None:
        queryset = (
            ProductSKU.objects.select_related(
                "group",
                "group__brand",
                "group__category",
                "group__category__parent",
            )
            .order_by("article")
            .iterator(chunk_size=500)
        )
    return [sku_to_row(sku) for sku in queryset]


def export_catalog(fmt: str) -> tuple[bytes, str, str]:
    rows = iter_export_rows()
    return write_file(fmt, rows)


def empty_template_rows() -> list[dict[str, Any]]:
    return [{f: "" for f in FULL_DUMP_FIELDS}]
