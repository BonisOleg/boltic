from django.db import connection
from django.http import HttpResponse
from django.views.generic import TemplateView


def healthz(request):
    connection.ensure_connection()
    return HttpResponse("ok", content_type="text/plain")


class RobotsTxtView(TemplateView):
    content_type = "text/plain"

    def get(self, request, *args, **kwargs):
        lines = [
            "User-agent: *",
            "Allow: /",
            f"Sitemap: {request.build_absolute_uri('/sitemap.xml')}",
            "",
        ]
        return HttpResponse("\n".join(lines), content_type="text/plain")
