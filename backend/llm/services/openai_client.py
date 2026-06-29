"""
Client OpenAI — génération de quiz via l'API Chat Completions (PAYANT).

[Note pédagogique] OpenAI est le fournisseur dont les autres ont copié le format
d'API. Ce client est donc une simple sous-classe de OpenAICompatibleClient : il
fixe juste l'URL et lit ses clés. Comparez avec groq_client.py / mistral_client.py
— ils ne diffèrent que par l'URL et les variables d'environnement.

⚠️ PAYANT : OpenAI exige du crédit prépayé (sinon erreur insufficient_quota).
En développement, préférez Ollama (gratuit, local) ou un free tier (Gemini, Groq…).
"""

from django.conf import settings

from .openai_compatible import OpenAICompatibleClient


class OpenAILLMClient(OpenAICompatibleClient):
    """Client pour l'API Chat Completions d'OpenAI."""

    def __init__(
        self, *, api_key: str | None = None, model: str | None = None, timeout: int | None = None
    ) -> None:
        super().__init__(
            api_key=api_key if api_key is not None else settings.OPENAI_API_KEY,
            model=model or settings.OPENAI_MODEL,
            base_url="https://api.openai.com/v1",
            provider_label="OpenAI",
            hint="Clé + crédit sur https://platform.openai.com/api-keys.",
            json_mode=True,
            timeout=timeout,
        )
