import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.core.exceptions import PaymentError
from apps.orders.models import Order
from apps.payments.services import handle_webhook

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def liqpay_callback(request):
    data_b64 = request.POST.get("data", "")
    signature = request.POST.get("signature", "")
    if not data_b64 or not signature:
        return HttpResponse("Bad request", status=400)
    try:
        handle_webhook(data_b64=data_b64, signature=signature)
    except PaymentError as exc:
        logger.warning("LiqPay webhook: %s", exc)
        return HttpResponse(str(exc), status=400)
    except Exception:
        logger.exception("LiqPay webhook error")
        return HttpResponse("Internal error", status=500)
    return HttpResponse("OK", status=200)


@require_http_methods(["GET", "POST"])
def liqpay_result(request):
    """Повернення з LiqPay → success лише з перевіреним підписом або валідним token.

    Ніколи не підставляємо order.access_token за голим number (IDOR).
    """
    number = (request.GET.get("number") or request.POST.get("order_id") or "").strip()
    token = (request.GET.get("token") or "").strip()
    verified = False

    data_b64 = request.POST.get("data", "")
    signature = request.POST.get("signature", "")
    if data_b64 and signature:
        try:
            order = handle_webhook(data_b64=data_b64, signature=signature)
            number = order.number
            token = str(order.access_token)
            verified = True
        except PaymentError:
            pass

    if not number:
        messages.error(request, "Немає номера замовлення")
        return redirect("content:home")

    order = Order.objects.filter(number=number).first()
    if order is None:
        messages.error(request, "Замовлення не знайдено")
        return redirect("content:home")

    if not verified:
        if not token or str(order.access_token) != str(token):
            messages.error(request, "Немає доступу до замовлення")
            return redirect("content:home")

    url = reverse("orders:success", kwargs={"number": order.number})
    return redirect(f"{url}?token={token}")
