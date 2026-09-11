from unittest.mock import patch

from django.test import TestCase, override_settings

from apps.orders import nova_poshta


@override_settings(NOVA_POSHTA_API_KEY="")
class NovaPoshtaConfigTests(TestCase):
    def test_not_configured_without_key(self):
        self.assertFalse(nova_poshta.is_configured())
        with self.assertRaises(nova_poshta.NovaPoshtaError) as ctx:
            nova_poshta.search_cities("Київ")
        self.assertIn("не налаштовано", str(ctx.exception))


@override_settings(NOVA_POSHTA_API_KEY="test-key")
class NovaPoshtaSearchTests(TestCase):
    def test_search_cities_maps_delivery_city(self):
        payload = [
            {
                "Addresses": [
                    {
                        "Present": "м. Київ, Київська обл.",
                        "DeliveryCity": "city-ref-1",
                        "Ref": "settlement-ref",
                    }
                ]
            }
        ]
        with patch.object(nova_poshta, "_call", return_value=payload) as mocked:
            items = nova_poshta.search_cities("Київ")
        mocked.assert_called_once()
        self.assertEqual(items, [{"ref": "city-ref-1", "name": "м. Київ, Київська обл."}])

    def test_search_cities_short_query(self):
        with patch.object(nova_poshta, "_call") as mocked:
            self.assertEqual(nova_poshta.search_cities("К"), [])
        mocked.assert_not_called()

    def test_warehouses_uses_category_then_fallback(self):
        full = [
            {
                "Ref": "wh-1",
                "Description": "Відділення №1",
                "CategoryOfWarehouse": "Branch",
            },
            {
                "Ref": "pm-1",
                "Description": "Поштомат №2",
                "CategoryOfWarehouse": "Postomat",
            },
        ]
        with patch.object(
            nova_poshta,
            "_call",
            side_effect=[nova_poshta.NovaPoshtaError("bad category"), full],
        ) as mocked:
            items = nova_poshta.search_warehouses(
                "city-ref", delivery_type="warehouse"
            )
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(items, [{"ref": "wh-1", "name": "Відділення №1"}])

    def test_invalid_delivery_type(self):
        with self.assertRaises(nova_poshta.NovaPoshtaError):
            nova_poshta.search_warehouses("city-ref", delivery_type="courier")

    def test_call_rejects_api_errors(self):
        with patch.object(
            nova_poshta,
            "_post_json",
            return_value={"success": False, "errors": ["API key expired"]},
        ):
            with self.assertRaises(nova_poshta.NovaPoshtaError) as ctx:
                nova_poshta.search_cities("Київ")
        self.assertIn("API key expired", str(ctx.exception))

    def test_np_cities_view_returns_items(self):
        with patch.object(
            nova_poshta,
            "search_cities",
            return_value=[{"ref": "r", "name": "Київ"}],
        ):
            resp = self.client.get("/oformlennya/api/np/cities/", {"q": "Київ"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["items"][0]["name"], "Київ")

    def test_np_cities_view_network_error(self):
        with patch.object(
            nova_poshta,
            "search_cities",
            side_effect=nova_poshta.NovaPoshtaError(
                "Не вдалося звернутися до API Нової Пошти"
            ),
        ):
            resp = self.client.get("/oformlennya/api/np/cities/", {"q": "Київ"})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["ok"])
