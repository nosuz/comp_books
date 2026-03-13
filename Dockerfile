# syntax=docker/dockerfile:1.4
FROM python:3-alpine

WORKDIR /app

# install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ARG UV_CACHE_DIR=/tmp/uv.cache
RUN mkdir -p $UV_CACHE_DIR
# Disable development dependencies
ENV UV_NO_DEV=1
# specify `__pycache__` directory
ENV PYTHONPYCACHEPREFIX=/tmp/pycache

COPY pyproject.toml uv.lock ./
# set `--frozen` to `uv sync` on runtime
RUN --mount=type=cache,target=$UV_CACHE_DIR,sharing=locked \
    uv venv venv \
    && if [ -s uv.lock ]; then uv sync --frozen; fi

COPY . .

ENTRYPOINT ["uv", "run", "gunicorn", "app:app", \
    "--bind", "0.0.0.0:7000", \
    "--no-control-socket", \
    "--access-logfile", "-", \
    "--error-logfile", "-"]
