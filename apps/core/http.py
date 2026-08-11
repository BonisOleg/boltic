"""Хелпери для безпечних редіректів за параметром ?next."""

from django.http import HttpRequest
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme, urlencode


def safe_next(
    request: HttpRequest, *, fallback: str = "", allow_referer: bool = False
) -> str:
    """Повернути next з POST/GET (за потреби — з Referer), якщо хост той самий."""
    candidates = [request.POST.get("next"), request.GET.get("next")]
    if allow_referer:
        candidates.append(request.META.get("HTTP_REFERER"))
    for candidate in candidates:
        if not candidate:
            continue
        if url_has_allowed_host_and_scheme(
            candidate,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return candidate
    return fallback


def url_with_next(url_name: str, next_url: str) -> str:
    """Побудувати URL за іменем маршруту з екранованим ?next."""
    target = reverse(url_name)
    if not next_url:
        return target
    return f"{target}?{urlencode({'next': next_url})}"
