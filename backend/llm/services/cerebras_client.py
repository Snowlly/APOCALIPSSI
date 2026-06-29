"""
Client Cerebras Cloud — API au format OpenAI, inférence ultra-rapide (wafer-scale).

[Note pédagogique] Cerebras sert des modèles open-source (Llama…) à très haut
débit, avec un free tier. API compatible OpenAI -> client minimal hérité.
Données envoyées à un service cloud (enjeu RGPD, cf. J3-bis).
"""

from django.conf import settings

from .openai_compatible import OpenAICompatibleClient


class CerebrasLLMClient(OpenAICompatibleClient):
    def __init__(
        self, *, api_key: str | None = None, model: str | None = None, timeout: int | None = None
    ) -> None:
        super().__init__(
            api_key=api_key if api_key is not None else settings.CEREBRAS_API_KEY,
            model=model or settings.CEREBRAS_MODEL,
            base_url="https://api.cerebras.ai/v1",
            provider_label="Cerebras",
            hint="Clé GRATUITE sur https://cloud.cerebras.ai/.",
            json_mode=True,
            timeout=timeout,
        )
