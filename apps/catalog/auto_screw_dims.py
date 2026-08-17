"""Автосаморізи: розмір «довжина × діаметр × ширина головки»."""

from __future__ import annotations

from decimal import Decimal

from apps.catalog.models import ProductGroup, ProductSKU

AUTO_SCREW_L2_PATH = "автокріплення/саморізи/"


def fmt_mm(value: Decimal | None) -> str:
    if value is None:
        return ""
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text.replace(".", ",")


def group_is_auto_screw(group: ProductGroup) -> bool:
    cat = getattr(group, "category", None)
    if cat is None:
        return False
    return (cat.path or "") == AUTO_SCREW_L2_PATH


def sku_has_auto_screw_dims(sku: ProductSKU) -> bool:
    return (
        sku.length is not None
        or sku.diameter is not None
        or sku.head_width_mm is not None
    )


def size_label_from_auto_dims(
    length: Decimal, diameter: Decimal, head_width: Decimal
) -> str:
    """Формат як у прайсі: 24×4,2×7,6 (кома в десяткових)."""
    return f"{fmt_mm(length)}×{fmt_mm(diameter)}×{fmt_mm(head_width)}"
