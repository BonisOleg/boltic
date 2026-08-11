"""Клієнт API Нової Пошти (Address / AddressGeneral)."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from django.conf import settings

logger = logging.getLogger(__name__)

NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"
# CategoryOfWarehouse: Branch = відділення, Postomat = поштомат
NP_CATEGORY = {
    "warehouse": "Branch",
    "postomat": "Postomat",
}


class NovaPoshtaError(Exception):
    pass


def _api_key() -> str:
    return (getattr(settings, "NOVA_POSHTA_API_KEY", "") or "").strip()


def is_configured() -> bool:
    return bool(_api_key())


def _call(model_name: str, method: str, props: dict[str, Any]) -> list[dict]:
    key = _api_key()
    if not key:
        raise NovaPoshtaError("API Нової Пошти не налаштовано")

    payload = {
        "apiKey": key,
        "modelName": model_name,
        "calledMethod": method,
        "methodProperties": props,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        NP_API_URL,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("Nova Poshta API error: %s", exc)
        raise NovaPoshtaError("Не вдалося звернутися до API Нової Пошти") from exc

    if not body.get("success"):
        errors = body.get("errors") or body.get("warnings") or ["Помилка API"]
        msg = "; ".join(str(e) for e in errors)
        logger.warning("Nova Poshta API rejected: %s", msg)
        raise NovaPoshtaError(msg or "Помилка API Нової Пошти")

    return body.get("data") or []


def search_cities(query: str, *, limit: int = 20) -> list[dict[str, str]]:
    q = (query or "").strip()
    if len(q) < 2:
        return []
    rows = _call(
        "Address",
        "searchSettlements",
        {"CityName": q, "Limit": str(limit)},
    )
    out: list[dict[str, str]] = []
    for block in rows:
        for item in block.get("Addresses") or []:
            ref = item.get("DeliveryCity") or item.get("Ref") or ""
            name = item.get("Present") or item.get("MainDescription") or ""
            if ref and name:
                out.append({"ref": ref, "name": name})
    return out


def search_warehouses(
    city_ref: str,
    *,
    delivery_type: str,
    query: str = "",
    limit: int = 50,
) -> list[dict[str, str]]:
    city_ref = (city_ref or "").strip()
    if not city_ref:
        return []
    category = NP_CATEGORY.get(delivery_type)
    if not category:
        raise NovaPoshtaError("Невірний тип доставки НП")

    props: dict[str, Any] = {
        "CityRef": city_ref,
        "CategoryOfWarehouse": category,
        "Limit": str(limit),
    }
    q = (query or "").strip()
    if q:
        props["FindByString"] = q

    rows = _call("Address", "getWarehouses", props)
    out: list[dict[str, str]] = []
    for item in rows:
        ref = item.get("Ref") or ""
        name = item.get("Description") or item.get("DescriptionRu") or ""
        if ref and name:
            out.append({"ref": ref, "name": name})
    return out
