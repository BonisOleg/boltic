#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

COMPOSE=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
SERVICES=(db web nginx)

if ls /etc/letsencrypt/live/*/fullchain.pem >/dev/null 2>&1; then
  COMPOSE+=(-f docker-compose.ssl.yml)
  echo "==> SSL overlay enabled"
fi

free_host_ports() {
  if command -v systemctl >/dev/null 2>&1; then
    systemctl stop nginx 2>/dev/null || true
    systemctl disable nginx 2>/dev/null || true
    systemctl stop gunicorn 2>/dev/null || true
  fi
}

free_host_ports

echo "==> build + up"
"${COMPOSE[@]}" up -d --build --remove-orphans || true

echo "==> wait healthz"
ok=0
for _ in $(seq 1 60); do
  if curl -sf http://127.0.0.1/healthz/ >/dev/null 2>&1; then
    ok=1
    break
  fi
  sleep 3
done

"${COMPOSE[@]}" up -d --remove-orphans || true

echo "==> inventory"
missing=0
for svc in "${SERVICES[@]}"; do
  if "${COMPOSE[@]}" ps "$svc" 2>/dev/null | grep -q "running"; then
    echo "OK: $svc"
  else
    echo "MISSING: $svc"
    missing=1
  fi
done

if [ "$ok" -ne 1 ]; then
  echo "WARN: /healthz/ not ready — logs:"
  "${COMPOSE[@]}" logs --tail=40 web nginx db
  exit 1
fi

echo "==> HTTP healthz OK"
if [ "$missing" -ne 0 ]; then
  exit 1
fi
