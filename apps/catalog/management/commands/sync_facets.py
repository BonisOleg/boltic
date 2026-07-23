from django.core.management.base import BaseCommand

from apps.catalog.facet_sync import sync_facets_from_skus


class Command(BaseCommand):
    help = (
        "Побудувати фасети (стандарт, матеріал, клас міцності, "
        "діаметр, довжина) з полів ProductGroup / ProductSKU"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-unused",
            action="store_true",
            help="Не видаляти значення без привʼязок до SKU",
        )

    def handle(self, *args, **options):
        stats = sync_facets_from_skus(prune_unused=not options["keep_unused"])
        self.stdout.write(
            self.style.SUCCESS(
                "Готово: "
                f"атрибутів={stats['attributes']}, "
                f"значень={stats['values']}, "
                f"SKU={stats['skus']}, "
                f"звʼязків={stats['sku_links']}, "
                f"прибрано={stats['pruned_values']}"
            )
        )
