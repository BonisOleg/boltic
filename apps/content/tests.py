from django.test import TestCase, override_settings
from django.urls import reverse

CREDIT_URL = "https://www.prometeylabs.com/internet-shop-v2/"


class FooterDeveloperLinkTests(TestCase):
    def test_home_has_nofollow_credit_link(self):
        response = self.client.get(reverse("content:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, CREDIT_URL)
        self.assertContains(response, "nofollow")
        self.assertContains(response, ">PrometeyLabs</a>")
        self.assertContains(response, 'rel="nofollow noopener noreferrer"')

    def test_inner_pages_show_credit_without_link(self):
        for name in ("content:promo_list", "content:contacts", "content:news_list"):
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "PrometeyLabs")
                self.assertNotContains(response, CREDIT_URL)
                self.assertNotContains(response, "footer-credit__link")
                self.assertNotContains(response, 'href="https://www.prometeylabs.com/"')


@override_settings(SITE_URL="http://testserver")
class SeoMetaTests(TestCase):
    def _assert_seo(self, response, *, path: str, title_fragment: str):
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="description"')
        self.assertContains(response, f'href="http://testserver{path}"')
        self.assertContains(response, 'property="og:title"')
        self.assertContains(response, 'property="og:description"')
        self.assertContains(response, title_fragment)
        # description content non-empty
        self.assertRegex(
            response.content.decode(),
            r'<meta name="description" content="[^"]{20,}"',
        )

    def test_home_seo_meta(self):
        self._assert_seo(
            self.client.get(reverse("content:home")),
            path="/",
            title_fragment="og:title",
        )

    def test_catalog_seo_meta(self):
        self._assert_seo(
            self.client.get(reverse("catalog:root")),
            path="/katalog/",
            title_fragment="Каталог",
        )

    def test_promos_seo_meta(self):
        self._assert_seo(
            self.client.get(reverse("content:promo_list")),
            path="/aktsiyi/",
            title_fragment="Акції",
        )


class Err26HtmxStaticTests(TestCase):
    """ERR-26: ядро HTMX лише з /static/js/htmx.min.js, не CDN."""

    def test_home_uses_local_htmx_not_cdn(self):
        response = self.client.get(reverse("content:home"))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn("/static/js/htmx.min.js", html)
        self.assertNotIn("unpkg.com", html)
        self.assertNotIn("htmx.org", html)
        self.assertNotIn("cdn.jsdelivr", html)
        self.assertNotIn("django_htmx/htmx.min.js", html)
