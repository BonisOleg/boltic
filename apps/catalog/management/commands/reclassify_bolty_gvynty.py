from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Застаріла назва: делегує в restructure_catalog_tree "
        "(нове дерево Болти/Гвинти/Стрижні/Меблеве)"
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        call_command("seed_catalog")
        kwargs = {}
        if options["dry_run"]:
            kwargs["dry_run"] = True
        call_command("restructure_catalog_tree", **kwargs)
