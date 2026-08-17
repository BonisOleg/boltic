"""Заповнити стандартні d/D/B для SKU підшипників (можна перезаписати в адмінці)."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.bearing_dims import (
    BEARING_L2_PATH,
    extract_bearing_code,
    lookup_standard_dims,
    size_label_from_dims,
)
from apps.catalog.facet_sync import sync_facets_from_skus
from apps.catalog.models import Category, ProductSKU


class Command(BaseCommand):
    help = (
        "Проставити bore_d_mm / od_d_mm / width_b_mm зі стандартів "
        "за кодом у назві (607, 608, 6202…). "
        "За замовчуванням не перезаписує вже заповнені поля."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Перезаписати d/D/B навіть якщо вже задані",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Лише показати зміни, без запису",
        )
        parser.add_argument(
            "--skip-facets",
            action="store_true",
            help="Не викликати sync_facets_from_skus після запису",
        )

    def handle(self, *args, **options):
        force = options["force"]
        dry = options["dry_run"]
        cat = Category.objects.filter(path=BEARING_L2_PATH).first()
        if cat is None:
            self.stderr.write("Немає категорії підшипники-сальники/підшипники/")
            return

        qs = (
            ProductSKU.objects.filter(group__category=cat)
            .select_related("group")
            .order_by("article")
        )
        updated = 0
        skipped = 0
        unknown = 0
        seals_cleared = 0

        with transaction.atomic():
            for sku in qs:
                name_l = (sku.name or "").lower()
                # сальники в L2 підшипників — прибрати хибні diametr/dovzhyna
                if "сальник" in name_l or "ущільнен" in name_l:
                    if sku.diameter is not None or sku.length is not None:
                        seals_cleared += 1
                        self.stdout.write(
                            f"  clear fastener size {sku.article}: {sku.name}"
                        )
                        if not dry:
                            sku.diameter = None
                            sku.length = None
                            sku.save(update_fields=["diameter", "length", "updated_at"])
                    skipped += 1
                    continue

                code = extract_bearing_code(sku.name)
                dims = lookup_standard_dims(code) if code else None
                if dims is None:
                    unknown += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ? {sku.article} «{sku.name}» code={code!r}"
                        )
                    )
                    continue

                bore, od, width = dims
                has_any = (
                    sku.bore_d_mm is not None
                    or sku.od_d_mm is not None
                    or sku.width_b_mm is not None
                )
                if has_any and not force:
                    skipped += 1
                    continue

                label = size_label_from_dims(bore, od, width)
                self.stdout.write(
                    f"  {sku.article} {code} → d={bore} D={od} B={width}"
                )
                updated += 1
                if dry:
                    continue
                sku.bore_d_mm = bore
                sku.od_d_mm = od
                sku.width_b_mm = width
                # прибрати кріпильні діаметр/довжину, якщо були
                sku.diameter = None
                sku.length = None
                fields = [
                    "bore_d_mm",
                    "od_d_mm",
                    "width_b_mm",
                    "diameter",
                    "length",
                    "updated_at",
                ]
                if not sku.size_label or sku.size_label.strip() in ("—", "-", "–"):
                    sku.size_label = label
                    fields.append("size_label")
                sku.save(update_fields=fields)

            if dry:
                transaction.set_rollback(True)

        self.stdout.write(
            self.style.SUCCESS(
                f"updated={updated} skipped={skipped} unknown={unknown} "
                f"seals_cleared={seals_cleared} dry_run={dry}"
            )
        )

        if not dry and not options["skip_facets"] and updated:
            stats = sync_facets_from_skus()
            self.stdout.write(f"facets: {stats}")
