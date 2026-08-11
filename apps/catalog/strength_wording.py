"""Заміна «кл. пр.» (прочність) → «кл. міц.» (міцність)."""

from __future__ import annotations

import re

# кл.пр. / кл. пр. / кл.пр → кл.міц. / кл. міц. / кл.міц
_ABBR_RE = re.compile(r"(кл\.?\s*)пр(\.?)", re.IGNORECASE)
_SLUG_HYPHEN_RE = re.compile(r"кл-пр", re.IGNORECASE)
_SLUG_GLUED_RE = re.compile(r"клпр", re.IGNORECASE)


def fix_strength_wording(text: str) -> str:
    if not text:
        return text
    return _ABBR_RE.sub(r"\1міц\2", text)


def fix_strength_slug(slug: str) -> str:
    if not slug:
        return slug
    s = _SLUG_HYPHEN_RE.sub("кл-міц", slug)
    s = _SLUG_GLUED_RE.sub("клміц", s)
    return s
