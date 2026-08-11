from django.db.models import Prefetch, Q
from django.utils import timezone

from apps.catalog.models import ProductGroup, ProductImage
from apps.catalog.selectors import annotate_price_from, root_categories
from apps.content.models import ContactBranch, NewsPost, Promotion, StaticPage
from apps.core.block_render import get_block_text, get_block_url, is_section_visible
from apps.core.hero_slides import get_hero_slides


def _primary_prefetch():
    return Prefetch(
        "images",
        queryset=ProductImage.objects.filter(is_primary=True),
        to_attr="primary_images",
    )


def promo_products(*, limit: int | None = None):
    qs = annotate_price_from(
        ProductGroup.objects.filter(is_active=True, is_promo=True).prefetch_related(
            _primary_prefetch()
        )
    )
    if limit is not None:
        return qs[:limit]
    return qs


def home_context():
    now = timezone.now()
    promos = (
        Promotion.objects.filter(is_published=True)
        .filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gte=now),
        )
        .prefetch_related("groups")[:8]
    )
    tops = annotate_price_from(
        ProductGroup.objects.filter(is_active=True, is_top=True).prefetch_related(
            _primary_prefetch()
        )
    )[:12]
    promos_groups = promo_products(limit=12)
    news = NewsPost.objects.filter(is_published=True).order_by(
        "-published_at", "-id"
    )[:4]

    advantages = []
    for i in range(1, 5):
        title = get_block_text("home", f"advantage_{i}_title")
        text = get_block_text("home", f"advantage_{i}_text")
        if title or text:
            advantages.append({"title": title, "text": text})

    services = []
    for i in range(1, 4):
        title = get_block_text("home", f"service_{i}_title")
        text = get_block_text("home", f"service_{i}_text")
        url = get_block_url("home", f"service_{i}_url")
        services.append({"title": title, "text": text, "url": url, "url_name": None})

    return {
        "slides": get_hero_slides(),
        "show_hero": is_section_visible("home", "hero_section_visible"),
        "show_advantages": is_section_visible("home", "advantages_section_visible"),
        "show_catalog": is_section_visible("home", "catalog_section_visible"),
        "show_promo": is_section_visible("home", "promo_section_visible"),
        "show_tops": is_section_visible("home", "tops_section_visible"),
        "show_news": is_section_visible("home", "news_section_visible"),
        "show_seo": is_section_visible("home", "seo_section_visible"),
        "show_services": is_section_visible("home", "services_section_visible"),
        "catalog_title": get_block_text("home", "catalog_title"),
        "catalog_link_label": get_block_text("home", "catalog_link_label"),
        "promo_title": get_block_text("home", "promo_title"),
        "promo_link_label": get_block_text("home", "promo_link_label"),
        "tops_title": get_block_text("home", "tops_title"),
        "tops_link_label": get_block_text("home", "tops_link_label"),
        "news_title": get_block_text("home", "news_title"),
        "news_link_label": get_block_text("home", "news_link_label"),
        "seo_title": get_block_text("home", "seo_title"),
        "seo_body": get_block_text("home", "seo_body"),
        "advantages": advantages,
        "services": services,
        "categories": root_categories(),
        "promotions": promos,
        "promo_products": promos_groups,
        "top_products": tops,
        "news_posts": news,
    }


def active_promotions():
    now = timezone.now()
    return Promotion.objects.filter(is_published=True).filter(
        Q(starts_at__isnull=True) | Q(starts_at__lte=now),
        Q(ends_at__isnull=True) | Q(ends_at__gte=now),
    )


def get_promotion(slug: str):
    return active_promotions().filter(slug=slug).first()


def promotion_groups(promo: Promotion):
    return annotate_price_from(
        promo.groups.filter(is_active=True).prefetch_related(_primary_prefetch())
    )


def published_news():
    return NewsPost.objects.filter(is_published=True).order_by("-published_at", "-id")


def get_news(slug: str):
    return published_news().filter(slug=slug).first()


def get_static_page(slug: str):
    return StaticPage.objects.filter(slug=slug, is_published=True).first()


def contact_branches():
    return ContactBranch.objects.filter(is_active=True)
