"""
Helpers d'envoi d'email pour l'app accounts.

[Note pédagogique] On centralise ici l'envoi d'email. Le backend réel (SMTP
Brevo ou console) est choisi automatiquement dans settings.py selon la présence
d'une clé Brevo. Le code applicatif n'a donc PAS à savoir COMMENT l'email part :
il appelle simplement send_email(). C'est une bonne séparation des
responsabilités (le « quoi » envoyer vs le « comment » l'envoyer).

Au Lot 3, ce module accueillera les emails métier : validation de compte et
réinitialisation de mot de passe (avec leurs liens et leurs tokens).
"""

from smtplib import SMTPAuthenticationError, SMTPException

from django.conf import settings
from django.core.mail import send_mail


class EmailError(Exception):
    """Erreur d'envoi d'email, avec un message déjà explicite pour l'utilisateur."""


def send_email(to_email: str, subject: str, body: str) -> None:
    """Envoie un email texte simple.

    En mode console (dev, pas de clé Brevo), l'email est écrit dans les logs.
    Avec une clé Brevo, un vrai email part via SMTP.

    Raises:
        EmailError: avec un message clair si l'envoi échoue (clé expirée, etc.).
    """
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except SMTPAuthenticationError as exc:
        # 535 = identifiants refusés. En formation, la clé Brevo est TEMPORAIRE :
        # ce cas se produira typiquement quand elle aura expiré.
        raise EmailError(
            "Authentification Brevo refusée (clé SMTP expirée ou invalide). "
            "En formation, la clé est temporaire : demandez la clé à jour à votre "
            "formateur, ou laissez BREVO_SMTP_KEY vide dans le .env pour repasser "
            "en mode console (emails affichés dans les logs)."
        ) from exc
    except SMTPException as exc:
        # Autres erreurs SMTP (expéditeur non validé, quota dépassé, réseau…).
        raise EmailError(f"Échec de l'envoi de l'email via SMTP : {exc}") from exc


# ----------------------------------------------------------------------------
# Emails métier (validation de compte, réinitialisation de mot de passe)
# ----------------------------------------------------------------------------


def _frontend(path: str) -> str:
    """Construit une URL absolue vers le frontend (pour les liens des emails)."""
    from django.conf import settings as s

    return f"{s.FRONTEND_URL.rstrip('/')}{path}"


def send_verification_email(user) -> None:
    """Email de confirmation d'adresse, envoyé à l'inscription."""
    from .tokens import make_email_verify_token

    link = _frontend(f"/verify-email?token={make_email_verify_token(user)}")
    body = (
        "Bonjour,\n\n"
        "Bienvenue sur EduTutor IA ! Pour confirmer votre adresse email, "
        "cliquez sur le lien ci-dessous :\n\n"
        f"{link}\n\n"
        "Ce lien est valable 3 jours. Vous pouvez utiliser votre compte dès "
        "maintenant ; cette confirmation nous permet simplement de vérifier "
        "votre adresse.\n\n"
        "— L'équipe EduTutor IA"
    )
    send_email(user.email, "Confirmez votre adresse email — EduTutor IA", body)


def send_password_reset_email(user) -> None:
    """Email de réinitialisation de mot de passe (lien avec token)."""
    from .tokens import make_password_reset_tokens

    uidb64, token = make_password_reset_tokens(user)
    link = _frontend(f"/reset-password?uid={uidb64}&token={token}")
    body = (
        "Bonjour,\n\n"
        "Vous avez demandé la réinitialisation de votre mot de passe EduTutor IA. "
        "Cliquez sur le lien ci-dessous pour en choisir un nouveau :\n\n"
        f"{link}\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez simplement cet "
        "email : votre mot de passe restera inchangé.\n\n"
        "— L'équipe EduTutor IA"
    )
    send_email(user.email, "Réinitialisation de votre mot de passe — EduTutor IA", body)
