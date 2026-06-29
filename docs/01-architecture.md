# 01 — Architecture

Vue d'ensemble du kit et flux principaux.

---

## 🗺️ Vue d'ensemble

```mermaid
flowchart LR
    user[👤 Utilisateur]

    subgraph Browser["Navigateur"]
        react[React + Vite<br/>:3000]
    end

    subgraph Backend["Backend Django"]
        api[DRF API<br/>:8000]
        admin[Django Admin]
        swagger[Swagger UI<br/>/api/docs]
    end

    subgraph DB["Données"]
        pg[(PostgreSQL 16<br/>:5432)]
    end

    subgraph LLM["LLM"]
        ollama[Ollama<br/>:11434]
        model[(Llama 3.1 8B)]
    end

    user -->|HTTPS| react
    react -->|REST + Token| api
    api -->|ORM| pg
    api -->|HTTP /api/generate| ollama
    ollama --> model
    admin -.->|debug only| pg
```

---

## 📦 Composants

### Backend (Django + DRF)

| App | Responsabilité |
|---|---|
| `apocal/` | Projet Django (settings, urls, wsgi/asgi) |
| `accounts/` | Auth REST : signup, login, logout, me — token DRF + session |
| `llm/` | Intégration LLM : ping + génération de quiz, abstraction Ollama/Mock |
| `quizzes/` | Modèles métier : Quiz + Question, historique, correction |

**Choix techniques** :
- `IsAuthenticated` par défaut sur toute l'API (sauf signup/login)
- Token DRF persisté en localStorage côté front
- Session Django activée en parallèle (utile pour Swagger UI)
- `drf-spectacular` pour générer le schéma OpenAPI automatiquement

### Frontend (React + Vite + TS)

| Dossier | Contenu |
|---|---|
| `src/api/` | Clients axios par domaine (auth, llm, quizzes) |
| `src/contexts/AuthContext.tsx` | Provider + hook `useAuth()` |
| `src/components/` | `Layout`, `RequireAuth` |
| `src/pages/` | 5 pages (Home, Login, Signup, Upload, Quiz, History) |

**Choix techniques** :
- React Router 6 (data routers non utilisés pour rester simple)
- TypeScript strict (`noUnusedLocals`, `noUncheckedIndexedAccess`)
- Tailwind CSS avec palette alignée site (indigo + ambre)
- Axios avec interceptors token + 401 handling

### Infrastructure

| Service | Image | Volume | Port |
|---|---|---|---|
| `postgres` | postgres:16-alpine | postgres-data | 5432 |
| `ollama` | ollama/ollama:latest | ollama-data | 11434 |
| `backend` | local (Dockerfile) | `./backend:/app` | 8000 |
| `frontend` | local (Dockerfile) | `./frontend:/app` + node_modules séparé | 3000 |

---

## 🔐 Flux d'authentification

```mermaid
sequenceDiagram
    actor U as Utilisateur
    participant F as Frontend
    participant B as Backend (DRF)
    participant DB as Postgres

    U->>F: Remplit form signup
    F->>B: POST /api/accounts/signup/
    B->>DB: INSERT user (password hashé bcrypt)
    B-->>F: 201 { user }
    F->>B: POST /api/accounts/login/<br/>(auto-login)
    B->>DB: SELECT user + verify password
    B->>DB: INSERT token
    B-->>F: 200 { token, user }
    F->>F: localStorage.setItem('apocal_token', ...)
    Note over F: Toutes les requêtes suivantes<br/>incluent header Authorization
```

---

## 🤖 Flux de génération de quiz

```mermaid
sequenceDiagram
    actor U as Utilisateur
    participant F as Frontend
    participant B as Backend
    participant O as Ollama
    participant DB as Postgres

    U->>F: Upload PDF + titre
    F->>B: POST /api/llm/generate-quiz/<br/>(multipart)
    B->>B: extract_text_from_pdf()
    B->>O: POST /api/generate<br/>(prompt + format=json)
    Note over O: Llama 3.1 8B<br/>~30s-2min
    O-->>B: { "questions": [...] }
    B->>B: validate JSON structure<br/>(10 q, 4 options chacune)
    B->>DB: INSERT Quiz + 10 Questions<br/>(transaction)
    B-->>F: 201 { quiz complet }
    F->>F: navigate(`/quiz/${id}`)
```

---

## 🔍 Lire le code hérité en 20 min (avant d'ajouter quoi que ce soit)

Le projet est **repris (brownfield)**. Avant de coder, **lisez les 2 flux cœur** en suivant
le chemin **fichier par fichier**. C'est l'exercice qui nourrit votre inventaire et votre
repriorisation MoSCoW avec le PO — et qui met Bachelor B3 et Master M1 à égalité.

### Flux A — Connexion par email (~10 min)

1. `frontend/src/pages/LoginPage.tsx` — le formulaire (point d'entrée UI).
2. `frontend/src/api/auth.ts` → `login(email, password)` — l'appel API.
3. `frontend/src/api/client.ts` — l'instance axios (base URL + token + gestion 401).
4. `backend/apocal/urls.py` → `path("api/accounts/", include("accounts.urls"))`.
5. `backend/accounts/urls.py` → `path("login/", LoginView.as_view())`.
6. `backend/accounts/views.py` → `LoginView.post()` — orchestre la connexion.
7. `backend/accounts/serializers.py` → `LoginSerializer` — **trouve l'utilisateur par EMAIL** puis authentifie (subtilité clé du kit : le login se fait par email, pas par username).
8. `backend/accounts/models.py` — `User` + `Profile` (`email_verified`…).

Le token renvoyé est stocké par `frontend/src/contexts/AuthContext.tsx` (puis renvoyé à chaque requête).

### Flux B — Génération d'un quiz (~10 min)

1. `frontend/src/pages/UploadPage.tsx` — upload PDF/texte + titre.
2. `frontend/src/api/llm.ts` → `generateQuiz(input)` — POST multipart.
3. `backend/apocal/urls.py` → `path("api/llm/", include("llm.urls"))`.
4. `backend/llm/urls.py` → `path("generate-quiz/", GenerateQuizView.as_view())`.
5. `backend/llm/views.py` → `GenerateQuizView.post()` — extrait le texte du PDF, appelle le LLM, **valide le JSON** (10 questions × 4 options).
6. `backend/llm/providers.py` — abstraction des fournisseurs LLM (Ollama / cloud / mock).
7. `backend/quizzes/models.py` — `Quiz` + `Question` insérés en transaction.

La réponse renvoie vers `frontend/src/pages/QuizPage.tsx` (via `frontend/src/api/quizzes.ts`).

> 💡 **Astuce inventaire** : pour chaque flux, notez ce qui est **solide** (à garder),
> **fragile** (à fiabiliser) et **manquant** (à ajouter). C'est votre matière pour la
> repriorisation **MoSCoW** avec le PO — et pour la **carte rétro** de chaque perturbation.

---

## 🎯 Où en est la base (✅ déjà là / 🔧 à recalibrer)

Ce qui est **déjà câblé** dans le kit :

- ✅ Auth complète (signup/login/logout/me)
- ✅ Modèles Quiz + Question + migrations
- ✅ Endpoint génération LLM avec mock + Ollama
- ✅ Endpoint correction (score + détails)
- ✅ Endpoint historique paginé
- ✅ Frontend skeleton avec 5 pages fonctionnelles

Ce qui **reste à faire** pour la Release 1 (MVP must-have) :
- Polir le frontend (design, UX, transitions)
- Tester avec de vrais cours étudiants
- Améliorer le prompt LLM si la qualité des QCM est médiocre
- Ajouter validation supplémentaire (longueur prompts, etc.)
- Documenter votre code

Ce qui est **catalogue Release 2** (libre) :
- Questions ouvertes (LLM-graded)
- Dashboard de progression
- Identification des lacunes
- Plan de révision personnalisé
- Multi-cours, multi-difficulté, flashcards…

---

## 👉 Suite

- [02-llm-integration.md](./02-llm-integration.md) — Modifier l'intégration LLM
- [03-auth.md](./03-auth.md) — Auth REST en détail
