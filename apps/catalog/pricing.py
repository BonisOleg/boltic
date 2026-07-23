from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal("0.01")


def line_total(unit_price: Decimal, qty: int) -> Decimal:
    return (unit_price * qty).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def net_from_gross(price: Decimal, vat_rate: Decimal) -> Decimal:
    if vat_rate <= 0:
        return price
    return (price / (1 + vat_rate / Decimal("100"))).quantize(
        TWOPLACES, rounding=ROUND_HALF_UP
    )


def normalize_qty(qty: int, min_party: int) -> int:
    """qty >= min_party і кратна min_party; інакше підняти вгору."""
    if min_party < 1:
        min_party = 1
    if qty < min_party:
        return min_party
    remainder = qty % min_party
    if remainder == 0:
        return qty
    return qty + (min_party - remainder)
