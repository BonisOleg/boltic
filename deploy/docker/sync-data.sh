#!/usr/bin/env bash
# Локальна sqlite + media → Postgres/volume на Droplet.
#
#   ./deploy/docker/sync-data.sh export
#   ./deploy/docker/sync-data.sh import --yes
#   ./deploy/docker/sync-data.sh push user@droplet:/opt/Boltiko --yes
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

DATA_DIR="$ROOT/deploy/data"
DUMP_JSON="$DATA_DIR/boltiko_data.json"
MEDIA_TAR="$DATA_DIR/media.tar.gz"
DUMP_APPS=(
  auth.user
  accounts
  catalog
  content
  core
  reviews
  cart
  orders
  payments
)

compose_cmd() {
  local -a cmd=(docker compose -f docker-compose.yml -f docker-compose.prod.yml)
  if ls /etc/letsencrypt/live/*/fullchain.pem >/dev/null 2>&1; then
    cmd+=(-f docker-compose.ssl.yml)
  fi
  "${cmd[@]}" "$@"
}

local_python() {
  if [ -x "$ROOT/.venv/bin/python3" ]; then
    echo "$ROOT/.venv/bin/python3"
  else
    echo "python3"
  fi
}

cmd_export() {
  mkdir -p "$DATA_DIR"
  local py
  py="$(local_python)"
  echo "==> dumpdata → $DUMP_JSON"
  DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-boltiko.settings}" \
    "$py" manage.py dumpdata "${DUMP_APPS[@]}" \
    --natural-foreign --natural-primary \
    --indent 2 \
    -o "$DUMP_JSON"
  echo "==> media → $MEDIA_TAR"
  if [ -d "$ROOT/media" ]; then
    tar -C "$ROOT/media" -czf "$MEDIA_TAR" .
  else
    echo "WARN: media/ відсутня — створюю порожній архів"
    tar -czf "$MEDIA_TAR" -T /dev/null
  fi
  echo "==> export OK"
  ls -lh "$DUMP_JSON" "$MEDIA_TAR"
}

confirm_replace() {
  if [ "${1:-}" = "--yes" ] || [ "${1:-}" = "-y" ]; then
    return 0
  fi
  echo "Імпорт ПЕРЕЗАПИШЕ Postgres (товари, тема, сторінки, юзери)."
  read -r -p "Продовжити? [y/N] " ans
  case "$ans" in
    y|Y|yes|YES) ;;
    *) echo "Скасовано"; exit 1 ;;
  esac
}

cmd_import() {
  confirm_replace "${1:-}"
  if [ ! -f "$DUMP_JSON" ]; then
    echo "FATAL: немає $DUMP_JSON — спочатку export"
    exit 1
  fi
  if [ ! -f "$MEDIA_TAR" ]; then
    echo "FATAL: немає $MEDIA_TAR — спочатку export"
    exit 1
  fi

  echo "==> wait web"
  local i=0
  while [ "$i" -lt 40 ]; do
    if compose_cmd exec -T web python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz/', timeout=5)" >/dev/null 2>&1; then
      break
    fi
    i=$((i + 1))
    sleep 3
  done
  if [ "$i" -ge 40 ]; then
    echo "FATAL: web/healthz не готовий"
    compose_cmd logs --tail=40 web
    exit 1
  fi

  echo "==> flush + loaddata"
  compose_cmd cp "$DUMP_JSON" web:/tmp/boltiko_data.json
  compose_cmd exec -T web python manage.py flush --noinput
  compose_cmd exec -T web python manage.py loaddata /tmp/boltiko_data.json
  compose_cmd exec -T web python manage.py reset_pk_sequences

  echo "==> media → volume"
  compose_cmd exec -T web mkdir -p /app/media
  compose_cmd cp "$MEDIA_TAR" web:/tmp/media.tar.gz
  compose_cmd exec -T web tar -xzf /tmp/media.tar.gz -C /app/media
  compose_cmd exec -T web rm -f /tmp/boltiko_data.json /tmp/media.tar.gz

  echo "==> import OK"
}

cmd_push() {
  local target="${1:-}"
  local yes_flag="${2:-}"
  if [ -z "$target" ] || [ "$target" = "${target#*:}" ]; then
    echo "Usage: $0 push user@host:/path/to/Boltiko [--yes]"
    exit 1
  fi
  local host="${target%%:*}"
  local rpath="${target#*:}"
  cmd_export
  echo "==> scp → $host:$rpath/deploy/data/"
  ssh "$host" "mkdir -p '$rpath/deploy/data'"
  scp "$DUMP_JSON" "$MEDIA_TAR" "$host:$rpath/deploy/data/"
  echo "==> remote import"
  ssh "$host" "cd '$rpath' && bash ./deploy/docker/sync-data.sh import ${yes_flag:---yes}"
}

usage() {
  echo "Usage: $0 export | import [--yes] | push user@host:/path [--yes]"
  exit 1
}

case "${1:-}" in
  export) cmd_export ;;
  import) cmd_import "${2:-}" ;;
  push) cmd_push "${2:-}" "${3:-}" ;;
  *) usage ;;
esac
