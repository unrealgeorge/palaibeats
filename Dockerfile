# syntax=docker/dockerfile:1
#
# Multi-stage build so the final image doesn't carry compilers/headers.
# Builds fine on both amd64 (dev machine) and arm64 (Raspberry Pi 4).

FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.11-slim

# ffmpeg: audio decoding/encoding for local files, links and radio streams.
# libopus0: Discord voice codec. libsodium23: voice encryption (PyNaCl).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libopus0 \
        libsodium23 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

WORKDIR /app
COPY src ./src

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

RUN useradd --create-home --uid 1000 palaibeats \
    && mkdir -p /data /music \
    && chown -R palaibeats:palaibeats /app /data
USER palaibeats

VOLUME ["/data"]

ENTRYPOINT ["python", "-m", "palaibeats"]
