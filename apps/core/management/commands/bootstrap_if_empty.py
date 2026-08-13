from django.core.management import call_command
from django.core.management.base import BaseCommand

from apps.catalog.models import ProductGroup
from apps.content.models import StaticPage


class Command(BaseCommand):
    help = "seed_catalog лише якщо немає товарів і службових сторінок"

    def handle(self, *args, **options):
        if ProductGroup.objects.exists() or StaticPage.objects.exists():
            self.stdout.write("skip bootstrap: data already present")
            return
        call_command("seed_catalog")
