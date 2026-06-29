"""
Commande `python manage.py send_test_email <destinataire>`
----------------------------------------------------------
Vérifie la configuration email du kit.

- En mode console (aucune clé Brevo dans le .env) : l'email s'affiche dans les
  logs du backend (aucun envoi réel). Idéal pour valider le câblage en dev.
- Avec une clé SMTP Brevo : un vrai email est envoyé au destinataire.

Exemple :
    docker exec apocalipssi-2026-backend python manage.py send_test_email moi@example.com
"""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.emails import send_email


class Command(BaseCommand):
    help = "Envoie un email de test pour vérifier la configuration (Brevo ou console)."

    def add_arguments(self, parser):
        parser.add_argument("destinataire", help="Adresse email du destinataire")

    def handle(self, *args, **options):
        to = options["destinataire"]
        # Les backends SMTP et console portent tous deux le nom de classe
        # "EmailBackend" : on se base donc sur le CHEMIN complet pour les distinguer.
        backend_path = settings.EMAIL_BACKEND
        is_console = "console" in backend_path.lower()

        self.stdout.write(f"Backend email : {backend_path}")
        self.stdout.write(f"Expéditeur    : {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"Destinataire  : {to}")
        self.stdout.write("-" * 60)

        try:
            send_email(
                to_email=to,
                subject="Test EduTutor IA — configuration email",
                body=(
                    "Bonjour,\n\n"
                    "Ceci est un email de test envoyé depuis le kit EduTutor IA.\n"
                    "Si vous lisez ce message, la configuration email fonctionne.\n\n"
                    "— L'équipe EduTutor IA"
                ),
            )
        except Exception as exc:  # noqa: BLE001 — on veut afficher toute erreur SMTP
            raise CommandError(f"Échec de l'envoi : {exc}") from exc

        self.stdout.write("-" * 60)
        if is_console:
            self.stdout.write(
                self.style.WARNING(
                    "Mode CONSOLE : aucun email réel envoyé — l'email ci-dessus est "
                    "affiché dans les logs. Renseignez BREVO_SMTP_KEY pour un envoi réel."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS(f"Email envoyé à {to} via Brevo. ✓"))
