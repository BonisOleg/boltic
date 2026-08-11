import re

from django.core.exceptions import ValidationError

PHONE_PREFIX = "+380"
PHONE_SUBSCRIBER_DIGITS = 9
PHONE_RE = re.compile(rf"^{re.escape(PHONE_PREFIX)}\d{{{PHONE_SUBSCRIBER_DIGITS}}}$")
NAME_HAS_DIGIT_RE = re.compile(r"\d")
NAME_HAS_LETTER_RE = re.compile(r"[^\W\d_]", re.UNICODE)


def normalize_ua_phone(raw: str) -> str:
    """Приводить до +380XXXXXXXXX (макс. 9 цифр абонента)."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("380"):
        digits = digits[3:]
    elif digits.startswith("0") and len(digits) >= 10:
        digits = digits[1:]
    digits = digits[:PHONE_SUBSCRIBER_DIGITS]
    return f"{PHONE_PREFIX}{digits}"


def validate_customer_name(value: str) -> str:
    name = (value or "").strip()
    if not name:
        raise ValidationError("Вкажіть ПІБ")
    if NAME_HAS_DIGIT_RE.search(name):
        raise ValidationError("ПІБ не може містити цифри")
    if not NAME_HAS_LETTER_RE.search(name):
        raise ValidationError("Вкажіть коректне ПІБ")
    return name


def validate_ua_phone(value: str) -> str:
    normalized = normalize_ua_phone(value)
    if not PHONE_RE.fullmatch(normalized):
        raise ValidationError(
            "Вкажіть номер у форматі +380 і 9 цифр (наприклад +380501234567)"
        )
    return normalized
