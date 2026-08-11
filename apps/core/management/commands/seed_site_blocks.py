from django.core.management.base import BaseCommand

from apps.core.block_defaults import (
    block_content_type,
    block_default,
    block_label,
)
from apps.core.models import SiteBlock
from apps.core.site_content_registry import all_registry_block_keys


class Command(BaseCommand):
    help = "Ідемпотентний seed SiteBlock з registry"

    def handle(self, *args, **options):
        created = 0
        for page, key in all_registry_block_keys():
            ctype = block_content_type(page, key)
            defaults = {
                "label": block_label(page, key),
                "content_type": ctype,
                "text_html": block_default(page, key) if ctype == "text" else "",
                "is_active": True,
            }
            if ctype == "url":
                defaults["link_url"] = block_default(page, key)
            _, was_created = SiteBlock.objects.get_or_create(
                page=page, key=key, defaults=defaults
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"SiteBlock seed: +{created}"))
