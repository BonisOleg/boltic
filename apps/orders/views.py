from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.cart.services import cart_totals, resolve_cart, sync_cart
from apps.core.exceptions import OrderError, PaymentError
from apps.orders.forms import CheckoutForm
from apps.orders.services import get_order_for_success, place_order
from apps.payments.services import create_checkout


@require_http_methods(["GET", "POST"])
def checkout(request):
    cart = resolve_cart(request)
    sync_cart(cart)
    totals = cart_totals(cart)
    if not totals["lines"]:
        messages.warning(request, "Кошик порожній")
        return redirect("cart:detail")

    form = CheckoutForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            order = place_order(request, form.cleaned_data)
        except OrderError as exc:
            messages.error(request, str(exc))
            return redirect("cart:detail")

        result_url = request.build_absolute_uri(
            reverse("payments:liqpay_result")
            + f"?number={order.number}&token={order.access_token}"
        )
        server_url = getattr(settings, "LIQPAY_SERVER_URL", "") or request.build_absolute_uri(
            reverse("payments:liqpay_callback")
        )
        try:
            pay = create_checkout(order, result_url=result_url, server_url=server_url)
        except PaymentError as exc:
            messages.warning(
                request,
                f"Замовлення створено ({order.number}), але оплату не ініційовано: {exc}",
            )
            return redirect(
                reverse("orders:success", kwargs={"number": order.number})
                + f"?token={order.access_token}"
            )
        return render(
            request,
            "payments/liqpay_redirect.html",
            {
                "order": order,
                "liqpay_data": pay["data"],
                "liqpay_signature": pay["signature"],
                "liqpay_checkout_url": pay["checkout_url"],
            },
        )

    return render(
        request,
        "orders/checkout.html",
        {"form": form, "lines": totals["lines"], "subtotal": totals["subtotal"]},
    )


@require_http_methods(["GET"])
def order_success(request, number: str):
    token = request.GET.get("token")
    try:
        order = get_order_for_success(
            number, token=token, user=request.user
        )
    except OrderError:
        messages.error(request, "Замовлення не знайдено")
        return redirect("content:home")
    return render(request, "orders/success.html", {"order": order})
