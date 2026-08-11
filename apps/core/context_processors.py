from django.db.models import Prefetch

from apps.cart.models import WishlistItem
from apps.cart.services import cart_item_count
from apps.catalog.models import Category
from apps.core.block_render import load_site_blocks
from apps.core.models import SiteSettings


def site_settings(request):
    settings = SiteSettings.load()
    return {
        "site_settings": settings,
        "theme_vars": settings.theme_css_vars(),
        "site_blocks": load_site_blocks(),
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
