# 02 — Intégration LLM

Comment le LLM est câblé, comment changer de modèle, et comment ajouter un
nouveau backend (Hugging Face, OpenAI…).

---

## 🏗️ Architecture

```
backend/llm/
├── pdf_utils.py            ← extraction texte PDF (pypdf)
├── serializers.py          ← validation input
├── views.py                ← PingView + GenerateQuizView
├── urls.py
└── services/
    ├── base.py             ← interface LLMClient + LLMError
    ├── factory.py          ← get_llm_client() selon settings.LLM_BACKEND
    ├── quiz_prompt.py      ← prompt + validation PARTAGÉS (DRY) entre tous les clients
    ├── ollama_client.py    ← OllamaLLMClient   (LOCAL, gratuit — défaut)
    ├── openai_client.py    ← OpenAILLMClient   (API, payant)
    ├── anthropic_client.py ← AnthropicLLMClient (API Claude, payant)
    └── mock_client.py      ← MockLLMClient     (déterministe, pour tests)
```

**Pattern utilisé** : Strategy + Factory.
Le code applicatif (`views.py`) ne dépend que de l'interface `LLMClient`.
Le client concret est choisi à l'exécution via `LLM_BACKEND` (env var).

> 💡 **Note pédagogique — DRY.** Le prompt système et la validation de la sortie
> sont mutualisés dans `quiz_prompt.py` et réutilisés par les 4 clients. Améliorer
> le prompt ou durcir la validation (perturbations J3/J4) se fait donc à **un seul
> endroit**, et tous les fournisseurs en bénéficient.

---

## 🔀 Choisir le fournisseur LLM (gratuit vs payant)

Quatre fournisseurs sont disponibles, sélectionnés par `LLM_BACKEND` dans `.env` :

| `LLM_BACKEND` | Fournisseur | Coût | Données | Quand l'utiliser |
|---|---|---|---|---|
| `ollama` *(défaut)* | Modèle local (Llama, Phi…) | **Gratuit** | Restent sur le serveur (souveraineté) | Développement, démo, RGPD strict |
| `mock` | Faux QCM instantanés | Gratuit | Aucune | Tests, dev de l'UI sans attendre |
| `gemini` | API Google Gemini | **Free tier** puis payant | Envoyées hors UE | Tester une API cloud **sans carte bancaire** |
| `groq` | API Groq (Llama, Mixtral) | **Free tier** | Envoyées hors UE | Tester une API **ultra-rapide** gratuitement |
| `cerebras` | API Cerebras Cloud | **Free tier** | Envoyées hors UE | Inférence ultra-rapide, gratuite |
| `mistral` | API Mistral AI | **Free tier** | **En UE 🇪🇺 (français)** | Alternative cloud **souveraine** (RGPD) |
| `openrouter` | Passerelle multi-modèles | Variable (modèles `:free`) | Envoyées hors UE | Accéder à **des centaines** de modèles via 1 clé |
| `openai` | API OpenAI (GPT) | 💸 **Payant** (crédit requis) | Envoyées hors UE | Future version premium |
| `anthropic` | API Anthropic (Claude) | 💸 **Payant** | Envoyées hors UE | Future version premium |

```bash
# .env — exemples
LLM_BACKEND=ollama                       # gratuit, local (recommandé en dev)

# LLM_BACKEND=openai                     # payant
# OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini

# LLM_BACKEND=anthropic                  # payant
# ANTHROPIC_API_KEY=sk-ant-...
# ANTHROPIC_MODEL=claude-3-5-haiku-20241022

# LLM_BACKEND=gemini                     # free tier (clé gratuite, sans CB)
# GEMINI_API_KEY=AIza...                 # https://aistudio.google.com/apikey
# GEMINI_MODEL=gemini-1.5-flash

# Idem (format OpenAI) pour : groq / cerebras / mistral / openrouter
# -> chacun a ses variables <PROVIDER>_API_KEY et <PROVIDER>_MODEL, voir .env.example.
# Ex. : LLM_BACKEND=groq + GROQ_API_KEY=gsk_... + GROQ_MODEL=llama-3.3-70b-versatile
```

> 💡 **Architecture.** Groq, Cerebras, Mistral et OpenRouter parlent tous le
> format OpenAI : leurs clients héritent de `OpenAICompatibleClient`
> (`openai_compatible.py`) et tiennent en ~10 lignes. Ollama, Anthropic et
> Gemini ont des formats propres, donc des clients dédiés.

> 💡 **Gemini = le meilleur moyen de tester une API cloud gratuitement.** Sa clé
> s'obtient sans carte bancaire sur Google AI Studio et le free tier suffit
> largement à générer des quiz en démo. OpenAI, lui, exige du crédit prépayé
> (sinon erreur `insufficient_quota`).

> ⚠️ **Garde-fou pédagogique.** En développement, **restez sur `ollama` (gratuit)**.
> Les fournisseurs payants envoient le cours sur des serveurs hors UE (enjeu RGPD,
> cf. perturbation J3-bis) et facturent chaque génération. Le factory loggue un
> avertissement à chaque usage payant. Ces backends sont pensés pour une future
> **version premium** de l'application — pas pour vos itérations de dev.

---

## ⚙️ Changer de modèle Ollama

Le plus simple — éditer `.env` :

```bash
OLLAMA_MODEL=llama3.2:3b      # plus léger (2 Go) si vous avez peu de RAM
# ou
OLLAMA_MODEL=mistral:7b        # alternative
# ou
OLLAMA_MODEL=phi3:mini         # 2.3 Go, rapide
```

Puis :

```bash
docker compose down
docker compose up -d
docker exec apocalipssi-2026-ollama ollama pull <nouveau-modèle>
```

> 📝 **Documenter ce choix par un ADR** (voir [07-bonnes-pratiques.md](./07-bonnes-pratiques.md)). C'est attendu en perturbation J2.

---

## 🧠 Le prompt

Dans `services/quiz_prompt.py` (partagé par TOUS les clients : Ollama, OpenAI, Claude) :

```python
SYSTEM_PROMPT = """Tu es un assistant pédagogique francophone spécialisé en
génération de QCM. À partir du cours fourni, tu génères exactement 10 questions
à choix multiples pour aider un étudiant à réviser.

Règles ABSOLUES :
- Exactement 10 questions.
- Chaque question a EXACTEMENT 4 options.
- Une seule bonne réponse par question, indiquée par "correct_index" (0 à 3).
- Pas de markdown, pas de balises HTML, pas d'explications hors JSON.
- Sortie = JSON STRICT et UNIQUEMENT JSON.
"""
```

Astuces si la qualité est médiocre :

1. **Baisser la température** (déjà à 0.4) → encore plus factuel
2. **Ajouter des exemples (few-shot)** dans le SYSTEM_PROMPT
3. **Chunker le texte** si > 8000 chars : générer plusieurs lots de questions par chapitre
4. **Validation sémantique** : demander au LLM de vérifier sa propre sortie

---

## 🛡️ Validation post-LLM

`quiz_prompt.parse_and_validate_quiz` (partagé par tous les clients) impose :

- JSON parseable (avec fallback regex `{...}`)
- Clé `questions` est une liste de **10** éléments
- Chaque question a `prompt` (str non vide) + `options` (4 str) + `correct_index` (int 0-3)

Si une seule condition échoue → `LLMError` levée → réponse HTTP 502.

> 🛡️ **C'est cette validation qui protège contre le prompt injection** (perturbation J3). Étendez-la pour ajouter des contrôles métier (mots interdits, longueur min/max, etc.).

---

## 🧪 Tester sans Ollama (mode mock)

Pour développer / lancer les tests sans Ollama :

```bash
# Dans .env
LLM_BACKEND=mock
```

Le `MockLLMClient` génère 10 questions déterministes basées sur un hash
du texte source. Pratique pour :

- Lancer la CI sans GPU
- Tester rapidement le front sans attendre 30s par requête
- Reproduire des bugs (même texte → mêmes questions)

---

## ➕ Ajouter un nouveau backend (ex. Hugging Face)

### 1. Créer la classe

```python
# backend/llm/services/huggingface_client.py
import requests
from django.conf import settings

from .base import LLMClient, LLMError
# On RÉUTILISE le prompt et la validation partagés (DRY) :
from .quiz_prompt import build_full_prompt, parse_and_validate_quiz


class HuggingFaceLLMClient(LLMClient):
    def __init__(self):
        self.token = settings.HF_TOKEN
        self.model = settings.HF_MODEL  # ex: "mistralai/Mistral-7B-Instruct-v0.3"

    def generate_quiz(self, source_text: str, title: str) -> list[dict]:
        prompt = build_full_prompt(source_text, title)   # prompt mutualisé
        # ... appel HTTP à inference.huggingface.co avec `prompt`, récupérer `raw`
        raw = "..."  # À toi de jouer !
        return parse_and_validate_quiz(raw)              # validation mutualisée
```

### 2. L'enregistrer dans la factory

```python
# backend/llm/services/factory.py
from .huggingface_client import HuggingFaceLLMClient   # import en haut du fichier

_BACKENDS = {
    "mock":        MockLLMClient,
    "ollama":      OllamaLLMClient,
    "openai":      OpenAILLMClient,
    "anthropic":   AnthropicLLMClient,
    "huggingface": HuggingFaceLLMClient,                # ← AJOUT (une seule ligne !)
}
```

> 💡 Grâce au dictionnaire `_BACKENDS`, ajouter un fournisseur = **une ligne**.
> C'est tout l'intérêt du factory pattern.

### 3. Configurer

```bash
# Dans .env
LLM_BACKEND=huggingface
HF_TOKEN=hf_xxx
HF_MODEL=mistralai/Mistral-7B-Instruct-v0.3
```

### 4. Ajouter les settings Django

```python
# backend/apocal/settings.py
HF_TOKEN = config("HF_TOKEN", default="")
HF_MODEL = config("HF_MODEL", default="")
```

### 5. Écrire un test mock similaire

Dans `llm/tests.py`, ajouter un test avec `@override_settings(LLM_BACKEND="huggingface")` et un mock du `requests.post`.

---

## 👉 Suite

- [04-testing.md](./04-testing.md) — Tester l'intégration + tests adversariaux
- [07-bonnes-pratiques.md](./07-bonnes-pratiques.md) — Le format ADR pour documenter votre choix
