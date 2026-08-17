"""Піни / клеї / герметики — розміри характеристик і підписи цін."""

from __future__ import annotations

from apps.catalog.models import ProductGroup

PATH_PREFIX = "піни-клеї-герметики/"

PRICE_UNIT_PCS = "грн / шт"
PRICE_UNIT_PACK = "грн / упак."


def group_is_foam_glue_sealant(group: ProductGroup) -> bool:
    cat = getattr(group, "category", None)
    if cat is None:
        return False
    path = cat.path or ""
    return path.startswith(PATH_PREFIX)


def price_unit_for_group(group: ProductGroup | None) -> str:
    """Базова ціна — завжди за штуку в цьому розділі."""
    if group is not None and group_is_foam_glue_sealant(group):
        return PRICE_UNIT_PCS
    return PRICE_UNIT_PCS


def party_price_unit_for_group(group: ProductGroup | None) -> str:
    if group is not None and group_is_foam_glue_sealant(group):
        return PRICE_UNIT_PACK
    return PRICE_UNIT_PCS
