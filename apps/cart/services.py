from django.db import transaction
from django.utils import timezone

from apps.cart.models import Cart, CartItem, WishlistItem
from apps.catalog.models import ProductSKU
from apps.catalog.pricing import line_total, normalize_qty
from apps.core.exceptions import CartError


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
    """Прибрати неактивні SKU; нормалізувати qty. Повертає повідомлення."""
    messages: list[str] = []
    for item in cart.items.select_related("sku").all():
        sku = item.sku
        if not sku.is_active or not sku.group.is_active:
            item.delete()
            messages.append(f"Видалено недоступний товар {sku.article}")
            continue
        new_qty = normalize_qty(item.quantity, sku.min_party)
        if new_qty != item.quantity:
            item.quantity = new_qty
            item.save(update_fields=["quantity"])
            messages.append(f"{sku.article}: кількість змінено до {new_qty}")
    return messages


def cart_totals(cart: Cart) -> dict:
    items = list(cart.items.select_related("sku").all())
    lines = []
    subtotal = 0
    from decimal import Decimal

    subtotal = Decimal("0.00")
    for item in items:
        lt = line_total(item.sku.price, item.quantity)
        subtotal += lt
        lines.append({"item": item, "line_total": lt})
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
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        sku=sku,
        defaults={"quantity": qty},
    )
    if not created:
        item.quantity = normalize_qty(item.quantity + qty, sku.min_party)
        item.save(update_fields=["quantity"])
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
    item.quantity = normalize_qty(qty, item.sku.min_party)
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
        if existing:
            existing.quantity = normalize_qty(
                existing.quantity + item.quantity, item.sku.min_party
            )
            existing.save(update_fields=["quantity"])
        else:
            item.cart = user_cart
            item.quantity = normalize_qty(item.quantity, item.sku.min_party)
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
