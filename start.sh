#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CADDY_PID=""
GUNICORN_PID=""

cleanup() {
  local exit_code=${1:-0}

  echo "[start.sh] shutting down..."

  if [ -n "${GUNICORN_PID}" ] && kill -0 "${GUNICORN_PID}" 2>/dev/null; then
    kill -TERM "${GUNICORN_PID}" 2>/dev/null || true
  fi

  if [ -n "${CADDY_PID}" ] && kill -0 "${CADDY_PID}" 2>/dev/null; then
    kill -TERM "${CADDY_PID}" 2>/dev/null || true
  fi

  wait || true
  return "$exit_code"
}

on_signal() {
  echo "[start.sh] signal received"
  cleanup 0
  exit 0
}

trap on_signal TERM INT

start_caddy() {
  caddy run --config "$SCRIPT_DIR/Caddyfile" 2>&1 \
    | sed -u 's/^/[caddy] /' &
  CADDY_PID=$!
}

start_gunicorn() {
  uv run gunicorn app:app \
    --bind localhost:7000 \
    --no-control-socket \
    --access-logfile - \
    --error-logfile - \
    2>&1 | sed -u 's/^/[gunicorn] /' &
  GUNICORN_PID=$!
}

start_caddy
start_gunicorn

set +e
wait -n "$CADDY_PID" "$GUNICORN_PID"
EXIT_CODE=$?
set -e

echo "[start.sh] one process exited with code $EXIT_CODE"

cleanup "$EXIT_CODE"
exit "$EXIT_CODE"
