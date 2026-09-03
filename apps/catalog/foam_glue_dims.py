"""Піни / клеї / герметики — розміри характеристик і підписи цін."""

from __future__ import annotations

from apps.catalog.models import ProductGroup

PATH_PREFIX = "піни-клеї-герметики/"

PRICE_UNIT_PCS = "грн / шт"


def group_is_foam_glue_sealant(group: ProductGroup) -> bool:
    cat = getattr(group, "category", None)
    if cat is None:
        return False
    path = cat.path or ""
    return path.startswith(PATH_PREFIX)


def price_unit_for_group(group: ProductGroup | None) -> str:
    """Базова та оптова ціна в цьому розділі — завжди за штуку."""
    return PRICE_UNIT_PCS


def party_price_unit_for_group(group: ProductGroup | None) -> str:
    """Опт також грн/шт (поріг — wholesale_from_qty)."""
    return PRICE_UNIT_PCS
