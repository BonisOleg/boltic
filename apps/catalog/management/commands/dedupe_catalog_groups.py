"""Зливає дублікати DOCX ↔ goods.xlsx: залишає goods-групу з реальними цінами."""

from __future__ import annotations

from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.goods_xlsx import normalize_size_label
from apps.catalog.models import ProductGroup


# (id_docx_дубля, id_канонічної_goods_групи)
MERGE_PAIRS: list[tuple[int, int]] = [
    (7, 30),   # DIN 931 10.9
    (8, 35),   # DIN 931 12.9
    (2, 37),   # DIN 933 5.8
    (3, 38),   # DIN 933 8.8
    (4, 31),   # DIN 933 10.9
    (5, 34),   # DIN 933 12.9
    (9, 32),   # DIN 961 10.9
    (10, 33),  # DIN 960 10.9
    (15, 56),  # DIN 912 8.8
    (18, 55),  # DIN 7991 10.9
    (11, 41),  # лемішний
    (12, 39),  # норійний
]

# Порожні DOCX-групи без сенсу лишати
DELETE_EMPTY_IDS: list[int] = [
    14,  # Болт меблевий 8,8 к.м. — 0 SKU
]


def _size_key(label: str) -> str:
    """M8×1×40 і M8×40 → один ключ M8×40 (діаметр × довжина)."""
    norm = normalize_size_label(label or "")
    if not norm:
        return ""
    parts = norm.split("×")
    if len(parts) >= 2:
        return f"{parts[0]}×{parts[-1]}"
    return norm


class Command(BaseCommand):
    help = "Прибрати дублікати груп DOCX/goods: злити в goods, перенести прапорці"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише звіт без змін у БД",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        stats = {
            "merged_pairs": 0,
            "skus_moved": 0,
            "skus_dropped": 0,
            "groups_deleted": 0,
            "flags_copied": 0,
        }

        if dry:
            self._run(stats, apply=False)
        else:
            with transaction.atomic():
                self._run(stats, apply=True)
            from apps.catalog.facet_sync import sync_facets_from_skus

            facet_stats = sync_facets_from_skus()
            self.stdout.write(
                f"Фасети: values={facet_stats['values']} "
                f"links={facet_stats['sku_links']}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"{'DRY-RUN ' if dry else ''}Готово: "
                f"pairs={stats['merged_pairs']} "
                f"skus_moved={stats['skus_moved']} "
                f"skus_dropped={stats['skus_dropped']} "
                f"groups_deleted={stats['groups_deleted']} "
                f"flags={stats['flags_copied']}"
            )
        )

    def _run(self, stats: dict, *, apply: bool) -> None:
        for dup_id, keep_id in MERGE_PAIRS:
            dup = ProductGroup.objects.filter(id=dup_id).first()
            keep = ProductGroup.objects.filter(id=keep_id).first()
            if dup is None and keep is None:
                self.stdout.write(f"skip {dup_id}→{keep_id}: обидві відсутні")
                continue
            if dup is None:
                self.stdout.write(f"skip {dup_id}→{keep_id}: дубль уже видалений")
                continue
            if keep is None:
                self.stderr.write(
                    self.style.WARNING(
                        f"skip {dup_id}→{keep_id}: немає канонічної групи"
                    )
                )
                continue

            self.stdout.write(
                f"merge #{dup.id} «{dup.name[:50]}» → "
                f"#{keep.id} «{keep.name[:50]}»"
            )
            self._merge_pair(dup, keep, stats, apply=apply)
            stats["merged_pairs"] += 1

        for gid in DELETE_EMPTY_IDS:
            g = ProductGroup.objects.filter(id=gid).first()
            if g is None:
                continue
            if g.skus.exists():
                self.stderr.write(
                    self.style.WARNING(
                        f"не видаляю #{gid}: є SKU ({g.skus.count()})"
                    )
                )
                continue
            self.stdout.write(f"delete empty #{gid} «{g.name[:60]}»")
            if apply:
                g.delete()
            stats["groups_deleted"] += 1

    def _merge_pair(
        self,
        dup: ProductGroup,
        keep: ProductGroup,
        stats: dict,
        *,
        apply: bool,
    ) -> None:
        keep_keys = {
            _size_key(label)
            for label in keep.skus.values_list("size_label", flat=True)
            if _size_key(label)
        }

        for sku in list(dup.skus.all()):
            key = _size_key(sku.size_label)
            if key and key in keep_keys:
                self.stdout.write(
                    f"  drop SKU {sku.article} ({sku.size_label}) — є в goods"
                )
                if apply:
                    sku.delete()
                stats["skus_dropped"] += 1
                continue

            # Placeholder DOCX-ціна без унікального розміру не переносимо як «товар»
            is_placeholder = (
                sku.article.startswith(("BLT-", "GVN-"))
                and sku.price == Decimal("10.00")
            )
            if is_placeholder and key and key in keep_keys:
                if apply:
                    sku.delete()
                stats["skus_dropped"] += 1
                continue

            self.stdout.write(
                f"  move SKU {sku.article} ({sku.size_label}) → #{keep.id}"
            )
            if apply:
                sku.group = keep
                sku.save(update_fields=["group", "updated_at"])
            stats["skus_moved"] += 1
            if key:
                keep_keys.add(key)

        # Прапорці з дубля на канонічну
        updates: list[str] = []
        if dup.is_promo and not keep.is_promo:
            keep.is_promo = True
            updates.append("is_promo")
        if dup.is_top and not keep.is_top:
            keep.is_top = True
            updates.append("is_top")
        # Доповнити стандарт / матеріал, якщо в goods порожньо
        if dup.standard and not keep.standard:
            keep.standard = dup.standard
            updates.append("standard")
        if dup.material and not keep.material:
            keep.material = dup.material
            updates.append("material")
        if updates:
            self.stdout.write(f"  flags/meta → {', '.join(updates)}")
            if apply:
                keep.save(update_fields=[*updates, "updated_at"])
            stats["flags_copied"] += 1

        # M2M акцій: перенести на keep
        promo_ids = list(dup.promotions.values_list("id", flat=True))
        if promo_ids and apply:
            keep.promotions.add(*promo_ids)

        if apply:
            dup.delete()
        stats["groups_deleted"] += 1
