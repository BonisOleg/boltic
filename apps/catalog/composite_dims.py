"""Композитна арматура / сітка / клинки — розміри та одиниці ціни на вітрині."""

from __future__ import annotations

from apps.catalog.models import ProductGroup

PATH_REBAR = "композитна-арматура-сітка-фіксатори-клинки/композитна-арматура/"
PATH_MESH = "композитна-арматура-сітка-фіксатори-клинки/композитна-сітка/"
PATH_WEDGE = "композитна-арматура-сітка-фіксатори-клинки/клинки/"

PRICE_UNIT_MP = "грн / м.п."
PRICE_UNIT_M2 = "грн / м²"
PRICE_UNIT_PCS = "грн / шт"


def _path(group: ProductGroup) -> str:
    cat = getattr(group, "category", None)
    return (getattr(cat, "path", None) or "") if cat is not None else ""


def group_is_rebar(group: ProductGroup) -> bool:
    return _path(group) == PATH_REBAR


def group_is_mesh(group: ProductGroup) -> bool:
    return _path(group) == PATH_MESH


def group_is_wedge(group: ProductGroup) -> bool:
    return _path(group) == PATH_WEDGE


def price_unit_for_group(group: ProductGroup | None) -> str:
    if group is None:
        return PRICE_UNIT_PCS
    path = _path(group)
    if path == PATH_REBAR:
        return PRICE_UNIT_MP
    if path == PATH_MESH:
        return PRICE_UNIT_M2
    return PRICE_UNIT_PCS
