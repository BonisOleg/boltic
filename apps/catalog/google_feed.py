"""Google Merchant RSS 2.0 фід: 1 item = 1 ProductSKU."""

from __future__ import annotations

import re
from decimal import Decimal
from xml.sax.saxutils import escape

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.http import require_GET

from apps.catalog.models import ProductImage, ProductSKU
from apps.catalog.pricing import retail_unit_price
from apps.core.models import SiteSettings

_G_NS = "http://base.google.com/ns/1.0"
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_WS = re.compile(r"\s+")
_PRICE = Decimal("0.01")
_MAX_TITLE = 150
_MAX_DESC = 5000
_MAX_EXTRA_IMGS = 10
_CACHE_KEY = "catalog:google_merchant_feed_v1"


def _site_base() -> str:
    return settings.SITE_URL.rstrip("/")


def absolute_url(path: str) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = _site_base()
    return f"{base}{path}" if path.startswith("/") else f"{base}/{path}"


def _xml(text: str) -> str:
    return escape(_CTRL.sub("", text or ""))


def _plain(text: str, limit: int) -> str:
    cleaned = _WS.sub(" ", strip_tags(text or "")).strip()
    if len(cleaned) > limit:
        return cleaned[: limit - 1].rstrip() + "…"
    return cleaned


def _price_text(amount: Decimal) -> str:
    return f"{amount.quantize(_PRICE)} UAH"


def _media_url(field) -> str:
    if not field:
        return ""
    try:
        return field.url
    except ValueError:
        return ""


def _group_images(sku: ProductSKU) -> list[ProductImage]:
    images = list(sku.group.images.all())
    images.sort(key=lambda img: (not img.is_primary, img.sort_order, img.pk or 0))
    return [img for img in images if _media_url(img.image)]


def _image_urls(sku: ProductSKU) -> tuple[str, list[str]]:
    extra: list[str] = []
    sku_url = _media_url(sku.image)
    group_imgs = _group_images(sku)
    if sku_url:
        primary = absolute_url(sku_url)
        for img in group_imgs:
            url = absolute_url(_media_url(img.image))
            if url and url != primary:
                extra.append(url)
        return primary, extra[:_MAX_EXTRA_IMGS]
    if not group_imgs:
        return "", []
    primary = absolute_url(_media_url(group_imgs[0].image))
    for img in group_imgs[1:]:
        url = absolute_url(_media_url(img.image))
        if url and url != primary:
            extra.append(url)
    return primary, extra[:_MAX_EXTRA_IMGS]


def _availability(sku: ProductSKU) -> str:
    if sku.stock_status == ProductSKU.StockStatus.ON_ORDER:
        return "backorder"
    if sku.stock_qty == 0:
        return "out_of_stock"
    return "in_stock"


def _brand(sku: ProductSKU, fallback: str) -> str:
    brand = sku.group.brand
    if brand is not None and brand.is_active and brand.name.strip():
        return brand.name.strip()
    manufacturer = (sku.manufacturer or "").strip()
    if manufacturer:
        return manufacturer
    return fallback


def _product_type(sku: ProductSKU) -> str:
    category = sku.group.category
    if category is None:
        return ""
    parent = category.parent
    if parent is not None:
        return f"{parent.name} > {category.name}"
    return category.name


def _description(sku: ProductSKU) -> str:
    group = sku.group
    for raw in (group.description, group.short_description, sku.name, group.name):
        text = _plain(raw, _MAX_DESC)
        if text:
            return text
    return sku.article


def feed_skus_qs():
    return (
        ProductSKU.objects.filter(
            is_active=True,
            group__is_active=True,
            price__gt=0,
        )
        .select_related(
            "group",
            "group__category",
            "group__category__parent",
            "group__brand",
        )
        .prefetch_related("group__images")
        .order_by("article")
    )


def _item_xml(sku: ProductSKU, *, brand_fallback: str) -> str | None:
    image_link, extra = _image_urls(sku)
    if not image_link:
        return None
    title = _plain(sku.name or sku.article, _MAX_TITLE)
    if not title:
        return None
    retail = retail_unit_price(sku)
    if retail <= 0:
        return None
    link = absolute_url(
        reverse(
            "catalog:sku_detail",
            kwargs={"slug": sku.group.slug, "article": sku.article},
        )
    )
    parts = [
        "<item>",
        f"<g:id>{_xml(sku.article)}</g:id>",
        f"<title>{_xml(title)}</title>",
        f"<description>{_xml(_description(sku))}</description>",
        f"<link>{_xml(link)}</link>",
        f"<g:image_link>{_xml(image_link)}</g:image_link>",
    ]
    for url in extra:
        parts.append(f"<g:additional_image_link>{_xml(url)}</g:additional_image_link>")
    parts.extend(
        [
            f"<g:availability>{_availability(sku)}</g:availability>",
            "<g:condition>new</g:condition>",
            f"<g:brand>{_xml(_brand(sku, brand_fallback))}</g:brand>",
            f"<g:item_group_id>{sku.group_id}</g:item_group_id>",
            f"<g:mpn>{_xml(sku.article)}</g:mpn>",
            "<g:identifier_exists>no</g:identifier_exists>",
            f"<g:price>{_price_text(sku.price)}</g:price>",
        ]
    )
    sale = sku.sale_price
    if sale is not None and sale > 0 and sale < sku.price:
        parts.append(f"<g:sale_price>{_price_text(sale)}</g:sale_price>")
    product_type = _product_type(sku)
    if product_type:
        parts.append(f"<g:product_type>{_xml(product_type)}</g:product_type>")
    size_label = (sku.size_label or "").strip()
    if size_label:
        parts.append(f"<g:size>{_xml(size_label)}</g:size>")
    parts.append("</item>")
    return "".join(parts)


def build_google_feed_xml() -> str:
    site = SiteSettings.load()
    name = site.site_name or "БОЛТіК°"
    home = f"{_site_base()}/"
    chunks = [
        "<?xml version='1.0' encoding='utf-8'?>",
        f'<rss xmlns:g="{_G_NS}" version="2.0"><channel>',
        f"<title>{_xml(name)}</title>",
        f"<link>{_xml(home)}</link>",
        f"<description>{_xml(f'Каталог {name} для Google Ads')}</description>",
    ]
    for sku in feed_skus_qs():
        item = _item_xml(sku, brand_fallback=name)
        if item:
            chunks.append(item)
    chunks.append("</channel></rss>")
    return "".join(chunks)


@require_GET
def google_merchant_feed(request):
    ttl = int(getattr(settings, "GOOGLE_FEED_CACHE_SECONDS", 0) or 0)
    xml = cache.get(_CACHE_KEY) if ttl > 0 else None
    if not xml:
        xml = build_google_feed_xml()
        if ttl > 0:
            cache.set(_CACHE_KEY, xml, ttl)
    response = HttpResponse(xml, content_type="application/xml; charset=utf-8")
    if ttl > 0:
        response["Cache-Control"] = f"public, max-age={ttl}"
    else:
        response["Cache-Control"] = "no-store"
    return response
