# 10 — Gestion de projet sur GitHub

> 🎯 Pendant APOCAL'IPSSI, **tout passe par GitHub** : code, documents ET suivi de
> projet. Pas de GitLab ni d'autre outil de versioning. Teams sert uniquement à la
> communication / visio. Le dépôt est **public** et **noté** (contenu *et* fréquence
> des commits **par membre**) — voir la [grille d'évaluation](https://apocalipssi26.elafrit.com/pages/evaluation.php).

## 1. Le dépôt

- **Forkez** le kit dans le compte de votre équipe, en **public**.
- Invitez tous les membres + le jury (animateur) comme collaborateurs dès J1.
- Travaillez à plusieurs : chacun commit **sous son propre compte**.

## 2. Workflow Git (branches + Pull Requests)

```
main ← branche stable (toujours fonctionnelle, taguée pour les releases)
  └── feat/generation-quiz      ← une branche par fonctionnalité
  └── fix/login-email           ← une branche par correctif
```

1. Créez une branche depuis `main` : `git switch -c feat/ma-fonctionnalite`.
2. Committez petit et souvent (voir §4).
3. Ouvrez une **Pull Request** vers `main` (le modèle se remplit automatiquement).
4. **Faites-vous relire** par un coéquipier, puis fusionnez.
5. Évitez de pousser directement sur `main` (activez la protection de branche si possible).

## 3. Issues & templates

Le kit fournit des **modèles d'issues** (onglet *Issues → New issue*) :

| Modèle | Pour quoi |
|---|---|
| 📝 **User story** | Besoin au format INVEST + critères d'acceptation + DoR/DoD |
| 🐛 **Bug** | Dysfonctionnement reproductible |
| 🌀 **Tâche perturbation** | Tracer une décision/livrable lié à une perturbation (J1, J2, J3, J3-bis, J4 — 5 perturbations) |

Et un **modèle de Pull Request** (checklist Definition of Done).

### Labels conseillés
`user story` · `bug` · `perturbation` · `must` · `should` · `could` ·
`sprint-1` … `sprint-7` · `blocked` · `in review`.

## 4. Commits : ils racontent votre projet (et sont notés)

- **Conventional Commits** : `feat(quiz): génère 10 QCM via Ollama`, `fix(auth): …`, `docs: …`, `test: …`.
- **Petits et fréquents** : un commit = une intention claire. Évitez le « gros commit » de fin de journée.
- **Répartis sur tous les membres** : chacun doit avoir un historique de contributions **régulier et significatif**.
- Messages **en français**, à l'impératif, explicites (le *quoi* et le *pourquoi*).

## 5. Tableau de bord — GitHub Projects

Créez un **Project** (onglet *Projects → New project → Board*) avec les colonnes :

```
📥 Backlog → 🎯 Sprint en cours → 🔨 En cours → 👀 En revue → ✅ Terminé
```

- Ajoutez vos issues au board, glissez-les de colonne en colonne.
- Une issue par user story / tâche / perturbation ; assignez un responsable.
- En début de sprint, tirez du Backlog vers « Sprint en cours » à **70 % de votre capacité**.
- En revue de sprint, ne déplacez en « Terminé » que ce qui respecte la **Definition of Done**.

## 6. Rythme type d'une journée

1. **Daily** (10 min) : qui fait quoi, quels blocages.
2. Travail sur les branches + commits réguliers.
3. Quand une perturbation tombe : créez une **issue « perturbation »**, décidez (MoSCoW / ADR), repriorisez le board.
4. Fin de journée : PR relues et fusionnées, board à jour.

## 👉 Suite
- [05-ci-cd.md](./05-ci-cd.md) — CI GitHub Actions & Conventional Commits
- [07-bonnes-pratiques.md](./07-bonnes-pratiques.md) — INVEST, MoSCoW, ADR, post-mortem
