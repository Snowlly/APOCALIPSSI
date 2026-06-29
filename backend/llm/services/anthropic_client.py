"""
Client Anthropic (Claude) — génération de quiz via l'API Messages (PAYANT).

[Note pédagogique] Deuxième alternative PAYANTE (comme OpenAI). Même contrat
LLMClient, mais une API au format légèrement différent : en-tête `x-api-key`,
en-tête de version `anthropic-version`, un champ `system` séparé, et un
`max_tokens` OBLIGATOIRE. Comparer ce client avec openai_client.py est un bon
exercice pour comprendre que « brancher un autre fournisseur » = adapter le
transport HTTP, pas réécrire toute la logique (prompt + validation restent
mutualisés dans quiz_prompt.py).

En dev : préférez Ollama (gratuit, local). Ce client vise une future version premium.
"""

import requests
from django.conf import settings

from .base import LLMClient, LLMError
from .quiz_prompt import SYSTEM_PROMPT, build_user_prompt, parse_and_validate_quiz

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


class AnthropicLLMClient(LLMClient):
    """Client HTTP pour l'API Messages d'Anthropic (Claude)."""

    def __init__(
        self, *, api_key: str | None = None, model: str | None = None, timeout: int | None = None
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.timeout = timeout or settings.LLM_API_TIMEOUT
        if not self.api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY manquante. Renseignez-la dans le .env, ou utilisez "
                "LLM_BACKEND=ollama (gratuit, local) pour le développement."
            )

    def generate_quiz(self, source_text: str, title: str) -> list[dict]:
        raw = self._call_anthropic(source_text, title)
        return parse_and_validate_quiz(raw)

    # ----- internals -----

    def _call_anthropic(self, source_text: str, title: str) -> str:
        try:
            response = requests.post(
                ANTHROPIC_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": ANTHROPIC_VERSION,
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,  # obligatoire chez Anthropic ; large pour 10 QCM
                    "system": SYSTEM_PROMPT,  # consignes isolées du contenu utilisateur
                    "messages": [
                        {"role": "user", "content": build_user_prompt(source_text, title)},
                    ],
                    "temperature": 0.4,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"Appel Anthropic échoué : {exc}") from exc

        data = response.json()
        # La réponse Claude est une liste de blocs de contenu ; on prend le texte.
        # parse_and_validate_quiz récupère le JSON même si du texte l'entoure.
        try:
            return data["content"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Réponse Anthropic inattendue : {exc}") from exc
