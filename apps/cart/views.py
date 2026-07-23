from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.cart.services import (
    add_item,
    cart_totals,
    remove_item,
    resolve_cart,
    sync_cart,
    update_item,
    wishlist_qs,
    wishlist_toggle,
)
from apps.core.exceptions import CartError


@require_GET
def cart_detail(request):
    cart = resolve_cart(request)
    notes = sync_cart(cart)
    for note in notes:
        messages.info(request, note)
    totals = cart_totals(cart)
    return render(
        request,
        "cart/detail.html",
        {"cart": cart, "lines": totals["lines"], "subtotal": totals["subtotal"]},
    )


@require_POST
def cart_add(request):
    sku_id = int(request.POST.get("sku_id") or 0)
    qty = int(request.POST.get("qty") or 1)
    try:
        add_item(request, sku_id=sku_id, qty=qty)
        messages.success(request, "Додано до кошика")
    except CartError as exc:
        messages.error(request, str(exc))
    if getattr(request, "htmx", False):
        cart = resolve_cart(request)
        totals = cart_totals(cart)
        return render(
            request,
            "cart/partials/add_response.html",
            {"cart_count": sum(i.quantity for i in cart.items.all()), "subtotal": totals["subtotal"]},
        )
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/koshyk/"
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


@login_required
@require_http_methods(["GET", "POST"])
def wishlist(request):
    if request.method == "POST":
        sku_id = int(request.POST.get("sku_id") or 0)
        try:
            added = wishlist_toggle(request.user, sku_id=sku_id)
            messages.success(
                request, "Додано в бажане" if added else "Прибрано з бажаного"
            )
        except CartError as exc:
            messages.error(request, str(exc))
        if request.POST.get("next"):
            return redirect(request.POST["next"])
    return render(
        request,
        "cart/wishlist.html",
        {"items": wishlist_qs(request.user)},
    )
