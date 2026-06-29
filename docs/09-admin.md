# 09 — Interface d'administration

Le kit fournit **deux** interfaces d'administration complémentaires :

| Interface | URL | Pour quoi |
|---|---|---|
| **Admin React** (intégrée) | `http://localhost:3000/admin` | Config LLM, config app, utilisateurs, données — pensée pour l'app |
| **Django admin** (natif) | `http://localhost:8000/admin/` | Gestion fine de tous les modèles, dépannage |

> 🏗️ Architecture **hybride** : l'admin React couvre les besoins courants avec
> une UX soignée ; le Django admin reste disponible pour la puissance brute.

---

## 🔑 Devenir administrateur

> ⚠️ **Aucun admin n'est créé automatiquement.** `make seed` ne crée qu'un compte
> **normal** de démo (`test` / `motdepasse123`), sans droits admin. Vous devez créer
> le premier admin vous-même.

L'accès à `/admin` (React) et à `/admin/` (Django) exige un compte **staff**
(`is_staff = True`). Le plus simple : créer un **super-utilisateur**.

```bash
docker exec -it apocalipssi-2026-backend python manage.py createsuperuser
```

La commande demande un **nom d'utilisateur**, un **email** et un **mot de passe**.
⚠️ Renseignez bien l'**email** : l'application se connecte **par email** (le nom
d'utilisateur ne sert qu'au Django admin natif).

Un super-utilisateur est `is_staff` ET `is_superuser`. Une fois connecté dans
l'app, un lien **« Admin »** (ambre) apparaît dans l'en-tête (rechargez la page si
besoin).

> 👥 Vous pouvez ensuite **promouvoir** d'autres comptes en admin depuis l'onglet
> *Utilisateurs* (bouton « Rendre admin ») — sans repasser par `createsuperuser`.

---

## 🧭 Les onglets de l'admin React

### 1. Vue d'ensemble
Statistiques globales : nombre d'utilisateurs, de quiz, score moyen, etc.

### 2. Config LLM ⭐
Choisir le **fournisseur**, le **modèle** et la **clé API**, avec une **aide
spécifique à chaque fournisseur** (gratuit/cloud/payant, comment obtenir une clé,
lien direct, modèle conseillé).

**Priorité de configuration** : *la base l'emporte si renseignée, sinon repli sur
le `.env`*. Le changement est **actif immédiatement** (pas de redéploiement).
La « config effective » affichée indique ce qui sera réellement utilisé.

- Backend : modèle `llm.LLMConfig` (singleton) + `llm/providers.py` (registre).
- La résolution se fait dans `llm/services/factory.py` → `resolve_active()`.

> ⚠️ **Sécurité des clés** : elles sont stockées **en base** et **jamais
> réaffichées en clair** (l'UI indique seulement « déjà définie »). Pour la
> production, chiffrez-les (ex. *Fernet*) ou utilisez un gestionnaire de secrets.

### 3. Config app
Réglages globaux (modèle `administration.SiteConfig`) :
- **Nom de l'application** (en-tête + emails),
- **Inscriptions on/off** (le `SignupView` refuse si fermé),
- **Validation d'email obligatoire** (bloque la génération de quiz si l'email
  n'est pas confirmé),
- **Bannière globale** (message visible par tous).

Un endpoint **public** `GET /api/site-config/` expose le nom de l'app, la
bannière et l'état des inscriptions, pour que le front s'y adapte.

### 4. Utilisateurs
Liste + recherche + actions : activer/désactiver, donner/retirer le rôle admin,
forcer ou renvoyer la validation d'email, supprimer.
**Garde-fous** : on ne peut pas se saboter soi-même (modifier/supprimer son
propre compte) ni toucher un super-administrateur.

### 5. Données
- **Seed** : insère des données de démo (commande `seed`).
- **Réinitialiser la base** ⚠️ : action **destructive** (supprime les quiz, et
  optionnellement les comptes non-admin), protégée par **double confirmation**
  (taper `RESET` + mot de passe administrateur).

---

## 🛠️ Endpoints (réservés `IsAdminUser`)

| Méthode | URL | Rôle |
|---|---|---|
| GET | `/api/admin/stats/` | Vue d'ensemble |
| GET/PATCH | `/api/admin/site-config/` | Config de l'app |
| GET/PATCH | `/api/admin/llm-config/` | Config LLM (+ aide fournisseurs) |
| GET | `/api/admin/users/?q=` | Liste + recherche |
| PATCH/DELETE | `/api/admin/users/<id>/` | Modifier / supprimer un user |
| POST | `/api/admin/users/<id>/resend-verification/` | Renvoyer l'email |
| POST | `/api/admin/seed/` | Données de démo |
| POST | `/api/admin/reset-data/` | Réinitialiser (destructif) |
| GET | `/api/site-config/` | **Public** : nom app, bannière, inscriptions |

---

## ➕ Étendre : ajouter une nouvelle app Django

Si vous créez une app (comme `administration` ici) :

1. Créez les fichiers (`apps.py`, `models.py`, `migrations/__init__.py`…).
2. Ajoutez l'app à `INSTALLED_APPS` (`backend/apocal/settings.py`).
3. **Redémarrez le conteneur backend** :
   ```bash
   docker restart apocalipssi-2026-backend
   ```
   > ⚠️ **Gotcha** : ajouter une app à `INSTALLED_APPS` n'est PAS pris en compte
   > par le rechargement à chaud. Si vous voyez `ModuleNotFoundError: No module
   > named '...'`, c'est presque toujours ça → un simple `docker restart` règle.
4. Générez et appliquez les migrations :
   ```bash
   docker exec apocalipssi-2026-backend python manage.py makemigrations
   docker exec apocalipssi-2026-backend python manage.py migrate
   ```

---

## 👉 Suite
- [03-auth.md](./03-auth.md) — auth, permissions, `IsAdminUser`
- [02-llm-integration.md](./02-llm-integration.md) — fournisseurs LLM
