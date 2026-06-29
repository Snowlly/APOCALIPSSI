"""
Registre central des fournisseurs LLM (Lot 8).

[Note pédagogique] Cette table décrit CHAQUE fournisseur en un seul endroit :
- ses métadonnées (cloud ? payant ? clé requise ?),
- les attributs de `settings` servant de valeurs par défaut (repli `.env`),
- une AIDE de configuration affichée dans la page d'admin (« comment obtenir une
  clé », modèle conseillé, lien).

Elle est utilisée à la fois par la factory (pour instancier le bon client) et par
l'API d'administration (pour proposer les choix + l'aide par fournisseur). Un seul
endroit à maintenir : ajouter un fournisseur = ajouter une entrée ici.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Provider:
    key: str  # identifiant interne (= valeur de LLM_BACKEND)
    label: str  # nom lisible
    cloud: bool  # les données quittent-elles le serveur local ?
    paid: bool  # crédit requis dès le 1er appel ?
    needs_key: bool  # une clé API est-elle nécessaire ?
    settings_model_attr: str  # attribut settings du modèle par défaut ("" si N/A)
    settings_key_attr: str  # attribut settings de la clé par défaut ("" si N/A)
    default_model: str  # modèle conseillé (affiché en placeholder)
    help: str  # aide de configuration (affichée dans l'admin)
    keys_url: str  # où obtenir une clé ("" si N/A)


# Ordre = ordre d'affichage dans l'admin (gratuit/local d'abord).
PROVIDERS: dict[str, Provider] = {
    "ollama": Provider(
        key="ollama",
        label="Ollama (local)",
        cloud=False,
        paid=False,
        needs_key=False,
        settings_model_attr="OLLAMA_MODEL",
        settings_key_attr="",
        default_model="llama3.1:8b",
        help="Modèle open-source exécuté EN LOCAL (gratuit, souverain, hors-ligne). "
        "Téléchargez-le une fois avec `make pull-model`. Aucune clé requise. "
        "Lent sur CPU (cf. perturbation J2).",
        keys_url="",
    ),
    "gemini": Provider(
        key="gemini",
        label="Google Gemini",
        cloud=True,
        paid=False,
        needs_key=True,
        settings_model_attr="GEMINI_MODEL",
        settings_key_attr="GEMINI_API_KEY",
        default_model="gemini-1.5-flash",
        help="Cloud avec FREE TIER généreux, idéal pour tester une API sans carte "
        "bancaire. Créez une clé gratuite sur Google AI Studio.",
        keys_url="https://aistudio.google.com/apikey",
    ),
    "groq": Provider(
        key="groq",
        label="Groq",
        cloud=True,
        paid=False,
        needs_key=True,
        settings_model_attr="GROQ_MODEL",
        settings_key_attr="GROQ_API_KEY",
        default_model="llama-3.3-70b-versatile",
        help="Cloud très rapide (LPU), free tier généreux, modèles open-source.",
        keys_url="https://console.groq.com/keys",
    ),
    "cerebras": Provider(
        key="cerebras",
        label="Cerebras Cloud",
        cloud=True,
        paid=False,
        needs_key=True,
        settings_model_attr="CEREBRAS_MODEL",
        settings_key_attr="CEREBRAS_API_KEY",
        default_model="llama-3.3-70b",
        help="Cloud très rapide, free tier disponible.",
        keys_url="https://cloud.cerebras.ai/",
    ),
    "mistral": Provider(
        key="mistral",
        label="Mistral AI",
        cloud=True,
        paid=False,
        needs_key=True,
        settings_model_attr="MISTRAL_MODEL",
        settings_key_attr="MISTRAL_API_KEY",
        default_model="mistral-small-latest",
        help="Fournisseur EUROPÉEN (données en UE — meilleur pour le RGPD), free tier.",
        keys_url="https://console.mistral.ai/",
    ),
    "openrouter": Provider(
        key="openrouter",
        label="OpenRouter",
        cloud=True,
        paid=False,
        needs_key=True,
        settings_model_attr="OPENROUTER_MODEL",
        settings_key_attr="OPENROUTER_API_KEY",
        default_model="meta-llama/llama-3.1-8b-instruct",
        help="Passerelle multi-modèles. Certains modèles sont gratuits (suffixe "
        "« :free »). Modèle au format « éditeur/modèle ».",
        keys_url="https://openrouter.ai/keys",
    ),
    "openai": Provider(
        key="openai",
        label="OpenAI",
        cloud=True,
        paid=True,
        needs_key=True,
        settings_model_attr="OPENAI_MODEL",
        settings_key_attr="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
        help="Cloud PAYANT (crédit requis dès le 1er appel). Réservé à une future "
        "version « premium ».",
        keys_url="https://platform.openai.com/api-keys",
    ),
    "anthropic": Provider(
        key="anthropic",
        label="Anthropic (Claude)",
        cloud=True,
        paid=True,
        needs_key=True,
        settings_model_attr="ANTHROPIC_MODEL",
        settings_key_attr="ANTHROPIC_API_KEY",
        default_model="claude-3-5-haiku-20241022",
        help="Cloud PAYANT (crédit requis). Réservé à une future version « premium ».",
        keys_url="https://console.anthropic.com/settings/keys",
    ),
    "mock": Provider(
        key="mock",
        label="Mock (faux quiz)",
        cloud=False,
        paid=False,
        needs_key=False,
        settings_model_attr="",
        settings_key_attr="",
        default_model="—",
        help="Génère des QCM bidon INSTANTANÉMENT, sans LLM. Parfait pour développer "
        "le frontend sans attendre la génération.",
        keys_url="",
    ),
}
