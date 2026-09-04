from django.core.management.base import BaseCommand

from apps.content.static_page_defaults import ensure_static_pages


class Command(BaseCommand):
    help = (
        "Заповнити службові StaticPage дефолтами "
        "(не затирає текст, відредагований в адмінці)"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Перезаписати body навіть якщо вже не заглушка",
        )

    def handle(self, *args, **options):
        stats = ensure_static_pages(force=bool(options["force"]))
        self.stdout.write(
            self.style.SUCCESS(
                f"StaticPage: created={stats['created']} "
                f"updated={stats['updated']} skipped={stats['skipped']}"
            )
        )
