#!/bin/sh
set -eu

echo "==> Waiting for PostgreSQL..."
i=0
while [ "$i" -lt 60 ]; do
  if nc -z "${DB_HOST:-db}" "${DB_PORT:-5432}"; then
    echo "==> DB ready"
    break
  fi
  i=$((i + 1))
  sleep 1
done
if [ "$i" -ge 60 ]; then
  echo "FATAL: DB not ready"
  exit 1
fi

echo "==> migrate + collectstatic"
python manage.py migrate --noinput
python manage.py collectstatic --noinput

STATIC_ROOT="${STATIC_ROOT:-/app/staticfiles}"
count=$(find "$STATIC_ROOT" -type f 2>/dev/null | wc -l | tr -d ' ')
echo "==> static files: ${count}"
if [ "${count:-0}" -lt 10 ]; then
  echo "WARN: staticfiles count low — check STATIC_ROOT and collectstatic"
fi

exec "$@"
