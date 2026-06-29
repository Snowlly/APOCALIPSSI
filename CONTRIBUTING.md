# Contribuer à IPSSI_APOCAL_KIT

> Ce fichier sert de référence interne. Pour les équipes APOCAL'IPSSI, il
> documente le **workflow Git imposé** et les **conventions** attendues
> pendant la semaine.

---

## 🌳 Workflow Git

### Branche principale

- `main` est protégée — pas de push direct, uniquement via Pull Request
- Toute PR doit avoir au minimum une **review** d'un membre de l'équipe
- La CI doit être ✅ verte avant merge

### Branches feature

Convention : `<type>/<courte-description-kebab-case>`

Exemples :
- `feat/upload-pdf`
- `fix/score-not-saved`
- `docs/architecture-diagram`
- `refactor/llm-service-abstraction`

### Cycle de vie d'une feature

```bash
# Partir d'un main à jour
git checkout main && git pull

# Créer une branche feature
git checkout -b feat/dashboard-progression

# Faire ses changements, commits atomiques
git add .
git commit -m "feat(quizzes): ajoute le calcul de score moyen"

# Pousser et ouvrir une PR
git push -u origin feat/dashboard-progression
gh pr create --fill   # ou interface GitHub
```

---

## 💬 Conventional Commits

Format imposé : `<type>(<scope>): <description>`

### Types autorisés

| Type | Quand l'utiliser |
|---|---|
| `feat` | Nouvelle fonctionnalité visible utilisateur |
| `fix` | Correction de bug |
| `refactor` | Réorganisation du code sans changement de comportement |
| `docs` | Documentation (README, docs/, commentaires) |
| `test` | Ajout / modification de tests |
| `chore` | Maintenance (deps, configs, CI) |
| `perf` | Optimisation de performances |
| `style` | Formatage (espaces, semi-colons, etc. — pas de logique) |

### Scopes courants

`accounts` · `llm` · `quizzes` · `frontend` · `docker` · `ci` · `docs`

### Exemples

```
feat(llm): supporte les modèles Hugging Face en plus d'Ollama
fix(quizzes): le score est désormais persisté après soumission
refactor(frontend): extrait useQuiz hook depuis QuizPage
docs(architecture): ajoute diagramme Mermaid Django ↔ Ollama
chore(ci): cache npm pour accélérer les workflows
```

### Squash & Merge

À la fusion, GitHub squash les commits de la branche en un seul.
Le message du squash doit lui aussi respecter Conventional Commits.

---

## 🧹 Qualité de code

### Avant chaque commit, le pre-commit lance :

| Outil | Cible | Rôle |
|---|---|---|
| `black` | Backend Python | Formate (line-length 100) |
| `ruff` | Backend Python | Lint (E, F, W, I, B, C4, UP) |
| `prettier` | Frontend TS/TSX/CSS/JSON | Formate |
| `trailing-whitespace` | Tous | Nettoie les espaces de fin de ligne |
| `end-of-file-fixer` | Tous | Force le saut de ligne final |
| `detect-private-key` | Tous | Empêche de commit des clés privées |
| `check-merge-conflict` | Tous | Détecte les marqueurs <<<< / >>>> |

### Installation locale

```bash
pip install pre-commit
pre-commit install
pre-commit install --hook-type commit-msg
```

Les hooks tournent ensuite à chaque `git commit` — il n'y a rien à faire.

### Linting manuel

```bash
make lint   # backend + frontend
make test   # backend + frontend
make ci     # raccourci équivalent à la CI GitHub
```

---

## ✅ Definition of Done (DoD)

Avant de marquer une story comme "Done" en Sprint Review :

- [ ] Critères d'acceptation tous satisfaits
- [ ] Code review par ≥ 1 membre de l'équipe
- [ ] Tests pytest / vitest pertinents ajoutés ou mis à jour
- [ ] Lint et tests **verts** en CI
- [ ] Documentation mise à jour (docs/, README, docstrings)
- [ ] Pas de TODO/FIXME laissé sans ticket de suivi
- [ ] Pas de secret commité (utiliser `.env`)

---

## 🆘 Ressources

- [Conventional Commits 1.0](https://www.conventionalcommits.org/fr/v1.0.0/)
- [Cours Agile/Scrum de référence](https://mohamedelafrit.com/teaching/Master_Classe_Agile/cours.html)
- [Documentation détaillée du kit](./docs/)
