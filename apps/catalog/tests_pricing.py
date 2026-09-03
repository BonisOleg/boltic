from decimal import Decimal
from unittest.mock import MagicMock

from django.test import SimpleTestCase, TestCase

from apps.catalog.pricing import (
    clamp_qty,
    line_total,
    max_orderable_qty,
    normalize_qty,
    retail_unit_price,
    unit_price_for_qty,
)


def _sku(**kwargs):
    defaults = {
        "price": Decimal("10.00"),
        "sale_price": None,
        "party_price": None,
        "wholesale_from_qty": None,
        "min_party": 1,
    }
    defaults.update(kwargs)
    sku = MagicMock()
    for key, value in defaults.items():
        setattr(sku, key, value)
    return sku


class NormalizeQtyTests(SimpleTestCase):
    def test_raises_to_min(self):
        self.assertEqual(normalize_qty(0, 5), 5)
        self.assertEqual(normalize_qty(3, 5), 5)

    def test_any_integer_above_min(self):
        self.assertEqual(normalize_qty(7, 1), 7)
        self.assertEqual(normalize_qty(11, 5), 11)

    def test_no_multiplicity(self):
        self.assertEqual(normalize_qty(12, 10), 12)


class StockClampTests(SimpleTestCase):
    def test_max_orderable(self):
        self.assertIsNone(max_orderable_qty(1, None))
        self.assertEqual(max_orderable_qty(5, 3), 0)
        self.assertEqual(max_orderable_qty(1, 17), 17)

    def test_clamp(self):
        self.assertEqual(clamp_qty(3, 1, 10), 3)
        self.assertEqual(clamp_qty(20, 1, 10), 10)
        self.assertEqual(clamp_qty(1, 5, 3), 0)


class UnitPriceTests(SimpleTestCase):
    def test_retail_base(self):
        sku = _sku(price=Decimal("10.00"))
        self.assertEqual(unit_price_for_qty(sku, 1), Decimal("10.00"))
        self.assertEqual(retail_unit_price(sku), Decimal("10.00"))

    def test_sale_only_retail(self):
        sku = _sku(
            price=Decimal("10.00"),
            sale_price=Decimal("8.00"),
            party_price=Decimal("6.00"),
            wholesale_from_qty=100,
        )
        self.assertEqual(unit_price_for_qty(sku, 1), Decimal("8.00"))
        self.assertEqual(unit_price_for_qty(sku, 99), Decimal("8.00"))
        self.assertEqual(unit_price_for_qty(sku, 100), Decimal("6.00"))
        self.assertEqual(unit_price_for_qty(sku, 150), Decimal("6.00"))

    def test_wholesale_requires_threshold(self):
        sku = _sku(
            price=Decimal("10.00"),
            party_price=Decimal("7.00"),
            wholesale_from_qty=None,
        )
        self.assertEqual(unit_price_for_qty(sku, 500), Decimal("10.00"))

    def test_line_total(self):
        self.assertEqual(line_total(Decimal("1.50"), 3), Decimal("4.50"))


class PricingIntegrationTests(TestCase):
    def test_migration_fields_exist(self):
        from apps.catalog.models import ProductSKU

        field_names = {f.name for f in ProductSKU._meta.get_fields()}
        self.assertIn("wholesale_from_qty", field_names)
        self.assertIn("sale_price", field_names)
