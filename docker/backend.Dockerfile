# ============================================================================
# IPSSI_APOCAL_KIT — Dockerfile backend (Django)
# ----------------------------------------------------------------------------
# Image Python 3.11 slim — installation des deps + lancement runserver.
# Pour la production, remplacer runserver par gunicorn (cf docs/05-ci-cd.md).
# ============================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances système nécessaires à psycopg
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Installer requirements en premier (cache layer)
COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements.txt -r requirements-dev.txt

# Copier le reste du code
COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
