from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_GET, require_http_methods
from django.views.generic import TemplateView

from apps.cart.services import wishlist_sku_ids
from apps.catalog import selectors
from apps.catalog.metric_size import group_uses_metric_m
from apps.catalog.auto_screw_dims import group_is_auto_screw
from apps.catalog.composite_dims import (
    group_is_mesh,
    group_is_rebar,
    group_is_wedge,
    price_unit_for_group,
)
from apps.catalog.foam_glue_dims import (
    group_is_foam_glue_sealant,
    party_price_unit_for_group,
)
from apps.core.exceptions import ReviewError
from apps.orders.forms import ReviewForm
from apps.reviews.services import create_pending_review


class CatalogRootView(TemplateView):
    template_name = "catalog/root.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["categories"] = selectors.root_categories()
        return ctx


class CategoryView(View):
    template_name = "catalog/category.html"
    partial_name = "catalog/partials/product_grid.html"

    def get(self, request, path: str):
        category = selectors.resolve_category(path)
        if category is None:
            raise Http404
        selected = selectors.parse_facets(request.GET)
        sort = request.GET.get("sort", "name")
        groups = selectors.list_groups_for_category(
            category, selected=selected, sort=sort
        )
        page = Paginator(groups, 24).get_page(request.GET.get("page") or 1)
        ctx = {
            "category": category,
            "children": selectors.category_children(category),
            "page_obj": page,
            "selected_facets": selected,
            "facet_attributes": selectors.facet_attributes(category),
            "sort": sort,
            "canonical_path": category.path,
        }
        if getattr(request, "htmx", False):
            return render(request, self.partial_name, ctx)
        return render(request, self.template_name, ctx)


def _mark_wishlist(request, skus):
    """Позначити SKU, які вже в обраному, для стану кнопки."""
    ids = wishlist_sku_ids(getattr(request, "user", None))
    items = list(skus)
    for sku in items:
        sku.in_wishlist = sku.id in ids
    return items


class ProductDetailView(View):
    template_name = "catalog/product_detail.html"

    def get(self, request, slug: str):
        group = selectors.get_pdp(slug)
        if group is None:
            raise Http404
        highlight = request.GET.get("sku", "")
        reviews = [r for r in group.reviews.all() if r.is_published]
        skus = _mark_wishlist(request, group.skus.all())
        return render(
            request,
            self.template_name,
            {
                "group": group,
                "skus": skus,
                "reviews": reviews,
                "review_form": ReviewForm(),
                "highlight_sku": highlight,
                "group_image_url": selectors.group_primary_image_url(group),
                "uses_metric_m": group_uses_metric_m(group),
                "show_bearing_dims": any(
                    s.bore_d_mm is not None
                    or s.od_d_mm is not None
                    or s.width_b_mm is not None
                    for s in skus
                ),
                "show_auto_screw_dims": group_is_auto_screw(group)
                or any(
                    s.head_width_mm is not None
                    for s in skus
                ),
                "show_rebar_dims": group_is_rebar(group),
                "show_mesh_dims": group_is_mesh(group),
                "show_wedge_dims": group_is_wedge(group),
                "show_foam_glue_dims": group_is_foam_glue_sealant(group),
                "price_unit": price_unit_for_group(group),
                "party_price_unit": party_price_unit_for_group(group)
                if group_is_foam_glue_sealant(group)
                else price_unit_for_group(group),
            },
        )


class SKUDetailView(View):
    template_name = "catalog/sku_detail.html"

    def get(self, request, slug: str, article: str):
        sku = selectors.get_sku(slug, article)
        if sku is None:
            raise Http404
        _mark_wishlist(request, [sku])
        return render(
            request,
            self.template_name,
            {
                "sku": sku,
                "group": sku.group,
                "sku_image_url": selectors.sku_display_image_url(sku),
                "price_unit": price_unit_for_group(sku.group),
                "party_price_unit": party_price_unit_for_group(sku.group)
                if group_is_foam_glue_sealant(sku.group)
                else price_unit_for_group(sku.group),
                "show_rebar_dims": group_is_rebar(sku.group),
                "show_mesh_dims": group_is_mesh(sku.group),
                "show_wedge_dims": group_is_wedge(sku.group),
                "show_foam_glue_dims": group_is_foam_glue_sealant(sku.group),
            },
        )


@login_required
@require_http_methods(["POST"])
def product_review(request, slug: str):
    form = ReviewForm(request.POST)
    if form.is_valid():
        try:
            create_pending_review(
                user=request.user,
                group_slug=slug,
                rating=form.cleaned_data["rating"],
                body=form.cleaned_data["body"],
            )
        except ReviewError:
            pass
    return redirect("catalog:product", slug=slug)


@require_GET
def search(request):
    q = request.GET.get("q", "")
    groups = selectors.search_groups(q)[:40]
    skus = selectors.search_skus(q)[:20]
    ctx = {"q": q, "groups": groups, "skus": skus}
    if getattr(request, "htmx", False) and request.GET.get("suggest"):
        return render(request, "catalog/partials/search_suggest.html", ctx)
    return render(request, "catalog/search.html", ctx)


class BrandListView(TemplateView):
    template_name = "catalog/brand_list.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["brands"] = selectors.active_brands()
        return ctx


class BrandDetailView(View):
    def get(self, request, slug: str):
        brand = selectors.get_brand(slug)
        if brand is None:
            raise Http404
        return render(
            request,
            "catalog/brand_detail.html",
            {"brand": brand, "groups": selectors.groups_for_brand(brand)},
        )


class CollectionDetailView(View):
    def get(self, request, slug: str):
        collection = selectors.get_collection(slug)
        if collection is None:
            raise Http404
        return render(
            request,
            "catalog/collection_detail.html",
            {"collection": collection},
        )
