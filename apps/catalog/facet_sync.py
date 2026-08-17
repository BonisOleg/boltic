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
    ("d", "Внутрішній діаметр (мм) d", 60),
    ("D", "Зовнішній діаметр (мм) D", 70),
    ("B", "Ширина (мм) B", 80),
    ("shiryna-golovky", "Ширина головки (мм)", 90),
    ("yacheyka-a", "Ячейка A (мм)", 100),
    ("yacheyka-b", "Ячейка B (мм)", 110),
    ("shyryna", "Ширина (мм)", 120),
    ("tovshchyna", "Товщина (мм)", 130),
    ("obiem", "Обʼєм (мл)", 140),
    ("vyrobnyk", "Виробник", 150),
    ("zona", "Зона застосування", 160),
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

    if sku.bore_d_mm is not None:
        num = _fmt_num(sku.bore_d_mm)
        specs.append(("d", f"d-{num}"[:128], num, int(sku.bore_d_mm * 100)))

    if sku.od_d_mm is not None:
        num = _fmt_num(sku.od_d_mm)
        specs.append(("D", f"D-{num}"[:128], num, int(sku.od_d_mm * 100)))

    if sku.width_b_mm is not None:
        num = _fmt_num(sku.width_b_mm)
        specs.append(("B", f"B-{num}"[:128], num, int(sku.width_b_mm * 100)))

    # Кріпильні diametr/dovzhyna — лише якщо немає підшипникових d/D/B
    has_bearing_dims = (
        sku.bore_d_mm is not None
        or sku.od_d_mm is not None
        or sku.width_b_mm is not None
    )

    if not has_bearing_dims and sku.diameter is not None:
        metric = group_uses_metric_m(group)
        specs.append(
            (
                "diametr",
                diameter_facet_slug(sku.diameter, metric=metric),
                diameter_facet_label(sku.diameter, metric=metric),
                int(sku.diameter * 100),
            )
        )

    if not has_bearing_dims and sku.length is not None:
        num = _fmt_num(sku.length)
        specs.append(
            (
                "dovzhyna",
                f"l-{num}"[:128],
                _length_label(sku.length),
                int(sku.length * 100),
            )
        )

    if sku.head_width_mm is not None:
        num = _fmt_num(sku.head_width_mm)
        specs.append(
            (
                "shiryna-golovky",
                f"hg-{num}"[:128],
                f"{num} мм",
                int(sku.head_width_mm * 100),
            )
        )

    if sku.cell_a_mm is not None:
        num = _fmt_num(sku.cell_a_mm)
        specs.append(
            (
                "yacheyka-a",
                f"ya-{num}"[:128],
                num,
                int(sku.cell_a_mm * 100),
            )
        )

    if sku.cell_b_mm is not None:
        num = _fmt_num(sku.cell_b_mm)
        specs.append(
            (
                "yacheyka-b",
                f"yb-{num}"[:128],
                num,
                int(sku.cell_b_mm * 100),
            )
        )

    if sku.width_mm is not None:
        num = _fmt_num(sku.width_mm)
        specs.append(
            (
                "shyryna",
                f"w-{num}"[:128],
                f"{num} мм",
                int(sku.width_mm * 100),
            )
        )

    if sku.thickness_mm is not None:
        num = _fmt_num(sku.thickness_mm)
        specs.append(
            (
                "tovshchyna",
                f"t-{num}"[:128],
                f"{num} мм",
                int(sku.thickness_mm * 100),
            )
        )

    if sku.volume_ml is not None:
        num = _fmt_num(sku.volume_ml)
        specs.append(
            (
                "obiem",
                f"v-{num}"[:128],
                f"{num} мл",
                int(sku.volume_ml * 100),
            )
        )

    manufacturer = (sku.manufacturer or "").strip()
    if manufacturer:
        slug = slugify(manufacturer, allow_unicode=True) or "vyrobnyk"
        specs.append(("vyrobnyk", slug[:128], manufacturer, 0))

    zone = (sku.application_zone or "").strip()
    if zone:
        zone_labels = {
            "internal": "Внутрішні роботи",
            "external": "Зовнішні роботи",
            "both": "Внутрішні та зовнішні",
        }
        label = zone_labels.get(zone, zone)
        specs.append(("zona", zone[:128], label, 0))

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
