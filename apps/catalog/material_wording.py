"""Заміна матеріалу «к.м.» → «сталь»."""

from __future__ import annotations

import re

MATERIAL_STEEL = "сталь"

# окреме «к.м.» / «к.м» (не частина «кл.міц»)
_KM_TEXT_RE = re.compile(
    r"(?<![А-Яа-яІіЇїЄєҐґA-Za-z])к\.м\.?(?![А-Яа-яІіЇїЄєҐґA-Za-z])",
    re.IGNORECASE,
)
_KM_SLUG_RE = re.compile(r"(^|-)км($|-)", re.IGNORECASE)

# повна стара фасет-мітка
_FACET_OLD = re.compile(
    r"конструкційна\s+сталь\s*\(\s*к\.м\.?\s*\)",
    re.IGNORECASE,
)


def is_km_material(raw: str) -> bool:
    key = (raw or "").strip().lower().replace("ё", "е")
    return key in {"к.м.", "к.м", "км"} or bool(_FACET_OLD.fullmatch(key))


def normalize_material(raw: str) -> str:
    if is_km_material(raw):
        return MATERIAL_STEEL
    return (raw or "").strip()


def fix_km_wording(text: str) -> str:
    if not text:
        return text
    s = _FACET_OLD.sub(MATERIAL_STEEL, text)
    return _KM_TEXT_RE.sub(MATERIAL_STEEL, s)


def fix_km_slug(slug: str) -> str:
    if not slug:
        return slug
    return _KM_SLUG_RE.sub(
        lambda m: f"{m.group(1)}сталь{m.group(2)}", slug
    )
