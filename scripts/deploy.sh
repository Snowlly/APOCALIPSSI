#!/usr/bin/env bash
# ============================================================================
# deploy.sh — Déploiement / mise à jour en PRODUCTION (Linux / VPS)
# ----------------------------------------------------------------------------
# Enchaîne, en une commande :
#   1. git pull               (récupère le nouveau code depuis GitHub)
#   2. docker compose build + up -d (mode PRODUCTION : gunicorn + nginx, ports fermés)
#   3. reconnexion au reverse proxy existant (si PROXY_NETWORK défini dans .env)
#   4. affiche l'état des conteneurs
#
# Usage (sur le serveur) :
#   bash scripts/deploy.sh             # git pull + build + déploiement
#   bash scripts/deploy.sh --no-pull   # déploie le code local sans git pull
#
# Lançable depuis n'importe où : le script se replace à la racine du projet.
# ============================================================================
set -euo pipefail

cd "$(dirname "$0")/.."

PROD=(-f docker-compose.yml -f docker-compose.prod.yml)
CONTAINERS=(apocalipssi-2026-backend apocalipssi-2026-frontend)

# ---------- Options ----------
SKIP_PULL=0
for arg in "$@"; do
  case "$arg" in
    --no-pull) SKIP_PULL=1 ;;
    --help|-h)
      echo "Usage : bash scripts/deploy.sh [--no-pull]"
      echo "  --no-pull   Ne pas faire 'git pull' (déploie le code déjà présent)."
      exit 0
      ;;
    *) echo "Option inconnue : $arg" >&2; exit 1 ;;
  esac
done

# ---------- Préflight ----------
if ! docker compose version >/dev/null 2>&1; then
  echo "ERREUR : 'docker compose' (v2) introuvable." >&2
  exit 1
fi
if [ ! -f .env ]; then
  echo "ERREUR : .env absent. Copiez .env.prod.example en .env et complétez-le." >&2
  exit 1
fi

# ---------- 1. Récupération du code ----------
if [ "$SKIP_PULL" -eq 0 ]; then
  echo "==> git pull --ff-only"
  git pull --ff-only
else
  echo "==> git pull ignoré (--no-pull)."
fi

# ---------- 2. Build + déploiement (production) ----------
echo "==> Build + (re)démarrage en production..."
docker compose "${PROD[@]}" up -d --build --remove-orphans

# ---------- 3. Reconnexion au reverse proxy existant ----------
# Si PROXY_NETWORK est défini dans .env (ex. PROXY_NETWORK=formaplanner_formaplanner),
# on (re)connecte les conteneurs au réseau du proxy. Le 'up' ci-dessus ayant recréé
# les conteneurs, cette étape restaure le lien réseau à CHAQUE déploiement.
PROXY_NETWORK="$(sed -n 's/^[[:space:]]*PROXY_NETWORK[[:space:]]*=[[:space:]]*//p' .env | head -n1)"
if [ -n "${PROXY_NETWORK:-}" ]; then
  echo "==> Reconnexion au réseau proxy : $PROXY_NETWORK"
  for c in "${CONTAINERS[@]}"; do
    if docker network connect "$PROXY_NETWORK" "$c" 2>/dev/null; then
      echo "    + $c connecté à $PROXY_NETWORK"
    else
      echo "    = $c déjà connecté (ou rien à faire)"
    fi
  done
else
  echo "==> PROXY_NETWORK non défini dans .env : pas de proxy externe (OK pour un VPS dédié)."
fi

# ---------- 4. État ----------
echo ""
echo "==> État des conteneurs :"
docker compose "${PROD[@]}" ps
echo ""
echo "OK. Déploiement terminé."
