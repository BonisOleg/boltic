"""Тимчасові фото товарів (заглушки) — замінити, коли будуть фінальні."""

from __future__ import annotations

import io
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from apps.catalog.models import ProductGroup, ProductImage


# Тип → колір плями / підпис на тимчасовій картинці
TYPE_STYLES: list[tuple[str, tuple[int, int, int], str]] = [
    ("саморіз", (46, 125, 50), "SAMORIZ"),
    ("шуруп", (56, 142, 60), "SHURUP"),
    ("гвинт", (25, 118, 210), "GVYNT"),
    ("гайка", (121, 85, 72), "GAYKA"),
    ("шайба", (96, 125, 139), "SHAYBA"),
    ("анкер", (245, 124, 0), "ANKER"),
    ("дюбель", (255, 143, 0), "DYUBEL"),
    ("шпилька", (0, 151, 167), "SHPYLKA"),
    ("хомут", (123, 31, 162), "KHOMUT"),
    ("біта", (69, 90, 100), "BITA"),
    ("болт", (55, 71, 79), "BOLT"),
]


def _detect_type(name: str) -> tuple[tuple[int, int, int], str]:
    low = (name or "").lower()
    for key, color, label in TYPE_STYLES:
        if key in low:
            return color, label
    return (90, 110, 90), "KRIPYZH"


def _make_image(color: tuple[int, int, int], label: str) -> bytes:
    """Проста тимчасова картинка (не сток) — легко замінити пізніше."""
    w, h = 640, 480
    img = Image.new("RGB", (w, h), (245, 247, 244))
    draw = ImageDraw.Draw(img)

    # фон-пляма
    draw.ellipse((80, 60, 560, 420), fill=(*color, ))
    # світліше кільце
    draw.ellipse((180, 140, 460, 340), fill=(255, 255, 255))
    # «болт» — шестигранник + стрижень
    cx, cy = 320, 220
    draw.regular_polygon((cx, cy, 48), n_sides=6, fill=color)
    draw.rectangle((cx - 14, cy + 30, cx + 14, cy + 130), fill=color)
    # насічки різьби
    for y in range(cy + 40, cy + 120, 10):
        draw.line((cx - 18, y, cx + 18, y), fill=(255, 255, 255), width=2)

    draw.text((24, 24), "TEMP", fill=(120, 120, 120))
    draw.text((24, h - 40), label, fill=color)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


class Command(BaseCommand):
    help = "Додати тимчасові фото до груп без зображень (за типом товару)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Перезаписати primary, якщо вже є зображення",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Обмежити кількість груп (0 = усі)",
        )

    def handle(self, *args, **options):
        try:
            from PIL import Image as _  # noqa: F401
        except ImportError as exc:
            raise CommandError("Потрібен Pillow") from exc

        force = options["force"]
        limit = options["limit"]
        qs = ProductGroup.objects.filter(is_active=True).order_by("id")
        if not force:
            qs = qs.filter(images__isnull=True).distinct()
        if limit:
            qs = qs[:limit]

        created = 0
        cache: dict[str, bytes] = {}

        with transaction.atomic():
            for group in qs:
                color, label = _detect_type(group.name)
                if label not in cache:
                    cache[label] = _make_image(color, label)
                data = cache[label]

                if force:
                    group.images.all().delete()

                filename = f"temp_{label.lower()}_{group.id}.jpg"
                img = ProductImage(
                    group=group,
                    alt=f"{group.name} (тимчасове фото)",
                    sort_order=0,
                    is_primary=True,
                )
                img.image.save(filename, ContentFile(data), save=False)
                img.save()
                created += 1

        cache_dir = Path("media/products")
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {created} тимчасових фото → {cache_dir}/ "
                f"(типів згенеровано: {len(cache)})"
            )
        )
