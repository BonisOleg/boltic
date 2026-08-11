"""Тести нормалізації фото товарів (4:3 · 1200×900)."""

from __future__ import annotations

import io

from django.core.files.base import ContentFile
from django.test import SimpleTestCase
from PIL import Image

from apps.catalog.image_process import (
    PRODUCT_IMAGE_HEIGHT,
    PRODUCT_IMAGE_WIDTH,
    normalize_product_image,
)


def _jpeg_file(width: int, height: int, name: str = "shot.jpg") -> ContentFile:
    img = Image.new("RGB", (width, height), (40, 120, 80))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return ContentFile(buf.getvalue(), name=name)


class NormalizeProductImageTests(SimpleTestCase):
    def test_portrait_is_cropped_to_target(self):
        src = _jpeg_file(600, 900)
        out = normalize_product_image(src)
        self.assertIsNotNone(out)
        with Image.open(out) as img:
            self.assertEqual(img.size, (PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT))

    def test_already_normalized_returns_none(self):
        src = _jpeg_file(PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT)
        self.assertIsNone(normalize_product_image(src))

    def test_wide_landscape_is_cropped(self):
        src = _jpeg_file(1600, 900, name="wide.png")
        out = normalize_product_image(src)
        self.assertIsNotNone(out)
        self.assertTrue(out.name.endswith(".jpg"))
        with Image.open(out) as img:
            self.assertEqual(img.size, (PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT))
