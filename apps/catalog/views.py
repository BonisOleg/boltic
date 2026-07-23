from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import redirect, render
from django.views import View
from django.views.decorators.http import require_GET, require_http_methods
from django.views.generic import TemplateView

from apps.catalog import selectors
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
            "facet_attributes": selectors.facet_attributes(),
            "sort": sort,
            "canonical_path": category.path,
        }
        if getattr(request, "htmx", False):
            return render(request, self.partial_name, ctx)
        return render(request, self.template_name, ctx)


class ProductDetailView(View):
    template_name = "catalog/product_detail.html"

    def get(self, request, slug: str):
        group = selectors.get_pdp(slug)
        if group is None:
            raise Http404
        highlight = request.GET.get("sku", "")
        reviews = [r for r in group.reviews.all() if r.is_published]
        return render(
            request,
            self.template_name,
            {
                "group": group,
                "skus": group.skus.all(),
                "reviews": reviews,
                "review_form": ReviewForm(),
                "highlight_sku": highlight,
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
