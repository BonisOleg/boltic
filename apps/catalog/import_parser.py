"""Парсер рядків асортименту з БОЛТИ.docx / ГВИНТИ.docx."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ParsedSKU:
    diameter: Decimal
    length: Decimal
    thread_pitch: Decimal | None
    size_label: str


# м8х1,25х20,30  |  м4х10,14,16  |  М8х40
_SIZE_RE = re.compile(
    r"^[мm]\s*(?P<d>\d+(?:[.,]\d+)?)"
    r"(?:\s*[xх×]\s*(?P<p>\d+(?:[.,]\d+)?))?"
    r"\s*[xх×]\s*(?P<rest>.+)$",
    re.IGNORECASE,
)


def _dec(value: str) -> Decimal:
    return Decimal(value.replace(",", ".").strip())


def _fmt_num(value: Decimal) -> str:
    text = format(value.normalize(), "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def parse_size_line(line: str) -> list[ParsedSKU]:
    """
    'м8х14,16,20' → M8×14, M8×16, M8×20
    'м10х1,25х20,30,40' → M10×1.25×20 …
    'м8х1х40,50,60' → M8×1×40 …
    """
    raw = line.strip().rstrip(":")
    if not raw:
        return []
    # прибрати зайві пробіли біля ком
    raw = re.sub(r"\s*,\s*", ",", raw)
    raw = re.sub(r"\s+", "", raw)

    match = _SIZE_RE.match(raw)
    if not match:
        return []

    diameter = _dec(match.group("d"))
    pitch_raw = match.group("p")
    rest = match.group("rest")
    parts = [p for p in rest.split(",") if p]

    if not parts:
        return []

    # Якщо є pitch-група і rest має кілька чисел — pitch заданий.
    # Якщо pitch відсутній — усі parts = довжини.
    # Евристика для 'м8х1х20': p=1, rest=20 → pitch=1
    # Для 'м4х10,14': p=None у regex? Actually м4х10,14 → d=4, p=None won't match
    # because we need x between. Pattern: d (?: x p)? x rest
    # м4х10,14 → d=4, p=None fails optional, then x rest — but after d we need x.
    # Flow: м4х10,14 → d=4, then (?:x p)? tries x10 as pitch? 
    # Optional non-greedy: (?:x p)? then x rest
    # For м4х10,14: after d=4, (?:х p)? could match х10 as pitch, then need another х for rest — fail
    # So we need different approach.

    return _parse_size_parts(diameter, pitch_raw, parts, raw)


def _parse_size_parts(
    diameter: Decimal,
    pitch_raw: str | None,
    parts: list[str],
    raw: str,
) -> list[ParsedSKU]:
    # Перепарсити надійніше: split by х/x/×
    tokens = re.split(r"[xх×]", raw, flags=re.IGNORECASE)
    tokens = [t.strip() for t in tokens if t.strip()]
    if len(tokens) < 2:
        return []

    # tokens[0] like м4 or м10
    d_match = re.match(r"^[мm](\d+(?:[.,]\d+)?)$", tokens[0], re.I)
    if not d_match:
        return []
    diameter = _dec(d_match.group(1))

    if len(tokens) == 2:
        # м4х10,14,16
        lengths = [_dec(x) for x in tokens[1].split(",") if x]
        pitch = None
    elif len(tokens) >= 3:
        # м10х1,25х20,30 або м8х1х40,50
        pitch = _dec(tokens[1])
        lengths = [_dec(x) for x in tokens[2].split(",") if x]
        # якщо ще токени — злити (рідко)
        for extra in tokens[3:]:
            lengths.extend(_dec(x) for x in extra.split(",") if x)
    else:
        return []

    result: list[ParsedSKU] = []
    for length in lengths:
        if pitch is None:
            label = f"M{_fmt_num(diameter)}×{_fmt_num(length)}"
        else:
            label = (
                f"M{_fmt_num(diameter)}×{_fmt_num(pitch)}×{_fmt_num(length)}"
            )
        result.append(
            ParsedSKU(
                diameter=diameter,
                length=length,
                thread_pitch=pitch,
                size_label=label,
            )
        )
    return result


def parse_group_meta(title: str) -> dict:
    """Витягнути standard, strength_class, material з назви групи."""
    title = title.strip().rstrip(":")
    standard = ""
    din = re.search(r"DIN\s*(\d+)", title, re.I)
    if din:
        standard = f"DIN {din.group(1)}"

    strength = ""
    sm = re.search(
        r"(?:кл\.?\s*(?:пр|міц)\.?|клас(?:\s*м(?:іц(?:н(?:ості)?)?)?\.?)?)\s*"
        r"(\d+[,.]\d+)",
        title,
        re.I,
    )
    if not sm:
        sm = re.search(r"(\d+[,.]\d+)\s*к\.?\s*м", title, re.I)
    if sm:
        strength = sm.group(1).replace(",", ".")

    material = ""
    if re.search(r"\bА2\b|нержав", title, re.I):
        material = "А2 нержавіюча сталь"
    elif re.search(
        r"(?<![А-Яа-яІіЇїЄєҐґA-Za-z])к\.м\.?(?![А-Яа-яІіЇїЄєҐґA-Za-z])",
        title,
        re.I,
    ):
        material = "сталь"

    return {
        "name": title,
        "standard": standard,
        "strength_class": strength,
        "material": material,
    }


def is_group_header(line: str) -> bool:
    t = line.strip()
    if not t or t.upper() in {"БОЛТИ", "ГВИНТИ"}:
        return False
    if re.match(r"^[мmМM]\d", t):
        return False
    return bool(
        re.search(r"болт|гвинт|din|леміш|норійн|меблев|прес", t, re.I)
    )
