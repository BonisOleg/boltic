"""Registry CMS-секцій для Unfold sidebar + proxy admin."""

from __future__ import annotations

from dataclasses import dataclass

from django.urls import reverse_lazy


@dataclass(frozen=True)
class FieldGroup:
    title: str
    keys: tuple[str, ...]


@dataclass(frozen=True)
class ContentSection:
    slug: str
    page_slug: str
    title: str
    blocks: tuple[tuple[str, str], ...]
    sidebar_title: str = ""
    sidebar_icon: str = "edit_note"
    preview_url: str = "/"
    description: str = ""
    visibility_key: str = ""
    field_groups: tuple[FieldGroup, ...] = ()
    admin_model_name: str = ""


def _keys(page: str, *keys: str) -> tuple[tuple[str, str], ...]:
    return tuple((page, k) for k in keys)


CONTENT_SECTIONS: tuple[ContentSection, ...] = (
    ContentSection(
        slug="hero",
        page_slug="home",
        title="Hero-карусель",
        admin_model_name="homeherosettings",
        sidebar_title="Головна — Hero",
        sidebar_icon="image",
        preview_url="/",
        description="Слайди каруселі (фото, заголовок, текст, CTA) + видимість секції.",
        visibility_key="hero_section_visible",
        blocks=_keys("home", "hero_section_visible"),
        field_groups=(FieldGroup("Видимість", ("hero_section_visible",)),),
    ),
    ContentSection(
        slug="advantages",
        page_slug="home",
        title="Переваги",
        admin_model_name="homeadvantagessettings",
        sidebar_title="Головна — Переваги",
        sidebar_icon="star",
        preview_url="/",
        visibility_key="advantages_section_visible",
        blocks=_keys(
            "home",
            "advantages_section_visible",
            "advantage_1_title",
            "advantage_1_text",
            "advantage_2_title",
            "advantage_2_text",
            "advantage_3_title",
            "advantage_3_text",
            "advantage_4_title",
            "advantage_4_text",
        ),
        field_groups=(
            FieldGroup("Видимість", ("advantages_section_visible",)),
            FieldGroup("Картка 1", ("advantage_1_title", "advantage_1_text")),
            FieldGroup("Картка 2", ("advantage_2_title", "advantage_2_text")),
            FieldGroup("Картка 3", ("advantage_3_title", "advantage_3_text")),
            FieldGroup("Картка 4", ("advantage_4_title", "advantage_4_text")),
        ),
    ),
    ContentSection(
        slug="catalog",
        page_slug="home",
        title="Секція каталогу",
        admin_model_name="homecatalogsettings",
        sidebar_title="Головна — Каталог",
        sidebar_icon="category",
        preview_url="/",
        visibility_key="catalog_section_visible",
        blocks=_keys(
            "home",
            "catalog_section_visible",
            "catalog_title",
            "catalog_link_label",
        ),
        field_groups=(
            FieldGroup(
                "Секція",
                ("catalog_section_visible", "catalog_title", "catalog_link_label"),
            ),
        ),
    ),
    ContentSection(
        slug="promo",
        page_slug="home",
        title="Секція акцій",
        admin_model_name="homepromosettings",
        sidebar_title="Головна — Акції",
        sidebar_icon="local_offer",
        preview_url="/",
        visibility_key="promo_section_visible",
        blocks=_keys(
            "home", "promo_section_visible", "promo_title", "promo_link_label"
        ),
        field_groups=(
            FieldGroup(
                "Секція",
                ("promo_section_visible", "promo_title", "promo_link_label"),
            ),
        ),
    ),
    ContentSection(
        slug="tops",
        page_slug="home",
        title="Лідери продажів",
        admin_model_name="hometopssettings",
        sidebar_title="Головна — Лідери",
        sidebar_icon="trending_up",
        preview_url="/",
        visibility_key="tops_section_visible",
        blocks=_keys("home", "tops_section_visible", "tops_title", "tops_link_label"),
        field_groups=(
            FieldGroup(
                "Секція", ("tops_section_visible", "tops_title", "tops_link_label")
            ),
        ),
    ),
    ContentSection(
        slug="news",
        page_slug="home",
        title="Новини на головній",
        admin_model_name="homenewssettings",
        sidebar_title="Головна — Новини",
        sidebar_icon="newspaper",
        preview_url="/",
        visibility_key="news_section_visible",
        blocks=_keys("home", "news_section_visible", "news_title", "news_link_label"),
        field_groups=(
            FieldGroup(
                "Секція", ("news_section_visible", "news_title", "news_link_label")
            ),
        ),
    ),
    ContentSection(
        slug="seo",
        page_slug="home",
        title="SEO-текст",
        admin_model_name="homeseosettings",
        sidebar_title="Головна — SEO",
        sidebar_icon="article",
        preview_url="/",
        visibility_key="seo_section_visible",
        blocks=_keys("home", "seo_section_visible", "seo_title", "seo_body"),
        field_groups=(
            FieldGroup("SEO", ("seo_section_visible", "seo_title", "seo_body")),
        ),
    ),
    ContentSection(
        slug="services",
        page_slug="home",
        title="Сервісні картки",
        admin_model_name="homeservicessettings",
        sidebar_title="Головна — Сервіси",
        sidebar_icon="handyman",
        preview_url="/",
        visibility_key="services_section_visible",
        blocks=_keys(
            "home",
            "services_section_visible",
            "service_1_title",
            "service_1_text",
            "service_1_url",
            "service_2_title",
            "service_2_text",
            "service_2_url",
            "service_3_title",
            "service_3_text",
            "service_3_url",
        ),
        field_groups=(
            FieldGroup("Видимість", ("services_section_visible",)),
            FieldGroup(
                "Картка 1", ("service_1_title", "service_1_text", "service_1_url")
            ),
            FieldGroup(
                "Картка 2", ("service_2_title", "service_2_text", "service_2_url")
            ),
            FieldGroup(
                "Картка 3", ("service_3_title", "service_3_text", "service_3_url")
            ),
        ),
    ),
    ContentSection(
        slug="header",
        page_slug="site",
        title="Шапка",
        admin_model_name="siteheadersettings",
        sidebar_title="Шапка",
        sidebar_icon="web",
        preview_url="/",
        description="Підписи та видимість пунктів верхнього меню.",
        blocks=_keys(
            "site",
            "header_nav_promo_label",
            "header_nav_promo_visible",
            "header_nav_news_label",
            "header_nav_news_visible",
            "header_nav_delivery_label",
            "header_nav_delivery_visible",
            "header_nav_contacts_label",
            "header_nav_contacts_visible",
            "header_catalog_btn_label",
            "header_search_placeholder",
        ),
        field_groups=(
            FieldGroup(
                "Top-bar меню",
                (
                    "header_nav_promo_label",
                    "header_nav_promo_visible",
                    "header_nav_news_label",
                    "header_nav_news_visible",
                    "header_nav_delivery_label",
                    "header_nav_delivery_visible",
                    "header_nav_contacts_label",
                    "header_nav_contacts_visible",
                ),
            ),
            FieldGroup(
                "Пошук і каталог",
                ("header_catalog_btn_label", "header_search_placeholder"),
            ),
        ),
    ),
    ContentSection(
        slug="footer",
        page_slug="site",
        title="Підвал",
        admin_model_name="sitefootersettings",
        sidebar_title="Підвал",
        sidebar_icon="vertical_align_bottom",
        preview_url="/",
        blocks=_keys(
            "site",
            "footer_catalog_title",
            "footer_buyers_title",
            "footer_info_title",
            "footer_copy_suffix",
            "footer_cabinet_label",
        ),
        field_groups=(
            FieldGroup(
                "Колонки",
                (
                    "footer_catalog_title",
                    "footer_buyers_title",
                    "footer_info_title",
                    "footer_cabinet_label",
                    "footer_copy_suffix",
                ),
            ),
        ),
    ),
    ContentSection(
        slug="contacts",
        page_slug="contacts",
        title="Контакти",
        admin_model_name="contactspagesettings",
        sidebar_title="Контакти (тексти)",
        sidebar_icon="call",
        preview_url="/kontakty/",
        visibility_key="contacts_section_visible",
        blocks=_keys(
            "contacts",
            "contacts_section_visible",
            "contacts_title",
            "contacts_intro",
        ),
        field_groups=(
            FieldGroup(
                "Сторінка",
                ("contacts_section_visible", "contacts_title", "contacts_intro"),
            ),
        ),
    ),
)


def get_section(page_slug: str, section_slug: str) -> ContentSection | None:
    for section in CONTENT_SECTIONS:
        if section.page_slug == page_slug and section.slug == section_slug:
            return section
    return None


def all_registry_block_keys() -> list[tuple[str, str]]:
    keys: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for section in CONTENT_SECTIONS:
        for pair in section.blocks:
            if pair not in seen:
                seen.add(pair)
                keys.append(pair)
    return keys


def build_content_sidebar_items() -> list[dict]:
    items = [
        {
            "title": section.sidebar_title or section.title,
            "icon": section.sidebar_icon,
            "link": reverse_lazy(f"admin:core_{section.admin_model_name}_changelist"),
        }
        for section in CONTENT_SECTIONS
    ]
    items.append(
        {
            "title": "Філії",
            "icon": "store",
            "link": reverse_lazy("admin:content_contactbranch_changelist"),
        }
    )
    return items


def build_unfold_navigation() -> list[dict]:
    """Callable для UNFOLD SIDEBAR navigation (request-time)."""
    from django.urls import reverse_lazy as rl

    return [
        {
            "title": "Налаштування",
            "separator": False,
            "items": [
                {
                    "title": "Сайт і бренд",
                    "icon": "settings",
                    "link": rl("admin:core_sitesettings_changelist"),
                },
            ],
        },
        {
            "title": "Контент сторінок",
            "separator": True,
            "items": build_content_sidebar_items(),
        },
        {
            "title": "Контент",
            "separator": True,
            "items": [
                {
                    "title": "Статичні сторінки",
                    "icon": "description",
                    "link": rl("admin:content_staticpage_changelist"),
                },
                {
                    "title": "Новини",
                    "icon": "newspaper",
                    "link": rl("admin:content_newspost_changelist"),
                },
                {
                    "title": "Акції",
                    "icon": "local_offer",
                    "link": rl("admin:content_promotion_changelist"),
                },
            ],
        },

        {
            "title": "Каталог",
            "separator": True,
            "items": [
                {
                    "title": "Товарні групи",
                    "icon": "inventory_2",
                    "link": rl("admin:catalog_productgroup_changelist"),
                },
                {
                    "title": "SKU",
                    "icon": "qr_code_2",
                    "link": rl("admin:catalog_productsku_changelist"),
                },
                {
                    "title": "Імпорт / експорт",
                    "icon": "import_export",
                    "link": rl("admin:catalog_catalogimportexport_changelist"),
                },
                {
                    "title": "Категорії",
                    "icon": "category",
                    "link": rl("admin:catalog_category_changelist"),
                },
                {
                    "title": "Бренди",
                    "icon": "sell",
                    "link": rl("admin:catalog_brand_changelist"),
                },
                {
                    "title": "Підбірки",
                    "icon": "collections",
                    "link": rl("admin:catalog_collection_changelist"),
                },
                {
                    "title": "Фасети",
                    "icon": "filter_alt",
                    "link": rl("admin:catalog_facetattribute_changelist"),
                },
            ],
        },
        {
            "title": "Продажі",
            "separator": True,
            "items": [
                {
                    "title": "Замовлення",
                    "icon": "shopping_cart",
                    "link": rl("admin:orders_order_changelist"),
                },
                {
                    "title": "Платежі",
                    "icon": "payments",
                    "link": rl("admin:payments_paymenttransaction_changelist"),
                },
                {
                    "title": "Кошики",
                    "icon": "shopping_bag",
                    "link": rl("admin:cart_cart_changelist"),
                },
            ],
        },
        {
            "title": "Клієнти",
            "separator": True,
            "items": [
                {
                    "title": "Профілі",
                    "icon": "group",
                    "link": rl("admin:accounts_userprofile_changelist"),
                },
                {
                    "title": "Користувачі",
                    "icon": "person",
                    "link": rl("admin:auth_user_changelist"),
                },
                {
                    "title": "Відгуки",
                    "icon": "rate_review",
                    "link": rl("admin:reviews_review_changelist"),
                },
            ],
        },
    ]
