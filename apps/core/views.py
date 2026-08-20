from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.views.generic import TemplateView


def healthz(request):
    connection.ensure_connection()
    return HttpResponse("ok", content_type="text/plain")


class RobotsTxtView(TemplateView):
    content_type = "text/plain"

    # seo_skill + shop: noindex службових / транзакційних URL
    _DISALLOW = (
        "/admin/",
        "/manage/",
        "/koshyk/",
        "/bazhane/",
        "/oformlennya/",
        "/kabinet/",
        "/login/",
        "/register/",
        "/logout/",
        "/payments/",
    )

    def get(self, request, *args, **kwargs):
        site = settings.SITE_URL.rstrip("/")
        lines = [
            "User-agent: *",
            "Allow: /",
        ]
        for path in self._DISALLOW:
            lines.append(f"Disallow: {path}")
        lines.extend(
            [
                f"Sitemap: {site}/sitemap.xml",
                "",
            ]
        )
        return HttpResponse("\n".join(lines), content_type="text/plain")
