from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from io import StringIO

from apps.catalog.models import Category, ProductGroup, ProductSlugHistory


class SlugHistoryBase(TestCase):
    def setUp(self):
        self.l1 = Category.objects.create(
            name="Болти", slug="bolty", level=Category.Level.L1
        )
        self.l2 = Category.objects.create(
            name="Болти L2",
            slug="bolty-l2",
            level=Category.Level.L2,
            parent=self.l1,
        )


@override_settings(DEBUG=False)
class NotFoundPageTests(TestCase):
    def setUp(self):
        from apps.core.models import SiteSettings

        SiteSettings.get_solo()

    def test_404_page_has_gtm_and_nonce(self):
        client = Client(raise_request_exception=False)
        response = client.get("/this-page-definitely-does-not-exist-404/")
        self.assertEqual(response.status_code, 404)
        html = response.content.decode()
        self.assertIn("GTM-M63C7Z3F", html)
        self.assertIn("nonce=", html)
        self.assertRegex(html, r'nonce="[^"]+"')


class ProductSlugHistorySaveTests(SlugHistoryBase):
    def test_save_slug_change_creates_history(self):
        group = ProductGroup.objects.create(
            category=self.l2,
            name="Гайка мебельна",
            slug="гайка-мебельна",
        )
        group.slug = "гайка-мебельна-з-внутрішнім-шестигранником"
        group.save()
        self.assertTrue(
            ProductSlugHistory.objects.filter(
                old_slug="гайка-мебельна", product=group
            ).exists()
        )

    def test_chain_redirects_to_current(self):
        group = ProductGroup.objects.create(
            category=self.l2,
            name="Товар A",
            slug="slug-a",
        )
        group.slug = "slug-b"
        group.save()
        group.slug = "slug-c"
        group.save()

        self.assertEqual(group.slug, "slug-c")
        self.assertTrue(
            ProductSlugHistory.objects.filter(old_slug="slug-a", product=group).exists()
        )
        self.assertTrue(
            ProductSlugHistory.objects.filter(old_slug="slug-b", product=group).exists()
        )
        # новий slug не лишається в історії (немає циклу)
        self.assertFalse(ProductSlugHistory.objects.filter(old_slug="slug-c").exists())

        r_a = self.client.get(reverse("catalog:product", kwargs={"slug": "slug-a"}))
        self.assertEqual(r_a.status_code, 301)
        self.assertEqual(
            r_a["Location"],
            reverse("catalog:product", kwargs={"slug": "slug-c"}),
        )

        r_b = self.client.get(reverse("catalog:product", kwargs={"slug": "slug-b"}))
        self.assertEqual(r_b.status_code, 301)
        self.assertEqual(
            r_b["Location"],
            reverse("catalog:product", kwargs={"slug": "slug-c"}),
        )

    def test_old_slug_get_preserves_query_string(self):
        group = ProductGroup.objects.create(
            category=self.l2, name="Q", slug="old-q"
        )
        group.slug = "new-q"
        group.save()
        r = self.client.get(
            reverse("catalog:product", kwargs={"slug": "old-q"}) + "?sku=ART1"
        )
        self.assertEqual(r.status_code, 301)
        self.assertEqual(
            r["Location"],
            reverse("catalog:product", kwargs={"slug": "new-q"}) + "?sku=ART1",
        )

    def test_unknown_slug_is_404(self):
        r = self.client.get(
            reverse("catalog:product", kwargs={"slug": "неіснуючий-slug-xyz"})
        )
        self.assertEqual(r.status_code, 404)

    def test_revert_clears_history_for_new_slug(self):
        group = ProductGroup.objects.create(
            category=self.l2, name="R", slug="alpha"
        )
        group.slug = "beta"
        group.save()
        group.slug = "alpha"
        group.save()
        self.assertFalse(ProductSlugHistory.objects.filter(old_slug="alpha").exists())
        self.assertTrue(
            ProductSlugHistory.objects.filter(old_slug="beta", product=group).exists()
        )


class SeedProductSlugHistoryTests(SlugHistoryBase):
    def test_dry_run_does_not_write(self):
        ProductGroup.objects.create(
            category=self.l2,
            name="Гайка мебельна",
            slug="гайка-мебельна-з-внутрішнім-шестигранником",
        )
        out = StringIO()
        call_command("seed_product_slug_history", stdout=out)
        self.assertEqual(ProductSlugHistory.objects.count(), 0)
        self.assertIn("DRY-RUN", out.getvalue())

    def test_apply_writes(self):
        group = ProductGroup.objects.create(
            category=self.l2,
            name="Гайка мебельна",
            slug="гайка-мебельна-з-внутрішнім-шестигранником",
        )
        out = StringIO()
        call_command("seed_product_slug_history", "--apply", stdout=out)
        self.assertTrue(
            ProductSlugHistory.objects.filter(
                old_slug="гайка-мебельна", product=group
            ).exists()
        )
        self.assertIn("OK", out.getvalue())

    def test_pair_apply(self):
        group = ProductGroup.objects.create(
            category=self.l2, name="X", slug="current-slug"
        )
        call_command(
            "seed_product_slug_history",
            "--apply",
            "--pair",
            "legacy-slug:current-slug",
        )
        self.assertTrue(
            ProductSlugHistory.objects.filter(
                old_slug="legacy-slug", product=group
            ).exists()
        )
