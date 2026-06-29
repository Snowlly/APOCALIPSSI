#!/usr/bin/env bash
# ============================================================================
# redeploy.sh — Redéploiement du kit EduTutor IA (Linux / macOS)
# ----------------------------------------------------------------------------
# Reconstruit les images, recrée les conteneurs (prise en compte du code ET du
# .env), puis relance Docker. À lancer après une modification de code/config
# pour tester. Lançable depuis n'importe où : le script se replace tout seul
# à la racine du projet.
#
# Usage :
#   bash scripts/redeploy.sh           # redéploiement complet (avec rebuild)
#   bash scripts/redeploy.sh --fast    # rapide : recrée sans reconstruire les images
# ============================================================================
set -euo pipefail

# Se placer à la racine du projet (dossier parent de ce script).
cd "$(dirname "$0")/.."

# Mode rapide (--fast) : on saute le rebuild des images (utile si on n'a touché
# qu'à du code Python/JS monté en volume, pas aux dépendances/Dockerfiles).
BUILD_FLAG="--build"
if [ "${1:-}" = "--fast" ]; then
  BUILD_FLAG=""
  echo "==> Mode rapide : pas de reconstruction d'image."
fi

echo "==> Redeploiement EduTutor IA (projet docker : apocalipssi-2026)"
echo "==> docker compose up -d ${BUILD_FLAG} --force-recreate"
docker compose up -d ${BUILD_FLAG} --force-recreate

echo ""
echo "==> Etat des conteneurs :"
docker compose ps

echo ""
echo "OK. Services accessibles :"
echo "  Frontend : http://localhost:3000   (ou le port FRONTEND_HOST_PORT de votre .env)"
echo "  API      : http://localhost:8000/api"
echo "  API docs : http://localhost:8000/api/docs"
echo ""
echo "Premier lancement avec Ollama ? Telechargez le modele (une seule fois) :"
echo "  docker exec apocalipssi-2026-ollama ollama pull llama3.1:8b"
