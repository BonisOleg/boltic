from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods

from apps.cart.services import cart_totals, resolve_cart, sync_cart
from apps.core.exceptions import OrderError
from apps.core.models import SiteSettings
from apps.orders.checkout_session import (
    clear_checkout,
    get_checkout,
    has_contact,
    has_delivery,
    update_checkout,
)
from apps.orders.constants import MIN_ORDER_AMOUNT, SHIPPING_METHOD_LABELS
from apps.orders.forms import ContactForm, DeliveryForm, pickup_is_enabled
from apps.orders import nova_poshta
from apps.orders.services import assert_min_order_amount, get_order_for_success, place_order


def _cart_ready(request):
    cart = resolve_cart(request)
    sync_cart(cart)
    totals = cart_totals(cart)
    if not totals["lines"]:
        messages.warning(request, "Кошик порожній")
        return None, redirect("cart:detail")
    try:
        assert_min_order_amount(totals["subtotal"])
    except OrderError as exc:
        messages.error(request, str(exc))
        return None, redirect("cart:detail")
    return totals, None


def _contact_initial(request) -> dict:
    from apps.orders.validators import PHONE_PREFIX, normalize_ua_phone

    data = get_checkout(request)
    initial = {
        "customer_name": data.get("customer_name", ""),
        "phone": data.get("phone", "") or PHONE_PREFIX,
        "email": data.get("email", ""),
    }
    if data.get("customer_name") or data.get("phone") or data.get("email"):
        if initial["phone"] and initial["phone"] != PHONE_PREFIX:
            initial["phone"] = normalize_ua_phone(initial["phone"])
        return initial
    user = request.user
    if not user.is_authenticated:
        return initial
    name = (user.get_full_name() or "").strip()
    phone = ""
    profile = getattr(user, "profile", None)
    if profile is not None:
        phone = profile.phone or ""
    if phone:
        phone = normalize_ua_phone(phone)
    return {
        "customer_name": name,
        "phone": phone or PHONE_PREFIX,
        "email": user.email or "",
    }


def _delivery_initial(request) -> dict:
    data = get_checkout(request)
    return {
        "shipping_method": data.get("shipping_method", ""),
        "np_delivery_type": data.get("np_delivery_type", ""),
        "np_city": data.get("np_city", ""),
        "np_city_ref": data.get("np_city_ref", ""),
        "np_warehouse": data.get("np_warehouse", ""),
        "np_warehouse_ref": data.get("np_warehouse_ref", ""),
        "comment": data.get("comment", ""),
    }


def _order_summary_ctx(data: dict) -> dict:
    site = SiteSettings.load()
    method = data.get("shipping_method") or ""
    method_label = SHIPPING_METHOD_LABELS.get(method, method)
    if method == "pickup":
        delivery_text = site.pickup_description or method_label
    else:
        parts = [method_label]
        if data.get("np_delivery_type") == "postomat":
            parts.append("поштомат")
        elif data.get("np_delivery_type") == "warehouse":
            parts.append("відділення")
        if data.get("np_city"):
            parts.append(data["np_city"])
        if data.get("np_warehouse"):
            parts.append(data["np_warehouse"])
        delivery_text = " — ".join(parts)
    return {
        "summary_name": data.get("customer_name", ""),
        "summary_phone": data.get("phone", ""),
        "summary_email": data.get("email", ""),
        "summary_delivery": delivery_text,
        "summary_comment": data.get("comment", ""),
    }


@require_http_methods(["GET", "POST"])
def checkout_contact(request):
    totals, early = _cart_ready(request)
    if early:
        return early

    form = ContactForm(request.POST or None, initial=_contact_initial(request))
    if request.method == "POST" and form.is_valid():
        update_checkout(request, **form.cleaned_data)
        return redirect("orders:checkout_delivery")

    return render(
        request,
        "orders/checkout.html",
        {
            "step": 1,
            "form": form,
            "lines": totals["lines"],
            "subtotal": totals["subtotal"],
            "min_order": MIN_ORDER_AMOUNT,
        },
    )


@require_http_methods(["GET", "POST"])
def checkout_delivery(request):
    totals, early = _cart_ready(request)
    if early:
        return early
    data = get_checkout(request)
    if not has_contact(data):
        messages.info(request, "Спочатку заповніть контактні дані")
        return redirect("orders:checkout")

    pickup_on = pickup_is_enabled()
    form = DeliveryForm(
        request.POST or None,
        initial=_delivery_initial(request),
        pickup_enabled=pickup_on,
    )
    if request.method == "POST" and form.is_valid():
        update_checkout(request, **form.cleaned_data)
        return redirect("orders:checkout_confirm")

    site = SiteSettings.load()
    return render(
        request,
        "orders/checkout.html",
        {
            "step": 2,
            "form": form,
            "lines": totals["lines"],
            "subtotal": totals["subtotal"],
            "min_order": MIN_ORDER_AMOUNT,
            "pickup_enabled": pickup_on,
            "pickup_description": site.pickup_description,
            "np_configured": nova_poshta.is_configured(),
        },
    )


@require_http_methods(["GET", "POST"])
def checkout_confirm(request):
    totals, early = _cart_ready(request)
    if early:
        return early
    data = get_checkout(request)
    if not has_contact(data):
        return redirect("orders:checkout")
    if not has_delivery(data):
        messages.info(request, "Оберіть спосіб доставки")
        return redirect("orders:checkout_delivery")

    if request.method == "POST":
        try:
            order = place_order(request, data)
        except OrderError as exc:
            messages.error(request, str(exc))
            return redirect("cart:detail")
        clear_checkout(request)
        messages.success(request, f"Замовлення {order.number} прийнято")
        return redirect(
            reverse("orders:success", kwargs={"number": order.number})
            + f"?token={order.access_token}"
        )

    return render(
        request,
        "orders/checkout.html",
        {
            "step": 3,
            "lines": totals["lines"],
            "subtotal": totals["subtotal"],
            "min_order": MIN_ORDER_AMOUNT,
            **_order_summary_ctx(data),
        },
    )


@require_GET
def np_cities(request):
    q = request.GET.get("q", "")
    try:
        items = nova_poshta.search_cities(q)
    except nova_poshta.NovaPoshtaError as exc:
        return JsonResponse({"ok": False, "error": str(exc), "items": []}, status=400)
    return JsonResponse({"ok": True, "items": items})


@require_GET
def np_warehouses(request):
    city_ref = request.GET.get("city_ref", "")
    delivery_type = request.GET.get("type", "warehouse")
    q = request.GET.get("q", "")
    try:
        items = nova_poshta.search_warehouses(
            city_ref, delivery_type=delivery_type, query=q
        )
    except nova_poshta.NovaPoshtaError as exc:
        return JsonResponse({"ok": False, "error": str(exc), "items": []}, status=400)
    return JsonResponse({"ok": True, "items": items})


# Зворотна сумісність імпорту (старі тести/посилання)
checkout = checkout_contact


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
