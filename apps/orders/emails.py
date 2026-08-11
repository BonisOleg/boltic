import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.core.models import SiteSettings
from apps.orders.models import Order

logger = logging.getLogger(__name__)


def _manager_email(site: SiteSettings) -> str:
    return (site.orders_email or site.email or "").strip()


def _from_email() -> str:
    return getattr(settings, "DEFAULT_FROM_EMAIL", "") or "noreply@localhost"


def send_order_emails(order: Order) -> None:
    """Лист менеджеру + клієнту (якщо є email). Помилки не валять checkout."""
    site = SiteSettings.load()
    order = (
        Order.objects.filter(pk=order.pk)
        .prefetch_related("items")
        .first()
        or order
    )
    ctx = {"order": order, "site": site}

    manager_to = _manager_email(site)
    if manager_to:
        try:
            body = render_to_string("orders/emails/order_manager.txt", ctx)
            send_mail(
                subject=f"Нове замовлення {order.number}",
                message=body,
                from_email=_from_email(),
                recipient_list=[manager_to],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Не вдалося надіслати лист менеджеру %s", manager_to)

    customer = (order.email or "").strip()
    if customer:
        try:
            body = render_to_string("orders/emails/order_customer.txt", ctx)
            send_mail(
                subject=f"Ваше замовлення {order.number} — {site.site_name}",
                message=body,
                from_email=_from_email(),
                recipient_list=[customer],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Не вдалося надіслати лист клієнту %s", customer)
