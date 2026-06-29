"""ASGI config — entrée pour les serveurs ASGI (uvicorn, daphne, etc.)."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apocal.settings")
application = get_asgi_application()
