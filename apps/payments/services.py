import base64
import hashlib
import json
import logging

from django.conf import settings
from django.db import transaction

from apps.core.exceptions import PaymentError
from apps.orders.models import Order
from apps.payments.models import PaymentTransaction

logger = logging.getLogger(__name__)

LIQPAY_CHECKOUT_URL = "https://www.liqpay.ua/api/3/checkout"


class LiqPayClient:
    def __init__(self, public_key: str, private_key: str):
        self.public_key = public_key
        self.private_key = private_key

    def _encode(self, payload: dict) -> str:
        return base64.b64encode(
            json.dumps(payload, ensure_ascii=False).encode()
        ).decode()

    def _sign(self, data_b64: str) -> str:
        raw = (self.private_key + data_b64 + self.private_key).encode()
        return base64.b64encode(hashlib.sha1(raw).digest()).decode()

    def decode_data(self, data_b64: str) -> dict:
        try:
            return json.loads(base64.b64decode(data_b64).decode())
        except Exception as exc:
            logger.error("LiqPay decode_data: %s", exc)
            return {}

    def verify_callback(self, data_b64: str, signature: str) -> bool:
        return self._sign(data_b64) == signature

    def create_checkout_data(
        self,
        *,
        order_id: str,
        amount: float,
        description: str,
        result_url: str,
        server_url: str,
        currency: str = "UAH",
    ) -> dict:
        payload = {
            "public_key": self.public_key,
            "version": "3",
            "action": "pay",
            "amount": amount,
            "currency": currency,
            "description": description,
            "order_id": order_id,
            "result_url": result_url,
            "server_url": server_url,
            "sandbox": 1 if getattr(settings, "LIQPAY_SANDBOX", True) else 0,
        }
        data_b64 = self._encode(payload)
        return {
            "data": data_b64,
            "signature": self._sign(data_b64),
            "checkout_url": LIQPAY_CHECKOUT_URL,
            "payload": payload,
        }


def get_liqpay_client() -> LiqPayClient:
    pub = getattr(settings, "LIQPAY_PUBLIC_KEY", "") or ""
    priv = getattr(settings, "LIQPAY_PRIVATE_KEY", "") or ""
    if not pub or not priv:
        raise PaymentError("LiqPay ключі не налаштовані")
    return LiqPayClient(pub, priv)


@transaction.atomic
def create_checkout(order: Order, *, result_url: str, server_url: str) -> dict:
    client = get_liqpay_client()
    tx = PaymentTransaction.objects.create(
        order=order,
        provider=PaymentTransaction.Provider.LIQPAY,
        status=PaymentTransaction.Status.CREATED,
        amount=order.total,
        currency="UAH",
        external_id=order.number,
    )
    form_data = client.create_checkout_data(
        order_id=order.number,
        amount=float(order.total),
        description=f"Замовлення {order.number}",
        result_url=result_url,
        server_url=server_url,
    )
    tx.status = PaymentTransaction.Status.REDIRECTED
    tx.raw_request = form_data.get("payload", {})
    tx.save(update_fields=["status", "raw_request", "updated_at"])
    return {
        "transaction": tx,
        "data": form_data["data"],
        "signature": form_data["signature"],
        "checkout_url": form_data["checkout_url"],
    }


@transaction.atomic
def handle_webhook(*, data_b64: str, signature: str) -> Order:
    client = get_liqpay_client()
    if not client.verify_callback(data_b64, signature):
        raise PaymentError("Невірний підпис LiqPay")

    payload = client.decode_data(data_b64)
    order_number = payload.get("order_id", "")
    status = payload.get("status", "")
    payment_id = str(payload.get("payment_id", ""))
    if not order_number:
        raise PaymentError("Немає order_id")

    order = Order.objects.select_for_update().filter(number=order_number).first()
    if order is None:
        raise PaymentError("Замовлення не знайдено")

    idem_key = f"liqpay_{payment_id}_{status}"
    tx = (
        order.payments.filter(provider=PaymentTransaction.Provider.LIQPAY)
        .order_by("-created_at")
        .first()
    )
    if tx and tx.idempotency_key == idem_key:
        return order

    if status in ("success", "sandbox"):
        order.payment_status = Order.PaymentStatus.PAID
        order.status = Order.Status.PAID
        order.save(update_fields=["payment_status", "status", "updated_at"])
        if tx:
            tx.status = PaymentTransaction.Status.SUCCESS
            tx.external_id = payment_id or tx.external_id
            tx.idempotency_key = idem_key
            tx.raw_response = payload
            tx.save(
                update_fields=[
                    "status",
                    "external_id",
                    "idempotency_key",
                    "raw_response",
                    "updated_at",
                ]
            )
    elif status in ("failure", "error", "reversed"):
        order.payment_status = Order.PaymentStatus.FAILED
        order.save(update_fields=["payment_status", "updated_at"])
        if tx:
            tx.status = PaymentTransaction.Status.FAILURE
            tx.idempotency_key = idem_key
            tx.raw_response = payload
            tx.save(
                update_fields=[
                    "status",
                    "idempotency_key",
                    "raw_response",
                    "updated_at",
                ]
            )
    return order
