from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.io_goods_import import import_goods_dicts
from apps.catalog.io_formats import CatalogIOError, read_tabular_file


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
        path = Path(options["file"]).resolve()
        if not path.exists():
            raise CommandError(f"Немає файлу: {path}")

        dry = options["dry_run"]
        try:
            content = path.read_bytes()
            fmt, rows = read_tabular_file(path.name, content)
            if fmt != "goods":
                raise CommandError(
                    "Файл не схожий на goods.xlsx (очікуються колонки «Код», «Ім'я товару»)"
                )
            stats = import_goods_dicts(
                rows,
                apply=not dry,
                log=lambda msg: self.stderr.write(msg),
            )
        except CatalogIOError as exc:
            raise CommandError(str(exc)) from exc

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
