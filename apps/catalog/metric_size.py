"""Метричний префікс M лише для болт / гвинт / стрижень / гайка (+ автоболти)."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from apps.catalog.models import Category, ProductGroup

# L1: усі L2 — метрична різьба
_METRIC_L1 = frozenset(
    {
        "болти",
        "гвинти",
        "стрижні",
        "меблеве-кріплення",
        "болти-гвинти-стрижні",  # legacy
    }
)
# L2 гайки (не шайби/гровери)
_METRIC_L2 = frozenset({"гайки", "гайки-нержавіючі"})
# Автокріплення → лише болти
_METRIC_AUTO_L1 = "автокріплення"
_METRIC_AUTO_L2 = "болти"

_M_PREFIX_RE = re.compile(r"^[MmМм]")


def _fmt_num(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _dec(raw: str) -> Decimal:
    return Decimal(raw.replace(",", ".").strip())


def uses_metric_m_slugs(l1_slug: str, l2_slug: str) -> bool:
    l1 = (l1_slug or "").strip()
    l2 = (l2_slug or "").strip()
    if l1 in _METRIC_L1:
        return True
    if l2 in _METRIC_L2:
        return True
    if l1 == _METRIC_AUTO_L1 and l2 == _METRIC_AUTO_L2:
        return True
    return False


def category_uses_metric_m(category: Category | None) -> bool:
    if category is None:
        return False
    if category.level == Category.Level.L1:
        return category.slug in _METRIC_L1
    parent = getattr(category, "parent", None)
    l1 = parent.slug if parent is not None else ""
    return uses_metric_m_slugs(l1, category.slug)


def group_uses_metric_m(group: ProductGroup | None) -> bool:
    if group is None:
        return False
    return category_uses_metric_m(group.category)


def format_size_label(
    diameter: Decimal,
    length: Decimal | None = None,
    pitch: Decimal | None = None,
    *,
    metric: bool,
) -> str:
    head = f"M{_fmt_num(diameter)}" if metric else _fmt_num(diameter)
    if pitch is not None and length is not None:
        return f"{head}×{_fmt_num(pitch)}×{_fmt_num(length)}"
    if length is not None:
        return f"{head}×{_fmt_num(length)}"
    return head


def diameter_facet_label(value: Decimal, *, metric: bool) -> str:
    num = _fmt_num(value)
    return f"M{num}" if metric else num


def diameter_facet_slug(value: Decimal, *, metric: bool) -> str:
    num = _fmt_num(value)
    return (f"m-{num}" if metric else f"d-{num}")[:128]


def normalize_size_label(label: str, *, metric: bool) -> str:
    """Нормалізувати розмір; префікс M — лише якщо metric=True."""
    if not label or label == "—":
        return ""
    s = (
        label.strip()
        .replace("Х", "×")
        .replace("х", "×")
        .replace("x", "×")
        .replace("*", "×")
        .replace(" ", "")
    )
    s = _M_PREFIX_RE.sub("", s)
    if s.lower().startswith("m") and len(s) > 1 and (s[1].isdigit() or s[1] == "."):
        s = s[1:]
    parts = s.split("×")
    out: list[str] = []
    for i, part in enumerate(parts):
        token = part
        if i == 0:
            token = _M_PREFIX_RE.sub("", token)
        try:
            num = _fmt_num(_dec(token))
        except InvalidOperation:
            out.append(token)
            continue
        if i == 0 and metric:
            out.append("M" + num)
        else:
            out.append(num)
    return "×".join(out)


def canonical_size_key(label: str) -> str:
    """Ключ зіставлення без префікса M (M8×40 == 8×40)."""
    return normalize_size_label(label or "", metric=False)


def rebuild_size_label_from_parts(
    diameter: Decimal | None,
    length: Decimal | None,
    pitch: Decimal | None,
    *,
    metric: bool,
    fallback: str = "",
) -> str:
    if diameter is None:
        if fallback and fallback != "—":
            return normalize_size_label(fallback, metric=metric) or fallback
        return fallback or "—"
    return format_size_label(diameter, length, pitch, metric=metric)


_SIZE_TOKEN_RE = re.compile(
    r"(?<![/\w])[MmМм]\s*"
    r"(\d+(?:[.,]\d+)?)"
    r"(?:\s*[xх\*×]\s*(\d+(?:[.,]\d+)?)"
    r"(?:\s*[xх\*×]\s*(\d+(?:[.,]\d+)?))?)?",
    re.IGNORECASE,
)


def strip_m_prefix_in_text(text: str, *, metric: bool) -> str:
    """У назві прибрати зайвий M/М перед розміром (для неметричних)."""
    if not text or metric:
        return text

    def repl(m: re.Match) -> str:
        d = m.group(1).replace(",", ".")
        try:
            d = _fmt_num(_dec(d))
        except InvalidOperation:
            d = m.group(1)
        parts = [d]
        if m.group(2):
            try:
                parts.append(_fmt_num(_dec(m.group(2))))
            except InvalidOperation:
                parts.append(m.group(2))
        if m.group(3):
            try:
                parts.append(_fmt_num(_dec(m.group(3))))
            except InvalidOperation:
                parts.append(m.group(3))
        return "×".join(parts)

    return _SIZE_TOKEN_RE.sub(repl, text)
