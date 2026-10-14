from django.conf import settings
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import TemplateView


def healthz(request):
    connection.ensure_connection()
    return HttpResponse("ok", content_type="text/plain")


def page_not_found(request, exception=None):
    """Кастомний 404 з GTM/nonce; fallback якщо context processors падають."""
    gtm_id = getattr(settings, "GTM_CONTAINER_ID", "") or ""
    try:
        return render(request, "404.html", status=404)
    except Exception:
        try:
            return render(
                request,
                "404_minimal.html",
                {"gtm_container_id": gtm_id},
                status=404,
            )
        except Exception:
            nonce = getattr(request, "csp_nonce", "") or ""
            body = (
                "<!DOCTYPE html><html lang=\"uk\"><head><meta charset=\"utf-8\">"
                f"<script nonce=\"{nonce}\">window.dataLayer=window.dataLayer||[];"
                "</script>"
            )
            if gtm_id:
                body += (
                    f"<script nonce=\"{nonce}\">(function(w,d,s,l,i){{w[l]=w[l]||[];"
                    "w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});"
                    "var f=d.getElementsByTagName(s)[0],j=d.createElement(s),"
                    "dl=l!='dataLayer'?'&l='+l:'';j.async=true;"
                    "j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;"
                    "f.parentNode.insertBefore(j,f);"
                    f"}})(window,document,'script','dataLayer','{gtm_id}');</script>"
                )
            body += (
                "</head><body><h1>Сторінку не знайдено</h1>"
                "<p><a href=\"/\">На головну</a></p></body></html>"
            )
            return HttpResponse(body, status=404, content_type="text/html; charset=utf-8")


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
