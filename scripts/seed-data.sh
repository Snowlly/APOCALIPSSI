#!/usr/bin/env bash
# ============================================================================
# seed-data.sh — Insère les données de test (1 user + 2 quizz)
# ============================================================================

set -euo pipefail

echo "🌱 Insertion des données de test..."

docker compose exec backend python manage.py seed

echo ""
echo "✅ Données de test insérées."
echo ""
echo "   User test : test@apocal.local / motdepasse123"
echo "   2 quizz exemples disponibles dans l'historique"
