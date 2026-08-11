"""Схема повного дампу каталогу (SKU + група + категорії)."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


FORMAT_ID = "boltiko_catalog_full"
FORMAT_VERSION = 1

# Порядок колонок для CSV / XLSX / XML / JSON items
FULL_DUMP_FIELDS: tuple[str, ...] = (
    "article",
    "name",
    "size_label",
    "diameter",
    "length",
    "thread_pitch",
    "strength_class",
    "min_party",
    "stock_status",
    "stock_qty",
    "price",
    "price_includes_vat",
    "vat_rate",
    "party_price",
    "is_active",
    "group_name",
    "group_slug",
    "group_standard",
    "group_material",
    "group_coating",
    "group_industry",
    "group_short_description",
    "group_description",
    "group_is_top",
    "group_is_promo",
    "group_is_active",
    "group_seo_title",
    "group_seo_description",
    "brand_slug",
    "brand_name",
    "category_l1_slug",
    "category_l1_name",
    "category_l2_slug",
    "category_l2_name",
    "barcode",
)

GOODS_HEADER_ALIASES = {
    "ім'я товару": "name",
    "имя товару": "name",
    "код": "code",
    "група товарів": "group_name",
    "штрихкод": "barcode",
    "штрихкоди": "barcodes",
    "укт зед": "uktzed",
    "ціна (в гривнях)": "price",
    "ціна": "price",
    "ваговий товар": "is_weighted",
    "тип товару": "product_type",
    "податкові ставки": "tax",
    "залишок": "stock_qty",
}


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "так", "t", "on"}:
        return True
    if text in {"0", "false", "no", "n", "ні", "f", "off"}:
        return False
    return default


def _as_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip().replace(" ", "").replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return None


def _as_int(value: Any, default: int | None = None) -> int | None:
    if value is None or value == "":
        return default
    if isinstance(value, int):
        return value
    try:
        return int(Decimal(str(value).strip().replace(",", ".")))
    except (InvalidOperation, ValueError):
        return default


def normalize_header(raw: Any) -> str:
    text = _as_str(raw).lower().replace("\ufeff", "")
    return GOODS_HEADER_ALIASES.get(text, text)


def detect_format(headers: list[str]) -> str:
    """Повертає 'goods' | 'full' | ''."""
    normalized = {normalize_header(h) for h in headers if h}
    if "code" in normalized and ("name" in normalized or "group_name" in normalized):
        # goods.xlsx (Код) без колонки article
        if "article" not in normalized:
            return "goods"
    if "article" in normalized:
        return "full"
    return ""


def cell_to_export(value: Any) -> str | int | float | bool | None:
    if value is None:
        return ""
    if isinstance(value, bool):
        return value
    if isinstance(value, Decimal):
        text = format(value.normalize(), "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    return value


def parse_full_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Нормалізує рядок повного дампу до типізованого dict."""
    get = lambda key: raw.get(key, raw.get(key.lower()))
    article = _as_str(get("article"))
    price = _as_decimal(get("price"))
    if price is None:
        price = Decimal("0.00")
    return {
        "article": article[:64],
        "name": _as_str(get("name"))[:255] or article,
        "size_label": _as_str(get("size_label"))[:64] or "—",
        "diameter": _as_decimal(get("diameter")),
        "length": _as_decimal(get("length")),
        "thread_pitch": _as_decimal(get("thread_pitch")),
        "strength_class": _as_str(get("strength_class"))[:32],
        "min_party": max(1, _as_int(get("min_party"), 1) or 1),
        "stock_status": _as_str(get("stock_status")) or "in_stock",
        "stock_qty": _as_int(get("stock_qty"), None),
        "price": price.quantize(Decimal("0.01")),
        "price_includes_vat": _as_bool(get("price_includes_vat"), True),
        "vat_rate": (_as_decimal(get("vat_rate")) or Decimal("20")).quantize(
            Decimal("0.01")
        ),
        "party_price": _as_decimal(get("party_price")),
        "is_active": _as_bool(get("is_active"), True),
        "group_name": _as_str(get("group_name"))[:255],
        "group_slug": _as_str(get("group_slug"))[:255],
        "group_standard": _as_str(get("group_standard"))[:64],
        "group_material": _as_str(get("group_material"))[:128],
        "group_coating": _as_str(get("group_coating"))[:128],
        "group_industry": _as_str(get("group_industry"))[:128],
        "group_short_description": _as_str(get("group_short_description")),
        "group_description": _as_str(get("group_description")),
        "group_is_top": _as_bool(get("group_is_top"), False),
        "group_is_promo": _as_bool(get("group_is_promo"), False),
        "group_is_active": _as_bool(get("group_is_active"), True),
        "group_seo_title": _as_str(get("group_seo_title"))[:255],
        "group_seo_description": _as_str(get("group_seo_description")),
        "brand_slug": _as_str(get("brand_slug"))[:255],
        "brand_name": _as_str(get("brand_name"))[:255],
        "category_l1_slug": _as_str(get("category_l1_slug"))[:255],
        "category_l1_name": _as_str(get("category_l1_name"))[:255],
        "category_l2_slug": _as_str(get("category_l2_slug"))[:255],
        "category_l2_name": _as_str(get("category_l2_name"))[:255],
        "barcode": _as_str(get("barcode"))[:64],
    }
