from django.conf import settings as dj_settings
from django.db.models import Prefetch

from apps.cart.models import WishlistItem
from apps.cart.services import cart_item_count
from apps.catalog.models import Category
from apps.core.block_render import load_site_blocks
from apps.core.models import SiteSettings

_DEFAULT_META = (
    "Інтернет-магазин кріплення {name}. Болти, гайки, саморізи, анкери — "
    "опт і роздріб з доставкою по Україні."
)


def site_settings(request):
    site = SiteSettings.load()
    base = dj_settings.SITE_URL.rstrip("/")
    meta = (site.meta_description or "").strip()
    if not meta:
        meta = _DEFAULT_META.format(name=site.site_name)
    return {
        "site_settings": site,
        "theme_vars": site.theme_css_vars(),
        "site_blocks": load_site_blocks(),
        "seo_canonical": f"{base}{request.path}",
        "seo_description_default": meta,
        "gtm_container_id": getattr(dj_settings, "GTM_CONTAINER_ID", "") or "",
    }


def cart_counter(request):
    try:
        return {"cart_count": cart_item_count(request)}
    except Exception:
        return {"cart_count": 0}


def nav_catalog(request):
    children_qs = Category.objects.filter(is_active=True).order_by(
        "sort_order", "name"
    )
    cats = (
        Category.objects.filter(
            parent__isnull=True,
            is_active=True,
            level=Category.Level.L1,
        )
        .prefetch_related(Prefetch("children", queryset=children_qs))
        .order_by("sort_order", "name")
    )
    wishlist_count = 0
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        wishlist_count = WishlistItem.objects.filter(user=user).count()
    return {
        "nav_categories": cats,
        "wishlist_count": wishlist_count,
    }
