"""Кнопка Unfold «Синхронізувати фільтри» для changelist каталогу."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from unfold.decorators import action
from unfold.enums import ActionVariant

from apps.catalog.facet_sync import sync_facets_from_skus


class SyncFacetsAdminMixin:
    """Додає actions_list-кнопку sync фасетів (не залежить від виділених рядків)."""

    actions_list = ("sync_facets_action",)

    @action(
        description="Синхронізувати фільтри",
        url_path="sync-facets",
        permissions=["change"],
        icon="sync",
        variant=ActionVariant.PRIMARY,
    )
    def sync_facets_action(self, request: HttpRequest) -> HttpResponse:
        stats = sync_facets_from_skus()
        messages.success(
            request,
            (
                "Фільтри синхронізовано: "
                f"атрибутів={stats['attributes']}, "
                f"значень={stats['values']}, "
                f"SKU={stats['skus']}, "
                f"звʼязків={stats['sku_links']}, "
                f"прибрано={stats['pruned_values']}"
            ),
        )
        opts = self.model._meta
        return redirect(
            reverse(f"admin:{opts.app_label}_{opts.model_name}_changelist")
        )
