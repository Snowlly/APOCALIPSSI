"""WSGI config — entrée pour les serveurs WSGI (gunicorn, etc.)."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apocal.settings")
application = get_wsgi_application()
