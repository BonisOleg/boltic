from django.db.models import Prefetch, Q
from django.utils import timezone

from apps.catalog.models import ProductGroup, ProductImage
from apps.catalog.selectors import annotate_price_from, root_categories
from apps.content.models import (
    ContactBranch,
    HomeBlock,
    NewsPost,
    Promotion,
    StaticPage,
)

DEFAULT_ADVANTAGES = [
    {
        "title": "Великий асортимент",
        "text": "Усі види кріплень для будівництва, ремонту та промисловості",
    },
    {
        "title": "Доставка по Україні",
        "text": "Швидка відправка замовлень у зручний для вас спосіб",
    },
    {
        "title": "Онлайн-оплата",
        "text": "Безпечна оплата карткою через LiqPay",
    },
    {
        "title": "Якість і стандарти",
        "text": "Кріплення за DIN / ГОСТ із зрозумілими характеристиками",
    },
]

DEFAULT_SERVICES = [
    {
        "title": "Каталог кріплення",
        "text": "Болти, гайки, самонарізи, анкери та інше — з фільтрами за розміром",
        "url_name": "catalog:root",
    },
    {
        "title": "Оплата і доставка",
        "text": "Умови доставки та онлайн-оплати замовлення",
        "url_name": "content:oplata_i_dostavka",
    },
    {
        "title": "Повернення 14 днів",
        "text": "Прозорі правила обміну та повернення товарів",
        "url_name": "content:povernennya_ta_obmin",
    },
]


def _blocks_map():
    return {b.key: b for b in HomeBlock.objects.filter(is_active=True)}


def _primary_prefetch():
    return Prefetch(
        "images",
        queryset=ProductImage.objects.filter(is_primary=True),
        to_attr="primary_images",
    )


def home_context():
    now = timezone.now()
    blocks = _blocks_map()
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
    promos_groups = annotate_price_from(
        ProductGroup.objects.filter(is_active=True, is_promo=True).prefetch_related(
            _primary_prefetch()
        )
    )[:12]
    news = NewsPost.objects.filter(is_published=True).order_by(
        "-published_at", "-id"
    )[:4]

    advantages = []
    for i in range(1, 5):
        b = blocks.get(f"advantage_{i}")
        if b:
            advantages.append({"title": b.title or b.key, "text": b.body})
    if not advantages:
        advantages = DEFAULT_ADVANTAGES

    services = []
    for i in range(1, 4):
        b = blocks.get(f"service_{i}")
        if b:
            services.append(
                {"title": b.title or b.key, "text": b.body, "url": None, "url_name": None}
            )
    if not services:
        services = DEFAULT_SERVICES

    slides = []
    for key, b in sorted(blocks.items(), key=lambda x: x[1].sort_order):
        if key == "hero" or key.startswith("slider"):
            slides.append(b)
    if not slides and "hero" not in blocks:
        slides = []

    return {
        "blocks": list(blocks.values()),
        "blocks_map": blocks,
        "slides": slides,
        "hero": blocks.get("hero"),
        "seo_block": blocks.get("seo_text"),
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
    return active_promotions().filter(slug=slug).prefetch_related("groups").first()


def published_news():
    return NewsPost.objects.filter(is_published=True).order_by("-published_at", "-id")


def get_news(slug: str):
    return published_news().filter(slug=slug).first()


def get_static_page(slug: str):
    return StaticPage.objects.filter(slug=slug, is_published=True).first()


def contact_branches():
    return ContactBranch.objects.filter(is_active=True)
