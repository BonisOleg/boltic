from django import template

from apps.catalog.composite_dims import price_unit_for_group

register = template.Library()


@register.filter
def price_unit(group) -> str:
    """Підпис одиниці ціни: грн / шт | м.п. | м²."""
    return price_unit_for_group(group)
