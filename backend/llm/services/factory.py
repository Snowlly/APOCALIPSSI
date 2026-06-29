"""
Factory de client LLM.

[Note pédagogique] Le « factory pattern » centralise le choix du fournisseur.
Le reste de l'application appelle get_llm_client() sans savoir lequel est branché.

Depuis le Lot 8, la configuration peut venir de DEUX sources, avec priorité :
1. La base de données (modèle LLMConfig), modifiable depuis l'interface d'admin.
2. À défaut, le fichier `.env` (settings).
=> « La base l'emporte si renseignée, sinon repli sur le .env. »

Le catalogue des fournisseurs (métadonnées + attributs settings de repli) est
décrit une seule fois dans llm/providers.py.
"""

import logging

from django.conf import settings

from ..providers import PROVIDERS
from .anthropic_client import AnthropicLLMClient
from .base import LLMClient
from .cerebras_client import CerebrasLLMClient
from .gemini_client import GeminiLLMClient
from .groq_client import GroqLLMClient
from .mistral_client import MistralLLMClient
from .mock_client import MockLLMClient
from .ollama_client import OllamaLLMClient
from .openai_client import OpenAILLMClient
from .openrouter_client import OpenRouterLLMClient

logger = logging.getLogger(__name__)

# Backends CLOUD : les données du cours sortent du serveur local (enjeu RGPD,
# cf. perturbation J3-bis). Dérivé du registre des fournisseurs.
CLOUD_BACKENDS = {k for k, p in PROVIDERS.items() if p.cloud}
PAID_BACKENDS = {k for k, p in PROVIDERS.items() if p.paid}

_BACKENDS = {
    "mock": MockLLMClient,
    "ollama": OllamaLLMClient,
    "openai": OpenAILLMClient,
    "anthropic": AnthropicLLMClient,
    "gemini": GeminiLLMClient,
    "groq": GroqLLMClient,
    "openrouter": OpenRouterLLMClient,
    "cerebras": CerebrasLLMClient,
    "mistral": MistralLLMClient,
}


def resolve_active() -> dict:
    """Résout la config LLM effective (base prioritaire, repli .env).

    Renvoie un dict : { backend, model, api_key, ollama_host, timeout }.
    Import local de LLMConfig pour éviter les soucis d'ordre de chargement.
    """
    from ..models import LLMConfig

    cfg = LLMConfig.load()
    backend = (cfg.backend or settings.LLM_BACKEND or "ollama").lower()
    prov = PROVIDERS.get(backend)

    model, api_key = "", ""
    if prov is not None:
        # Modèle : valeur en base sinon défaut .env du fournisseur.
        if prov.settings_model_attr:
            model = cfg.model or getattr(settings, prov.settings_model_attr, "")
        # Clé : valeur en base sinon défaut .env (uniquement si le fournisseur en a besoin).
        if prov.needs_key and prov.settings_key_attr:
            api_key = (cfg.api_keys or {}).get(backend) or getattr(
                settings, prov.settings_key_attr, ""
            )

    return {
        "backend": backend,
        "model": model,
        "api_key": api_key,
        "ollama_host": cfg.ollama_host or "",
        "timeout": cfg.timeout or None,
    }


def effective_backend() -> str:
    """Renvoie le nom du backend actif (utile pour /ping)."""
    return resolve_active()["backend"]


def get_llm_client() -> LLMClient:
    """Renvoie le client LLM correspondant à la configuration effective."""
    conf = resolve_active()
    backend = conf["backend"]

    if backend in CLOUD_BACKENDS:
        # Garde-fou pédagogique (on N'INTERROMPT PAS, c'est un choix assumé).
        cout = "PAYANT (crédit requis)" if backend in PAID_BACKENDS else "free tier disponible"
        logger.warning(
            "[LLM] Backend CLOUD activé : '%s' (%s). Les données du cours quittent "
            "le serveur local (enjeu RGPD, cf. perturbation J3-bis). En développement, "
            "préférez Ollama (local, gratuit, souverain).",
            backend,
            cout,
        )

    client_cls = _BACKENDS.get(backend)
    if client_cls is None:
        raise ValueError(
            f"LLM_BACKEND inconnu : '{backend}'. Valeurs autorisées : "
            + " | ".join(f"'{k}'" for k in _BACKENDS)
        )

    model = conf["model"] or None
    timeout = conf["timeout"]

    if backend == "mock":
        return MockLLMClient()
    if backend == "ollama":
        return OllamaLLMClient(model=model, host=conf["ollama_host"] or None, timeout=timeout)
    if backend in ("gemini", "anthropic"):
        return client_cls(api_key=conf["api_key"], model=model, timeout=timeout)
    # Fournisseurs au format OpenAI (openai, groq, cerebras, mistral, openrouter)
    return client_cls(api_key=conf["api_key"], model=model, timeout=timeout)
