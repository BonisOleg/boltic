from django.test import TestCase
from django.urls import reverse


class HealthzTests(TestCase):
    def test_healthz_ok(self):
        response = self.client.get(reverse("healthz"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
