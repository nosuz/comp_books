#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

CADDY_PID=""
GUNICORN_PID=""

cleanup() {
  echo "Shutting down..."

  if [ -n "${GUNICORN_PID}" ] && kill -0 "${GUNICORN_PID}" 2>/dev/null; then
    kill -TERM "${GUNICORN_PID}" 2>/dev/null || true
  fi

  if [ -n "${CADDY_PID}" ] && kill -0 "${CADDY_PID}" 2>/dev/null; then
    kill -TERM "${CADDY_PID}" 2>/dev/null || true
  fi

  wait || true
}

trap cleanup TERM INT

caddy run --config "$SCRIPT_DIR/Caddyfile" \
  2>&1 | tee -a "$LOG_DIR/caddy.log" &
CADDY_PID=$!

gunicorn app:app \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  2>&1 | tee -a "$LOG_DIR/gunicorn.log" &
GUNICORN_PID=$!

wait -n

cleanup
exit $?
