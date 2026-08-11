from django.core.management.base import BaseCommand

from apps.core.hero_slides import ensure_default_hero_slides


class Command(BaseCommand):
    help = "Ідемпотентний seed HeroSlide"

    def handle(self, *args, **options):
        n = ensure_default_hero_slides()
        self.stdout.write(self.style.SUCCESS(f"HeroSlide seed: +{n}"))
