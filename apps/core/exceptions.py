"""Спільні винятки бізнес-логіки."""


class DomainError(Exception):
    """Базовий доменний виняток (повідомлення безпечне для UI)."""


class CartError(DomainError):
    pass


class OrderError(DomainError):
    pass


class PaymentError(DomainError):
    pass


class ReviewError(DomainError):
    pass
