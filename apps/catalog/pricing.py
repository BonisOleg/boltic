from decimal import Decimal, ROUND_HALF_UP
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from apps.catalog.models import ProductSKU


TWOPLACES = Decimal("0.01")


def retail_unit_price(sku: "ProductSKU") -> Decimal:
    """Роздрібна unit-ціна: sale_price якщо задана, інакше price."""
    sale = sku.sale_price
    if sale is not None and sale > 0:
        return sale
    return sku.price


def unit_price_for_qty(sku: "ProductSKU", qty: int) -> Decimal:
    """
    Опт (party_price грн/шт) при qty >= wholesale_from_qty;
    інакше роздріб (sale_price або price). Опт без акції.
    """
    party = sku.party_price
    wholesale_from = sku.wholesale_from_qty
    if (
        party is not None
        and wholesale_from is not None
        and int(wholesale_from) > 0
        and int(qty) >= int(wholesale_from)
    ):
        return party
    return retail_unit_price(sku)


def line_total(unit_price: Decimal, qty: int) -> Decimal:
    return (unit_price * qty).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def net_from_gross(price: Decimal, vat_rate: Decimal) -> Decimal:
    if vat_rate <= 0:
        return price
    return (price / (1 + vat_rate / Decimal("100"))).quantize(
        TWOPLACES, rounding=ROUND_HALF_UP
    )


def normalize_qty(qty: int, min_party: int) -> int:
    """qty >= min_party; крок = 1 (без кратності партії)."""
    if min_party < 1:
        min_party = 1
    qty = int(qty)
    if qty < min_party:
        return min_party
    return qty


def max_orderable_qty(min_party: int, stock_qty: int | None) -> int | None:
    """Макс. кількість для замовлення. None = без ліміту."""
    if stock_qty is None:
        return None
    if min_party < 1:
        min_party = 1
    stock = int(stock_qty)
    if stock < min_party:
        return 0
    return stock


def clamp_qty(qty: int, min_party: int, stock_qty: int | None) -> int:
    """Нормалізувати qty і обмежити залишком (0 якщо залишку менше мін.)."""
    qty = normalize_qty(int(qty), min_party)
    max_q = max_orderable_qty(min_party, stock_qty)
    if max_q is None:
        return qty
    if max_q < min_party:
        return 0
    return min(qty, max_q)
