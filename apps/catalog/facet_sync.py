"""Побудова FacetAttribute / FacetValue / SKUFacet з полів товарів."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils.text import slugify

from apps.catalog.metric_size import (
    diameter_facet_label,
    diameter_facet_slug,
    group_uses_metric_m,
)
from apps.catalog.models import (
    FacetAttribute,
    FacetValue,
    ProductSKU,
    SKUFacet,
)

# code → (назва, порядок атрибута)
FACET_DEFS: tuple[tuple[str, str, int], ...] = (
    ("standart", "Стандарт", 10),
    ("material", "Матеріал", 20),
    ("klas-micnosti", "Клас міцності", 30),
    ("diametr", "Діаметр", 40),
    ("dovzhyna", "Довжина", 50),
)

_MATERIAL_LABELS = {
    "к.м.": "сталь",
    "к.м": "сталь",
    "сталь": "сталь",
    "конструкційна сталь (к.м.)": "сталь",
    "конструкційна сталь (к.м)": "сталь",
    "а2 нержавіюча сталь": "Нержавіюча сталь А2",
    "а2": "Нержавіюча сталь А2",
}


def _fmt_num(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _material_label(raw: str) -> str:
    key = raw.strip().lower().replace("ё", "е")
    return _MATERIAL_LABELS.get(key, raw.strip())


def _strength_label(raw: str) -> str:
    return f"Клас {raw.strip()}"


def _length_label(value: Decimal) -> str:
    return f"{_fmt_num(value)} мм"


def _ensure_attributes() -> dict[str, FacetAttribute]:
    result: dict[str, FacetAttribute] = {}
    for code, name, sort_order in FACET_DEFS:
        attr, _ = FacetAttribute.objects.update_or_create(
            code=code,
            defaults={"name": name, "sort_order": sort_order},
        )
        result[code] = attr
    return result


def _strength_sort(raw: str) -> int:
    try:
        return int(Decimal(raw.replace(",", ".")) * 100)
    except (InvalidOperation, ValueError, ArithmeticError):
        return 0


def _collect_specs(sku: ProductSKU) -> list[tuple[str, str, str, int]]:
    """Повертає (code, slug, label, sort_order) для SKU."""
    specs: list[tuple[str, str, str, int]] = []
    group = sku.group

    standard = (group.standard or "").strip()
    if standard:
        slug = slugify(standard, allow_unicode=True) or "standart"
        specs.append(("standart", slug[:128], standard, 0))

    material = (group.material or "").strip()
    if material:
        label = _material_label(material)
        slug = slugify(label, allow_unicode=True) or "material"
        specs.append(("material", slug[:128], label, 0))

    strength = (sku.strength_class or "").strip()
    if strength:
        normalized = strength.replace(",", ".")
        slug = normalized.replace(".", "-")
        specs.append(
            (
                "klas-micnosti",
                slug[:128],
                _strength_label(normalized),
                _strength_sort(normalized),
            )
        )

    if sku.diameter is not None:
        metric = group_uses_metric_m(group)
        specs.append(
            (
                "diametr",
                diameter_facet_slug(sku.diameter, metric=metric),
                diameter_facet_label(sku.diameter, metric=metric),
                int(sku.diameter * 100),
            )
        )

    if sku.length is not None:
        num = _fmt_num(sku.length)
        specs.append(
            (
                "dovzhyna",
                f"l-{num}"[:128],
                _length_label(sku.length),
                int(sku.length * 100),
            )
        )

    return specs


@transaction.atomic
def sync_facets_from_skus(*, prune_unused: bool = True) -> dict[str, int]:
    """Ідемпотентно зібрати фасети з активних SKU."""
    attrs = _ensure_attributes()
    attr_ids = [a.id for a in attrs.values()]
    value_cache: dict[tuple[str, str], FacetValue] = {}

    skus = list(
        ProductSKU.objects.filter(is_active=True, group__is_active=True)
        .select_related("group", "group__category", "group__category__parent")
        .order_by("pk")
    )

    # спочатку всі унікальні значення
    pending: dict[tuple[str, str], tuple[str, int]] = {}
    sku_specs: list[list[tuple[str, str, str, int]]] = []
    for sku in skus:
        specs = _collect_specs(sku)
        sku_specs.append(specs)
        for code, slug, label, sort_order in specs:
            key = (code, slug)
            prev = pending.get(key)
            if prev is None or sort_order < prev[1]:
                pending[key] = (label, sort_order)

    for (code, slug), (label, sort_order) in pending.items():
        obj, _ = FacetValue.objects.update_or_create(
            attribute=attrs[code],
            slug=slug,
            defaults={"value": label, "sort_order": sort_order},
        )
        value_cache[(code, slug)] = obj

    SKUFacet.objects.filter(value__attribute_id__in=attr_ids).delete()
    to_create: list[SKUFacet] = []
    for sku, specs in zip(skus, sku_specs, strict=True):
        for code, slug, _label, _sort in specs:
            to_create.append(
                SKUFacet(sku=sku, value=value_cache[(code, slug)])
            )
    SKUFacet.objects.bulk_create(to_create, ignore_conflicts=True)

    for code in ("standart", "material"):
        for i, val in enumerate(
            FacetValue.objects.filter(attribute=attrs[code]).order_by("value")
        ):
            if val.sort_order != i:
                FacetValue.objects.filter(pk=val.pk).update(sort_order=i)

    pruned = 0
    if prune_unused:
        unused = FacetValue.objects.filter(
            attribute_id__in=attr_ids, sku_links__isnull=True
        )
        pruned = unused.count()
        unused.delete()

    return {
        "attributes": len(attrs),
        "values": FacetValue.objects.filter(attribute_id__in=attr_ids).count(),
        "sku_links": len(to_create),
        "skus": len(skus),
        "pruned_values": pruned,
    }
