"""Дефолти службових StaticPage: seed без затирання правок адмінки."""

from __future__ import annotations

from apps.content.models import StaticPage
from apps.content.static_page_bodies_1 import (
    BODY_OPLATA_I_DOSTAVKA,
    BODY_POVERNENNYA_TA_OBMIN,
)
from apps.content.static_page_bodies_2 import (
    BODY_POLITYKA_KONFIDENTSIYNOSTI,
    BODY_PUBLICHNYY_DOHOVIR,
)

# Старі заглушки з раннього seed — можна замінити повним текстом.
_STUB_BODIES: frozenset[str] = frozenset(
    {
        "Текст про оплату та доставку.",
        "Повернення протягом 14 днів.",
        "Текст оферти.",
        "Політика обробки персональних даних.",
    }
)

STATIC_PAGE_DEFAULTS: tuple[dict[str, str], ...] = (
    {
        "slug": "oplata-i-dostavka",
        "title": "Оплата і доставка",
        "body": BODY_OPLATA_I_DOSTAVKA,
        "seo_title": "Оплата і доставка — БОЛТіК°",
        "seo_description": (
            "Мінімальна сума 400 грн, самовивіз безкоштовно, доставка Новою Поштою, "
            "оплата рахунком або готівкою при отриманні."
        ),
    },
    {
        "slug": "povernennya-ta-obmin",
        "title": "Повернення та обмін",
        "body": BODY_POVERNENNYA_TA_OBMIN,
        "seo_title": "Повернення та обмін — БОЛТіК°",
        "seo_description": (
            "Правила повернення протягом 14 днів, обмін кріплення, претензії "
            "щодо якості та оформлення повернення в БОЛТіК°."
        ),
    },
    {
        "slug": "publichnyy-dohovir",
        "title": "Публічний договір",
        "body": BODY_PUBLICHNYY_DOHOVIR,
        "seo_title": "Публічний договір (оферта) — БОЛТіК°",
        "seo_description": (
            "Публічна оферта інтернет-магазину БОЛТіК°: умови купівлі-продажу, "
            "оплата, доставка та відповідальність сторін."
        ),
    },
    {
        "slug": "polityka-konfidentsiynosti",
        "title": "Політика конфіденційності",
        "body": BODY_POLITYKA_KONFIDENTSIYNOSTI,
        "seo_title": "Політика конфіденційності — БОЛТіК°",
        "seo_description": (
            "Як БОЛТіК° обробляє персональні дані замовлень, кабінету та cookies "
            "згідно із законодавством України."
        ),
    },
)


def _is_replaceable_body(body: str) -> bool:
    text = (body or "").strip()
    if not text:
        return True
    if text in _STUB_BODIES:
        return True
    return False


def ensure_static_pages(*, force: bool = False) -> dict[str, int]:
    """
    Створює сторінки, якщо немає.
    Оновлює body лише для порожніх / заглушок (або force=True).
    """
    created = 0
    updated = 0
    skipped = 0
    for item in STATIC_PAGE_DEFAULTS:
        slug = item["slug"]
        defaults = {
            "title": item["title"],
            "body": item["body"],
            "seo_title": item["seo_title"],
            "seo_description": item["seo_description"],
            "is_published": True,
        }
        page, was_created = StaticPage.objects.get_or_create(
            slug=slug, defaults=defaults
        )
        if was_created:
            created += 1
            continue
        if force or _is_replaceable_body(page.body):
            page.title = item["title"]
            page.body = item["body"]
            page.seo_title = item["seo_title"]
            page.seo_description = item["seo_description"]
            page.is_published = True
            page.save(
                update_fields=[
                    "title",
                    "body",
                    "seo_title",
                    "seo_description",
                    "is_published",
                ]
            )
            updated += 1
        else:
            skipped += 1
    return {"created": created, "updated": updated, "skipped": skipped}
