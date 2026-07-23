from django.http import HttpResponse
from django.views.generic import TemplateView


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
