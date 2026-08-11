"""Імпорт каталогу: goods.xlsx або повний дамп."""

from __future__ import annotations

from typing import Any, Callable

from django.db import transaction
from django.utils.text import slugify

from apps.catalog.classification import resolve_goods_category
from apps.catalog.io_formats import CatalogIOError, read_tabular_file
from apps.catalog.io_goods_import import import_goods_dicts
from apps.catalog.io_schema import parse_full_row
from apps.catalog.models import Brand, Category, ProductGroup, ProductSKU


LogFn = Callable[[str], None]


def import_catalog_file(
    filename: str,
    content: bytes,
    *,
    apply: bool = True,
    log: LogFn | None = None,
) -> tuple[str, dict[str, int]]:
    """
    Повертає (format_id, stats).
    format_id: 'goods' | 'full'
    """
    fmt, rows = read_tabular_file(filename, content)
    if fmt == "goods":
        stats = import_goods_dicts(rows, apply=apply, log=log)
        return fmt, stats
    stats = import_full_dicts(rows, apply=apply, log=log)
    return fmt, stats


def import_full_dicts(
    rows: list[dict[str, Any]],
    *,
    apply: bool = True,
    log: LogFn | None = None,
) -> dict[str, int]:
    stats = {
        "total": 0,
        "created": 0,
        "updated": 0,
        "errors": 0,
        "groups_created": 0,
    }
    parsed_rows = []
    for i, raw in enumerate(rows, start=2):
        row = parse_full_row(raw)
        if not row["article"]:
            continue
        row["_row_num"] = i
        parsed_rows.append(row)
    stats["total"] = len(parsed_rows)
    if not parsed_rows:
        raise CatalogIOError("У файлі немає рядків з артикулом (article)")

    def _run() -> None:
        _FullImporter(stats, apply=apply, log=log).run(parsed_rows)

    if apply:
        with transaction.atomic():
            _run()
        from apps.catalog.facet_sync import sync_facets_from_skus

        sync_facets_from_skus()
    else:
        _run()
    return stats


class _FullImporter:
    def __init__(self, stats: dict[str, int], *, apply: bool, log: LogFn | None):
        self.stats = stats
        self.apply = apply
        self.log = log or (lambda _m: None)
        self.categories = {
            (c.parent.slug, c.slug): c
            for c in Category.objects.filter(level=Category.Level.L2).select_related(
                "parent"
            )
            if c.parent_id
        }
        self.groups_by_slug = {
            g.slug: g for g in ProductGroup.objects.select_related("category", "brand")
        }
        self.groups_by_name = {g.name: g for g in self.groups_by_slug.values()}
        self.skus_by_article = {
            s.article: s
            for s in ProductSKU.objects.select_related("group", "group__category")
        }
        self.brands_by_slug = {b.slug: b for b in Brand.objects.all()}

    def run(self, rows: list[dict[str, Any]]) -> None:
        for row in rows:
            try:
                self._process(row)
            except Exception as exc:  # noqa: BLE001
                self.stats["errors"] += 1
                self.log(f"Рядок {row.get('_row_num')} [{row.get('article')}]: {exc}")

    def _process(self, row: dict[str, Any]) -> None:
        category = self._resolve_category(row)
        brand = self._resolve_brand(row)
        group = self._ensure_group(row, category, brand)
        article = row["article"]
        sku = self.skus_by_article.get(article)
        status = row["stock_status"]
        if status not in ProductSKU.StockStatus.values:
            status = (
                ProductSKU.StockStatus.IN_STOCK
                if (row["stock_qty"] or 0) > 0
                else ProductSKU.StockStatus.ON_ORDER
            )

        fields = {
            "group": group,
            "name": row["name"],
            "size_label": row["size_label"] or "—",
            "diameter": row["diameter"],
            "length": row["length"],
            "thread_pitch": row["thread_pitch"],
            "strength_class": row["strength_class"],
            "min_party": row["min_party"],
            "stock_status": status,
            "stock_qty": row["stock_qty"],
            "price": row["price"],
            "price_includes_vat": row["price_includes_vat"],
            "vat_rate": row["vat_rate"],
            "party_price": row["party_price"],
            "is_active": row["is_active"],
        }

        if sku is None:
            if self.apply:
                sku = ProductSKU.objects.create(article=article, **fields)
                self.skus_by_article[article] = sku
            self.stats["created"] += 1
            return

        if self.apply:
            for key, value in fields.items():
                setattr(sku, key, value)
            sku.save()
        self.stats["updated"] += 1

    def _resolve_category(self, row: dict[str, Any]) -> Category:
        l1 = row["category_l1_slug"]
        l2 = row["category_l2_slug"]
        if l1 and l2:
            cat = self.categories.get((l1, l2))
            if cat is not None:
                return cat
        group_name = row["group_name"] or row["name"]
        l1_slug, l2_slug = resolve_goods_category(group_name, row["name"])
        cat = self.categories.get((l1_slug, l2_slug))
        if cat is None:
            raise ValueError(f"Немає категорії {l1_slug}/{l2_slug}")
        return cat

    def _resolve_brand(self, row: dict[str, Any]) -> Brand | None:
        slug = row["brand_slug"]
        name = row["brand_name"]
        if slug and slug in self.brands_by_slug:
            return self.brands_by_slug[slug]
        if not name:
            return None
        slug = slug or slugify(name, allow_unicode=True)[:200]
        brand = self.brands_by_slug.get(slug)
        if brand is not None:
            return brand
        if not self.apply:
            brand = Brand(name=name, slug=slug, is_active=True)
            self.brands_by_slug[slug] = brand
            return brand
        brand, _ = Brand.objects.get_or_create(
            slug=slug, defaults={"name": name, "is_active": True}
        )
        self.brands_by_slug[slug] = brand
        return brand

    def _ensure_group(
        self,
        row: dict[str, Any],
        category: Category,
        brand: Brand | None,
    ) -> ProductGroup:
        name = row["group_name"] or row["name"]
        slug = row["group_slug"] or slugify(name, allow_unicode=True)[:200] or "group"
        group = self.groups_by_slug.get(slug) or self.groups_by_name.get(name)

        defaults = {
            "category": category,
            "brand": brand,
            "name": name,
            "standard": row["group_standard"],
            "material": row["group_material"],
            "coating": row["group_coating"],
            "industry": row["group_industry"],
            "short_description": row["group_short_description"] or name,
            "description": row["group_description"],
            "is_top": row["group_is_top"],
            "is_promo": row["group_is_promo"],
            "is_active": row["group_is_active"],
            "seo_title": row["group_seo_title"],
            "seo_description": row["group_seo_description"],
        }

        if group is None:
            if not self.apply:
                group = ProductGroup(slug=slug, **defaults)
                self.groups_by_slug[slug] = group
                self.groups_by_name[name] = group
                self.stats["groups_created"] += 1
                return group
            group = ProductGroup.objects.create(slug=slug, **defaults)
            self.groups_by_slug[slug] = group
            self.groups_by_name[name] = group
            self.stats["groups_created"] += 1
            return group

        if self.apply:
            for key, value in defaults.items():
                setattr(group, key, value)
            group.save()
        return group
