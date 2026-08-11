"""Defaults, labels, types для SiteBlock registry."""

from __future__ import annotations

BLOCK_LABELS: dict[tuple[str, str], str] = {
    ("home", "hero_section_visible"): "Показувати Hero",
    ("home", "advantages_section_visible"): "Показувати переваги",
    ("home", "advantage_1_title"): "Перевага 1 — заголовок",
    ("home", "advantage_1_text"): "Перевага 1 — текст",
    ("home", "advantage_2_title"): "Перевага 2 — заголовок",
    ("home", "advantage_2_text"): "Перевага 2 — текст",
    ("home", "advantage_3_title"): "Перевага 3 — заголовок",
    ("home", "advantage_3_text"): "Перевага 3 — текст",
    ("home", "advantage_4_title"): "Перевага 4 — заголовок",
    ("home", "advantage_4_text"): "Перевага 4 — текст",
    ("home", "catalog_section_visible"): "Показувати каталог",
    ("home", "catalog_title"): "Заголовок секції каталогу",
    ("home", "catalog_link_label"): "Посилання «усі категорії»",
    ("home", "promo_section_visible"): "Показувати акції",
    ("home", "promo_title"): "Заголовок секції акцій",
    ("home", "promo_link_label"): "Посилання «всі акції»",
    ("home", "tops_section_visible"): "Показувати лідерів",
    ("home", "tops_title"): "Заголовок лідерів продажів",
    ("home", "tops_link_label"): "Посилання «до каталогу»",
    ("home", "news_section_visible"): "Показувати новини",
    ("home", "news_title"): "Заголовок новин",
    ("home", "news_link_label"): "Посилання «всі новини»",
    ("home", "seo_section_visible"): "Показувати SEO-блок",
    ("home", "seo_title"): "SEO заголовок",
    ("home", "seo_body"): "SEO текст",
    ("home", "services_section_visible"): "Показувати сервіси",
    ("home", "service_1_title"): "Сервіс 1 — заголовок",
    ("home", "service_1_text"): "Сервіс 1 — текст",
    ("home", "service_1_url"): "Сервіс 1 — URL",
    ("home", "service_2_title"): "Сервіс 2 — заголовок",
    ("home", "service_2_text"): "Сервіс 2 — текст",
    ("home", "service_2_url"): "Сервіс 2 — URL",
    ("home", "service_3_title"): "Сервіс 3 — заголовок",
    ("home", "service_3_text"): "Сервіс 3 — текст",
    ("home", "service_3_url"): "Сервіс 3 — URL",
    ("site", "header_nav_promo_label"): "Меню: Акції",
    ("site", "header_nav_promo_visible"): "Показувати «Акції»",
    ("site", "header_nav_news_label"): "Меню: Новини",
    ("site", "header_nav_news_visible"): "Показувати «Новини»",
    ("site", "header_nav_delivery_label"): "Меню: Оплата і доставка",
    ("site", "header_nav_delivery_visible"): "Показувати «Оплата і доставка»",
    ("site", "header_nav_contacts_label"): "Меню: Контакти",
    ("site", "header_nav_contacts_visible"): "Показувати «Контакти»",
    ("site", "header_catalog_btn_label"): "Кнопка «Каталог»",
    ("site", "header_search_placeholder"): "Placeholder пошуку",
    ("site", "footer_catalog_title"): "Підвал — Каталог",
    ("site", "footer_buyers_title"): "Підвал — Покупцям",
    ("site", "footer_info_title"): "Підвал — Інформація",
    ("site", "footer_copy_suffix"): "Copyright (після назви)",
    ("site", "footer_cabinet_label"): "Посилання «Кабінет»",
    ("contacts", "contacts_section_visible"): "Показувати сторінку",
    ("contacts", "contacts_title"): "Заголовок",
    ("contacts", "contacts_intro"): "Вступний текст",
}

BLOCK_DEFAULTS: dict[tuple[str, str], str] = {
    ("home", "hero_section_visible"): "1",
    ("home", "advantages_section_visible"): "1",
    ("home", "advantage_1_title"): "Великий асортимент",
    ("home", "advantage_1_text"): "Усі види кріплень для будівництва, ремонту та промисловості",
    ("home", "advantage_2_title"): "Доставка по Україні",
    ("home", "advantage_2_text"): "Швидка відправка замовлень у зручний для вас спосіб",
    ("home", "advantage_3_title"): "Зручна оплата",
    ("home", "advantage_3_text"): "Рахунок-фактура на email або готівка при отриманні",
    ("home", "advantage_4_title"): "Якість і стандарти",
    ("home", "advantage_4_text"): "Кріплення за DIN / ГОСТ із зрозумілими характеристиками",
    ("home", "catalog_section_visible"): "1",
    ("home", "catalog_title"): "Каталог",
    ("home", "catalog_link_label"): "усі категорії",
    ("home", "promo_section_visible"): "1",
    ("home", "promo_title"): "Акційні пропозиції",
    ("home", "promo_link_label"): "всі акції",
    ("home", "tops_section_visible"): "1",
    ("home", "tops_title"): "Лідери продажів",
    ("home", "tops_link_label"): "до каталогу",
    ("home", "news_section_visible"): "1",
    ("home", "news_title"): "Новини та акції",
    ("home", "news_link_label"): "всі новини",
    ("home", "seo_section_visible"): "1",
    ("home", "seo_title"): "Інтернет-магазин кріплення БОЛТіК°. Надійне кріплення для бездоганного результату",
    ("home", "seo_body"): (
        "Вітаємо на сайті БОЛТіК°. У каталозі — болти, гайки, саморізи, анкери, "
        "заклепки та інші види кріплень із зручним підбором за розміром і характеристиками."
    ),
    ("home", "services_section_visible"): "1",
    ("home", "service_1_title"): "Каталог кріплення",
    ("home", "service_1_text"): "Болти, гайки, саморізи, анкери та інше — з фільтрами за розміром",
    ("home", "service_1_url"): "/katalog/",
    ("home", "service_2_title"): "Оплата і доставка",
    ("home", "service_2_text"): "Умови доставки та онлайн-оплати замовлення",
    ("home", "service_2_url"): "/oplata-i-dostavka/",
    ("home", "service_3_title"): "Повернення 14 днів",
    ("home", "service_3_text"): "Прозорі правила обміну та повернення товарів",
    ("home", "service_3_url"): "/povernennya-ta-obmin/",
    ("site", "header_nav_promo_label"): "Акції",
    ("site", "header_nav_promo_visible"): "1",
    ("site", "header_nav_news_label"): "Новини",
    ("site", "header_nav_news_visible"): "1",
    ("site", "header_nav_delivery_label"): "Оплата і доставка",
    ("site", "header_nav_delivery_visible"): "1",
    ("site", "header_nav_contacts_label"): "Контакти",
    ("site", "header_nav_contacts_visible"): "1",
    ("site", "header_catalog_btn_label"): "Каталог",
    ("site", "header_search_placeholder"): "Я шукаю",
    ("site", "footer_catalog_title"): "Каталог",
    ("site", "footer_buyers_title"): "Покупцям",
    ("site", "footer_info_title"): "Інформація",
    ("site", "footer_copy_suffix"): "Всі види кріплень.",
    ("site", "footer_cabinet_label"): "Кабінет",
    ("contacts", "contacts_section_visible"): "1",
    ("contacts", "contacts_title"): "Контакти",
    ("contacts", "contacts_intro"): "",
}

BLOCK_CONTENT_TYPES: dict[tuple[str, str], str] = {
    ("home", "service_1_url"): "url",
    ("home", "service_2_url"): "url",
    ("home", "service_3_url"): "url",
}

INLINE_KEYS = frozenset(
    {
        "advantage_1_title",
        "advantage_2_title",
        "advantage_3_title",
        "advantage_4_title",
        "catalog_title",
        "catalog_link_label",
        "promo_title",
        "promo_link_label",
        "tops_title",
        "tops_link_label",
        "news_title",
        "news_link_label",
        "seo_title",
        "service_1_title",
        "service_2_title",
        "service_3_title",
        "header_nav_promo_label",
        "header_nav_news_label",
        "header_nav_delivery_label",
        "header_nav_contacts_label",
        "header_catalog_btn_label",
        "header_search_placeholder",
        "footer_catalog_title",
        "footer_buyers_title",
        "footer_info_title",
        "footer_copy_suffix",
        "footer_cabinet_label",
        "contacts_title",
    }
)

MULTILINE_KEYS = frozenset(
    {
        "advantage_1_text",
        "advantage_2_text",
        "advantage_3_text",
        "advantage_4_text",
        "seo_body",
        "service_1_text",
        "service_2_text",
        "service_3_text",
        "contacts_intro",
    }
)


def is_visibility_key(key: str) -> bool:
    return key.endswith("_visible")


def block_label(page: str, key: str) -> str:
    return BLOCK_LABELS.get((page, key), key)


def block_default(page: str, key: str) -> str:
    if (page, key) in BLOCK_DEFAULTS:
        return BLOCK_DEFAULTS[(page, key)]
    return "1" if is_visibility_key(key) else ""


def block_content_type(page: str, key: str) -> str:
    if is_visibility_key(key):
        return "text"
    return BLOCK_CONTENT_TYPES.get((page, key), "text")
