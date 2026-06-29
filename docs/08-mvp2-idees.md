# 08 — Catalogue d'idées MVP2

> **MVP2 = la prochaine itération après le MVP.** Une fois le cœur fonctionnel
> (générer un quiz à partir d'un cours, le passer, voir son score), voici un
> catalogue d'idées pour aller plus loin. **Ce n'est pas une to-do list à faire
> en entier** : c'est un menu dans lequel votre équipe **choisit et priorise**
> (backlog Scrum) selon la valeur apportée et le temps disponible.

Pour chaque idée : une **description**, sa **valeur**, une **complexité** estimée
(🟢 faible · 🟡 moyenne · 🔴 élevée) et des **pistes techniques**.

---

## ✅ Déjà implémenté dans le kit (exemples de référence)

Trois fonctionnalités sont **déjà codées** dans le kit pour vous servir de
modèle — lisez leur code, inspirez-vous-en, améliorez-les.

### 1. Tableau de bord de progression 🟢
- **Quoi** : page `/dashboard` avec KPIs (quiz passés, score moyen, meilleur
  score, précision) et un graphique de progression des scores.
- **Valeur** : l'apprenant visualise ses progrès → motivation.
- **Où regarder** :
  - Backend : `quizzes/views.py` → `StatsView` (agrégations ORM : `Avg`, `Count`, `Max`).
  - Frontend : `pages/DashboardPage.tsx` (graphique en barres « maison », sans librairie).
- **Pour aller plus loin** : remplacer le graphique par `recharts`, filtrer par
  période, comparer à une moyenne de promo.

### 2. Révision des erreurs 🟢
- **Quoi** : page `/review` qui liste les questions ratées (votre réponse en
  rouge, la bonne en vert).
- **Valeur** : on apprend surtout de ses erreurs.
- **Où regarder** :
  - Backend : champ `Question.selected_index` (dernière réponse) + `MistakesView`.
  - Frontend : `pages/ReviewMistakesPage.tsx`.
- **Pour aller plus loin** : refaire un quiz **uniquement** avec ses erreurs,
  répétition espacée (revoir une erreur à J+1, J+3, J+7).

### 3. Mode sombre 🟢
- **Quoi** : bascule clair/sombre dans le header, mémorisée (localStorage) et
  suivant la préférence système au premier chargement.
- **Valeur** : confort visuel, accessibilité.
- **Où regarder** :
  - `contexts/ThemeContext.tsx`, `tailwind.config.js` (`darkMode: 'class'`),
    `index.css` (rétrofit des classes neutres en sombre).

---

## 🎓 Apprentissage & pédagogie

### 4. Niveaux de difficulté 🟡
- **Quoi** : générer le quiz en « facile / moyen / difficile ».
- **Pistes** : adapter le prompt LLM (`llm/services/quiz_prompt.py`) selon le niveau choisi.

### 5. Explication des réponses 🟡
- **Quoi** : pour chaque question, une explication « pourquoi cette réponse ».
- **Valeur** : transforme le quiz en outil d'apprentissage, pas juste d'évaluation.
- **Pistes** : ajouter un champ `explanation` à `Question` + demander l'explication au LLM.

### 6. Types de questions variés 🔴
- **Quoi** : vrai/faux, réponse courte, association, au-delà du QCM.
- **Pistes** : généraliser le modèle `Question` (champ `type`), adapter la correction.

### 7. Fiches de révision / résumé automatique 🟡
- **Quoi** : générer un résumé du cours en plus du quiz (clin d'œil au projet
  2025 « ComplySummarize »).
- **Pistes** : second appel LLM avec un prompt de synthèse.

---

## 🎮 Engagement & gamification

### 8. Badges & récompenses 🟡
- **Quoi** : badges « 5 quiz réussis », « sans-faute », « série de 3 jours ».
- **Pistes** : modèle `Badge` + règles d'attribution à la fin d'un quiz.

### 9. Séries (streaks) & objectifs 🟢
- **Quoi** : « X jours d'affilée », objectif hebdomadaire de quiz.
- **Pistes** : calcul à partir des dates de `Quiz.created_at`.

### 10. Classement (leaderboard) 🟡
- **Quoi** : classement anonyme/pseudonymisé par score moyen.
- **⚠️ Attention RGPD** : ne pas exposer d'emails — utiliser un pseudo.

---

## 👤 Personnalisation & compte

### 11. Avatar & pseudo 🟢
- **Quoi** : photo de profil (upload) et pseudonyme affiché.
- **Pistes** : champ image sur `Profile`, stockage média Django.

### 12. Export RGPD de mes données 🟡  *(placeholder déjà présent dans le profil)*
- **Quoi** : bouton « Exporter mes données » → fichier JSON/PDF.
- **Valeur** : droit à la portabilité (RGPD). **Bon sujet J3-bis.**
- **Pistes** : endpoint qui sérialise User + quiz + réponses.

### 13. Multilingue (i18n) 🔴
- **Quoi** : interface FR/EN, voire génération de quiz dans la langue choisie.
- **Pistes** : `react-i18next` côté front ; langue dans le prompt LLM.

---

## 🤝 Collaboration & contenu

### 14. Partage de quiz 🟡
- **Quoi** : partager un quiz par lien, le rendre public/privé.
- **Pistes** : champ `is_public` + `share_token` sur `Quiz`.

### 15. Catégories / matières & recherche 🟢
- **Quoi** : ranger les quiz par matière, rechercher dans l'historique.
- **Pistes** : champ `subject` + filtre côté `QuizListView`.

### 16. Import multi-format 🔴
- **Quoi** : accepter Word, PowerPoint, pages web en plus du PDF.
- **Pistes** : étendre l'extraction de texte côté backend.

---

## 🔔 Notifications & infra

### 17. Rappels par email 🟡
- **Quoi** : « ça fait 3 jours, révisez ! » (réutilise Brevo, déjà branché au Lot 3).
- **Pistes** : tâche planifiée (cron) + `accounts/emails.py`.

### 18. Application installable (PWA) 🟡
- **Quoi** : installer EduTutor sur mobile, usage hors-ligne partiel.
- **Pistes** : manifest + service worker (plugin Vite PWA).

### 19. Accessibilité (a11y) 🟢
- **Quoi** : navigation clavier, contrastes, lecteurs d'écran, `aria-*`.
- **Valeur** : inclusif **et** souvent attendu juridiquement.

---

## 🧭 Comment choisir ? (méthode Scrum)

1. **Valeur d'abord** : qu'est-ce qui aide le plus l'apprenant ?
2. **Effort ensuite** : visez quelques 🟢/🟡 plutôt qu'un seul 🔴 risqué.
3. **Matrice Valeur / Effort** : priorisez le « beaucoup de valeur, peu d'effort ».
4. **Mettez-le au backlog**, découpez en user stories, estimez, engagez-vous sur
   un périmètre réaliste pour le sprint.

> 💡 Rappel APOCAL'IPSSI : ce qui est évalué, ce n'est pas le nombre de
> fonctionnalités, mais **votre réaction agile** (priorisation, adaptation aux
> perturbations, qualité de l'incrément livré).

Voir aussi le cours :
[Master Classe Agile](https://mohamedelafrit.com/teaching/Master_Classe_Agile/cours.html).
