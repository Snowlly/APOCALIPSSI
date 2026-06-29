"""
Client générique pour toute API au format « OpenAI Chat Completions ».

[Note pédagogique] BEAUCOUP de fournisseurs ont copié le format d'API d'OpenAI :
OpenAI, Groq, OpenRouter, Cerebras, Mistral… exposent tous le même endpoint
`POST /chat/completions` avec le même corps `{model, messages, temperature}`.
Plutôt que d'écrire 5 clients quasi identiques, on écrit UNE base ici, et chaque
fournisseur devient une petite sous-classe qui fixe juste son URL et ses clés.
C'est le principe DRY poussé jusqu'au bout (et une vraie illustration de
l'héritage en POO).

Les fournisseurs au format DIFFÉRENT (Ollama, Anthropic, Gemini) gardent, eux,
leur propre client dédié.
"""

import requests
from django.conf import settings

from .base import LLMClient, LLMError
from .quiz_prompt import SYSTEM_PROMPT, build_user_prompt, parse_and_validate_quiz


class OpenAICompatibleClient(LLMClient):
    """Base réutilisable pour les API compatibles OpenAI Chat Completions."""

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        provider_label: str,
        hint: str = "",
        json_mode: bool = True,
        extra_headers: dict | None = None,
        timeout: int | None = None,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.provider_label = provider_label
        self.json_mode = json_mode  # response_format json_object supporté ?
        self.extra_headers = extra_headers or {}
        self.timeout = timeout or settings.LLM_API_TIMEOUT
        if not self.api_key:
            raise LLMError(
                f"{provider_label} : clé API manquante. "
                + (hint + " " if hint else "")
                + "Ou utilisez LLM_BACKEND=ollama (gratuit, local) pour le développement."
            )

    def generate_quiz(self, source_text: str, title: str) -> list[dict]:
        raw = self._call(source_text, title)
        return parse_and_validate_quiz(raw)

    # ----- internals -----

    def _call(self, source_text: str, title: str) -> str:
        payload = {
            "model": self.model,
            # Séparation system / user (défense de base contre l'injection, cf. J3).
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(source_text, title)},
            ],
            "temperature": 0.4,
        }
        # La plupart des fournisseurs supportent le mode JSON strict ; certains
        # modèles (via OpenRouter) non -> on le rend désactivable. Dans tous les
        # cas, parse_and_validate_quiz sait extraire le JSON même entouré de texte.
        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        headers.update(self.extra_headers)

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise LLMError(f"Appel {self.provider_label} échoué : {exc}") from exc

        data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Réponse {self.provider_label} inattendue : {exc}") from exc
