from django import template

from apps.catalog.composite_dims import price_unit_for_group
from apps.catalog.foam_glue_dims import (
    group_is_foam_glue_sealant,
    party_price_unit_for_group,
)

register = template.Library()


@register.filter
def price_unit(group) -> str:
    """Підпис одиниці базової ціни: грн / шт | м.п. | м²."""
    return price_unit_for_group(group)


@register.filter
def party_price_unit(group) -> str:
    """Підпис оптової ціни — завжди за шт (як і роздріб у розділі)."""
    if group_is_foam_glue_sealant(group):
        return party_price_unit_for_group(group)
    return price_unit_for_group(group)
