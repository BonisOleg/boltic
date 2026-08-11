"""Парсинг і зіставлення рядків goods.xlsx з ProductSKU."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Iterable

from apps.catalog.classification import infer_group_name, resolve_goods_category
from apps.catalog.import_parser import parse_group_meta
from apps.catalog.metric_size import (
    canonical_size_key,
    format_size_label,
    normalize_size_label,
    uses_metric_m_slugs,
)


_SIZE_RE = re.compile(
    r"(?<![/\w])[MmМм]?\s*"
    r"(\d+(?:[.,]\d+)?)"
    r"(?:\s*/\s*\d+(?:[.,]\d+)?)?"
    r"\s*[xх\*×]\s*"
    r"(?:(\d+(?:[.,]\d+)?)\s*[xх\*×]\s*)?"
    r"(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)
_DIN_RE = re.compile(r"DIN\s*(\d+)", re.I)
_CLS_RE = re.compile(
    r"(?:кл\.?\s*(?:пр|міц)\.?|клас(?:\s*м(?:іц(?:н(?:ості)?)?)?\.?)?|"
    r"к\.?\s*м\.?)\s*([0-9]+[.,][0-9]+)",
    re.I,
)
_BARE_CLS_RE = re.compile(r"\b(5[.,]8|8[.,]8|10[.,]9|12[.,]9)\b")


def _dec(raw: str) -> Decimal:
    return Decimal(raw.replace(",", ".").strip())


@dataclass(frozen=True)
class ParsedGoodsRow:
    row_num: int
    name: str
    code: str
    group_name: str
    price: Decimal
    stock_qty: int
    size_label: str
    diameter: Decimal | None
    length: Decimal | None
    thread_pitch: Decimal | None
    din: str
    strength_class: str
    barcode: str


def parse_size_from_name(
    name: str, *, metric: bool = True
) -> tuple[str, Decimal | None, Decimal | None, Decimal | None]:
    m = _SIZE_RE.search(name or "")
    if not m:
        return "", None, None, None
    d = _dec(m.group(1))
    pitch_raw = m.group(2)
    length = _dec(m.group(3))
    pitch = _dec(pitch_raw) if pitch_raw else None
    # евристика: M10×1×20 (pitch), а не M10×1 як розмір
    if pitch is not None and pitch < 3 and length >= 5:
        label = format_size_label(d, length, pitch, metric=metric)
        return label, d, length, pitch
    if pitch is not None:
        # рідкісний випадок двох чисел без явного pitch — трактуємо як d×l
        label = format_size_label(d, pitch, None, metric=metric)
        return label, d, pitch, None
    label = format_size_label(d, length, None, metric=metric)
    return label, d, length, None


def extract_din(*texts: str) -> str:
    for t in texts:
        m = _DIN_RE.search(t or "")
        if m:
            return m.group(1)
    return ""


def extract_strength(*texts: str) -> str:
    for t in texts:
        m = _CLS_RE.search(t or "") or _BARE_CLS_RE.search(t or "")
        if m:
            return m.group(1).replace(",", ".")
    return ""


def parse_price(raw) -> Decimal:
    if raw is None or raw == "":
        raise InvalidOperation("empty price")
    if isinstance(raw, (int, float, Decimal)):
        return Decimal(str(raw)).quantize(Decimal("0.01"))
    text = str(raw).strip().replace(" ", "").replace(",", ".")
    return Decimal(text).quantize(Decimal("0.01"))


def parse_stock(raw) -> int:
    if raw is None or raw == "":
        return 0
    if isinstance(raw, (int, float, Decimal)):
        return max(0, int(Decimal(str(raw))))
    text = str(raw).strip().replace(" ", "").replace(",", ".")
    try:
        return max(0, int(Decimal(text)))
    except InvalidOperation:
        return 0


def iter_goods_rows(rows: Iterable[tuple]) -> list[ParsedGoodsRow]:
    result: list[ParsedGoodsRow] = []
    for i, row in enumerate(rows, start=2):
        cells = list(row) + [None] * 11
        name_raw, code_raw, group_raw = cells[0], cells[1], cells[2]
        barcode_raw, price_raw, stock_raw = cells[3], cells[6], cells[10]
        if code_raw is None and name_raw is None:
            continue
        code = str(code_raw).strip() if code_raw is not None else ""
        if not code:
            continue
        name = str(name_raw).strip() if name_raw is not None else code
        group_name = str(group_raw).strip() if group_raw else ""
        if not group_name:
            group_name = infer_group_name(name)
        l1, l2 = resolve_goods_category(group_name, name)
        metric = uses_metric_m_slugs(l1, l2)
        size_label, diameter, length, pitch = parse_size_from_name(
            name, metric=metric
        )
        size_label = (
            normalize_size_label(size_label, metric=metric) if size_label else ""
        )
        din = extract_din(name, group_name)
        strength = extract_strength(name, group_name)
        if not strength:
            meta = parse_group_meta(group_name)
            strength = meta.get("strength_class") or ""
        if not din:
            meta = parse_group_meta(group_name)
            std = meta.get("standard") or ""
            din = extract_din(std)
        try:
            price = parse_price(price_raw)
        except InvalidOperation:
            price = Decimal("0.00")
        result.append(
            ParsedGoodsRow(
                row_num=i,
                name=name[:255],
                code=code[:64],
                group_name=group_name[:255],
                price=price,
                stock_qty=parse_stock(stock_raw),
                size_label=size_label[:64] if size_label else "—",
                diameter=diameter,
                length=length,
                thread_pitch=pitch,
                din=din,
                strength_class=strength,
                barcode=str(barcode_raw).strip() if barcode_raw is not None else "",
            )
        )
    return result


def match_key(size: str, din: str, strength: str) -> tuple[str, str, str]:
    return (
        canonical_size_key(size),
        str(din or ""),
        (strength or "").replace(",", "."),
    )
