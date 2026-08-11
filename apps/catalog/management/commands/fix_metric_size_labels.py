"""Прибрати зайвий префікс M з неметричних розмірів і перезібрати фасети."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.facet_sync import sync_facets_from_skus
from apps.catalog.metric_size import (
    group_uses_metric_m,
    rebuild_size_label_from_parts,
    strip_m_prefix_in_text,
)
from apps.catalog.models import ProductSKU


class Command(BaseCommand):
    help = (
        "M у розмірі лише для болт/гвинт/стрижень/гайка (+ автоболти); "
        "інше → 6 / 6×40; оновити назви та фасети"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише звіт без змін",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]
        updated_labels = 0
        updated_names = 0
        scanned = 0

        qs = (
            ProductSKU.objects.select_related(
                "group", "group__category", "group__category__parent"
            )
            .order_by("pk")
            .iterator(chunk_size=500)
        )

        to_update: list[ProductSKU] = []

        for sku in qs:
            scanned += 1
            metric = group_uses_metric_m(sku.group)
            new_label = rebuild_size_label_from_parts(
                sku.diameter,
                sku.length,
                sku.thread_pitch,
                metric=metric,
                fallback=sku.size_label or "",
            )
            if not new_label:
                new_label = "—"

            new_name = strip_m_prefix_in_text(sku.name or "", metric=metric)
            # якщо size_label змінився — підмінити старий варіант у назві
            old_label = (sku.size_label or "").strip()
            if (
                not metric
                and old_label
                and old_label != "—"
                and old_label != new_label
                and old_label in new_name
            ):
                new_name = new_name.replace(old_label, new_label)

            changed = False
            if new_label != (sku.size_label or ""):
                sku.size_label = new_label[:64]
                updated_labels += 1
                changed = True
            if new_name != (sku.name or ""):
                sku.name = new_name[:255]
                updated_names += 1
                changed = True
            if changed:
                to_update.append(sku)

        if dry:
            self.stdout.write(
                f"DRY: scanned={scanned} labels={updated_labels} "
                f"names={updated_names} (без запису)"
            )
            for sku in to_update[:20]:
                self.stdout.write(
                    f"  {sku.article}: size={sku.size_label!r} name={sku.name[:70]!r}"
                )
            return

        with transaction.atomic():
            if to_update:
                ProductSKU.objects.bulk_update(
                    to_update, ["size_label", "name"], batch_size=500
                )
            facet_stats = sync_facets_from_skus()

        self.stdout.write(
            self.style.SUCCESS(
                f"OK scanned={scanned} labels={updated_labels} "
                f"names={updated_names} facets={facet_stats}"
            )
        )
