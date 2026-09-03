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
        admin_path = f"/{settings.ADMIN_URL.lstrip('/')}"
        if not admin_path.endswith("/"):
            admin_path = f"{admin_path}/"
        if admin_path not in self._DISALLOW and admin_path != "/admin/":
            lines.append(f"Disallow: {admin_path}")
        lines.extend(
            [
                f"Sitemap: {site}/sitemap.xml",
                "",
            ]
        )
        return HttpResponse("\n".join(lines), content_type="text/plain")
