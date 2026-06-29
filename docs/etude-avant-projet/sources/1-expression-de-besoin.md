# Expression de besoin initiale — EduTutor IA

## 1. Contexte et enjeux

EduTutor IA est une plateforme web développée par une startup edtech française, conçue pour transformer la manière dont les étudiants du supérieur révisent leurs cours. Le constat de départ est simple : la révision active par auto-évaluation (le *testing effect*) est l'une des méthodes d'apprentissage les plus efficaces selon la recherche en sciences cognitives, mais elle reste sous-exploitée parce que la création de questionnaires pertinents est chronophage. L'étudiant qui veut se tester doit soit trouver des banques de questions génériques rarement alignées sur son cours réel, soit fabriquer ses propres QCM — un effort qu'il fournit rarement.

L'irruption des modèles de langage (LLM) lève ce verrou : il devient possible de générer automatiquement, à partir du support de cours de l'étudiant lui-même, un quiz pertinent et contextualisé en quelques secondes. C'est le pari d'EduTutor IA : l'étudiant dépose son cours (PDF ou texte), la plateforme produit dix questions à choix multiples, l'étudiant se teste, obtient un score et révise ses erreurs.

Le marché est déjà animé par plusieurs acteurs — Wilgo, Leo, Quizlet AI, Khanmigo, Notion AI — majoritairement adossés à des API d'IA propriétaires américaines. La proposition de valeur différenciante d'EduTutor IA se construit sur trois axes :

- **Ancrage pédagogique réel** : des prompts métier pensés avec et pour les enseignants, et non des questions génériques.
- **Conformité RGPD by design** : l'IA tourne en **local** (Ollama / Llama 3.1 8B) par défaut, garantissant la souveraineté des données et l'absence de transfert des cours déposés vers un tiers.
- **Souveraineté et coût maîtrisé** : le moteur local est gratuit à l'usage, sans dépendance facturée à un fournisseur externe.

L'enjeu stratégique dépasse le simple outil de quiz : il s'agit de poser les fondations d'une plateforme d'apprentissage adaptatif crédible auprès des établissements, où la confiance (données, pédagogie) est le véritable actif.

## 2. Problème adressé

| Problème | Conséquence pour l'étudiant |
|---|---|
| La création manuelle de QCM alignés sur son propre cours est trop coûteuse en temps. | L'auto-évaluation, pourtant efficace, est délaissée. |
| Les banques de questions génériques sont mal alignées sur le contenu réellement enseigné. | Révision peu pertinente, faux sentiment de maîtrise. |
| Les outils IA concurrents transfèrent les données vers des serveurs tiers. | Risque RGPD, perte de souveraineté sur des contenus pédagogiques. |
| L'étudiant manque de visibilité sur sa progression et ses erreurs récurrentes. | Pas de pilotage de la révision, effort dispersé. |

En synthèse, EduTutor IA répond au besoin : *« transformer en quelques secondes n'importe quel support de cours en un dispositif d'auto-évaluation pertinent, mesurable et respectueux des données »*.

## 3. Parties prenantes

| Acteur | Rôle | Attentes principales |
|---|---|---|
| Étudiant du supérieur (BTS / Licence / Master) | Utilisateur primaire : dépose ses cours, génère et passe les quiz, suit sa progression. | Rapidité de génération, pertinence des questions, suivi clair de la progression, simplicité d'usage. |
| Enseignant (persona « Mme Lefèvre ») | Cible secondaire émergente : prescripteur, futur utilisateur de prompts métier. | Qualité pédagogique des questions, alignement sur les objectifs d'apprentissage, contrôle du contenu. |
| Administrateur de la plateforme | Configure le fournisseur LLM et l'application, gère les utilisateurs et les données. | Contrôle de la configuration, sécurité, capacité d'exploitation et de maintenance. |
| Startup edtech (porteur du projet) | Sponsor : finance et oriente le produit, vise l'adoption établissements. | Différenciation marché, conformité RGPD, maîtrise des coûts, crédibilité pédagogique. |
| Délégué à la protection des données (DPO) | Garant de la conformité réglementaire. | Souveraineté des données, traitement local, droit à l'effacement effectif. |
| Équipe de développement | Conçoit, livre et maintient la plateforme. | Stack maîtrisée, architecture évolutive, exécution locale reproductible. |

Le diagramme ci-dessous synthétise les acteurs et les principaux cas d'utilisation de la plateforme.

[[DIAGRAMME: cas-utilisation.svg]]
*Figure 1 — Diagramme de cas d'utilisation : acteurs (étudiant, administrateur) et cas d'utilisation du MVP.*

## 4. Besoins fonctionnels (must-have F1–F6)

Les six besoins fonctionnels structurants du MVP sont exprimés ci-dessous comme des besoins métier, priorisés selon la méthode MoSCoW. Ils constituent le socle minimal sans lequel la proposition de valeur ne tient pas : tous sont classés *Must have*.

| Réf. | Besoin métier | Description | Priorité MoSCoW |
|---|---|---|---|
| **F1** | S'authentifier de façon sécurisée | L'étudiant crée un compte par email, valide son adresse (`Profile.email_verified`), se connecte et peut réinitialiser son mot de passe. L'email est l'identifiant unique. | Must have |
| **F2** | Déposer un support de cours | L'étudiant soumet son contenu, soit par fichier **PDF ≤ 5 Mo** (extraction via pypdf), soit par **texte brut ≥ 200 caractères**, comme source de génération. | Must have |
| **F3** | Générer un quiz de 10 QCM | À partir du cours déposé, la plateforme génère via le LLM un quiz de **10 questions**, chacune avec **4 options** et une bonne réponse, en moins de 60 secondes. | Must have |
| **F4** | Passer le quiz et être corrigé | L'étudiant répond aux 10 questions ; la plateforme enregistre les réponses sélectionnées et les confronte aux bonnes réponses. | Must have |
| **F5** | Obtenir un score et le détail | L'étudiant obtient un **score sur 10** et le détail question par question (réponse choisie vs. réponse correcte) pour réviser ses erreurs. | Must have |
| **F6** | Consulter son historique | L'étudiant retrouve la liste de ses quiz passés, avec leurs scores et dates, pour piloter sa progression dans le temps. | Must have |

Au-delà de ce socle, des besoins complémentaires sont identifiés mais classés en priorité inférieure pour les itérations suivantes : tableau de bord de progression et révision ciblée des erreurs (*Should have*), gestion fine du profil et suppression de compte (*Should have*), mode sombre et confort d'usage (*Could have*), back-office d'administration avancé — configuration LLM, gestion des utilisateurs, paramètres applicatifs (*Should have*, partiellement requis pour l'exploitation).

## 5. Besoins non fonctionnels

| Catégorie | Exigence | Critère / cible |
|---|---|---|
| **Performance** | Génération d'un quiz dans un délai acceptable malgré la latence d'un LLM local sur CPU. | Génération complète d'un quiz de 10 QCM en **moins de 60 secondes** sur un poste de 16 Go de RAM. |
| **Sécurité** | Authentification robuste, vérification d'email, gestion des rôles et des sessions. | Mots de passe hachés, vérification d'email obligatoire (paramétrable), comptes activables/désactivables par l'administrateur. |
| **RGPD / Souveraineté** | Traitement des données par défaut **en local**, sans transfert vers un tiers. | IA locale (Ollama) par défaut ; droit à l'effacement (suppression de compte et données) ; minimisation des données collectées. |
| **Ergonomie** | Interface claire, parcours fluide, accessibilité du suivi de progression. | Parcours dépôt → quiz → score en quelques clics ; mode sombre disponible ; retours visuels explicites. |
| **Portabilité** | Déploiement reproductible sur n'importe quel poste de développement. | Lancement intégral par `docker compose up` (conteneurs postgres, ollama, backend, frontend) ; aucune dépendance hors conteneurs. |
| **Maintenabilité / Évolutivité** | Architecture ouverte au changement de fournisseur d'IA. | Factory LLM multi-fournisseurs ; tout changement de fournisseur tracé par un **ADR** ; documentation API via Swagger. |

## 6. Périmètre

### Dans le périmètre (MVP)

- Authentification par email avec vérification et réinitialisation de mot de passe.
- Dépôt de cours par PDF (≤ 5 Mo) ou texte (≥ 200 caractères).
- Génération d'un quiz de 10 QCM à 4 options via LLM local (Ollama / Llama 3.1 8B).
- Passage du quiz, correction automatique, score sur 10 et détail des réponses.
- Historique des quiz par utilisateur.
- Gestion du profil utilisateur (modification, suppression du compte).
- Back-office d'administration : configuration du fournisseur LLM et de l'application, gestion des utilisateurs et des données.
- Exécution conteneurisée locale via Docker Compose.

### Hors périmètre (MVP)

- Génération de questions ouvertes ou d'autres formats que le QCM à 4 options.
- Quiz collaboratifs, classes, partage entre étudiants ou affectation par un enseignant.
- Application mobile native (iOS / Android).
- Module enseignant complet (création de prompts métier, suivi de cohorte) — la cible enseignant reste émergente.
- Apprentissage adaptatif avancé (répétition espacée, recommandations personnalisées).
- Intégration avec des LMS / ENT externes.
- Recours par défaut à des fournisseurs d'IA payants (OpenAI, Anthropic) : disponibles en option, non activés par défaut.

## 7. Contraintes

| Type | Contrainte |
|---|---|
| **Technique — matériel** | Cible d'exécution : poste laptop doté de **16 Go de RAM**, sans GPU dédié garanti ; la latence d'un LLM local sur CPU est un enjeu de performance réel. |
| **Technique — stack** | Backend **Django 5 + DRF** (Python 3.11+) ; frontend **React 18 + Vite + TypeScript** ; base **PostgreSQL 16** ; IA via **Ollama (Llama 3.1 8B)** en local par défaut. |
| **Technique — déploiement** | Lancement par un unique `docker compose up` (conteneurs `apocalipssi-2026-postgres`, `-ollama`, `-backend`, `-frontend`). |
| **Technique — architecture IA** | Architecture multi-fournisseurs (Ollama, Gemini, Groq, Cerebras, Mistral, OpenRouter, OpenAI, Anthropic, mock) ; tout changement de fournisseur formalisé par un **ADR**. |
| **Réglementaire** | Conformité RGPD by design ; traitement local des données ; droit à l'effacement. |
| **Délais** | Livraison d'un MVP couvrant les besoins F1–F6 dans le cadre de la durée du projet (semaine immersive). |
| **Budget** | Maîtrise des coûts : moteur d'IA local gratuit par défaut ; recours aux API externes en free tier ou en option premium uniquement. |
| **Ouverture** | Dépôt de code hébergé sur un **GitHub public** : exigence de propreté, de documentation et de reproductibilité. |

## 8. Objectifs SMART

| # | Objectif SMART |
|---|---|
| **O1** | **Livrer le MVP F1–F6 fonctionnel** d'ici la fin de la semaine immersive : un utilisateur peut s'inscrire, déposer un cours, générer un quiz de 10 QCM, le passer et consulter son score et son historique. |
| **O2** | **Générer un quiz de 10 QCM en moins de 60 secondes** sur un poste de 16 Go de RAM avec le moteur Ollama local, dans au moins 90 % des dépôts conformes (PDF ≤ 5 Mo ou texte ≥ 200 caractères). |
| **O3** | **Garantir le traitement 100 % local des cours** par défaut (aucun transfert vers un fournisseur tiers sans activation explicite), démontrable par la configuration par défaut du conteneur `ollama`. |
| **O4** | **Assurer un déploiement reproductible** : l'application complète démarre via une unique commande `docker compose up`, sans étape manuelle supplémentaire, sur un poste de développement standard. |
| **O5** | **Sécuriser l'accès** : 100 % des comptes créés passent par une vérification d'email (lorsque l'option est activée) et toute donnée utilisateur est effaçable sur demande, conformément au RGPD. |
| **O6** | **Maintenir la traçabilité des choix techniques** : tout changement de fournisseur LLM est documenté par un ADR versionné dans le dépôt GitHub public. |
