"""Upsert SKU з рядків формату goods.xlsx."""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Callable

from django.db import transaction
from django.utils.text import slugify

from apps.catalog.classification import resolve_goods_category
from apps.catalog.goods_xlsx import ParsedGoodsRow, iter_goods_rows, match_key
from apps.catalog.import_parser import parse_group_meta
from apps.catalog.metric_size import canonical_size_key
from apps.catalog.models import Category, ProductGroup, ProductSKU


LogFn = Callable[[str], None]


def import_goods_dicts(
    rows: list[dict],
    *,
    apply: bool = True,
    log: LogFn | None = None,
) -> dict[str, int]:
    """Імпорт зі словників (після read_tabular_file для goods)."""
    tuples = []
    for row in rows:
        tuples.append(
            (
                row.get("name"),
                row.get("code"),
                row.get("group_name"),
                row.get("barcode"),
                None,
                None,
                row.get("price"),
                None,
                None,
                None,
                row.get("stock_qty"),
            )
        )
    parsed = iter_goods_rows(tuples)
    return import_goods_parsed(parsed, apply=apply, log=log)


def import_goods_parsed(
    parsed: list[ParsedGoodsRow],
    *,
    apply: bool = True,
    log: LogFn | None = None,
) -> dict[str, int]:
    stats = {
        "total": len(parsed),
        "created": 0,
        "updated_article": 0,
        "updated_fuzzy": 0,
        "category_fixed": 0,
        "group_moved": 0,
        "price_set": 0,
        "zero_stock": 0,
        "errors": 0,
    }
    if not parsed:
        return stats

    def _run() -> None:
        _GoodsImporter(stats, apply=apply, log=log).run(parsed)

    if apply:
        with transaction.atomic():
            _run()
        from apps.catalog.facet_sync import sync_facets_from_skus

        sync_facets_from_skus()
    else:
        _run()
    return stats


class _GoodsImporter:
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
        self.groups_by_slug: dict[str, ProductGroup] = {
            g.slug: g for g in ProductGroup.objects.select_related("category")
        }
        self.skus_by_article = {
            s.article: s
            for s in ProductSKU.objects.select_related("group", "group__category")
        }
        self.fuzzy_index: dict[tuple[str, str, str], list[ProductSKU]] = {}
        for sku in self.skus_by_article.values():
            size = canonical_size_key(sku.size_label)
            din = ""
            std = sku.group.standard or ""
            m = re.search(
                r"DIN\s*(\d+)",
                f"{std} {sku.group.name} {sku.name}",
                re.I,
            )
            if m:
                din = m.group(1)
            cls = (sku.strength_class or "").replace(",", ".")
            if size:
                self.fuzzy_index.setdefault(match_key(size, din, cls), []).append(sku)
                self.fuzzy_index.setdefault(match_key(size, din, ""), []).append(sku)
        self.claimed_ids: set[int] = set()

    def run(self, parsed: list[ParsedGoodsRow]) -> None:
        for row in parsed:
            try:
                self._process_row(row)
            except Exception as exc:  # noqa: BLE001
                self.stats["errors"] += 1
                self.log(f"Рядок {row.row_num} [{row.code}]: {exc}")

    def _process_row(self, row: ParsedGoodsRow) -> None:
        category = self._resolve_category(row.group_name, row.name)
        group = self._ensure_group(category, row.group_name)
        sku, how = self._find_sku(row)
        stock_status = (
            ProductSKU.StockStatus.IN_STOCK
            if row.stock_qty > 0
            else ProductSKU.StockStatus.ON_ORDER
        )
        if row.stock_qty == 0:
            self.stats["zero_stock"] += 1

        defaults = {
            "group": group,
            "name": row.name,
            "size_label": row.size_label,
            "diameter": row.diameter,
            "length": row.length,
            "thread_pitch": row.thread_pitch,
            "strength_class": row.strength_class,
            "price": row.price,
            "price_includes_vat": True,
            "vat_rate": Decimal("20.00"),
            "stock_qty": row.stock_qty,
            "stock_status": stock_status,
            "is_active": True,
        }

        if sku is None:
            if self.apply:
                sku = ProductSKU.objects.create(article=row.code, **defaults)
                self.skus_by_article[row.code] = sku
            self.stats["created"] += 1
            self.stats["price_set"] += 1
            return

        self.claimed_ids.add(sku.pk)
        old_group_id = sku.group_id
        old_cat_id = sku.group.category_id
        old_article = sku.article

        if self.apply:
            sku.group = group
            sku.name = defaults["name"]
            if row.size_label and row.size_label != "—":
                sku.size_label = row.size_label
                sku.diameter = row.diameter
                sku.length = row.length
                sku.thread_pitch = row.thread_pitch
            if row.strength_class:
                sku.strength_class = row.strength_class
            sku.price = row.price
            sku.stock_qty = row.stock_qty
            sku.stock_status = stock_status
            sku.is_active = True
            sku.price_includes_vat = True
            if sku.article != row.code:
                if (
                    row.code in self.skus_by_article
                    and self.skus_by_article[row.code].pk != sku.pk
                ):
                    raise ValueError(f"Конфлікт артикула {row.code}")
                self.skus_by_article.pop(old_article, None)
                sku.article = row.code
            sku.save()
            self.skus_by_article[row.code] = sku
            sku.group = group

        self.stats["price_set"] += 1
        if how == "article":
            self.stats["updated_article"] += 1
        else:
            self.stats["updated_fuzzy"] += 1
        if old_group_id != group.id:
            self.stats["group_moved"] += 1
        if old_cat_id != group.category_id:
            self.stats["category_fixed"] += 1

    def _resolve_category(self, group_name: str, product_name: str) -> Category:
        l1_slug, l2_slug = resolve_goods_category(group_name, product_name)
        cat = self.categories.get((l1_slug, l2_slug))
        if cat is None:
            raise ValueError(f"Немає категорії {l1_slug}/{l2_slug} для «{group_name}»")
        return cat

    def _ensure_group(self, category: Category, group_name: str) -> ProductGroup:
        meta = parse_group_meta(group_name)
        base_slug = slugify(group_name, allow_unicode=True)[:200] or "group"
        slug = base_slug
        group = self.groups_by_slug.get(slug)
        if group is None:
            for g in self.groups_by_slug.values():
                if g.name == group_name:
                    group = g
                    slug = g.slug
                    break

        if group is None:
            if not self.apply:
                group = ProductGroup(
                    category=category,
                    name=group_name,
                    slug=slug,
                    standard=meta.get("standard") or "",
                    material=meta.get("material") or "",
                )
                self.groups_by_slug[slug] = group
                return group
            group = ProductGroup.objects.create(
                category=category,
                name=group_name,
                slug=slug,
                standard=meta.get("standard") or "",
                material=meta.get("material") or "",
                short_description=group_name,
                is_active=True,
            )
            self.groups_by_slug[slug] = group
            return group

        if self.apply and (
            group.category_id != category.id
            or group.name != group_name
            or (meta.get("standard") and group.standard != meta["standard"])
        ):
            group.category = category
            group.name = group_name
            if meta.get("standard"):
                group.standard = meta["standard"]
            if meta.get("material"):
                group.material = meta["material"]
            group.is_active = True
            group.save()
        elif not self.apply:
            group.category = category
        return group

    def _find_sku(self, row: ParsedGoodsRow) -> tuple[ProductSKU | None, str]:
        sku = self.skus_by_article.get(row.code)
        if sku is not None and sku.pk not in self.claimed_ids:
            return sku, "article"
        if not row.size_label or row.size_label == "—":
            return None, ""
        keys = [match_key(row.size_label, row.din, row.strength_class)]
        if row.strength_class:
            keys.append(match_key(row.size_label, row.din, ""))
        for key in keys:
            candidates = [
                s for s in self.fuzzy_index.get(key, []) if s.pk not in self.claimed_ids
            ]
            uniq = {s.pk: s for s in candidates}
            if len(uniq) == 1:
                return next(iter(uniq.values())), "fuzzy"
        return None, ""
