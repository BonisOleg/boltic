from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

from apps.core.block_render import (
    get_block,
    get_block_text,
    get_block_url,
    get_block_url_label,
    is_section_visible,
)

register = template.Library()


@register.simple_tag(takes_context=True)
def block_plain(context, page: str, key: str, fallback: str = "") -> str:
    site_blocks = context.get("site_blocks")
    text = get_block_text(
        page, key, site_blocks=site_blocks, fallback=fallback or None
    )
    return escape(text)


@register.simple_tag(takes_context=True)
def section_visible(context, page: str, visibility_key: str) -> bool:
    return is_section_visible(
        page, visibility_key, site_blocks=context.get("site_blocks")
    )


@register.simple_tag(takes_context=True)
def block_url(context, page: str, key: str) -> str:
    return get_block_url(page, key, site_blocks=context.get("site_blocks"))


@register.simple_tag(takes_context=True)
def block_url_label(context, page: str, key: str, fallback: str = "") -> str:
    return escape(
        get_block_url_label(
            page, key, site_blocks=context.get("site_blocks"), fallback=fallback
        )
    )


@register.simple_tag(takes_context=True)
def block_image(context, page: str, key: str, css_class: str = "", alt: str = ""):
    block = get_block(page, key, site_blocks=context.get("site_blocks"))
    if not block or not block.image:
        return ""
    cls = f' class="{escape(css_class)}"' if css_class else ""
    alt_text = escape(alt or block.label or "")
    return mark_safe(
        f'<img src="{escape(block.image.url)}" alt="{alt_text}"{cls} loading="lazy">'
    )
