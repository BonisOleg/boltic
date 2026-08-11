"""Окрема admin-сторінка імпорту / експорту каталогу."""

from __future__ import annotations

from django import forms
from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import path, reverse
from unfold.admin import ModelAdmin

from apps.catalog.io_export import empty_template_rows, export_catalog
from apps.catalog.io_formats import CatalogIOError, SUPPORTED_EXTENSIONS, write_file
from apps.catalog.io_import import import_catalog_file
from apps.catalog.io_proxy import CatalogImportExport


class CatalogImportForm(forms.Form):
    file = forms.FileField(
        label="Файл",
        help_text="xlsx / csv / json / xml (повний дамп або goods.xlsx)",
    )


class CatalogExportForm(forms.Form):
    FORMAT_CHOICES = (
        ("xlsx", "Excel (.xlsx)"),
        ("csv", "CSV (.csv)"),
        ("json", "JSON (.json)"),
        ("xml", "XML (.xml)"),
    )
    format = forms.ChoiceField(label="Формат", choices=FORMAT_CHOICES, initial="xlsx")


def _stats_message(fmt: str, stats: dict[str, int]) -> str:
    if fmt == "goods":
        return (
            f"Імпорт goods: total={stats.get('total', 0)}, "
            f"створено={stats.get('created', 0)}, "
            f"оновлено(артикул)={stats.get('updated_article', 0)}, "
            f"оновлено(fuzzy)={stats.get('updated_fuzzy', 0)}, "
            f"помилки={stats.get('errors', 0)}"
        )
    return (
        f"Імпорт дампу: total={stats.get('total', 0)}, "
        f"створено={stats.get('created', 0)}, "
        f"оновлено={stats.get('updated', 0)}, "
        f"груп створено={stats.get('groups_created', 0)}, "
        f"помилки={stats.get('errors', 0)}"
    )


@admin.register(CatalogImportExport)
class CatalogImportExportAdmin(ModelAdmin):
    change_list_template = "admin/catalog/import_export.html"

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return request.user.is_staff

    def get_queryset(self, request: HttpRequest):
        return super().get_queryset(request).none()

    def changelist_view(self, request: HttpRequest, extra_context=None):
        import_form = CatalogImportForm()
        export_form = CatalogExportForm()

        if request.method == "POST":
            action = request.POST.get("action")
            if action == "import":
                import_form = CatalogImportForm(request.POST, request.FILES)
                if import_form.is_valid():
                    uploaded = import_form.cleaned_data["file"]
                    logs: list[str] = []
                    try:
                        content = uploaded.read()
                        fmt, stats = import_catalog_file(
                            uploaded.name,
                            content,
                            apply=True,
                            log=logs.append,
                        )
                        level = (
                            messages.WARNING
                            if stats.get("errors")
                            else messages.SUCCESS
                        )
                        messages.add_message(
                            request, level, _stats_message(fmt, stats)
                        )
                        for line in logs[:30]:
                            messages.warning(request, line)
                        if len(logs) > 30:
                            messages.warning(
                                request,
                                f"… ще {len(logs) - 30} повідомлень про помилки",
                            )
                        return HttpResponseRedirect(
                            reverse("admin:catalog_catalogimportexport_changelist")
                        )
                    except CatalogIOError as exc:
                        messages.error(request, str(exc))
                    except Exception as exc:  # noqa: BLE001
                        messages.error(request, f"Помилка імпорту: {exc}")
            elif action == "export":
                export_form = CatalogExportForm(request.POST)
                if export_form.is_valid():
                    try:
                        content, content_type, filename = export_catalog(
                            export_form.cleaned_data["format"]
                        )
                        response = HttpResponse(content, content_type=content_type)
                        response["Content-Disposition"] = (
                            f'attachment; filename="{filename}"'
                        )
                        return response
                    except CatalogIOError as exc:
                        messages.error(request, str(exc))
            elif action == "template":
                fmt = request.POST.get("format", "xlsx")
                try:
                    content, content_type, filename = write_file(
                        fmt, empty_template_rows()
                    )
                    filename = filename.replace("catalog_full", "catalog_template")
                    response = HttpResponse(content, content_type=content_type)
                    response["Content-Disposition"] = (
                        f'attachment; filename="{filename}"'
                    )
                    return response
                except CatalogIOError as exc:
                    messages.error(request, str(exc))

        context = {
            **self.admin_site.each_context(request),
            "title": "Імпорт / експорт каталогу",
            "import_form": import_form,
            "export_form": export_form,
            "supported": ", ".join(SUPPORTED_EXTENSIONS),
            "opts": self.model._meta,
            "cl": None,
            "has_permission": True,
            "is_popup": False,
            "is_nav_sidebar_enabled": True,
            "media": self.media,
        }
        if extra_context:
            context.update(extra_context)
        return render(request, self.change_list_template, context)


def register_catalog_io_urls() -> None:
    """Редирект зі старого URL на changelist proxy-моделі."""
    if getattr(admin.site, "_boltiko_catalog_io_registered", False):
        return

    original_get_urls = admin.site.get_urls

    def _legacy_redirect(request: HttpRequest):
        return redirect("admin:catalog_catalogimportexport_changelist")

    def get_urls():
        custom = [
            path(
                "catalog/import-export/",
                admin.site.admin_view(_legacy_redirect),
                name="catalog_import_export",
            ),
        ]
        return custom + original_get_urls()

    admin.site.get_urls = get_urls  # type: ignore[method-assign]
    admin.site._boltiko_catalog_io_registered = True  # type: ignore[attr-defined]
