from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem, WishlistItem
from apps.catalog.models import ProductSKU
from apps.catalog.pricing import clamp_qty, line_total, max_orderable_qty, normalize_qty
from apps.core.exceptions import CartError


def _enforce_stock(sku: ProductSKU, qty: int) -> int:
    """Повернути qty у межах залишку або кинути CartError."""
    max_q = max_orderable_qty(sku.min_party, sku.stock_qty)
    qty = normalize_qty(qty, sku.min_party)
    if max_q is None:
        return qty
    if max_q < sku.min_party:
        raise CartError("Товару немає в наявності")
    if qty > max_q:
        raise CartError(f"Доступно лише {max_q} шт.")
    return qty


def _ensure_session(request) -> str:
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def resolve_cart(request) -> Cart:
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    session_key = _ensure_session(request)
    cart, _ = Cart.objects.get_or_create(
        session_key=session_key,
        user=None,
        defaults={},
    )
    return cart


def cart_item_count(request) -> int:
    cart = resolve_cart(request)
    return sum(cart.items.values_list("quantity", flat=True))


def sync_cart(cart: Cart) -> list[str]:
    """Прибрати неактивні SKU; нормалізувати qty і залишок. Повертає повідомлення."""
    messages: list[str] = []
    for item in cart.items.select_related("sku", "sku__group").all():
        sku = item.sku
        if not sku.is_active or not sku.group.is_active:
            item.delete()
            messages.append(f"Видалено недоступний товар {sku.article}")
            continue
        new_qty = clamp_qty(item.quantity, sku.min_party, sku.stock_qty)
        if new_qty == 0:
            item.delete()
            messages.append(f"Видалено: {sku.article} — немає в наявності")
            continue
        if new_qty != item.quantity:
            item.quantity = new_qty
            item.save(update_fields=["quantity"])
            messages.append(f"{sku.article}: кількість змінено до {new_qty}")
    return messages


def cart_totals(cart: Cart) -> dict:
    items = list(cart.items.select_related("sku", "sku__group").all())
    from decimal import Decimal

    subtotal = Decimal("0.00")
    lines = []
    for item in items:
        lt = line_total(item.sku.price, item.quantity)
        subtotal += lt
        max_qty = max_orderable_qty(item.sku.min_party, item.sku.stock_qty)
        lines.append({"item": item, "line_total": lt, "max_qty": max_qty})
    return {"lines": lines, "subtotal": subtotal}


@transaction.atomic
def add_item(request, *, sku_id: int, qty: int) -> CartItem:
    sku = (
        ProductSKU.objects.select_related("group")
        .filter(pk=sku_id, is_active=True, group__is_active=True)
        .first()
    )
    if sku is None:
        raise CartError("Товар не знайдено")
    qty = normalize_qty(int(qty), sku.min_party)
    cart = resolve_cart(request)
    item = CartItem.objects.filter(cart=cart, sku=sku).first()
    desired = (item.quantity + qty) if item else qty
    desired = _enforce_stock(sku, desired)
    if item:
        item.quantity = desired
        item.save(update_fields=["quantity"])
    else:
        item = CartItem.objects.create(cart=cart, sku=sku, quantity=desired)
    cart.updated_at = timezone.now()
    cart.save(update_fields=["updated_at"])
    return item


@transaction.atomic
def update_item(request, *, item_id: int, qty: int) -> CartItem:
    cart = resolve_cart(request)
    item = (
        CartItem.objects.select_related("sku")
        .filter(pk=item_id, cart=cart)
        .first()
    )
    if item is None:
        raise CartError("Позицію не знайдено")
    qty = int(qty)
    if qty <= 0:
        item.delete()
        raise CartError("Позицію видалено")
    item.quantity = _enforce_stock(item.sku, qty)
    item.save(update_fields=["quantity"])
    return item


@transaction.atomic
def remove_item(request, *, item_id: int) -> None:
    cart = resolve_cart(request)
    deleted, _ = CartItem.objects.filter(pk=item_id, cart=cart).delete()
    if not deleted:
        raise CartError("Позицію не знайдено")


@transaction.atomic
def merge_on_login(request, user) -> None:
    session_key = request.session.session_key
    if not session_key:
        return
    session_cart = Cart.objects.filter(session_key=session_key, user=None).first()
    if session_cart is None:
        return
    user_cart, _ = Cart.objects.get_or_create(user=user)
    for item in session_cart.items.select_related("sku"):
        existing = user_cart.items.filter(sku=item.sku).first()
        desired = (existing.quantity + item.quantity) if existing else item.quantity
        desired = clamp_qty(desired, item.sku.min_party, item.sku.stock_qty)
        if desired == 0:
            item.delete()
            continue
        if existing:
            existing.quantity = desired
            existing.save(update_fields=["quantity"])
            item.delete()
        else:
            item.cart = user_cart
            item.quantity = desired
            item.save(update_fields=["cart", "quantity"])
    session_cart.delete()


@transaction.atomic
def wishlist_toggle(user, *, sku_id: int) -> bool:
    """Повертає True якщо додано, False якщо прибрано."""
    sku = ProductSKU.objects.filter(pk=sku_id, is_active=True).first()
    if sku is None:
        raise CartError("Товар не знайдено")
    existing = WishlistItem.objects.filter(user=user, sku=sku).first()
    if existing:
        existing.delete()
        return False
    WishlistItem.objects.create(user=user, sku=sku)
    return True


def wishlist_qs(user):
    return WishlistItem.objects.filter(user=user).select_related(
        "sku", "sku__group"
    )
