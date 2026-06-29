# ============================================================================
# redeploy.ps1 — Redéploiement du kit EduTutor IA (Windows / PowerShell)
# ----------------------------------------------------------------------------
# Reconstruit les images, recrée les conteneurs (prise en compte du code ET du
# .env), puis relance Docker. À lancer après une modification de code/config
# pour tester. Lançable depuis n'importe où : le script se replace tout seul
# à la racine du projet.
#
# Usage (dans un terminal PowerShell) :
#   powershell -ExecutionPolicy Bypass -File scripts\redeploy.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\redeploy.ps1 -Fast
# ============================================================================
param(
    [switch]$Fast  # -Fast : recrée sans reconstruire les images (plus rapide)
)

$ErrorActionPreference = "Stop"

# Se placer à la racine du projet (dossier parent de ce script).
Set-Location (Join-Path $PSScriptRoot "..")

$buildFlag = "--build"
if ($Fast) {
    $buildFlag = ""
    Write-Host "==> Mode rapide : pas de reconstruction d'image." -ForegroundColor Yellow
}

Write-Host "==> Redeploiement EduTutor IA (projet docker : apocalipssi-2026)" -ForegroundColor Cyan
Write-Host "==> docker compose up -d $buildFlag --force-recreate"
if ($Fast) {
    docker compose up -d --force-recreate
} else {
    docker compose up -d --build --force-recreate
}

Write-Host ""
Write-Host "==> Etat des conteneurs :" -ForegroundColor Cyan
docker compose ps

Write-Host ""
Write-Host "OK. Services accessibles :" -ForegroundColor Green
Write-Host "  Frontend : http://localhost:3000   (ou le port FRONTEND_HOST_PORT de votre .env)"
Write-Host "  API      : http://localhost:8000/api"
Write-Host "  API docs : http://localhost:8000/api/docs"
Write-Host ""
Write-Host "Premier lancement avec Ollama ? Telechargez le modele (une seule fois) :"
Write-Host "  docker exec apocalipssi-2026-ollama ollama pull llama3.1:8b"
