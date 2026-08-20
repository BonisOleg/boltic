from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST
from django_htmx.http import HttpResponseClientRedirect

from apps.cart.services import (
    add_item,
    cart_totals,
    remove_item,
    resolve_cart,
    sync_cart,
    update_item,
    wishlist_qs,
    wishlist_sku_ids,
    wishlist_toggle,
)
from apps.core.exceptions import CartError
from apps.core.http import safe_next, url_with_next
from apps.orders.constants import MIN_ORDER_AMOUNT


@require_GET
def cart_detail(request):
    cart = resolve_cart(request)
    notes = sync_cart(cart)
    for note in notes:
        messages.info(request, note)
    totals = cart_totals(cart)
    subtotal = totals["subtotal"]
    return render(
        request,
        "cart/detail.html",
        {
            "cart": cart,
            "lines": totals["lines"],
            "subtotal": subtotal,
            "min_order": MIN_ORDER_AMOUNT,
            "can_checkout": bool(totals["lines"]) and subtotal >= MIN_ORDER_AMOUNT,
            "min_order_shortfall": max(MIN_ORDER_AMOUNT - subtotal, 0)
            if totals["lines"]
            else MIN_ORDER_AMOUNT,
        },
    )


def _note_context(request, *, note: str, ok: bool) -> dict:
    """Контекст для htmx-підказки біля кнопки + лічильники в хедері."""
    cart = resolve_cart(request)
    user = getattr(request, "user", None)
    return {
        "note": note,
        "ok": ok,
        "cart_count": sum(cart.items.values_list("quantity", flat=True)),
        "wishlist_count": len(wishlist_sku_ids(user)),
    }


@require_POST
def cart_add(request):
    sku_id = int(request.POST.get("sku_id") or 0)
    qty = int(request.POST.get("qty") or 1)
    ok, note = True, "Додано до кошика"
    try:
        add_item(request, sku_id=sku_id, qty=qty)
    except CartError as exc:
        ok, note = False, str(exc)
    if getattr(request, "htmx", False):
        return render(
            request,
            "cart/partials/cart_note.html",
            _note_context(request, note=note, ok=ok),
        )
    if ok:
        messages.success(request, note)
    else:
        messages.error(request, note)
    next_url = safe_next(request, fallback="/koshyk/", allow_referer=True)
    return redirect(next_url)


@require_POST
def cart_update(request, item_id: int):
    qty = int(request.POST.get("qty") or 0)
    try:
        if qty <= 0:
            remove_item(request, item_id=item_id)
        else:
            update_item(request, item_id=item_id, qty=qty)
    except CartError as exc:
        messages.error(request, str(exc))
    return redirect("cart:detail")


@require_POST
def cart_remove(request, item_id: int):
    try:
        remove_item(request, item_id=item_id)
    except CartError as exc:
        messages.error(request, str(exc))
    return redirect("cart:detail")


@require_GET
def cart_count(request):
    cart = resolve_cart(request)
    count = sum(cart.items.values_list("quantity", flat=True))
    return render(request, "cart/partials/count.html", {"cart_count": count})


@require_POST
def wishlist_toggle_view(request):
    """Додати/прибрати SKU з обраного; гостя вести на реєстрацію."""
    back_url = safe_next(request, fallback="/koshyk/", allow_referer=True)
    is_htmx = getattr(request, "htmx", False)
    if not request.user.is_authenticated:
        target = url_with_next("accounts:register", back_url)
        return HttpResponseClientRedirect(target) if is_htmx else redirect(target)

    sku_id = int(request.POST.get("sku_id") or 0)
    ok, added, sku = True, False, None
    try:
        added, sku = wishlist_toggle(request.user, sku_id=sku_id)
        note = "Додано в обране" if added else "Прибрано з обраного"
    except CartError as exc:
        ok, note = False, str(exc)

    if is_htmx:
        ctx = _note_context(request, note=note, ok=ok)
        if sku is not None:
            sku.in_wishlist = added
        ctx["sku"] = sku
        ctx["btn_size"] = "lg" if request.POST.get("btn_size") == "lg" else ""
        return render(request, "cart/partials/wishlist_note.html", ctx)

    if ok:
        messages.success(request, note)
    else:
        messages.error(request, note)
    return redirect(back_url)


@require_GET
def wishlist(request):
    # Guest: 200 + unique title (no redirect to /login/) — PAGE-uniq / seo_skill.
    items = []
    if request.user.is_authenticated:
        items = list(wishlist_qs(request.user))
        for item in items:
            item.sku.in_wishlist = True
    return render(request, "cart/wishlist.html", {"items": items})
