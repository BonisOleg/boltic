from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify
from docx import Document

from apps.catalog.classification import resolve_fastener_category
from apps.catalog.import_parser import (
    is_group_header,
    parse_group_meta,
    parse_size_line,
)
from apps.catalog.models import Category, ProductGroup, ProductSKU


class Command(BaseCommand):
    help = "Імпорт БОЛТИ.docx / ГВИНТИ.docx → ProductGroup + ProductSKU"

    def add_arguments(self, parser):
        parser.add_argument(
            "--price",
            type=Decimal,
            default=Decimal("10.00"),
            help="Ціна за шт за замовчуванням (у DOCX цін немає)",
        )
        parser.add_argument(
            "--min-party",
            type=int,
            default=1,
            help="Мін. партія для SKU",
        )
        parser.add_argument(
            "--dir",
            type=str,
            default=".",
            help="Каталог з DOCX",
        )

    def handle(self, *args, **options):
        base = Path(options["dir"]).resolve()
        files = [
            ("БОЛТИ.docx", "BLT"),
            ("ГВИНТИ.docx", "GVN"),
        ]
        price: Decimal = options["price"]
        min_party: int = options["min_party"]

        if not Category.objects.filter(
            parent=None, slug="болти", level=Category.Level.L1, is_active=True
        ).exists():
            raise CommandError("Немає L1 «Болти». Спочатку seed_catalog.")

        total_groups = 0
        total_skus = 0

        with transaction.atomic():
            for filename, prefix in files:
                path = base / filename
                if not path.exists():
                    raise CommandError(f"Немає файлу: {path}")
                g_count, s_count = self._import_file(
                    path, prefix, price, min_party
                )
                total_groups += g_count
                total_skus += s_count
                self.stdout.write(f"{filename}: груп={g_count}, SKU={s_count}")

        from apps.catalog.facet_sync import sync_facets_from_skus

        facet_stats = sync_facets_from_skus()
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {total_groups} груп, {total_skus} SKU · ціна={price} · "
                f"фасети={facet_stats['values']} значень / "
                f"{facet_stats['sku_links']} звʼязків"
            )
        )

    def _resolve_category(self, meta: dict) -> Category:
        l1_slug, l2_slug = resolve_fastener_category(
            meta["name"],
            meta.get("standard") or "",
            meta.get("material") or "",
        )
        cat = (
            Category.objects.filter(
                parent__slug=l1_slug,
                parent__parent=None,
                slug=l2_slug,
                level=Category.Level.L2,
            )
            .select_related("parent")
            .first()
        )
        if cat is None:
            raise CommandError(
                f"Немає категорії {l1_slug}/{l2_slug}. "
                "Спочатку: seed_catalog + restructure_catalog_tree"
            )
        return cat

    def _import_file(
        self,
        path: Path,
        prefix: str,
        price: Decimal,
        min_party: int,
    ) -> tuple[int, int]:
        doc = Document(str(path))
        lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

        groups_n = 0
        skus_n = 0
        current_meta: dict | None = None
        current_group: ProductGroup | None = None
        diameters: list[Decimal] = []
        lengths: list[Decimal] = []

        def flush_ranges() -> None:
            nonlocal current_group, diameters, lengths
            if current_group is None:
                return
            if diameters:
                current_group.diameter_min = min(diameters)
                current_group.diameter_max = max(diameters)
            if lengths:
                current_group.length_min = min(lengths)
                current_group.length_max = max(lengths)
            current_group.save(
                update_fields=[
                    "diameter_min",
                    "diameter_max",
                    "length_min",
                    "length_max",
                    "updated_at",
                ]
            )
            diameters = []
            lengths = []

        for line in lines:
            if is_group_header(line):
                flush_ranges()
                current_meta = parse_group_meta(line)
                # виправлення «лемішний10,9»
                if "лемішний10" in current_meta["name"].replace(" ", ""):
                    current_meta["name"] = "Болт лемішний 10,9 сталь"
                    current_meta["strength_class"] = "10.9"
                    current_meta["material"] = "сталь"

                category = self._resolve_category(current_meta)
                slug = slugify(current_meta["name"], allow_unicode=True)[:200]
                current_group, created = ProductGroup.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "category": category,
                        "name": current_meta["name"],
                        "standard": current_meta["standard"],
                        "material": current_meta["material"],
                        "is_active": True,
                        "short_description": current_meta["name"],
                    },
                )
                groups_n += 1
                continue

            if current_group is None or current_meta is None:
                continue

            parsed = parse_size_line(line)
            for item in parsed:
                article = self._article(prefix, current_group.slug, item.size_label)
                name = f"{current_group.name} {item.size_label}"
                ProductSKU.objects.update_or_create(
                    article=article,
                    defaults={
                        "group": current_group,
                        "name": name[:255],
                        "size_label": item.size_label,
                        "diameter": item.diameter,
                        "length": item.length,
                        "thread_pitch": item.thread_pitch,
                        "strength_class": current_meta["strength_class"],
                        "min_party": min_party,
                        "price": price,
                        "price_includes_vat": True,
                        "vat_rate": Decimal("20.00"),
                        "stock_status": ProductSKU.StockStatus.IN_STOCK,
                        "is_active": True,
                    },
                )
                skus_n += 1
                diameters.append(item.diameter)
                lengths.append(item.length)

        flush_ranges()
        return groups_n, skus_n

    @staticmethod
    def _article(prefix: str, group_slug: str, size_label: str) -> str:
        short = group_slug.replace("болт-з-шестигранною-головкою-", "b-")
        short = short.replace("гвинт-з-внутрішнім-шестигранником-", "g-")
        short = short[:40]
        size = size_label.replace("×", "x").replace(".", "-")
        article = f"{prefix}-{short}-{size}"
        return article[:64]
