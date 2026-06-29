# ============================================================================
# start-windows.ps1 — Lancement complet du kit EduTutor IA (Windows / PowerShell)
# ----------------------------------------------------------------------------
# Build + deploiement + relance Docker, en UNE commande. Le script enchaine :
#   1. .env       : copie .env.example -> .env s'il manque
#   2. build      : docker compose build (saute si -Fast)
#   3. up         : docker compose up -d --force-recreate
#   4. sante      : attend que le backend reponde (http://localhost:8000)
#   5. migrate    : applique les migrations (idempotent)
#   6. seed       : insere les donnees de demo (saute si -NoSeed)
#   7. modele LLM : verifie sa presence ; s'il manque, propose le telechargement
#   8. URLs       : recapitulatif des adresses
#
# Prerequis : Docker Desktop doit etre LANCE. Lançable depuis n'importe ou :
# le script se replace tout seul a la racine du projet.
#
# Usage (terminal PowerShell) :
#   powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1
#   powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1 -Fast
#   powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1 -Yes
#   powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1 -NoSeed
#   powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1 -Logs
#   (options cumulables ; -Help pour l'aide)
# ============================================================================
param(
    [switch]$Fast,    # -Fast   : recree sans reconstruire les images
    [switch]$Yes,     # -Yes    : non-interactif (telecharge le modele s'il manque)
    [switch]$NoSeed,  # -NoSeed : ne pas inserer les donnees de demo
    [switch]$Logs,    # -Logs   : suivre les logs apres le demarrage
    [switch]$Help     # -Help   : afficher l'aide
)

$ErrorActionPreference = "Stop"

if ($Help) {
    Write-Host @"
Usage : powershell -ExecutionPolicy Bypass -File scripts\start-windows.ps1 [options]

  -Fast      Relance sans reconstruire les images (gain de temps).
  -Yes       Mode non-interactif : telecharge le modele LLM s'il manque,
             sans poser de question.
  -NoSeed    Ne pas inserer les donnees de demonstration.
  -Logs      Suivre les logs des conteneurs apres le demarrage.
  -Help      Afficher cette aide.
"@
    exit 0
}

# Se placer a la racine du projet (dossier parent de ce script).
Set-Location (Join-Path $PSScriptRoot "..")

$OllamaContainer = "apocalipssi-2026-ollama"
$DefaultModel    = "llama3.1:8b"

# Echec d'une commande native (code de sortie != 0) -> on arrete proprement.
function Assert-LastExit($message) {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERREUR : $message" -ForegroundColor Red
        exit 1
    }
}

# ---------- Preflight : Docker ----------
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERREUR : Docker n'est pas installe ou pas dans le PATH." -ForegroundColor Red
    Write-Host "  Installez Docker Desktop : https://www.docker.com/products/docker-desktop/"
    exit 1
}
# Sonde du demon Docker, sans laisser un stderr bruyant interrompre le script.
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
docker info > $null 2> $null
$dockerUp = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = $prevEAP
if (-not $dockerUp) {
    Write-Host "ERREUR : le demon Docker ne repond pas." -ForegroundColor Red
    Write-Host "  Lancez Docker Desktop, attendez qu'il soit pret, puis relancez ce script."
    exit 1
}

# ---------- 1. Fichier .env ----------
if (-not (Test-Path ".env")) {
    Write-Host "==> .env absent : copie depuis .env.example" -ForegroundColor Cyan
    Copy-Item ".env.example" ".env"
} else {
    Write-Host "==> .env present : conserve tel quel." -ForegroundColor Cyan
}

# Lecture du modele Ollama defini dans .env (fallback : llama3.1:8b).
$Model = $DefaultModel
$envLine = Select-String -Path ".env" -Pattern '^\s*OLLAMA_MODEL\s*=' -ErrorAction SilentlyContinue |
           Select-Object -First 1
if ($envLine) {
    $val = ($envLine.Line -replace '^\s*OLLAMA_MODEL\s*=\s*', '').Trim()
    if ($val) { $Model = $val }
}

# ---------- 2. Build ----------
if ($Fast) {
    Write-Host "==> Mode rapide : pas de reconstruction d'image (-Fast)." -ForegroundColor Yellow
} else {
    Write-Host "==> Build des images (docker compose build)..." -ForegroundColor Cyan
    docker compose build
    Assert-LastExit "le build des images a echoue."
}

# ---------- 3. Demarrage / recreation ----------
Write-Host "==> Demarrage des conteneurs (up -d --force-recreate)..." -ForegroundColor Cyan
docker compose up -d --force-recreate
Assert-LastExit "le demarrage des conteneurs a echoue."

# ---------- 4. Attente sante du backend ----------
Write-Host "==> Attente de la disponibilite du backend (http://localhost:8000)..." -ForegroundColor Cyan
function Test-Backend {
    try {
        $null = Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Uri "http://localhost:8000/api/docs/"
        return $true
    } catch {
        # Une reponse HTTP (meme 4xx/5xx) prouve que le serveur ecoute.
        if ($_.Exception.Response) { return $true }
        return $false
    }
}
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    if (Test-Backend) { $ready = $true; break }
    Start-Sleep -Seconds 2
}
if ($ready) {
    Write-Host "    Backend pret."
} else {
    Write-Host "    AVERTISSEMENT : le backend n'a pas repondu a temps. On continue." -ForegroundColor Yellow
    Write-Host "    Verifiez : docker compose logs -f backend"
}

# ---------- 5. Migrations ----------
# Le conteneur backend lance deja migrate a son demarrage ; on le rejoue ici
# par securite (idempotent) pour que ce soit explicite et visible.
Write-Host "==> Migrations de la base (manage.py migrate)..." -ForegroundColor Cyan
docker compose exec -T backend python manage.py migrate --noinput
Assert-LastExit "les migrations ont echoue."

# ---------- 6. Seed ----------
if ($NoSeed) {
    Write-Host "==> Seed ignore (-NoSeed)." -ForegroundColor Yellow
} else {
    Write-Host "==> Insertion des donnees de demonstration (manage.py seed)..." -ForegroundColor Cyan
    docker compose exec -T backend python manage.py seed
    Assert-LastExit "le seed a echoue."
}

# ---------- 7. Modele LLM ----------
Write-Host "==> Verification du modele LLM '$Model' dans Ollama..." -ForegroundColor Cyan
$prevEAP = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$modelList = docker exec $OllamaContainer ollama list 2> $null
$ErrorActionPreference = $prevEAP

$hasModel = $false
if ($modelList) {
    foreach ($line in $modelList) {
        $name = ($line -split '\s+')[0]
        if ($name -eq $Model) { $hasModel = $true; break }
    }
}

if ($hasModel) {
    Write-Host "    Modele '$Model' deja present."
} else {
    Write-Host "    Modele '$Model' absent." -ForegroundColor Yellow
    $doPull = $false
    if ($Yes) {
        $doPull = $true
    } else {
        $answer = Read-Host "    Telecharger le modele '$Model' maintenant ? (plusieurs Go) [o/N]"
        if ($answer -match '^[oOyY]') { $doPull = $true }
    }
    if ($doPull) {
        Write-Host "    Telechargement de '$Model' (cela peut prendre plusieurs minutes)..."
        docker exec $OllamaContainer ollama pull $Model
        if ($LASTEXITCODE -ne 0) {
            Write-Host "    AVERTISSEMENT : echec du telechargement du modele." -ForegroundColor Yellow
        }
    } else {
        Write-Host "    Telechargement ignore. La generation de QCM echouera tant que le"
        Write-Host "    modele n'est pas present (ou basculez LLM_BACKEND sur un fournisseur cloud)."
    }
}

# ---------- 8. Recapitulatif ----------
Write-Host ""
Write-Host "==> Etat des conteneurs :" -ForegroundColor Cyan
docker compose ps
Write-Host ""
Write-Host "OK. Services accessibles :" -ForegroundColor Green
Write-Host "  Frontend : http://localhost:3000   (ou FRONTEND_HOST_PORT du .env)"
Write-Host "  API      : http://localhost:8000/api"
Write-Host "  API docs : http://localhost:8000/api/docs"
Write-Host ""
Write-Host "  Compte de demo (si seed execute) : test / motdepasse123"
Write-Host ""

# ---------- 9. Logs ----------
if ($Logs) {
    Write-Host "==> Suivi des logs (Ctrl+C pour quitter)..." -ForegroundColor Cyan
    docker compose logs -f
}
