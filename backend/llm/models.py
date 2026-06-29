"""
Configuration LLM persistée en base (Lot 8).

[Note pédagogique] Jusqu'ici, le fournisseur LLM était piloté par le `.env`
(relu au redéploiement). Pour qu'un administrateur puisse changer de fournisseur
DEPUIS L'INTERFACE et que ça prenne effet À CHAUD, on stocke la configuration en
base, dans un enregistrement UNIQUE (pattern « singleton »).

Priorité retenue : **la base l'emporte si elle est renseignée, sinon on retombe
sur le `.env`** (voir llm/services/factory.py). L'application fonctionne donc
out-of-the-box avec le `.env`, et l'admin peut surcharger ensuite.

⚠️ Sécurité : les clés API sont stockées EN CLAIR dans `api_keys`. Acceptable
pour un kit pédagogique, mais en PRODUCTION il faudrait les chiffrer (ex. Fernet)
ou utiliser un gestionnaire de secrets. L'API d'admin ne les renvoie jamais en
clair (elle indique seulement si une clé est définie).
"""

from django.db import models


class LLMConfig(models.Model):
    """Configuration LLM unique (singleton, pk=1)."""

    SINGLETON_ID = 1

    backend = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Fournisseur actif. Vide = utiliser LLM_BACKEND du .env.",
    )
    model = models.CharField(
        max_length=120,
        blank=True,
        default="",
        help_text="Modèle pour le fournisseur actif. Vide = défaut du .env.",
    )
    api_keys = models.JSONField(
        default=dict,
        blank=True,
        help_text="Clés API par fournisseur : {provider: clé}. Stockées en base.",
    )
    ollama_host = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="URL du serveur Ollama. Vide = OLLAMA_HOST du .env.",
    )
    timeout = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Timeout (s) override. Vide = défaut selon le fournisseur.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuration LLM"
        verbose_name_plural = "Configuration LLM"

    def __str__(self) -> str:
        return f"LLMConfig(backend={self.backend or '(.env)'})"

    def save(self, *args, **kwargs):
        # Force le singleton : toujours la même ligne.
        self.pk = self.SINGLETON_ID
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> "LLMConfig":
        """Récupère (ou crée) l'unique configuration LLM."""
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_ID)
        return obj
