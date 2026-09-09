"""Google Merchant feed: 1 item = 1 SKU."""

from __future__ import annotations

import io
import tempfile
from decimal import Decimal

from django.core.files.base import ContentFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from apps.catalog.image_process import PRODUCT_IMAGE_HEIGHT, PRODUCT_IMAGE_WIDTH
from apps.catalog.models import Brand, Category, ProductGroup, ProductImage, ProductSKU
from apps.core.models import SiteSettings


def _jpeg_file(name: str = "p.jpg") -> ContentFile:
    img = Image.new("RGB", (PRODUCT_IMAGE_WIDTH, PRODUCT_IMAGE_HEIGHT), (40, 120, 80))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return ContentFile(buf.getvalue(), name=name)


@override_settings(SITE_URL="https://boltiko.com.ua", GOOGLE_FEED_CACHE_SECONDS=0)
class GoogleMerchantFeedTests(TestCase):
    def setUp(self):
        self._media = tempfile.TemporaryDirectory()
        self.addCleanup(self._media.cleanup)
        media_override = override_settings(MEDIA_ROOT=self._media.name)
        media_override.enable()
        self.addCleanup(media_override.disable)

        SiteSettings.get_solo()
        self.l1 = Category.objects.create(
            name="Болти, гвинти", slug="bolty-gvynty", level=Category.Level.L1
        )
        self.l2 = Category.objects.create(
            name="Болти", slug="bolty", level=Category.Level.L2, parent=self.l1
        )
        self.brand = Brand.objects.create(name="Haisser", slug="haisser")
        self.group = ProductGroup.objects.create(
            category=self.l2,
            brand=self.brand,
            name="Болт DIN 933",
            slug="bolt-din-933",
            description="Шестигранний болт з повною різьбою.",
        )
        ProductImage.objects.create(
            group=self.group,
            image=_jpeg_file("group.jpg"),
            is_primary=True,
            sort_order=0,
        )

    def _sku(self, **kwargs) -> ProductSKU:
        defaults = {
            "group": self.group,
            "article": "BLT-M8-20",
            "name": "Болт DIN 933 M8×20",
            "size_label": "M8×20",
            "price": Decimal("12.50"),
            "min_party": 1,
        }
        defaults.update(kwargs)
        return ProductSKU.objects.create(**defaults)

    def test_sku_row_uses_group_image_and_backorder(self):
        sku = self._sku(stock_status=ProductSKU.StockStatus.ON_ORDER)
        resp = self.client.get(reverse("catalog:google_feed"))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("application/xml", resp["Content-Type"])
        xml = resp.content.decode()
        self.assertIn('xmlns:g="http://base.google.com/ns/1.0"', xml)
        self.assertIn("<g:id>BLT-M8-20</g:id>", xml)
        self.assertIn("<g:availability>backorder</g:availability>", xml)
        self.assertIn("<g:brand>Haisser</g:brand>", xml)
        self.assertIn("<g:size>M8×20</g:size>", xml)
        self.assertIn("<g:product_type>Болти, гвинти &gt; Болти</g:product_type>", xml)
        self.assertIn(f"<g:item_group_id>{self.group.pk}</g:item_group_id>", xml)
        self.assertIn("/tovar/bolt-din-933/sku/BLT-M8-20/", xml)
        self.assertIn("https://boltiko.com.ua/media/", xml)
        self.assertNotIn("unisex", xml)
        self.assertNotIn("<g:gender>", xml)
        self.assertFalse(bool(sku.image))

    def test_skips_sku_without_any_image(self):
        bare = ProductGroup.objects.create(
            category=self.l2, name="Без фото", slug="bez-foto"
        )
        ProductSKU.objects.create(
            group=bare,
            article="NO-IMG",
            name="Без фото M6",
            size_label="M6",
            price=Decimal("5.00"),
        )
        xml = self.client.get(reverse("catalog:google_feed")).content.decode()
        self.assertNotIn("NO-IMG", xml)

    def test_skips_inactive_and_zero_price(self):
        self._sku(article="OFF-1", name="Вимкнений", is_active=False)
        self._sku(article="ZERO-1", name="Нуль", price=Decimal("0.00"))
        xml = self.client.get(reverse("catalog:google_feed")).content.decode()
        self.assertNotIn("OFF-1", xml)
        self.assertNotIn("ZERO-1", xml)

    def test_sale_price_and_in_stock(self):
        self._sku(
            article="SALE-1",
            name="Болт акція",
            price=Decimal("20.00"),
            sale_price=Decimal("15.00"),
            stock_status=ProductSKU.StockStatus.IN_STOCK,
        )
        xml = self.client.get(reverse("catalog:google_feed")).content.decode()
        self.assertIn("<g:id>SALE-1</g:id>", xml)
        self.assertIn("<g:price>20.00 UAH</g:price>", xml)
        self.assertIn("<g:sale_price>15.00 UAH</g:sale_price>", xml)
        self.assertIn("<g:availability>in_stock</g:availability>", xml)
        self.assertIn("<g:identifier_exists>no</g:identifier_exists>", xml)
        self.assertIn("<g:condition>new</g:condition>", xml)
