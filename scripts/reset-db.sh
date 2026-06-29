#!/usr/bin/env bash
# ============================================================================
# reset-db.sh — ⚠️ Supprime la DB Postgres et la recrée vide
# ============================================================================

set -euo pipefail

echo "⚠️  ATTENTION : cette commande va SUPPRIMER toutes les données."
echo ""
read -p "Êtes-vous sûr(e) ? [y/N] " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && { echo "Annulé."; exit 0; }

echo "🗑️  Suppression du volume postgres-data..."
docker compose down -v

echo "🚀 Redémarrage des services..."
docker compose up -d postgres

echo "⏳ Attente de Postgres ready..."
sleep 5

docker compose up -d

echo "🌱 Insertion des données de test..."
sleep 3
docker compose exec backend python manage.py seed

echo ""
echo "✅ DB réinitialisée et seedée."
