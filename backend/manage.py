#!/usr/bin/env python
"""Point d'entrée des commandes Django (manage.py)."""

import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "apocal.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django introuvable. Avez-vous activé votre environnement virtuel "
            "et installé requirements.txt ?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
