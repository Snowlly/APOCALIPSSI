# 07 — Bonnes pratiques

Vocabulaire agile mobilisé pendant la semaine, avec liens directs vers le
[cours Agile/Scrum de référence](https://mohamedelafrit.com/teaching/Master_Classe_Agile/cours.html).

---

## 📐 ADR — Architecture Decision Record

Document court (≤ 1 page) qui justifie une décision technique structurante.
Demandé en **perturbation J2**.

### Template

```markdown
# ADR-0001 : Bascule de Llama 3.1 8B vers Llama 3.2 3B

**Statut** : ✅ Accepté
**Date** : 2026-XX-XX
**Auteurs** : Alice, Bob

## Contexte

Notre LLM actuel (Llama 3.1 8B) prend en moyenne 45 secondes pour générer
un quiz. Le retour beta-test de mardi matin est sans appel : « inutilisable ».

## Options envisagées

| Option | Latence | Qualité | RAM | Effort |
|---|---|---|---|---|
| A — Garder Llama 3.1 8B + UX (spinner) | 45s | ★★★★ | 5 Go | Faible |
| B — Bascule Llama 3.2 3B | 12s | ★★★ | 2 Go | Moyen |
| C — Bascule Phi-3 mini | 15s | ★★★ | 2 Go | Moyen |
| D — HF Inference API | 5s | ★★★★ | 0 | Élevé + dépendance externe |

## Décision

Option B — Llama 3.2 3B.

## Justification

- Latence acceptable (< 15s = règle métier discutée en daily)
- Qualité suffisante après tests sur 5 cours différents
- Reste 100% local (cohérent avec la contrainte « pas d'API payante »)
- Effort de bascule < 1h (changement env var + pull modèle)

## Conséquences

✅ Positives :
- UX nettement améliorée
- Moins de RAM consommée → laptops 8 Go OK

⚠️ Négatives :
- Qualité légèrement inférieure → ajout d'un test adversarial pour valider
  que les questions restent factuelles
- Story "questions ouvertes" devient plus risquée (3B moins capable)

🔍 À surveiller :
- Taux de questions hors-sujet (mesurer sur 30 quizz)
- Retours beta-testeurs sous 48h
```

> 📚 Référence : [Architecture Decision Records de Michael Nygard](https://github.com/joelparkerhenderson/architecture-decision-record)

---

## 🪦 Post-mortem blameless

Document qui analyse un incident **sans chercher de coupable**. Demandé
en **perturbation J4**.

### Template

```markdown
# Post-mortem — Questions factuellement fausses signalées par Mme Lefèvre

**Date** : 2026-XX-XX
**Sévérité** : haute (utilisateur clé en colère)
**Auteurs** : Alice (rédaction), équipe complète (review)

## What happened

Le 2026-XX-XX à 16h30, Mme Sophie Lefèvre (persona enseignante intégrée J1)
a signalé que 4 questions sur 10 d'un quiz généré pour son cours d'économie
étaient factuellement fausses. L'une affirmait que « l'inflation est mesurée
par le PIB ».

28 étudiants ont révisé sur ces erreurs.

## Why (analyse 5 pourquoi)

1. **Pourquoi des questions fausses ?** Le LLM (Llama 3.1 8B) a halluciné.
2. **Pourquoi le LLM hallucine ?** Le modèle n'a pas accès au texte source au
   moment de générer (il génère depuis ses poids).
3. **Pourquoi pas d'ancrage au texte source ?** Notre prompt n'oblige pas le
   modèle à citer des passages.
4. **Pourquoi pas de vérification ?** Aucune étape de validation factuelle
   post-LLM.
5. **Pourquoi pas de feedback utilisateur ?** Mme Lefèvre a dû nous écrire
   par email — pas de bouton "signaler" dans l'app.

→ Cause racine : **manque de boucle utilisateur intégrée + manque d'ancrage**.

## What we're changing

Actions court terme (24h) :
- [x] Ajouter un bouton ⚠️ "signaler" sur chaque question
- [x] Persister les signalements en base
- [x] Ajout d'un check dans le prompt : "Ne génère que des questions qui ont
      une réponse trouvable dans le texte fourni"

Actions moyen terme (post-semaine) :
- [ ] Intégrer un RAG simple : retrouver le passage source de chaque question
- [ ] Dashboard admin pour visualiser les signalements
- [ ] Métrique "% de questions signalées par cours"

## What went well

- Réponse rapide à Mme Lefèvre (~3h)
- Communication transparente sur les causes
- Action concrète déployée le jour même

## What we'd do differently

- Intégrer un mécanisme de feedback DÈS la Release 1, pas en Release 2
- Tester la génération sur de vrais cours (pas seulement Lorem ipsum)
```

> 📚 Référence : [Google SRE — Blameless Post-Mortem Culture](https://sre.google/sre-book/postmortem-culture/)

---

## 🎯 INVEST — Critères d'une bonne user story

Une story doit être :

| Lettre | Signification | Question test |
|---|---|---|
| **I**ndépendante | Pas de dépendance avec une autre story | "Puis-je livrer cette story sans en attendre une autre ?" |
| **N**égociable | Le scope est discutable | "Le PO accepte-t-il de discuter du périmètre ?" |
| **V**aluable | Apporte de la valeur à un utilisateur | "Si je livre ça en l'état, qui en profite ?" |
| **E**stimable | On peut chiffrer l'effort | "L'équipe est-elle capable de mettre des points dessus ?" |
| **S**mall | Tient dans un sprint | "Petite ? Si > 5 points, à splitter." |
| **T**estable | Critères d'acceptation clairs | "Comment je sais quand c'est fini ?" |

---

## 🎪 MoSCoW — Priorisation

À chaque arbitrage scope, classer en :

- **M**ust have — sans ça, le produit n'a pas de sens
- **S**hould have — important, mais on peut s'en passer en cas de crise
- **C**ould have — bonus appréciable
- **W**on't have (this time) — décision explicite de ne PAS faire

> ⚠️ **Justifier par écrit** chaque classement, sinon ce n'est qu'un vœu.

---

## ✅ DoR — Definition of Ready

Avant qu'une story entre dans un Sprint Planning :

- [ ] Story rédigée au format INVEST
- [ ] Critères d'acceptation explicites et testables
- [ ] Dépendances identifiées (et non-bloquantes)
- [ ] Estimée par l'équipe (points / heures)
- [ ] Priorité MoSCoW assignée et justifiée
- [ ] Pas de question ouverte côté PO

---

## ✅ DoD — Definition of Done

Pour considérer une story terminée :

- [ ] Tous les critères d'acceptation satisfaits
- [ ] Code reviewé par ≥ 1 membre de l'équipe
- [ ] Tests pertinents ajoutés (pytest / vitest)
- [ ] Lint + tests **verts** en CI
- [ ] Documentation à jour (docs/, docstrings, README si besoin)
- [ ] Pas de TODO/FIXME sans ticket de suivi
- [ ] Démontrée et acceptée par le PO en Sprint Review

---

## 📜 Conventional Commits

Format imposé : `<type>(<scope>): <description>`

Cf [CONTRIBUTING.md](../CONTRIBUTING.md) pour le détail.

---

## 🆘 Ressources

- [Cours Agile/Scrum Mohamed EL AFRIT](https://mohamedelafrit.com/teaching/Master_Classe_Agile/cours.html)
- [Agile Manifesto](https://agilemanifesto.org/iso/fr/manifesto.html)
- [Scrum Guide 2020 (officiel)](https://scrumguides.org/scrum-guide.html)
- [Conventional Commits 1.0](https://www.conventionalcommits.org/fr/v1.0.0/)
- [Architecture Decision Records](https://adr.github.io/)
- [Google SRE Book — Postmortems](https://sre.google/sre-book/postmortem-culture/)

---

## 👉 Retour

- [README](../README.md) — Vue d'ensemble du kit
- [00-getting-started](./00-getting-started.md) — Setup
