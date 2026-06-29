#!/usr/bin/env bash
# ============================================================================
# start-macos.sh — Lancement complet du kit EduTutor IA (macOS)
# ----------------------------------------------------------------------------
# Build + deploiement + relance Docker, en UNE commande. Le script enchaine :
#   1. .env       : copie .env.example -> .env s'il manque
#   2. build      : docker compose build (saute si --fast)
#   3. up         : docker compose up -d --force-recreate
#   4. sante      : attend que le backend reponde (http://localhost:8000)
#   5. migrate    : applique les migrations (idempotent)
#   6. seed       : insere les donnees de demo (saute si --no-seed)
#   7. modele LLM : verifie sa presence ; s'il manque, propose le telechargement
#   8. URLs       : recapitulatif des adresses
#
# Prerequis macOS : Docker Desktop doit etre LANCE (icone baleine dans la barre
# de menus). Lançable depuis n'importe ou : le script se replace a la racine.
#
# Usage :
#   bash scripts/start-macos.sh                 # lancement complet
#   bash scripts/start-macos.sh --fast          # relance sans rebuild
#   bash scripts/start-macos.sh --yes           # non-interactif (pull modele auto)
#   bash scripts/start-macos.sh --no-seed       # sans donnees de demo
#   bash scripts/start-macos.sh --logs          # suit les logs apres demarrage
#   (options cumulables ; --help pour l'aide)
# ============================================================================
set -euo pipefail

# Se placer a la racine du projet (dossier parent de ce script).
cd "$(dirname "$0")/.."

OLLAMA_CONTAINER="apocalipssi-2026-ollama"
DEFAULT_MODEL="llama3.1:8b"

# ---------- Options ----------
FAST=0
ASSUME_YES=0
NO_SEED=0
FOLLOW_LOGS=0

usage() {
  cat <<'EOF'
Usage : bash scripts/start-macos.sh [options]

  --fast      Relance sans reconstruire les images (gain de temps).
  --yes       Mode non-interactif : telecharge le modele LLM s'il manque,
              sans poser de question.
  --no-seed   Ne pas inserer les donnees de demonstration.
  --logs      Suivre les logs des conteneurs apres le demarrage.
  --help      Afficher cette aide.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --fast)     FAST=1 ;;
    --yes|-y)   ASSUME_YES=1 ;;
    --no-seed)  NO_SEED=1 ;;
    --logs)     FOLLOW_LOGS=1 ;;
    --help|-h)  usage; exit 0 ;;
    *) echo "Option inconnue : $arg" >&2; usage; exit 1 ;;
  esac
done

# ---------- Preflight : Docker ----------
if ! command -v docker >/dev/null 2>&1; then
  echo "ERREUR : Docker n'est pas installe ou pas dans le PATH." >&2
  echo "  Installez Docker Desktop : https://www.docker.com/products/docker-desktop/" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "ERREUR : le demon Docker ne repond pas." >&2
  echo "  Lancez Docker Desktop (icone baleine dans la barre de menus), attendez" >&2
  echo "  qu'il soit pret, puis relancez ce script." >&2
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "ERREUR : 'docker compose' (v2) introuvable. Mettez Docker Desktop a jour." >&2
  exit 1
fi

# ---------- 1. Fichier .env ----------
if [ ! -f .env ]; then
  echo "==> .env absent : copie depuis .env.example"
  cp .env.example .env
else
  echo "==> .env present : conserve tel quel."
fi

# Lecture du modele Ollama defini dans .env (fallback : llama3.1:8b).
MODEL="$(sed -n 's/^[[:space:]]*OLLAMA_MODEL[[:space:]]*=[[:space:]]*//p' .env | head -n1)"
MODEL="${MODEL:-$DEFAULT_MODEL}"

# ---------- 2. Build ----------
if [ "$FAST" -eq 1 ]; then
  echo "==> Mode rapide : pas de reconstruction d'image (--fast)."
else
  echo "==> Build des images (docker compose build)..."
  docker compose build
fi

# ---------- 3. Demarrage / recreation ----------
echo "==> Demarrage des conteneurs (up -d --force-recreate)..."
docker compose up -d --force-recreate

# ---------- 4. Attente sante du backend ----------
echo "==> Attente de la disponibilite du backend (http://localhost:8000)..."
backend_ready=0
if command -v curl >/dev/null 2>&1; then
  # Toute reponse HTTP (meme 404/500) prouve que le serveur ecoute.
  for _ in $(seq 1 60); do
    if curl -s --max-time 3 -o /dev/null "http://localhost:8000/api/docs/"; then
      backend_ready=1; break
    fi
    sleep 2
  done
else
  echo "    (curl absent : attente fixe de 20s)"
  sleep 20
  backend_ready=1
fi
if [ "$backend_ready" -eq 1 ]; then
  echo "    Backend pret."
else
  echo "    AVERTISSEMENT : le backend n'a pas repondu a temps. On continue."
  echo "    Verifiez : docker compose logs -f backend"
fi

# ---------- 5. Migrations ----------
# Le conteneur backend lance deja migrate a son demarrage ; on le rejoue ici
# par securite (idempotent) pour que ce soit explicite et visible.
echo "==> Migrations de la base (manage.py migrate)..."
docker compose exec -T backend python manage.py migrate --noinput

# ---------- 6. Seed ----------
if [ "$NO_SEED" -eq 1 ]; then
  echo "==> Seed ignore (--no-seed)."
else
  echo "==> Insertion des donnees de demonstration (manage.py seed)..."
  docker compose exec -T backend python manage.py seed
fi

# ---------- 7. Modele LLM ----------
echo "==> Verification du modele LLM '$MODEL' dans Ollama..."
if docker exec "$OLLAMA_CONTAINER" ollama list 2>/dev/null | awk '{print $1}' | grep -qx "$MODEL"; then
  echo "    Modele '$MODEL' deja present."
else
  echo "    Modele '$MODEL' absent."
  do_pull=0
  if [ "$ASSUME_YES" -eq 1 ]; then
    do_pull=1
  else
    printf "    Telecharger le modele '%s' maintenant ? (plusieurs Go) [o/N] " "$MODEL"
    read -r answer || answer=""
    case "$answer" in
      [oOyY]*) do_pull=1 ;;
      *)       do_pull=0 ;;
    esac
  fi
  if [ "$do_pull" -eq 1 ]; then
    echo "    Telechargement de '$MODEL' (cela peut prendre plusieurs minutes)..."
    docker exec "$OLLAMA_CONTAINER" ollama pull "$MODEL" \
      || echo "    AVERTISSEMENT : echec du telechargement du modele."
  else
    echo "    Telechargement ignore. La generation de QCM echouera tant que le"
    echo "    modele n'est pas present (ou basculez LLM_BACKEND sur un fournisseur cloud)."
  fi
fi

# ---------- 8. Recapitulatif ----------
echo ""
echo "==> Etat des conteneurs :"
docker compose ps
echo ""
echo "OK. Services accessibles :"
echo "  Frontend : http://localhost:3000   (ou FRONTEND_HOST_PORT du .env)"
echo "  API      : http://localhost:8000/api"
echo "  API docs : http://localhost:8000/api/docs"
echo ""
echo "  Compte de demo (si seed execute) : test / motdepasse123"
echo ""

# ---------- 9. Logs ----------
if [ "$FOLLOW_LOGS" -eq 1 ]; then
  echo "==> Suivi des logs (Ctrl+C pour quitter)..."
  docker compose logs -f
fi
