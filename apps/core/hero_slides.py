"""HeroSlide service: seed + frontend fetch."""

from __future__ import annotations

from django.conf import settings

from apps.core.models import HeroSlide

DEFAULT_SLIDES = (
    {
        "title": "БОЛТіК° — всі види кріплень",
        "body": "Інтернет-магазин кріплення. Болти, гайки, саморізи, анкери та системи кріплення.",
        "cta_label": "Перейти в каталог",
        "cta_url": "/katalog/",
        "alt_text": "Кріплення БОЛТіК°",
        "sort_order": 0,
    },
)


def ensure_default_hero_slides() -> int:
    if HeroSlide.objects.exists():
        return 0
    created = 0
    for data in DEFAULT_SLIDES:
        HeroSlide.objects.create(**data, is_active=True)
        created += 1
    return created


def get_hero_slides() -> list[dict]:
    ensure_default_hero_slides()
    qs = HeroSlide.objects.filter(is_active=True).order_by("sort_order", "pk")
    static_fallback = settings.STATIC_URL.rstrip("/") + "/img/hero-fasteners.jpg"
    slides = []
    for slide in qs:
        image_url = ""
        if slide.image:
            try:
                image_url = slide.image.url
            except ValueError:
                image_url = ""
        if not image_url:
            image_url = static_fallback
        slides.append(
            {
                "title": slide.title,
                "body": slide.body,
                "cta_label": slide.cta_label or "Перейти в каталог",
                "cta_url": slide.cta_url or "/katalog/",
                "alt_text": slide.alt_text or slide.title,
                "image_url": image_url,
                "has_image": bool(image_url),
            }
        )
    if slides:
        return slides
    return [
        {
            "title": DEFAULT_SLIDES[0]["title"],
            "body": DEFAULT_SLIDES[0]["body"],
            "cta_label": DEFAULT_SLIDES[0]["cta_label"],
            "cta_url": DEFAULT_SLIDES[0]["cta_url"],
            "alt_text": DEFAULT_SLIDES[0]["alt_text"],
            "image_url": static_fallback,
            "has_image": True,
        }
    ]
