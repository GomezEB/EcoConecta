#!/usr/bin/env bash
set -euo pipefail
: "${DATABASE_URL:?Falta DATABASE_URL para conectar PostgreSQL}"
# Render Postgres ofrece postgresql://; el backend requiere el dialecto psycopg.
case "$DATABASE_URL" in
  postgresql://*) export DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgresql://}" ;;
  postgres://*) export DATABASE_URL="postgresql+psycopg://${DATABASE_URL#postgres://}" ;;
  postgresql+psycopg://*) ;;
  *) echo "DATABASE_URL debe ser una conexion PostgreSQL valida" >&2; exit 1 ;;
esac
PORT="${PORT:-10000}"
if ! [[ "$PORT" =~ ^[0-9]{2,5}$ ]] || (( PORT < 1024 || PORT > 65535 )); then
  echo "PORT invalido" >&2; exit 1
fi
sed "s/__PORT__/${PORT}/g" /etc/nginx/sites-available/ecoconecta.template > /etc/nginx/sites-enabled/ecoconecta
nginx -t

# El seed solo se ejecuta cuando el equipo lo habilita explicitamente.
if [[ "${DEMO_SEED_ENABLED:-false}" == "true" ]]; then
  python -m scripts.seed_demo
fi
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!
nginx -g 'daemon off;' &
nginx_pid=$!
trap 'kill "$api_pid" "$nginx_pid" 2>/dev/null || true' SIGINT SIGTERM
wait -n "$api_pid" "$nginx_pid"
exit_code=$?
kill "$api_pid" "$nginx_pid" 2>/dev/null || true
wait || true
exit "$exit_code"
