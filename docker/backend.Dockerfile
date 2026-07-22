# --- Stage 1: build dependencies in a throwaway layer ---
FROM python:3.12-slim AS builder

WORKDIR /build

# Compiler toolchain needed to build a couple of wheels (e.g. asyncpg) on
# some architectures; kept isolated to this stage so it never ships in the
# final image.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# --- Stage 2: slim runtime image ---
FROM python:3.12-slim

# Never run the app as root inside the container.
RUN groupadd --system ecomind && useradd --system --gid ecomind --create-home ecomind

WORKDIR /app

# curl is needed for the HEALTHCHECK below; kept minimal and pinned to
# --no-install-recommends to avoid pulling in unnecessary packages.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /home/ecomind/.local
COPY --chown=ecomind:ecomind app ./app

ENV PATH=/home/ecomind/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER ecomind

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Single worker by default — this is an MVP deployment target (AWS App
# Runner scales at the container level), not a multi-worker Gunicorn setup.
# Bump --workers here (and drop --reload, which is already absent) if a
# future deployment needs in-container concurrency.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
