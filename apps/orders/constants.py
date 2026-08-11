from decimal import Decimal

MIN_ORDER_AMOUNT = Decimal("400.00")

CHECKOUT_SESSION_KEY = "checkout"

SHIPPING_PICKUP = "pickup"
SHIPPING_NOVA_POSHTA = "nova_poshta"

NP_TYPE_WAREHOUSE = "warehouse"
NP_TYPE_POSTOMAT = "postomat"

SHIPPING_METHOD_LABELS = {
    SHIPPING_PICKUP: "Самовивіз",
    SHIPPING_NOVA_POSHTA: "Нова Пошта",
}

NP_TYPE_LABELS = {
    NP_TYPE_WAREHOUSE: "Відділення",
    NP_TYPE_POSTOMAT: "Поштомат",
}
