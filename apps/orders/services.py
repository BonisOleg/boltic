from decimal import Decimal

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.cart.services import resolve_cart, sync_cart
from apps.catalog.pricing import line_total
from apps.core.exceptions import OrderError
from apps.orders.models import Order, OrderItem


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    Order.Status.NEW: {Order.Status.PAID, Order.Status.CANCELED},
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


@transaction.atomic
def place_order(request, cleaned_data: dict) -> Order:
    cart = resolve_cart(request)
    sync_cart(cart)
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

    user = request.user if request.user.is_authenticated else None
    order = Order.objects.create(
        number=generate_order_number(),
        user=user,
        status=Order.Status.NEW,
        payment_status=Order.PaymentStatus.PENDING,
        customer_name=cleaned_data["customer_name"],
        phone=cleaned_data["phone"],
        email=cleaned_data.get("email", ""),
        shipping_method=cleaned_data.get("shipping_method", ""),
        shipping_address=cleaned_data.get("shipping_address", ""),
        comment=cleaned_data.get("comment", ""),
        total=0,
    )

    total = Decimal("0.00")
    for item in items:
        sku = item.sku
        # SEC-02: ціна лише з БД
        unit = sku.price
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
