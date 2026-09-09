"""dataLayer purchase для GTM (GA4 ecommerce)."""

from __future__ import annotations

from apps.orders.models import Order

SESSION_PENDING_KEY = "gtm_purchase_pending"


def mark_purchase_pending(request, order: Order) -> None:
    request.session[SESSION_PENDING_KEY] = order.number


def consume_purchase_payload(request, order: Order) -> dict | None:
    """Повернути payload лише один раз після place_order у цій сесії."""
    pending = request.session.pop(SESSION_PENDING_KEY, None)
    if pending != order.number:
        return None
    items = [
        {
            "item_id": item.article,
            "item_name": item.name,
            "price": float(item.unit_price),
            "quantity": int(item.quantity),
        }
        for item in order.items.all()
    ]
    return {
        "event": "purchase",
        "ecommerce": {
            "transaction_id": order.number,
            "value": float(order.total),
            "currency": "UAH",
            "items": items,
        },
    }
