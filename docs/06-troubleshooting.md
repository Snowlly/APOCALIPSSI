# 06 — Troubleshooting

Les problèmes les plus fréquents et leurs solutions.

---

## 🐳 Docker

### `docker compose up` échoue avec "port already in use"

Un autre processus utilise le port (3000, 5432, 8000, ou 11434).

**Solution rapide** : changer le port hôte via `.env`. Décommenter ce qui
vous arrange dans `.env` :

```bash
# .env
POSTGRES_HOST_PORT=5433     # défaut 5432
FRONTEND_HOST_PORT=3002     # défaut 3000
```

Puis relancer :

```bash
docker compose down
docker compose up -d
```

Le port du conteneur reste 5432 / 3000 (le backend Django parle à Postgres
en interne via le réseau Docker, indépendamment du port hôte).

**Identifier le coupable** :

```bash
# macOS / Linux
lsof -i :8000

# Windows
netstat -ano | findstr 8000
```

**Gotcha Windows + IPv6** : sur Windows, `localhost` peut résoudre en IPv6
(`::1`). Si un serveur PHP local (XAMPP ou `php -S`) écoute sur `::1:8000`,
il interceptera vos requêtes même si Docker bind sur `0.0.0.0:8000`. Testez
explicitement avec **`http://127.0.0.1:8000`** ou tuez le serveur PHP avant
de lancer Docker.

### Build d'image échoue avec "no space left on device"

Docker garde un cache énorme. Nettoyer :

```bash
docker system prune -a --volumes
# ⚠️ Cela supprime AUSSI les volumes (donc Postgres + Ollama models)
```

### `docker compose down -v` détruit la base — comment l'éviter ?

`-v` supprime les **volumes**. Sans le flag, vos données Postgres sont
préservées :

```bash
docker compose down       # garde les volumes ✓
docker compose down -v    # ⚠️ destructif (sauf si c'est ce que vous voulez)
```

---

## 🤖 Ollama

### `make pull-model` → "connection refused"

Ollama n'est pas (encore) démarré. Vérifier :

```bash
docker compose ps ollama   # statut
docker compose logs ollama # logs
```

Si nécessaire, relancer :

```bash
docker compose restart ollama
sleep 5
make pull-model
```

### Génération de quiz très lente (> 2 min)

Vous tournez sur CPU sans GPU. Solutions :

1. **Modèle plus petit** : `OLLAMA_MODEL=llama3.2:3b` (2 Go vs 4.7 Go)
2. **Phi-3 mini** : `OLLAMA_MODEL=phi3:mini` (2.3 Go, très rapide)
3. **GPU NVIDIA disponible** : décommenter le bloc `deploy.resources.reservations.devices` dans `docker-compose.yml`
4. **Mode mock pour dev** : `LLM_BACKEND=mock` (instantané, déterministe)
5. **Centraliser Ollama** : 1 seul membre héberge, les autres consomment via le réseau local

### Le LLM renvoie n'importe quoi (JSON cassé, hors-sujet)

Inspecter ce que renvoie Ollama directement :

```bash
docker exec -it apocalipssi-2026-ollama ollama run llama3.1:8b "Génère 1 QCM en JSON sur les bases du HTTP"
```

Si la qualité est mauvaise même en interactif :
- Modèle trop petit pour la tâche → upgrader
- Prompt à enrichir (few-shot examples)
- Voir [02-llm-integration.md](./02-llm-integration.md) section "Astuces si la qualité est médiocre"

---

## 🗄️ Postgres

### "connection refused" depuis le backend

Postgres met ~10s à démarrer. Le backend doit attendre via `depends_on:
condition: service_healthy` (déjà configuré dans `docker-compose.yml`).

Si ça arrive quand même :

```bash
docker compose logs postgres
docker compose restart backend
```

### "relation does not exist" (modèle Quiz / Question)

Les migrations n'ont pas tourné. Forcer :

```bash
docker compose exec backend python manage.py migrate
```

### Reset complet de la DB

```bash
make reset-db    # avec confirmation
```

Ou manuellement :

```bash
docker compose down -v
docker compose up -d
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py seed
```

---

## 🌐 CORS

### "Access to XMLHttpRequest blocked by CORS policy"

Le backend a une whitelist explicite dans `settings.py` :

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

Si vous accédez au frontend depuis une autre URL (ex. votre IP locale
`192.168.1.42:3000`) : ajouter cette URL à la liste.

---

## 🔐 Auth

### "Token invalide" alors que je viens de me logger

Vérifier ce qui est envoyé :

```javascript
// DevTools → Network → onglet Headers de la requête
Authorization: Token abc123...
```

Si l'en-tête est `Bearer abc123` au lieu de `Token abc123`, c'est que
votre front utilise un schéma JWT au lieu du Token DRF. Vérifier
`frontend/src/api/client.ts` :

```typescript
config.headers.Authorization = `Token ${token}`;  // ✓
```

### Session perdue à chaque rechargement

- Vérifier que `localStorage['apocal_token']` existe (DevTools → Application)
- Vérifier que `AuthContext` appelle bien `/api/accounts/me/` au mount
- Si `/me/` renvoie 401 → le token est invalide côté serveur → re-login

---

## 🧪 Tests

### `pytest` échoue avec "database access not allowed"

Ajouter `pytestmark = pytest.mark.django_db` en tête du fichier OU
décorer la fonction de test individuelle :

```python
@pytest.mark.django_db
def test_something():
    ...
```

### `vitest` ne trouve pas les imports `@/...`

Vérifier le `vite.config.ts` (alias `@` configuré) ET le `tsconfig.json`
(`paths` configuré).

---

## 🚦 CI GitHub Actions

### Job backend échoue sur `ruff check`

```bash
# Localement
docker compose exec backend ruff check .
# Ou avec auto-fix
docker compose exec backend ruff check . --fix
```

### Job frontend échoue sur `npm run lint`

```bash
docker compose exec frontend npm run lint
# Auto-fix possible (limité)
docker compose exec frontend npx eslint . --ext ts,tsx --fix
```

### Tests passent en local mais échouent en CI

Causes fréquentes :
- Variables d'env différentes (vérifier `env:` dans `ci.yml`)
- Postgres pas encore healthy (ajouter `wait-for-it` si besoin)
- Timeout court en CI (augmenter les timeouts pytest)

---

## ❓ Mon problème n'est pas listé

1. Lire le log complet : `docker compose logs --tail=200`
2. Demander sur Teams au coordinateur de votre équipe
3. Ouvrir une issue sur le repo du kit : <https://github.com/melafrit/IPSSI_APOCAL_KIT/issues>

---

## 👉 Suite

- [00-getting-started.md](./00-getting-started.md) — Revenir au démarrage
- [07-bonnes-pratiques.md](./07-bonnes-pratiques.md) — Post-mortem quand tout casse
