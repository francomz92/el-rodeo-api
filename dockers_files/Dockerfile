# FROM tiangolo/uvicorn-gunicorn-fastapi:python3.12

# RUN apt-get update && \
#     apt-get install systemctl && \
#     apt-get install -yq tzdata && \
#     ln -fs /usr/share/zoneinfo/America/Argentina/Buenos_Aires /etc/localtime && \
#     dpkg-reconfigure -f noninteractive tzdata

# ENV PYTHONUNBUFFERED 1
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV TZ="America/Argentina/Buenos_Aires"

# WORKDIR /usr/src/api

# COPY . .

# RUN pip install --no-cache-dir --upgrade uv

# RUN uv sync



# Build stage
FROM python:3.11-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync

# Run stage
FROM python:3.11-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

ENV TZ=America/Argentina/Buenos_Aires

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY ./app ./app
