"""
Configuration Django — APOCAL'IPSSI 2026.

Lit les variables sensibles depuis `.env` via python-decouple.
La config se veut pédagogique : commentaires partout, sections clairement
séparées. Adaptez ce qui vous est utile.
"""

from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------------
# Sécurité
# ----------------------------------------------------------------------------
SECRET_KEY = config(
    "DJANGO_SECRET_KEY",
    default="dev-secret-key-change-me-in-production",
)
DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="*", cast=Csv())

# Drapeau de production. Activé via docker-compose.prod.yml (DJANGO_SECURE_PROD=
# True). Il pilote le durcissement HTTPS/cookies (plus bas) et le stockage des
# fichiers statiques à manifeste, INDÉPENDAMMENT de DEBUG : la CI tourne avec
# DEBUG=False sans être en prod, on ne veut donc pas lier ce durcissement à DEBUG.
SECURE_PROD = config("DJANGO_SECURE_PROD", default=False, cast=bool)

# Origines de confiance CSRF (POST de l'admin Django / Swagger derrière HTTPS).
# DOIT comporter le schéma, ex. https://apocalipssi26.elafrit.com
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

# Derrière le reverse proxy Caddy (terminaison TLS), Django reconnaît l'HTTPS
# d'origine via l'en-tête X-Forwarded-Proto qu'ajoute Caddy.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ----------------------------------------------------------------------------
# Applications
# ----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tiers
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "drf_spectacular",
    # Apps locales
    "accounts",
    "llm",
    "quizzes",
    "administration",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # avant CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# WhiteNoise (service des fichiers statiques) n'est activé qu'en PRODUCTION,
# inséré juste après SecurityMiddleware (ordre recommandé). En dev/CI on s'en
# passe (runserver sert les statiques), ce qui évite d'imposer la dépendance
# whitenoise au conteneur de développement.
if SECURE_PROD:
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
        "whitenoise.middleware.WhiteNoiseMiddleware",
    )

ROOT_URLCONF = "apocal.urls"
WSGI_APPLICATION = "apocal.wsgi.application"
ASGI_APPLICATION = "apocal.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ----------------------------------------------------------------------------
# Base de données — Postgres via Docker
# ----------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB", default="apocal"),
        "USER": config("POSTGRES_USER", default="apocal"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="apocal-dev-only"),
        "HOST": config("POSTGRES_HOST", default="postgres"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

# ----------------------------------------------------------------------------
# Validation mots de passe
# ----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ----------------------------------------------------------------------------
# I18n
# ----------------------------------------------------------------------------
LANGUAGE_CODE = "fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_TZ = True

# ----------------------------------------------------------------------------
# Statics
# ----------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# En production (SECURE_PROD), WhiteNoise sert des statiques compressés avec un
# manifeste à hash (cache long + invalidation auto). `collectstatic` est lancé
# au démarrage du conteneur backend prod. En dev/CI, on garde le stockage standard.
if SECURE_PROD:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ----------------------------------------------------------------------------
# Django REST Framework
# ----------------------------------------------------------------------------
REST_FRAMEWORK = {
    # TokenAuthentication en premier : les requêtes du frontend (header
    # Authorization: Token ...) sont authentifiées par token, sans contrôle
    # CSRF. SessionAuthentication reste en second pour la navigation Swagger UI.
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ----------------------------------------------------------------------------
# drf-spectacular (OpenAPI / Swagger)
# ----------------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    "TITLE": "APOCAL'IPSSI 2026 — EduTutor IA API",
    "DESCRIPTION": "Plateforme de révision personnalisée à base de LLM. "
    "Auth, génération de quiz, historique de progression.",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "CONTACT": {
        "name": "Mohamed Amine EL AFRIT",
        "url": "https://www.mohamedelafrit.com",
    },
    "LICENSE": {"name": "CC BY-NC-SA 4.0"},
}

# ----------------------------------------------------------------------------
# CORS (autorise le frontend Vite)
# ----------------------------------------------------------------------------
# Le port hôte du frontend est configurable via FRONTEND_HOST_PORT (.env) en
# cas de conflit sur le port 3000. On autorise dynamiquement ce port (en plus
# du 3000 par défaut) pour éviter tout blocage CORS. Surcharge totale possible
# en définissant CORS_ALLOWED_ORIGINS dans le .env (liste séparée par virgules).
_frontend_port = config("FRONTEND_HOST_PORT", default="3000")
_default_cors = {
    f"http://localhost:{_frontend_port}",
    f"http://127.0.0.1:{_frontend_port}",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
}
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default=",".join(sorted(_default_cors)),
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ----------------------------------------------------------------------------
# Intégration LLM (Ollama)
# ----------------------------------------------------------------------------
# Fournisseur de génération de quiz. 9 valeurs possibles :
#   "ollama"     -> modèle LOCAL gratuit (défaut, recommandé en développement)
#   "gemini"     -> API Google Gemini (CLOUD, free tier)
#   "groq"       -> API Groq, inférence très rapide (CLOUD, free tier)
#   "cerebras"   -> API Cerebras Cloud, très rapide (CLOUD, free tier)
#   "mistral"    -> API Mistral AI, fournisseur EUROPÉEN (CLOUD, free tier)
#   "openrouter" -> passerelle multi-modèles (CLOUD, modèles ":free" dispo)
#   "openai"     -> API OpenAI (CLOUD, PAYANT, future version premium)
#   "anthropic"  -> API Anthropic / Claude (CLOUD, PAYANT, future version premium)
#   "mock"       -> faux QCM instantanés (tests / dev sans LLM)
LLM_BACKEND = config("LLM_BACKEND", default="ollama")

# --- Ollama (local, gratuit) ---
OLLAMA_HOST = config("OLLAMA_HOST", default="http://ollama:11434")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="llama3.1:8b")
# Délai max (secondes) d'attente d'une génération Ollama. Sur CPU, un modèle 8B
# met facilement 2 à 5 minutes pour 10 QCM : 120 s était trop court (timeout ->
# 502). Défaut généreux, ajustable via .env (OLLAMA_TIMEOUT).
OLLAMA_TIMEOUT = config("OLLAMA_TIMEOUT", default=600, cast=int)

# --- OpenAI (API payante) ---
# Laissez OPENAI_API_KEY vide en dev : le backend "openai" refusera de démarrer
# sans clé, ce qui est volontaire (évite les frais accidentels).
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
OPENAI_MODEL = config("OPENAI_MODEL", default="gpt-4o-mini")

# --- Anthropic / Claude (API payante) ---
ANTHROPIC_API_KEY = config("ANTHROPIC_API_KEY", default="")
ANTHROPIC_MODEL = config("ANTHROPIC_MODEL", default="claude-3-5-haiku-20241022")

# --- Google Gemini (API cloud, FREE TIER disponible) ---
# Clé gratuite : https://aistudio.google.com/apikey
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-1.5-flash")

# --- Groq (API cloud format OpenAI, très rapide, free tier) ---
# Clé gratuite : https://console.groq.com/keys
GROQ_API_KEY = config("GROQ_API_KEY", default="")
GROQ_MODEL = config("GROQ_MODEL", default="llama-3.3-70b-versatile")

# --- Cerebras Cloud (API cloud format OpenAI, très rapide, free tier) ---
# Clé gratuite : https://cloud.cerebras.ai/
CEREBRAS_API_KEY = config("CEREBRAS_API_KEY", default="")
CEREBRAS_MODEL = config("CEREBRAS_MODEL", default="llama-3.3-70b")

# --- Mistral AI (API cloud format OpenAI, fournisseur européen, free tier) ---
# Clé : https://console.mistral.ai/
MISTRAL_API_KEY = config("MISTRAL_API_KEY", default="")
MISTRAL_MODEL = config("MISTRAL_MODEL", default="mistral-small-latest")

# --- OpenRouter (passerelle multi-modèles, format OpenAI) ---
# Clé : https://openrouter.ai/keys  | modèle au format "editeur/modele" (suffixe ":free" possible)
OPENROUTER_API_KEY = config("OPENROUTER_API_KEY", default="")
OPENROUTER_MODEL = config("OPENROUTER_MODEL", default="meta-llama/llama-3.1-8b-instruct")

# Délai max (secondes) pour les API cloud, bien plus rapides qu'un modèle local sur CPU.
LLM_API_TIMEOUT = config("LLM_API_TIMEOUT", default=60, cast=int)

# ----------------------------------------------------------------------------
# Email (Brevo en production, console en développement)
# ----------------------------------------------------------------------------
# [Note pédagogique] Django envoie les emails via un « backend » configurable.
# Stratégie ici (bascule automatique) :
#   - Si une clé SMTP Brevo est fournie (.env) -> on envoie de VRAIS emails via
#     le relais SMTP de Brevo (smtp-relay.brevo.com).
#   - Sinon (dev) -> backend "console" : l'email s'affiche dans les LOGS du
#     backend. On peut ainsi tester tout le flux (validation de compte, reset
#     password du Lot 3) SANS compte Brevo ni adresse email réelle.
# Brevo distingue la « clé API v3 » et la « clé SMTP » : pour l'envoi SMTP,
# utilisez la clé SMTP (https://app.brevo.com/settings/keys/smtp).
BREVO_SMTP_KEY = config("BREVO_SMTP_KEY", default="")
if BREVO_SMTP_KEY:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = config("BREVO_SMTP_HOST", default="smtp-relay.brevo.com")
    EMAIL_PORT = config("BREVO_SMTP_PORT", default=587, cast=int)
    EMAIL_HOST_USER = config("BREVO_SMTP_LOGIN", default="")
    EMAIL_HOST_PASSWORD = BREVO_SMTP_KEY
    EMAIL_USE_TLS = True
else:
    # Fallback dev : aucun email réel envoyé, tout s'affiche dans les logs.
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Adresse expéditeur par défaut. En prod, ce doit être un expéditeur VALIDÉ
# dans Brevo (sinon les emails sont rejetés).
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="EduTutor IA <no-reply@edututor.local>")

# URL publique du frontend, utilisée pour construire les liens cliquables dans
# les emails (validation de compte, réinitialisation de mot de passe — Lot 3).
FRONTEND_URL = config("FRONTEND_URL", default="http://localhost:3000")

# ----------------------------------------------------------------------------
# Durcissement production (actif uniquement si DJANGO_SECURE_PROD=True)
# ----------------------------------------------------------------------------
# Réglages de sécurité activés derrière HTTPS (Caddy). Volontairement NON liés à
# DEBUG : la CI tourne avec DEBUG=False sans être « en prod ».
if SECURE_PROD:
    SECURE_SSL_REDIRECT = True  # redirige tout HTTP vers HTTPS
    # Le healthcheck interne du conteneur frappe http://127.0.0.1:8000/health/
    # (sans passer par Caddy) : on l'exempte du redirect HTTPS, sinon il reçoit
    # une 301 au lieu d'un 200 et le conteneur est marqué "unhealthy".
    SECURE_REDIRECT_EXEMPT = [r"^health/$"]
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SECURE_HSTS_SECONDS = 31536000  # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
