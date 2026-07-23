from django.db.models import Min, Prefetch, Q, QuerySet

from apps.catalog.models import (
    Brand,
    Category,
    Collection,
    FacetAttribute,
    ProductGroup,
    ProductImage,
    ProductSKU,
)


def active_groups() -> QuerySet[ProductGroup]:
    return ProductGroup.objects.filter(is_active=True)


def resolve_category(path: str) -> Category | None:
    normalized = path.strip().strip("/") + "/"
    return Category.objects.filter(path=normalized, is_active=True).first()


def category_children(category: Category) -> QuerySet[Category]:
    return category.children.filter(is_active=True).order_by("sort_order", "name")


def parse_facets(querydict) -> dict[str, list[str]]:
    allowed = set(
        FacetAttribute.objects.values_list("code", flat=True)
    )
    selected: dict[str, list[str]] = {}
    for key in querydict.keys():
        if key not in allowed:
            continue
        values = [v for v in querydict.getlist(key) if v]
        if values:
            selected[key] = values
    return selected


def apply_facets(
    groups: QuerySet[ProductGroup], selected: dict[str, list[str]]
) -> QuerySet[ProductGroup]:
    if not selected:
        return groups
    qs = groups
    for code, slugs in selected.items():
        qs = qs.filter(
            skus__is_active=True,
            skus__facets__value__attribute__code=code,
            skus__facets__value__slug__in=slugs,
        )
    return qs.distinct()


def annotate_price_from(groups: QuerySet[ProductGroup]) -> QuerySet[ProductGroup]:
    return groups.annotate(
        price_from=Min(
            "skus__price",
            filter=Q(skus__is_active=True),
        )
    )


def sort_groups(groups: QuerySet[ProductGroup], sort: str) -> QuerySet[ProductGroup]:
    groups = annotate_price_from(groups)
    if sort == "price":
        return groups.order_by("price_from", "name")
    if sort == "name":
        return groups.order_by("name")
    if sort == "new":
        return groups.order_by("-created_at")
    return groups.order_by("name")


def list_groups_for_category(
    category: Category,
    *,
    selected: dict[str, list[str]] | None = None,
    sort: str = "name",
) -> QuerySet[ProductGroup]:
    selected = selected or {}
    if category.level == Category.Level.L1:
        qs = active_groups().filter(category__parent=category)
    else:
        qs = active_groups().filter(category=category)
    qs = apply_facets(qs, selected)
    return sort_groups(qs, sort).select_related("category", "brand").prefetch_related(
        Prefetch(
            "images",
            queryset=ProductImage.objects.filter(is_primary=True),
            to_attr="primary_images",
        )
    )


def get_pdp(slug: str) -> ProductGroup | None:
    return (
        active_groups()
        .filter(slug=slug)
        .select_related("category", "brand")
        .prefetch_related(
            "images",
            "documents",
            Prefetch(
                "skus",
                queryset=ProductSKU.objects.filter(is_active=True).order_by(
                    "diameter", "length", "article"
                ),
            ),
            "reviews",
        )
        .first()
    )


def search_groups(q: str) -> QuerySet[ProductGroup]:
    q = (q or "").strip()
    if len(q) < 2:
        return active_groups().none()
    return annotate_price_from(
        active_groups()
        .filter(Q(name__icontains=q) | Q(slug__icontains=q))
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.filter(is_primary=True),
                to_attr="primary_images",
            )
        )
        .order_by("name")
    )


def search_skus(q: str) -> QuerySet[ProductSKU]:
    q = (q or "").strip()
    if len(q) < 2:
        return ProductSKU.objects.none()
    return (
        ProductSKU.objects.filter(is_active=True, group__is_active=True)
        .filter(Q(article__icontains=q) | Q(name__icontains=q))
        .select_related("group")
        .order_by("article")
    )


def active_brands() -> QuerySet[Brand]:
    return Brand.objects.filter(is_active=True).order_by("name")


def get_brand(slug: str) -> Brand | None:
    return active_brands().filter(slug=slug).first()


def groups_for_brand(brand: Brand) -> QuerySet[ProductGroup]:
    return annotate_price_from(
        active_groups()
        .filter(brand=brand)
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.filter(is_primary=True),
                to_attr="primary_images",
            )
        )
    ).order_by("name")


def get_collection(slug: str) -> Collection | None:
    return (
        Collection.objects.filter(slug=slug, is_published=True)
        .prefetch_related("groups")
        .first()
    )


def root_categories() -> QuerySet[Category]:
    return Category.objects.filter(
        parent__isnull=True, is_active=True, level=Category.Level.L1
    ).order_by("sort_order", "name")


def facet_attributes():
    return FacetAttribute.objects.prefetch_related("values").order_by(
        "sort_order", "name"
    )
