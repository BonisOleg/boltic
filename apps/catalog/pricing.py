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


def max_orderable_qty(min_party: int, stock_qty: int | None) -> int | None:
    """Макс. кількість для замовлення (кратна партії). None = без ліміту."""
    if stock_qty is None:
        return None
    if min_party < 1:
        min_party = 1
    return (int(stock_qty) // min_party) * min_party


def clamp_qty(qty: int, min_party: int, stock_qty: int | None) -> int:
    """Нормалізувати qty і обмежити залишком (0 якщо залишку менше мін. партії)."""
    qty = normalize_qty(int(qty), min_party)
    max_q = max_orderable_qty(min_party, stock_qty)
    if max_q is None:
        return qty
    if max_q < min_party:
        return 0
    return min(qty, max_q)
