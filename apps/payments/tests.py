from decimal import Decimal
from uuid import uuid4

from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.catalog.models import Category, ProductGroup, ProductSKU
from apps.orders.models import Order
from apps.payments.services import LiqPayClient


@override_settings(
    LIQPAY_PUBLIC_KEY="test_pub",
    LIQPAY_PRIVATE_KEY="test_priv",
)
class LiqPayResultAccessTests(TestCase):
    def setUp(self):
        l1 = Category.objects.create(name="L1", slug="l1", level=Category.Level.L1)
        l2 = Category.objects.create(
            name="L2", slug="l2", level=Category.Level.L2, parent=l1
        )
        group = ProductGroup.objects.create(category=l2, name="G", slug="g")
        ProductSKU.objects.create(
            group=group,
            article="A1",
            name="SKU",
            price=Decimal("100.00"),
            min_party=1,
        )
        self.order = Order.objects.create(
            number="BLT-20260817-0001",
            customer_name="Тест",
            phone="+380501112233",
            total=Decimal("100.00"),
        )
        self.client = Client()
        self.url = reverse("payments:liqpay_result")

    def test_number_only_does_not_leak_token(self):
        resp = self.client.get(self.url, {"number": self.order.number})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("content:home"))
        self.assertNotIn(str(self.order.access_token), resp.url)

    def test_wrong_token_denied(self):
        resp = self.client.get(
            self.url,
            {"number": self.order.number, "token": str(uuid4())},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("content:home"))
        self.assertNotIn(str(self.order.access_token), resp.url)

    def test_valid_token_redirects_to_success(self):
        token = str(self.order.access_token)
        resp = self.client.get(
            self.url,
            {"number": self.order.number, "token": token},
        )
        self.assertEqual(resp.status_code, 302)
        success = reverse("orders:success", kwargs={"number": self.order.number})
        self.assertEqual(resp.url, f"{success}?token={token}")

    def test_signed_post_grants_access(self):
        client = LiqPayClient("test_pub", "test_priv")
        payload = {
            "order_id": self.order.number,
            "status": "success",
            "amount": "100.00",
            "currency": "UAH",
            "payment_id": "pay-1",
        }
        data_b64 = client._encode(payload)
        signature = client._sign(data_b64)
        resp = self.client.post(
            self.url,
            {"data": data_b64, "signature": signature},
        )
        self.assertEqual(resp.status_code, 302)
        token = str(self.order.access_token)
        success = reverse("orders:success", kwargs={"number": self.order.number})
        self.assertEqual(resp.url, f"{success}?token={token}")
