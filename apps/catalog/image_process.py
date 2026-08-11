"""Нормалізація фото товарів: співвідношення 4:3 і цільовий розмір."""

from __future__ import annotations

import io
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

PRODUCT_IMAGE_RATIO = (4, 3)
PRODUCT_IMAGE_WIDTH = 1200
PRODUCT_IMAGE_HEIGHT = 900
PRODUCT_IMAGE_HELP = (
    "Формат 4:3, рекомендовано 1200×900 px (JPEG/PNG/WebP). "
    "Якщо співвідношення інше — фото автоматично обрізається по центру "
    "під 4:3 і масштабується до 1200×900."
)

_TARGET_RATIO = PRODUCT_IMAGE_WIDTH / PRODUCT_IMAGE_HEIGHT
_SIZE_TOLERANCE_PX = 2
_RATIO_TOLERANCE = 0.01


def _needs_normalize(img: Image.Image) -> bool:
    width, height = img.size
    if (
        abs(width - PRODUCT_IMAGE_WIDTH) > _SIZE_TOLERANCE_PX
        or abs(height - PRODUCT_IMAGE_HEIGHT) > _SIZE_TOLERANCE_PX
    ):
        return True
    if height == 0:
        return True
    return abs(width / height - _TARGET_RATIO) > _RATIO_TOLERANCE


def _center_crop_to_ratio(img: Image.Image, ratio_w: int, ratio_h: int) -> Image.Image:
    width, height = img.size
    target = ratio_w / ratio_h
    current = width / height if height else target
    if abs(current - target) < 0.001:
        return img
    if current > target:
        new_w = max(1, int(round(height * target)))
        left = max(0, (width - new_w) // 2)
        return img.crop((left, 0, left + new_w, height))
    new_h = max(1, int(round(width / target)))
    top = max(0, (height - new_h) // 2)
    return img.crop((0, top, width, top + new_h))


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode == "RGB":
        return img
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, (255, 255, 255))
        alpha = img.split()[-1]
        background.paste(img.convert("RGBA"), mask=alpha)
        return background
    return img.convert("RGB")


def normalize_product_image(image_field) -> ContentFile | None:
    """JPEG 1200×900 (4:3) або None, якщо вже відповідає / файл порожній."""
    if not image_field:
        return None

    try:
        image_field.open("rb")
        with Image.open(image_field) as opened:
            img = ImageOps.exif_transpose(opened)
            img.load()
            img = img.copy()
    except (OSError, ValueError):
        return None
    finally:
        try:
            image_field.seek(0)
        except (OSError, ValueError, AttributeError):
            pass

    img = _to_rgb(img)
    if not _needs_normalize(img):
        return None

    img = _center_crop_to_ratio(img, *PRODUCT_IMAGE_RATIO)
    img = img.resize(
        (PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT),
        Image.Resampling.LANCZOS,
    )

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=88, optimize=True)
    buf.seek(0)

    stem = Path(getattr(image_field, "name", "") or "product").stem or "product"
    return ContentFile(buf.read(), name=f"{stem}.jpg")
