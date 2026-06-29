# ============================================================================
# IPSSI_APOCAL_KIT — Dockerfile backend PRODUCTION (multi-stage, sans dev-deps)
# ----------------------------------------------------------------------------
# Stage 1 (builder) : compile les wheels (build-essential + libpq-dev présents
#                     ICI seulement, pas dans l'image finale).
# Stage 2 (runtime) : image slim SANS compilateur, installe les wheels.
# Le démarrage (migrate + collectstatic + gunicorn) est défini par
# docker-compose.prod.yml.
# ============================================================================

# ---- Stage 1 : builder ----
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# ---- Stage 2 : runtime ----
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# psycopg[binary] embarque sa propre libpq -> pas besoin de libpq au runtime.
COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels

# Code applicatif
COPY . .

EXPOSE 8000

# Commande par défaut (surchargée par docker-compose.prod.yml qui ajoute
# migrate + collectstatic avant gunicorn).
CMD ["gunicorn", "apocal.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
