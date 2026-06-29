# 🎓 Guide étudiant — EduTutor IA (kit APOCAL'IPSSI 2026)

Bienvenue ! Ce guide vous prend par la main, du **clone du projet** jusqu'à
**l'ajout de votre première fonctionnalité**. Il est volontairement progressif :
lisez-le dans l'ordre la première fois, puis revenez-y comme référence.

> 🧭 **Vous êtes pressé ?** Allez direct à [§2 Installation](#2-installation-pas-à-pas).
> **Vous voulez coder une feature ?** Voir [§5 Ajouter une fonctionnalité](#5-ajouter-une-fonctionnalité-le-workflow-type).

> ### Les 5 perturbations de la semaine
> La semaine compte **exactement 5 perturbations** (dont **2 le mercredi**) :
>
> | # | Jour | Créneau | Thème |
> |---|------|---------|-------|
> | P1 | J1 | lundi 14h00 | Produit / Scope |
> | P2 | J2 | mardi 10h00 | Technique (latence → ADR) |
> | P3 | J3 | mercredi 10h00 | Sécurité (prompt injection) |
> | P4 | J3-bis | mercredi 14h00 | RGPD / données personnelles |
> | P5 | J4 | jeudi 10h00 | Livraison / Crise |

---

## 1. C'est quoi, ce kit ?

**EduTutor IA** est une plateforme de révision : un étudiant colle (ou téléverse)
un cours, un **LLM** génère automatiquement **10 questions (QCM)**, l'étudiant y
répond, obtient son **score** et peut **réviser ses erreurs**.

Le kit vous fournit **~30 % du MVP déjà câblé** (la « plomberie ») pour que vous
vous concentriez sur la **valeur produit** et sur votre **réactivité agile** face
aux perturbations de la semaine.

### Ce qui est DÉJÀ dans le kit

| Domaine | Inclus |
|---|---|
| **Comptes** | Inscription / connexion **par email**, validation d'email, mot de passe oublié, **page profil** (modifier, supprimer) |
| **Quiz** | Upload PDF/texte, génération LLM de 10 QCM, correction + score, historique |
| **MVP2 (démos)** | Tableau de bord de progression, révision des erreurs, **mode sombre** |
| **Admin** | Interface d'admin : config LLM/app depuis l'UI, gestion des utilisateurs |
| **LLM** | 9 fournisseurs au choix (Ollama local par défaut + 7 cloud + mock) |
| **Emails** | Bascule auto console (dev) / Brevo (réel) |
| **Légal** | 4 pages légales **vierges** à compléter |
| **Outillage** | Docker, Makefile, CI GitHub Actions, tests, docs/ |

---

## 2. Installation pas à pas

### Prérequis

| Outil | Version | Note |
|---|---|---|
| Docker + Docker Compose | 24+ / v2 | Docker Desktop fait les deux |
| Git | 2.30+ | |
| RAM dispo | **≥ 8 Go** | Ollama charge ~5 Go |
| Disque | **≥ 8 Go** | Modèle Llama + images |

> 💡 Pas assez de RAM ? Utilisez un modèle plus léger (`OLLAMA_MODEL=llama3.2:3b`)
> ou un fournisseur cloud gratuit (voir [§6](#6-choisir-son-llm)).

### Étapes

```bash
# 1. Forkez le repo sur GitHub (dans le compte de VOTRE équipe), puis clonez
git clone https://github.com/VOTRE-EQUIPE/IPSSI_APOCAL_KIT.git
cd IPSSI_APOCAL_KIT

# 2. Copiez la configuration
cp .env.example .env

# 3. Lancez toute la stack (Postgres, Ollama, backend, frontend)
docker compose up -d

# 4. Téléchargez le modèle LLM (UNE seule fois, ~5 min)
make pull-model      # ou : docker exec apocalipssi-2026-ollama ollama pull llama3.1:8b

# 5. (Optionnel) Données de démo
make seed
```

Ouvrez ensuite :
- **Application** : <http://localhost:3000>
- **API + Swagger** : <http://localhost:8000/api/docs>

> 🪟 **Sous Windows**, `make` n'existe pas par défaut. Soit vous l'installez
> (`choco install make`), soit vous lancez la commande Docker équivalente
> indiquée à côté de chaque cible (ex. `docker exec ... ollama pull ...`).

---

## 3. Découverte de l'application

| Page | URL | À quoi ça sert |
|---|---|---|
| Accueil | `/` | Présentation |
| Inscription | `/signup` | Créer un compte **par email** (prénom/nom facultatifs) |
| Connexion | `/login` | Se connecter par email (+ « mot de passe oublié ») |
| Nouveau quiz | `/upload` | Coller un texte ou téléverser un PDF → génère 10 QCM |
| Quiz | `/quiz/:id` | Répondre aux questions, voir la correction |
| Historique | `/history` | Tous vos quiz passés |
| **Tableau de bord** | `/dashboard` | KPIs + graphique de progression |
| **Révision** | `/review` | Vos questions ratées (à revoir) |
| Profil | `/profile` | Modifier email/nom/mot de passe, supprimer le compte |
| **Admin** | `/admin` | (staff) config LLM/app, utilisateurs, données — voir `docs/09-admin.md` |
| Légal | `/legal/...` | Mentions, confidentialité, CGU, cookies (à compléter) |

### 👑 Créer le compte administrateur

**Le kit ne crée AUCUN admin automatiquement** — c'est à vous de le faire. La commande
`make seed` crée seulement un compte **normal** de démo (`test` / `motdepasse123`) qui
n'a **pas** les droits admin.

Pour créer votre **premier** administrateur :

```bash
docker exec -it apocalipssi-2026-backend python manage.py createsuperuser
```

La commande demande successivement un **nom d'utilisateur**, un **email** et un
**mot de passe**. ⚠️ Renseignez bien l'**email** : dans l'application, **on se connecte
par email** (le nom d'utilisateur ne sert qu'au Django admin).

Ce compte devient `is_staff` + `is_superuser`. Après connexion, un lien **« Admin »**
(ambre) apparaît dans l'en-tête et donne accès à :
- la page **`/admin`** de l'app (configurer le LLM et l'app, gérer les utilisateurs, seed/reset) ;
- le **Django admin** natif sur `http://localhost:8000/admin/`.

> 👥 **Pour les coéquipiers suivants**, pas besoin de `createsuperuser` : depuis
> l'onglet *Utilisateurs* de `/admin`, le premier admin peut promouvoir les autres
> avec le bouton **« Rendre admin »**.
>
> 🔁 Le lien « Admin » n'apparaît pas tout de suite ? **Rechargez la page** (le front
> recharge votre profil) ou déconnectez/reconnectez-vous.
>
> 🤖 **Variante non interactive** (utile en script/CI) :
> ```bash
> docker exec -e DJANGO_SUPERUSER_PASSWORD=motdepasse123 apocalipssi-2026-backend \
>   python manage.py createsuperuser --noinput --username admin --email admin@exemple.fr
> ```

🌙 **Mode sombre** : bouton lune/soleil en haut à droite (mémorisé).
✉️ **Validation d'email** : à l'inscription, un email part. En dev (sans Brevo),
il s'affiche dans les **logs du backend** :
```bash
docker logs apocalipssi-2026-backend --tail 40
```

---

## 4. Comment c'est rangé (architecture express)

```
IPSSI_APOCAL_KIT/
├── backend/                 # Django + DRF
│   ├── apocal/              # settings, urls racine
│   ├── accounts/            # comptes (auth email, profil, emails, tokens)
│   ├── quizzes/             # quiz, questions, score, stats, révision
│   └── llm/                 # intégration LLM (9 fournisseurs)
│       └── services/        # factory + clients + prompt
├── frontend/                # React + Vite + TypeScript
│   └── src/
│       ├── api/             # appels HTTP (auth.ts, quizzes.ts, llm.ts...)
│       ├── components/      # Layout, RequireAuth, bandeaux...
│       ├── contexts/        # AuthContext, ThemeContext
│       └── pages/           # une page = un écran
├── docs/                    # 9 fiches thématiques (lisez-les !)
├── scripts/                 # redeploy.sh / redeploy.ps1
└── docker-compose.yml
```

**Le flux d'une requête** : `page React` → `src/api/*.ts` (axios + token) →
`Django urls.py` → `views.py` → `serializers.py` → `models.py` → Postgres.

---

## 5. Ajouter une fonctionnalité (le workflow type)

Prenons un exemple concret : **ajouter un champ « matière » (`subject`) à un quiz**.

### Côté backend (Django)

1. **Modèle** — `backend/quizzes/models.py`
   ```python
   class Quiz(models.Model):
       # ...
       subject = models.CharField(max_length=100, blank=True, default="")
   ```
2. **Migration**
   ```bash
   docker exec apocalipssi-2026-backend python manage.py makemigrations
   docker exec apocalipssi-2026-backend python manage.py migrate
   ```
3. **Serializer** — `backend/quizzes/serializers.py` : ajoutez `"subject"` aux `fields`.
4. **Vue / URL** — souvent rien à changer si la vue existe déjà ; sinon ajoutez
   votre `APIView` dans `views.py` et la route dans `urls.py`.
5. **Test** — `backend/quizzes/tests.py` (voir `docs/04-testing.md`).

### Côté frontend (React)

1. **Type + appel API** — `frontend/src/api/quizzes.ts` : ajoutez `subject` au type `Quiz`.
2. **Page** — affichez/éditez le champ dans la page concernée (`pages/...`).
3. **Route** (si nouvelle page) — `frontend/src/App.tsx`, sous `<RequireAuth>` si protégée.
4. **Navigation** — ajoutez un lien dans `components/Layout.tsx` si besoin.

> 📌 **Astuce** : copiez une feature existante comme modèle. Le **Tableau de bord**
> (`StatsView` + `DashboardPage`) et la **Révision** (`MistakesView` +
> `ReviewMistakesPage`) sont des exemples complets backend↔frontend à imiter.

### Vérifier que ça compile

```bash
# Backend
docker exec apocalipssi-2026-backend python manage.py check
# Frontend (lint + types)
docker exec apocalipssi-2026-frontend npm run lint
```

---

## 6. Choisir son LLM

Le fournisseur se choisit dans `.env` via `LLM_BACKEND`. Par défaut : **Ollama**
(local, gratuit, hors-ligne).

| Valeur | Type | Clé requise |
|---|---|---|
| `ollama` | Local (défaut) | aucune |
| `gemini` | Cloud (offre gratuite) | `GEMINI_API_KEY` |
| `groq` · `cerebras` · `mistral` · `openrouter` | Cloud | clé du fournisseur |
| `openai` · `anthropic` | Cloud **payant** | clé + crédit |
| `mock` | Faux quiz instantané | aucune (utile pour développer le front) |

```bash
# Exemple : passer sur Gemini
LLM_BACKEND=gemini
GEMINI_API_KEY=AIza...
```
Puis redéployez (voir §8). 

> ⏱️ **En local (Ollama, CPU)**, la génération peut prendre **2–4 min** : c'est
> normal. Pour développer le **front** sans attendre, utilisez `LLM_BACKEND=mock`.

---

## 7. Emails (validation de compte, mot de passe oublié)

- **Sans clé Brevo (défaut)** → mode **console** : les emails s'affichent dans
  `docker logs apocalipssi-2026-backend`. Parfait pour tester sans rien configurer.
- **Avec une clé SMTP Brevo** → de **vrais emails** partent.

Configuration (dans `.env`) :
```bash
BREVO_SMTP_KEY=xsmtpsib-...
BREVO_SMTP_LOGIN=xxxxx@smtp-brevo.com   # ⚠ l'identifiant SMTP, PAS votre email
DEFAULT_FROM_EMAIL=EduTutor IA <no-reply@votre-domaine.fr>
FRONTEND_URL=http://localhost:3000      # pour que les liens des emails pointent bien
```
Tester :
```bash
docker exec apocalipssi-2026-backend python manage.py send_test_email vous@example.com
```

---

## 8. Commandes du quotidien

```bash
make dev          # démarre tout            make logs        # logs en direct
make down         # arrête tout             make test        # pytest + vitest
make seed         # données de démo         make lint        # formate + vérifie
make reset-db     # ⚠ réinitialise la DB    make pull-model  # télécharge le LLM
```

**Redéployer après une modif** :

| Quand | Commande (Linux/macOS) | Windows (PowerShell) |
|---|---|---|
| Modif **code** ou **`.env`** | `bash scripts/redeploy.sh --fast` | `powershell -ExecutionPolicy Bypass -File scripts\redeploy.ps1 -Fast` |
| Modif **dépendances**/Dockerfile | `bash scripts/redeploy.sh` | `powershell -ExecutionPolicy Bypass -File scripts\redeploy.ps1` |

---

## 9. Git & commits

Le projet suit les **Conventional Commits** :
```
feat(quizzes): ajoute le champ matière
fix(auth): corrige le login par email
docs: complète les mentions légales
```
Travaillez sur des **branches** (`feat/...`, `fix/...`), ouvrez des **Pull
Requests**, faites-vous **relire**. Voir `docs/05-ci-cd.md` et `docs/07-bonnes-pratiques.md`.

---

## 10. Où trouver de l'aide

| Besoin | Ressource |
|---|---|
| Premier démarrage / erreurs | `docs/00-getting-started.md`, `docs/06-troubleshooting.md` |
| Comprendre l'archi | `docs/01-architecture.md` |
| Brancher/changer le LLM | `docs/02-llm-integration.md` |
| Auth en détail | `docs/03-auth.md` |
| Écrire des tests | `docs/04-testing.md` |
| CI/CD, commits | `docs/05-ci-cd.md` |
| Bonnes pratiques agiles | `docs/07-bonnes-pratiques.md` |
| Idées pour la Release 2 | `docs/08-mvp2-idees.md` |
| Interface d'administration | `docs/09-admin.md` |
| Cours Agile/Scrum | <https://mohamedelafrit.com/teaching/Master_Classe_Agile/cours.html> |
| Infos de la semaine | <https://apocalipssi26.elafrit.com> |

---

## ✅ Checklist MVP (Release 1)

- [ ] Je peux **m'inscrire** et **me connecter** par email
- [ ] Je peux **coller un cours** ou **téléverser un PDF**
- [ ] Un quiz de **10 QCM** est **généré**
- [ ] Je peux **répondre** et voir mon **score /10**
- [ ] Mon **historique** est conservé
- [ ] Les **pages légales** sont **complétées** par mon équipe
- [ ] Le code est **testé**, **commité** proprement et **relu** en PR

Bon courage, et amusez-vous ! 🚀
