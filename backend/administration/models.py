"""
Configuration globale du site (Lot 8).

[Note pédagogique] Comme LLMConfig, c'est un « singleton » : une seule ligne en
base (pk=1) qui contient les réglages applicatifs modifiables depuis l'interface
d'administration, sans redéployer.
"""

from django.db import models


class SiteConfig(models.Model):
    """Réglages globaux de l'application (singleton, pk=1)."""

    SINGLETON_ID = 1

    app_name = models.CharField(
        max_length=80,
        default="EduTutor IA",
        help_text="Nom affiché dans l'en-tête et les emails.",
    )
    allow_signups = models.BooleanField(
        default=True,
        help_text="Si désactivé, plus aucune inscription n'est possible (le login reste ouvert).",
    )
    require_email_verification = models.BooleanField(
        default=False,
        help_text="Si activé, un email confirmé est requis pour générer des quiz.",
    )
    banner_enabled = models.BooleanField(
        default=False,
        help_text="Afficher une bannière d'information à tous les utilisateurs.",
    )
    banner_message = models.TextField(
        blank=True,
        default="",
        help_text="Texte de la bannière globale (maintenance, annonce…).",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration du site"
        verbose_name_plural = "Configuration du site"

    def __str__(self) -> str:
        return f"SiteConfig({self.app_name})"

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_ID  # force le singleton
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "SiteConfig":
        """Récupère (ou crée) l'unique configuration du site."""
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_ID)
        return obj
