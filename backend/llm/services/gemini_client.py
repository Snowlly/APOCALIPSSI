"""
Client Google Gemini — génération de quiz via l'API Generative Language.

[Note pédagogique] Gemini est un fournisseur CLOUD comme OpenAI et Claude
(données envoyées hors UE → enjeu RGPD, cf. perturbation J3-bis), MAIS il
propose un FREE TIER généreux via Google AI Studio : idéal pour TESTER une API
cloud sans carte bancaire (contrairement à OpenAI qui exige du crédit).

Comme les autres clients, on utilise `requests` (pas de SDK), on réutilise le
prompt et la validation partagés (quiz_prompt.py), et on isole les consignes
système du contenu utilisateur via `system_instruction` (bonne pratique
anti prompt-injection, cf. J3).
"""

import requests
from django.conf import settings

from .base import LLMClient, LLMError
from .quiz_prompt import SYSTEM_PROMPT, build_user_prompt, parse_and_validate_quiz

# L'API Gemini place le nom du modèle dans l'URL : .../models/<MODEL>:generateContent
GEMINI_URL_TEMPLATE = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


class GeminiLLMClient(LLMClient):
    """Client HTTP pour l'API Generative Language de Google (Gemini)."""

    def __init__(
        self, *, api_key: str | None = None, model: str | None = None, timeout: int | None = None
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.timeout = timeout or settings.LLM_API_TIMEOUT
        if not self.api_key:
            raise LLMError(
                "GEMINI_API_KEY manquante. Créez une clé gratuite sur "
                "https://aistudio.google.com/apikey, ou utilisez LLM_BACKEND=ollama "
                "(gratuit, local) pour le développement."
            )

    def generate_quiz(self, source_text: str, title: str) -> list[dict]:
        raw = self._call_gemini(source_text, title)
        return parse_and_validate_quiz(raw)

    # ----- internals -----

    def _call_gemini(self, source_text: str, title: str) -> str:
        url = GEMINI_URL_TEMPLATE.format(model=self.model)
        try:
            response = requests.post(
                url,
                # Clé dans l'en-tête (et non dans l'URL) : évite de la logger.
                headers={
                    "x-goog-api-key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    # Consignes système isolées du contenu utilisateur.
                    "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                    "contents": [{"parts": [{"text": build_user_prompt(source_text, title)}]}],
                    "generationConfig": {
                        "temperature": 0.4,
                        # Force une sortie JSON stricte (équivalent du JSON mode).
                        "responseMimeType": "application/json",
                    },
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"Appel Gemini échoué : {exc}") from exc

        data = response.json()
        # Réponse Gemini : candidates[0].content.parts[0].text contient le JSON.
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Réponse Gemini inattendue : {exc}") from exc
