from decimal import Decimal

from django.core import mail
from django.test import Client, TestCase, override_settings

from apps.catalog.models import Category, ProductGroup, ProductSKU
from apps.core.exceptions import OrderError
from apps.core.models import SiteSettings
from apps.orders.constants import MIN_ORDER_AMOUNT, SHIPPING_PICKUP
from apps.orders.forms import ContactForm
from apps.orders.models import Order
from apps.orders.services import assert_min_order_amount
from apps.orders.validators import normalize_ua_phone


class CheckoutFlowTests(TestCase):
    def setUp(self):
        SiteSettings.get_solo()
        l1 = Category.objects.create(name="Кріплення", slug="kr", level=Category.Level.L1)
        l2 = Category.objects.create(
            name="Болти", slug="bolty", level=Category.Level.L2, parent=l1
        )
        group = ProductGroup.objects.create(
            category=l2, name="Болт М8", slug="bolt-m8"
        )
        self.sku_cheap = ProductSKU.objects.create(
            group=group,
            article="CHEAP-1",
            name="Болт М8×20",
            size_label="M8×20",
            price=Decimal("50.00"),
            min_party=1,
            stock_qty=100,
        )
        self.sku_ok = ProductSKU.objects.create(
            group=group,
            article="OK-1",
            name="Болт М8×40",
            size_label="M8×40",
            price=Decimal("400.00"),
            min_party=1,
            stock_qty=100,
        )
        self.client = Client()

    def test_assert_min_order_amount(self):
        with self.assertRaises(OrderError):
            assert_min_order_amount(Decimal("399.99"))
        assert_min_order_amount(MIN_ORDER_AMOUNT)

    def test_cart_blocks_checkout_below_min(self):
        session = self.client.session
        session.save()
        request = self.client.get("/koshyk/").wsgi_request
        # add via POST
        self.client.post(
            "/koshyk/add/",
            {"sku_id": self.sku_cheap.id, "qty": 1},
        )
        resp = self.client.get("/koshyk/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Мінімальна сума замовлення")
        self.assertContains(resp, 'disabled')

    def test_checkout_redirects_when_below_min(self):
        self.client.post(
            "/koshyk/add/",
            {"sku_id": self.sku_cheap.id, "qty": 1},
        )
        resp = self.client.get("/oformlennya/")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/koshyk/")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        DEFAULT_FROM_EMAIL="shop@test.local",
    )
    def test_full_checkout_pickup_sends_emails(self):
        site = SiteSettings.get_solo()
        site.email = "manager@test.local"
        site.pickup_enabled = True
        site.save()

        self.client.post(
            "/koshyk/add/",
            {"sku_id": self.sku_ok.id, "qty": 1},
        )
        resp = self.client.post(
            "/oformlennya/",
            {
                "customer_name": "Тест Тестович",
                "phone": "+380991112233",
                "email": "client@test.local",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/oformlennya/dostavka/")

        resp = self.client.post(
            "/oformlennya/dostavka/",
            {
                "shipping_method": SHIPPING_PICKUP,
                "comment": "Передзвоніть",
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "/oformlennya/pidtverdzhennya/")

        resp = self.client.post("/oformlennya/pidtverdzhennya/")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(resp.url.startswith("/oformlennya/uspikh/"))

        order = Order.objects.get()
        self.assertEqual(order.shipping_method, SHIPPING_PICKUP)
        self.assertEqual(order.total, Decimal("400.00"))
        self.assertEqual(order.payment_status, Order.PaymentStatus.PENDING)
        self.assertEqual(len(mail.outbox), 2)
        subjects = {m.subject for m in mail.outbox}
        self.assertTrue(any(order.number in s for s in subjects))

    def test_contact_validation(self):
        self.client.post(
            "/koshyk/add/",
            {"sku_id": self.sku_ok.id, "qty": 1},
        )
        bad_name = ContactForm(
            {
                "customer_name": "Іван 2",
                "phone": "+380501234567",
                "email": "",
            }
        )
        self.assertFalse(bad_name.is_valid())
        self.assertIn("customer_name", bad_name.errors)

        bad_phone = ContactForm(
            {
                "customer_name": "Іван Петренко",
                "phone": "+38050",
                "email": "",
            }
        )
        self.assertFalse(bad_phone.is_valid())
        self.assertIn("phone", bad_phone.errors)

        bad_email = ContactForm(
            {
                "customer_name": "Іван Петренко",
                "phone": "+380501234567",
                "email": "not-an-email",
            }
        )
        self.assertFalse(bad_email.is_valid())
        self.assertIn("email", bad_email.errors)

        ok = ContactForm(
            {
                "customer_name": "Іван Петренко",
                "phone": "0501234567",
                "email": "",
            }
        )
        self.assertTrue(ok.is_valid())
        self.assertEqual(ok.cleaned_data["phone"], "+380501234567")
        self.assertEqual(normalize_ua_phone("380991112233"), "+380991112233")

    def test_pickup_disabled_rejected(self):
        site = SiteSettings.get_solo()
        site.pickup_enabled = False
        site.save()
        self.client.post(
            "/koshyk/add/",
            {"sku_id": self.sku_ok.id, "qty": 1},
        )
        self.client.post(
            "/oformlennya/",
            {
                "customer_name": "Тест",
                "phone": "+380991112233",
                "email": "",
            },
        )
        resp = self.client.post(
            "/oformlennya/dostavka/",
            {"shipping_method": SHIPPING_PICKUP},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Самовивіз тимчасово недоступний")
