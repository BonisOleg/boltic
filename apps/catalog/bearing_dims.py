"""Стандартні розміри підшипників (d / D / B) і парсинг позначення з назви SKU."""

from __future__ import annotations

import re
from decimal import Decimal

from apps.catalog.models import Category, ProductGroup, ProductSKU

# ISO deep groove (базові типорозміри з каталогу БОЛТіК°)
BEARING_STANDARD_DIMS: dict[str, tuple[Decimal, Decimal, Decimal]] = {
    "607": (Decimal("7"), Decimal("19"), Decimal("6")),
    "608": (Decimal("8"), Decimal("22"), Decimal("7")),
    "6000": (Decimal("10"), Decimal("26"), Decimal("8")),
    "6001": (Decimal("12"), Decimal("28"), Decimal("8")),
    "6202": (Decimal("15"), Decimal("35"), Decimal("11")),
    "6303": (Decimal("17"), Decimal("47"), Decimal("14")),
    "62203": (Decimal("17"), Decimal("40"), Decimal("16")),
}

_BEARING_CODE_RE = re.compile(
    r"(?i)підшипник\s+(\d{3,5})(?:\s|-|$|[A-Za-z])",
)
_BARE_CODE_RE = re.compile(r"(?i)\b(\d{3,5})(?:-?(?:2RS|ZZ|2Z|2RSC3|C3)|)\b")

BEARING_L2_PATH = "підшипники-сальники/підшипники/"


def fmt_mm(value: Decimal | None) -> str:
    if value is None:
        return ""
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def extract_bearing_code(name: str) -> str | None:
    """Витягнути базовий код (607, 6202, …) з назви SKU."""
    text = (name or "").strip()
    if not text:
        return None
    lower = text.lower()
    if "сальник" in lower or "ущільнен" in lower:
        return None
    m = _BEARING_CODE_RE.search(text)
    if m:
        return m.group(1)
    m2 = _BARE_CODE_RE.search(text)
    if m2 and "підшипник" in lower:
        return m2.group(1)
    return None


def lookup_standard_dims(
    code: str,
) -> tuple[Decimal, Decimal, Decimal] | None:
    return BEARING_STANDARD_DIMS.get(code)


def group_is_bearing(group: ProductGroup) -> bool:
    cat = getattr(group, "category", None)
    if cat is None:
        return False
    path = (cat.path or "").lower()
    return path == BEARING_L2_PATH or path.endswith("/підшипники/")


def category_is_bearing_tree(category: Category | None) -> bool:
    if category is None:
        return False
    path = (category.path or "").lower()
    return path.startswith("підшипники-сальники/") and "підшипники" in path


def sku_has_bearing_dims(sku: ProductSKU) -> bool:
    return (
        sku.bore_d_mm is not None
        or sku.od_d_mm is not None
        or sku.width_b_mm is not None
    )


def size_label_from_dims(
    bore: Decimal, od: Decimal, width: Decimal
) -> str:
    return f"{fmt_mm(bore)}×{fmt_mm(od)}×{fmt_mm(width)}"
