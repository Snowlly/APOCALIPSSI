# 05 — CI/CD

Comment fonctionne notre pipeline GitHub Actions et comment l'étendre.

---

## 🚦 Pipeline actuel

Le fichier `.github/workflows/ci.yml` définit **2 jobs en parallèle** :

### Job `backend`
1. Checkout
2. Setup Python 3.11 (avec cache pip)
3. Installer `requirements-dev.txt`
4. `ruff check .`
5. `black --check .`
6. `python manage.py check`
7. `python manage.py migrate --noinput`
8. `pytest --cov`

Variables d'env CI :
- `LLM_BACKEND=mock` → jamais d'appel Ollama
- `POSTGRES_*` pointent vers le service sidecar Postgres 16

### Job `frontend`
1. Checkout
2. Setup Node 20 (avec cache npm)
3. `npm ci` (ou `npm install`)
4. `npm run lint` (eslint)
5. `npm run format:check` (prettier)
6. `npm run build` (tsc + vite build)
7. `npm test -- --run` (vitest)

---

## 🎯 Déclencheurs

| Événement | Comportement |
|---|---|
| **Push sur `main`** | Tous les jobs tournent |
| **PR vers `main`** | Tous les jobs tournent, blocage du merge si rouge |
| **Push sur autre branche** | Pas de CI (économie d'actions minutes) |

Pour activer la CI sur toutes les branches, modifier :

```yaml
on:
  push:
    branches: ['**']
  pull_request:
```

---

## ➕ Étendre la CI

### Ajouter un nouveau check (ex. mypy)

Ajouter une étape dans le job `backend` :

```yaml
- name: Type check (mypy)
  run: |
    pip install mypy
    mypy apocal/ accounts/ llm/ quizzes/
```

### Ajouter le déploiement (Release 2)

Créer un nouveau job qui dépend de `backend` et `frontend` :

```yaml
deploy:
  needs: [backend, frontend]
  if: github.ref == 'refs/heads/main'
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Deploy to Fly.io   # ou Railway, ou OVH, ou ...
      run: |
        curl -L https://fly.io/install.sh | sh
        flyctl deploy --remote-only
      env:
        FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

### Ajouter un badge dans le README

```markdown
![CI](https://github.com/VOTRE-EQUIPE/IPSSI_APOCAL_KIT/actions/workflows/ci.yml/badge.svg)
```

---

## 💬 Conventional Commits — Vérification automatique

Le hook pre-commit `conventional-pre-commit` (cf `.pre-commit-config.yaml`)
**bloque les messages mal formés** :

```bash
git commit -m "fixed bug"
# ❌ ✗ commit message format does not match Conventional Commits

git commit -m "fix(quizzes): persiste le score à la soumission"
# ✓ accepté
```

Si vous voulez bypass exceptionnellement (à éviter) :

```bash
git commit --no-verify -m "..."
```

---

## 🪝 Hooks pre-commit — installation

```bash
pip install pre-commit
pre-commit install                       # hooks "normaux" (git commit)
pre-commit install --hook-type commit-msg  # hook Conventional Commits
```

Pour les lancer manuellement sur tous les fichiers :

```bash
pre-commit run --all-files
```

Pour mettre à jour les versions des hooks :

```bash
pre-commit autoupdate
```

---

## 🚀 Déploiement — pistes pour Release 2

Le kit ne prescrit pas un hébergement particulier — c'est laissé libre aux
équipes ambitieuses. Pistes possibles :

| Plateforme | Adapté pour | Effort |
|---|---|---|
| **Fly.io** | App full stack, Postgres managé, Ollama possible en VM | ★★★ |
| **Railway** | Déploiement Git push, Postgres inclus | ★★ |
| **OVH VPS** | Self-hosted, max contrôle, Ollama OK | ★★★★ |
| **Render** | Free tier généreux, Postgres managé | ★★ |
| **Vercel + Render** | Front Vercel, backend Render | ★★★ |

> ⚠️ Si vous tentez le déploiement, attention à **Ollama** : la plupart des
> plateformes n'ont pas de GPU et le modèle 8B est très lent en CPU.
> Vous pouvez passer en mode `LLM_BACKEND=huggingface` avec un endpoint
> Inference HF pour gérer ce problème (cf [02-llm-integration.md](./02-llm-integration.md)).

---

## 👉 Suite

- [06-troubleshooting.md](./06-troubleshooting.md) — CI rouge ? Voir ici.
- [07-bonnes-pratiques.md](./07-bonnes-pratiques.md) — Conventional Commits en détail
