from __future__ import annotations

import re
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.classification import resolve_goods_category
from apps.catalog.goods_xlsx import (
    iter_goods_rows,
    match_key,
    normalize_size_label,
)
from apps.catalog.import_parser import parse_group_meta
from apps.catalog.models import Category, ProductGroup, ProductSKU


class Command(BaseCommand):
    help = "Імпорт goods.xlsx: ціни, залишки, нові SKU, перевірка груп"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default="goods (1).xlsx",
            help="Шлях до xlsx",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише звіт без запису в БД",
        )

    def handle(self, *args, **options):
        try:
            import openpyxl
        except ImportError as exc:
            raise CommandError("Потрібен openpyxl: pip install openpyxl") from exc

        path = Path(options["file"]).resolve()
        if not path.exists():
            raise CommandError(f"Немає файлу: {path}")

        wb = openpyxl.load_workbook(path, data_only=True)
        if "Список товарів" not in wb.sheetnames:
            raise CommandError("Немає аркуша «Список товарів»")
        ws = wb["Список товарів"]
        parsed = iter_goods_rows(ws.iter_rows(min_row=2, values_only=True))
        if not parsed:
            raise CommandError("У файлі немає рядків товарів")

        dry = options["dry_run"]
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

        if dry:
            self._run(parsed, stats, apply=False)
        else:
            with transaction.atomic():
                self._run(parsed, stats, apply=True)
            from apps.catalog.facet_sync import sync_facets_from_skus

            facet_stats = sync_facets_from_skus()
            self.stdout.write(
                f"Фасети: values={facet_stats['values']} "
                f"links={facet_stats['sku_links']}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{'DRY-RUN ' if dry else ''}Готово: total={stats['total']} "
                f"created={stats['created']} "
                f"upd_article={stats['updated_article']} "
                f"upd_fuzzy={stats['updated_fuzzy']} "
                f"cat_fixed={stats['category_fixed']} "
                f"group_moved={stats['group_moved']} "
                f"prices={stats['price_set']} "
                f"zero_stock={stats['zero_stock']} "
                f"errors={stats['errors']}"
            )
        )
        if stats["total"] != (
            stats["created"] + stats["updated_article"] + stats["updated_fuzzy"]
        ):
            self.stderr.write(
                self.style.WARNING(
                    "Увага: сума create/update ≠ total — перевірте errors"
                )
            )

    def _run(self, parsed, stats, *, apply: bool) -> None:
        categories = {
            (c.parent.slug, c.slug): c
            for c in Category.objects.filter(level=Category.Level.L2).select_related(
                "parent"
            )
            if c.parent_id
        }
        groups_by_slug: dict[str, ProductGroup] = {
            g.slug: g for g in ProductGroup.objects.select_related("category")
        }
        skus_by_article = {
            s.article: s
            for s in ProductSKU.objects.select_related("group", "group__category")
        }

        fuzzy_index: dict[tuple[str, str, str], list[ProductSKU]] = {}
        for sku in skus_by_article.values():
            size = normalize_size_label(sku.size_label)
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
                fuzzy_index.setdefault(match_key(size, din, cls), []).append(sku)
                fuzzy_index.setdefault(match_key(size, din, ""), []).append(sku)

        claimed_ids: set[int] = set()

        for row in parsed:
            try:
                category = self._resolve_category(categories, row.group_name, row.name)
                group = self._ensure_group(
                    groups_by_slug, category, row.group_name, apply=apply
                )
                sku, how = self._find_sku(
                    row, skus_by_article, fuzzy_index, claimed_ids
                )
                stock_status = (
                    ProductSKU.StockStatus.IN_STOCK
                    if row.stock_qty > 0
                    else ProductSKU.StockStatus.ON_ORDER
                )
                if row.stock_qty == 0:
                    stats["zero_stock"] += 1

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
                    if apply:
                        sku = ProductSKU.objects.create(article=row.code, **defaults)
                        skus_by_article[row.code] = sku
                    stats["created"] += 1
                    stats["price_set"] += 1
                    continue

                claimed_ids.add(sku.pk)
                old_group_id = sku.group_id
                old_cat_id = sku.group.category_id
                old_article = sku.article

                if apply:
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
                        # звільнити артикул, якщо раптом зайнятий іншим
                        if (
                            row.code in skus_by_article
                            and skus_by_article[row.code].pk != sku.pk
                        ):
                            raise CommandError(
                                f"Конфлікт артикула {row.code} (рядок {row.row_num})"
                            )
                        skus_by_article.pop(old_article, None)
                        sku.article = row.code
                    sku.save()
                    skus_by_article[row.code] = sku
                    # оновити кеш group
                    sku.group = group

                stats["price_set"] += 1
                if how == "article":
                    stats["updated_article"] += 1
                else:
                    stats["updated_fuzzy"] += 1
                if old_group_id != group.id:
                    stats["group_moved"] += 1
                if old_cat_id != group.category_id:
                    stats["category_fixed"] += 1
            except Exception as exc:  # noqa: BLE001
                stats["errors"] += 1
                self.stderr.write(f"Рядок {row.row_num} [{row.code}]: {exc}")

    def _resolve_category(
        self,
        categories: dict[tuple[str, str], Category],
        group_name: str,
        product_name: str,
    ) -> Category:
        l1_slug, l2_slug = resolve_goods_category(group_name, product_name)
        cat = categories.get((l1_slug, l2_slug))
        if cat is None:
            raise CommandError(
                f"Немає категорії {l1_slug}/{l2_slug} для групи «{group_name}»"
            )
        return cat

    def _ensure_group(
        self,
        groups_by_slug: dict[str, ProductGroup],
        category: Category,
        group_name: str,
        *,
        apply: bool,
    ) -> ProductGroup:
        meta = parse_group_meta(group_name)
        base_slug = slugify(group_name, allow_unicode=True)[:200] or "group"
        slug = base_slug
        group = groups_by_slug.get(slug)
        if group is None:
            # можливий збіг зі старим slug DOCX — шукати за точним імʼям
            for g in groups_by_slug.values():
                if g.name == group_name:
                    group = g
                    slug = g.slug
                    break

        if group is None:
            if not apply:
                # фейковий обʼєкт для dry-run
                group = ProductGroup(
                    category=category,
                    name=group_name,
                    slug=slug,
                    standard=meta.get("standard") or "",
                    material=meta.get("material") or "",
                )
                groups_by_slug[slug] = group
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
            groups_by_slug[slug] = group
            return group

        if apply and (
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
        elif not apply:
            group.category = category
        return group

    def _find_sku(
        self,
        row,
        skus_by_article: dict[str, ProductSKU],
        fuzzy_index: dict,
        claimed_ids: set[int],
    ) -> tuple[ProductSKU | None, str]:
        sku = skus_by_article.get(row.code)
        if sku is not None and sku.pk not in claimed_ids:
            return sku, "article"

        if not row.size_label or row.size_label == "—":
            return None, ""

        keys = [
            match_key(row.size_label, row.din, row.strength_class),
        ]
        if row.strength_class:
            keys.append(match_key(row.size_label, row.din, ""))

        for key in keys:
            candidates = [
                s
                for s in fuzzy_index.get(key, [])
                if s.pk not in claimed_ids
            ]
            # унікальні pk
            uniq: dict[int, ProductSKU] = {s.pk: s for s in candidates}
            if len(uniq) == 1:
                return next(iter(uniq.values())), "fuzzy"
        return None, ""
