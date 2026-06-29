# 00 — Démarrage rapide

Guide pas-à-pas pour passer de **zéro à un quiz généré par LLM** en ~10 minutes.

---

## 🧰 Prérequis

| Outil | Version min | Comment installer |
|---|---|---|
| Docker | 24+ | https://docs.docker.com/get-docker/ |
| Docker Compose | v2 | Inclus dans Docker Desktop |
| Git | 2.30+ | https://git-scm.com/ |
| RAM disponible | **8 Go** | Ollama charge ~5 Go au lancement du modèle |
| Espace disque | **8 Go** | Llama 3.1 8B = 4.7 Go + images Docker |

> 💡 **Pas assez de RAM pour Llama 3.1 8B ?** Passez sur Llama 3.2 3B (`OLLAMA_MODEL=llama3.2:3b` dans `.env`) ou Phi-3 (`phi3:mini`).

---

## 🚀 Installation (5 étapes)

### 1. Forker et cloner

```bash
# Sur GitHub : Fork du repo IPSSI_APOCAL_KIT dans votre organisation d'équipe
git clone https://github.com/VOTRE-EQUIPE/IPSSI_APOCAL_KIT.git
cd IPSSI_APOCAL_KIT
```

### 2. Configurer l'environnement

```bash
cp .env.example .env
# (Optionnel) Éditer .env si vous voulez changer de modèle LLM ou de password Postgres
```

### 3. Lancer la stack

```bash
docker compose up -d
```

À la fin :
```
✔ Container apocalipssi-2026-postgres   Started
✔ Container apocalipssi-2026-ollama     Started
✔ Container apocalipssi-2026-backend    Started
✔ Container apocalipssi-2026-frontend   Started
```

### 4. Télécharger le modèle LLM

⚠️ **Cette étape prend 3 à 10 minutes selon votre connexion** (4.7 Go à télécharger).

```bash
make pull-model
```

### 5. Insérer les données de test

```bash
make seed
```

Vous aurez accès à :
- Email : `test@apocal.local` _(la connexion se fait par email, pas par nom d'utilisateur)_
- Password : `motdepasse123`
- 2 quizz d'exemple déjà dans l'historique

---

## ✅ Vérifier que tout marche

Ouvrez ces URLs dans le navigateur :

| URL | Attendu |
|---|---|
| http://localhost:3000 | Page d'accueil React |
| http://localhost:8000/api/docs | Swagger UI (12 endpoints listés) |
| http://localhost:8000/api/llm/ping/ | `{ ollama_alive: true, model_loaded: true }` |
| http://localhost:8000/admin/ | Admin Django (créer un superuser pour s'y connecter) |

Pour créer un superuser :
```bash
docker compose exec backend python manage.py createsuperuser
```

---

## 🎯 Premier quiz généré

1. Connectez-vous sur http://localhost:3000/login (`test@apocal.local` / `motdepasse123`)
2. Cliquez sur **Nouveau quiz**
3. Collez un paragraphe (≥ 200 caractères) — par exemple un extrait Wikipédia
4. Donnez un titre, cliquez **Générer**
5. Patientez 30s-2min (le LLM travaille…)
6. Répondez aux 10 questions, soumettez → score affiché

Si tout fonctionne : 🎉 **félicitations**, votre kit est opérationnel !

---

## 🆘 Problème ?

Consultez [docs/06-troubleshooting.md](./06-troubleshooting.md) pour les
problèmes courants (Docker, Ollama, ports, CORS).

---

## 👉 Suite

- [01-architecture.md](./01-architecture.md) — Comprendre l'architecture
- [02-llm-integration.md](./02-llm-integration.md) — Modifier l'intégration LLM
- [07-bonnes-pratiques.md](./07-bonnes-pratiques.md) — Conventions du projet
