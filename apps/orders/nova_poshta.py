"""Клієнт API Нової Пошти (Address). IPv4 + SNI — Docker/DO часто ламає AAAA."""

from __future__ import annotations

import http.client
import json
import logging
import socket
import ssl
from typing import Any
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger(__name__)

NP_API_URL = "https://api.novaposhta.ua/v2.0/json/"
NP_TIMEOUT = 12
NP_USER_AGENT = "Boltiko/1.0 (+https://boltiko.com.ua)"
# CategoryOfWarehouse у відповіді: Branch = відділення, Postomat = поштомат
NP_CATEGORY = {
    "warehouse": "Branch",
    "postomat": "Postomat",
}


class NovaPoshtaError(Exception):
    pass


class _IPv4HTTPSConnection(http.client.HTTPSConnection):
    def connect(self) -> None:
        timeout = self.timeout if self.timeout is not None else NP_TIMEOUT
        infos = socket.getaddrinfo(
            self.host, self.port, socket.AF_INET, socket.SOCK_STREAM
        )
        if not infos:
            raise OSError(f"Немає IPv4-адреси для {self.host}")
        sock = None
        err: OSError | None = None
        for family, socktype, proto, _canon, sockaddr in infos:
            candidate = socket.socket(family, socktype, proto)
            candidate.settimeout(timeout)
            try:
                candidate.connect(sockaddr)
                sock = candidate
                break
            except OSError as exc:
                err = exc
                candidate.close()
        if sock is None:
            raise err or OSError(f"Не вдалося зʼєднатися з {self.host}")
        context = self._context or ssl.create_default_context()
        self.sock = context.wrap_socket(sock, server_hostname=self.host)


def _api_key() -> str:
    return (getattr(settings, "NOVA_POSHTA_API_KEY", "") or "").strip()


def is_configured() -> bool:
    return bool(_api_key())


def _post_json(payload: dict[str, Any]) -> dict[str, Any]:
    parsed = urlparse(NP_API_URL)
    host = parsed.hostname or "api.novaposhta.ua"
    port = parsed.port or 443
    path = parsed.path or "/v2.0/json/"
    raw = json.dumps(payload).encode("utf-8")
    headers = {
        "Host": host,
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": NP_USER_AGENT,
    }
    ctx = ssl.create_default_context()
    conn = _IPv4HTTPSConnection(host, port, timeout=NP_TIMEOUT, context=ctx)
    try:
        conn.request("POST", path, body=raw, headers=headers)
        resp = conn.getresponse()
        body = resp.read()
        status = resp.status
    except (OSError, ssl.SSLError, TimeoutError, socket.timeout) as exc:
        logger.warning("Nova Poshta API error: %s", exc)
        raise NovaPoshtaError("Не вдалося звернутися до API Нової Пошти") from exc
    finally:
        conn.close()

    if status >= 400:
        logger.warning("Nova Poshta HTTP %s: %s", status, body[:300])
        raise NovaPoshtaError("Не вдалося звернутися до API Нової Пошти")

    try:
        parsed_body = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Nova Poshta API bad json: %s", exc)
        raise NovaPoshtaError("Не вдалося звернутися до API Нової Пошти") from exc
    if not isinstance(parsed_body, dict):
        raise NovaPoshtaError("Не вдалося звернутися до API Нової Пошти")
    return parsed_body


def _call(model_name: str, method: str, props: dict[str, Any]) -> list[dict]:
    key = _api_key()
    if not key:
        raise NovaPoshtaError("API Нової Пошти не налаштовано")

    body = _post_json(
        {
            "apiKey": key,
            "modelName": model_name,
            "calledMethod": method,
            "methodProperties": props,
        }
    )

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


def _warehouse_item(item: dict) -> dict[str, str] | None:
    ref = item.get("Ref") or ""
    name = item.get("Description") or item.get("DescriptionRu") or ""
    if not ref or not name:
        return None
    return {"ref": ref, "name": name}


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

    try:
        rows = _call("Address", "getWarehouses", props)
    except NovaPoshtaError:
        rows = []
    if not rows:
        fallback_props = {k: v for k, v in props.items() if k != "CategoryOfWarehouse"}
        rows = [
            item
            for item in _call("Address", "getWarehouses", fallback_props)
            if (item.get("CategoryOfWarehouse") or "") == category
        ]

    out: list[dict[str, str]] = []
    for item in rows:
        mapped = _warehouse_item(item)
        if mapped:
            out.append(mapped)
    return out
