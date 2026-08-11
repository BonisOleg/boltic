"""Help text для CMS / image profiles."""

IMAGE_PROFILES = {
    "hero": {
        "recommended": "1920×600",
        "max_size_mb": 3,
        "hint": "Рекомендовано 1920×600 (шир. банер ~16:5), WebP/JPG до 3 МБ. Важливі деталі — праворуч: зліва текст і затемнення.",
    },
    "brand": {
        "recommended": "SVG або PNG",
        "max_size_mb": 1,
        "hint": "Логотип PNG/SVG, висота ~56–80 px",
    },
    "product": {
        "recommended": "800×800",
        "max_size_mb": 2,
        "hint": "Квадратне фото товару до 2 МБ",
    },
}

TEXT_LIMITS = {
    "seo_title": 120,
    "seo_body": 2000,
    "advantage_title": 60,
    "hero_title": 100,
}


def get_image_hint(profile: str) -> str:
    data = IMAGE_PROFILES.get(profile, {})
    return data.get("hint", "")


def get_text_limit_hint(key: str) -> str:
    limit = TEXT_LIMITS.get(key)
    if not limit:
        return ""
    return f"Рекомендовано до {limit} символів"
