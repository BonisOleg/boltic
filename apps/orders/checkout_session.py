from apps.orders.constants import CHECKOUT_SESSION_KEY


def get_checkout(request) -> dict:
    data = request.session.get(CHECKOUT_SESSION_KEY)
    return dict(data) if isinstance(data, dict) else {}


def save_checkout(request, data: dict) -> None:
    request.session[CHECKOUT_SESSION_KEY] = data
    request.session.modified = True


def update_checkout(request, **fields) -> dict:
    data = get_checkout(request)
    data.update({k: v for k, v in fields.items() if v is not None})
    save_checkout(request, data)
    return data


def clear_checkout(request) -> None:
    if CHECKOUT_SESSION_KEY in request.session:
        del request.session[CHECKOUT_SESSION_KEY]
        request.session.modified = True


def has_contact(data: dict) -> bool:
    return bool(data.get("customer_name") and data.get("phone"))


def has_delivery(data: dict) -> bool:
    return bool(data.get("shipping_method"))
