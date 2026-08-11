from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.cart.services import cart_totals, resolve_cart, sync_cart
from apps.catalog.pricing import line_total, unit_price_for_qty
from apps.core.exceptions import OrderError
from apps.core.models import SiteSettings
from apps.orders.constants import (
    MIN_ORDER_AMOUNT,
    NP_TYPE_LABELS,
    SHIPPING_METHOD_LABELS,
    SHIPPING_NOVA_POSHTA,
    SHIPPING_PICKUP,
)
from apps.orders.emails import send_order_emails
from apps.orders.models import Order, OrderItem


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Order.Status.NEW: {
        Order.Status.PAID,
        Order.Status.PROCESSING,
        Order.Status.CANCELED,
    },
    Order.Status.PAID: {Order.Status.PROCESSING, Order.Status.CANCELED},
    Order.Status.PROCESSING: {Order.Status.SHIPPED, Order.Status.CANCELED},
    Order.Status.SHIPPED: {Order.Status.DONE},
    Order.Status.DONE: set(),
    Order.Status.CANCELED: set(),
}


def generate_order_number() -> str:
    today = timezone.localdate().strftime("%Y%m%d")
    prefix = f"BLT-{today}-"
    last = (
        Order.objects.filter(number__startswith=prefix)
        .aggregate(m=Max("number"))
        .get("m")
    )
    if last:
        try:
            seq = int(last.rsplit("-", 1)[-1]) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"


def assert_min_order_amount(subtotal: Decimal) -> None:
    if subtotal < MIN_ORDER_AMOUNT:
        raise OrderError(
            f"Мінімальна сума замовлення — {MIN_ORDER_AMOUNT:.0f} грн"
        )


def build_shipping_address(cleaned_data: dict) -> str:
    method = cleaned_data.get("shipping_method") or ""
    if method == SHIPPING_PICKUP:
        site = SiteSettings.load()
        parts = ["Самовивіз"]
        desc = (site.pickup_description or site.address or "").strip()
        if desc:
            parts.append(desc)
        return " — ".join(parts)

    if method == SHIPPING_NOVA_POSHTA:
        np_type = cleaned_data.get("np_delivery_type") or ""
        type_label = NP_TYPE_LABELS.get(np_type, "НП")
        city = (cleaned_data.get("np_city") or "").strip()
        wh = (cleaned_data.get("np_warehouse") or "").strip()
        bits = ["Нова Пошта", type_label]
        if city:
            bits.append(city)
        if wh:
            bits.append(wh)
        return " — ".join(bits)

    return SHIPPING_METHOD_LABELS.get(method, method)


def place_order(request, cleaned_data: dict) -> Order:
    order = _create_order(request, cleaned_data)
    send_order_emails(order)
    return order


@transaction.atomic
def _create_order(request, cleaned_data: dict) -> Order:
    cart = resolve_cart(request)
    sync_cart(cart)
    totals = cart_totals(cart)
    if not totals["lines"]:
        raise OrderError("Кошик порожній")
    assert_min_order_amount(totals["subtotal"])

    items = list(
        cart.items.select_related("sku", "sku__group").select_for_update()
    )
    if not items:
        raise OrderError("Кошик порожній")

    for item in items:
        sku = item.sku
        if not sku.is_active or not sku.group.is_active:
            raise OrderError(f"Товар {sku.article} недоступний")
        if sku.price <= 0:
            raise OrderError(f"Некоректна ціна для {sku.article}")

    method = cleaned_data.get("shipping_method") or ""
    if method == SHIPPING_PICKUP and not SiteSettings.load().pickup_enabled:
        raise OrderError("Самовивіз тимчасово недоступний")

    user = request.user if request.user.is_authenticated else None
    shipping_address = build_shipping_address(cleaned_data)
    order = Order.objects.create(
        number=generate_order_number(),
        user=user,
        status=Order.Status.NEW,
        payment_status=Order.PaymentStatus.PENDING,
        customer_name=cleaned_data["customer_name"],
        phone=cleaned_data["phone"],
        email=cleaned_data.get("email", "") or "",
        shipping_method=method,
        np_delivery_type=cleaned_data.get("np_delivery_type", "") or "",
        np_city=cleaned_data.get("np_city", "") or "",
        np_city_ref=cleaned_data.get("np_city_ref", "") or "",
        np_warehouse=cleaned_data.get("np_warehouse", "") or "",
        np_warehouse_ref=cleaned_data.get("np_warehouse_ref", "") or "",
        shipping_address=shipping_address,
        comment=cleaned_data.get("comment", "") or "",
        total=0,
    )

    total = Decimal("0.00")
    for item in items:
        sku = item.sku
        unit = unit_price_for_qty(sku, item.quantity)
        lt = line_total(unit, item.quantity)
        total += lt
        OrderItem.objects.create(
            order=order,
            sku=sku,
            article=sku.article,
            name=sku.name,
            size_label=sku.size_label,
            unit_price=unit,
            vat_rate=sku.vat_rate,
            price_includes_vat=sku.price_includes_vat,
            quantity=item.quantity,
            line_total=lt,
        )

    if total < MIN_ORDER_AMOUNT:
        raise OrderError(
            f"Мінімальна сума замовлення — {MIN_ORDER_AMOUNT:.0f} грн"
        )

    order.total = total
    order.save(update_fields=["total"])
    cart.items.all().delete()
    return order


def get_order_for_success(number: str, *, token=None, user=None) -> Order:
    qs = Order.objects.prefetch_related("items")
    order = qs.filter(number=number).first()
    if order is None:
        raise OrderError("Замовлення не знайдено")
    if user is not None and user.is_authenticated:
        if order.user_id == user.id or user.is_staff:
            return order
    if token and str(order.access_token) == str(token):
        return order
    raise OrderError("Немає доступу до замовлення")


def orders_for_user(user):
    return Order.objects.filter(user=user).order_by("-created_at")


@transaction.atomic
def change_order_status(order: Order, to_status: str) -> Order:
    allowed = ALLOWED_TRANSITIONS.get(order.status, set())
    if to_status not in allowed:
        raise OrderError(f"Перехід {order.status} → {to_status} заборонено")
    order.status = to_status
    order.save(update_fields=["status", "updated_at"])
    return order
