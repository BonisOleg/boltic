"""Helpers для SiteBlock на фронті."""

from __future__ import annotations

from django.core.cache import cache

from apps.core.block_defaults import block_default
from apps.core.models import SITE_BLOCKS_CACHE_KEY, SiteBlock

SITE_BLOCKS_CACHE_TTL = 60


def load_site_blocks() -> dict[str, SiteBlock]:
    cached = cache.get(SITE_BLOCKS_CACHE_KEY)
    if cached is not None:
        return cached
    blocks = {b.cache_key: b for b in SiteBlock.objects.filter(is_active=True)}
    cache.set(SITE_BLOCKS_CACHE_KEY, blocks, SITE_BLOCKS_CACHE_TTL)
    return blocks


def get_block(
    page: str, key: str, *, site_blocks: dict[str, SiteBlock] | None = None
) -> SiteBlock | None:
    mapping = site_blocks if site_blocks is not None else load_site_blocks()
    return mapping.get(f"{page}.{key}")


def get_block_text(
    page: str,
    key: str,
    *,
    site_blocks: dict[str, SiteBlock] | None = None,
    fallback: str | None = None,
) -> str:
    block = get_block(page, key, site_blocks=site_blocks)
    if block and block.text_html:
        return block.text_html
    if fallback is not None:
        return fallback
    return block_default(page, key)


def is_section_visible(
    page: str,
    visibility_key: str,
    *,
    site_blocks: dict[str, SiteBlock] | None = None,
) -> bool:
    value = get_block_text(
        page, visibility_key, site_blocks=site_blocks, fallback="1"
    )
    return value not in {"0", "false", "False", ""}


def get_block_url(
    page: str,
    key: str,
    *,
    site_blocks: dict[str, SiteBlock] | None = None,
) -> str:
    block = get_block(page, key, site_blocks=site_blocks)
    if block and block.link_url:
        return block.link_url
    return block_default(page, key)


def get_block_url_label(
    page: str,
    key: str,
    *,
    site_blocks: dict[str, SiteBlock] | None = None,
    fallback: str = "",
) -> str:
    block = get_block(page, key, site_blocks=site_blocks)
    if block and block.link_label:
        return block.link_label
    return fallback
