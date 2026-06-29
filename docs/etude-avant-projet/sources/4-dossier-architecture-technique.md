# Dossier d'architecture technique — EduTutor IA

## 1. Objectifs et principes d'architecture

EduTutor IA est une plateforme web permettant à un étudiant du supérieur de générer des quiz QCM à partir de ses propres cours (PDF ou texte), de les passer, d'obtenir un score sur 10 et de suivre sa progression. Le présent dossier consolide les décisions d'architecture héritées de la première équipe et constitue la référence technique pour toute évolution ultérieure.

L'architecture poursuit cinq objectifs structurants :

- **Souveraineté et conformité RGPD by design** : l'inférence IA s'exécute par défaut en local (Ollama / Llama 3.1 8B), sans transfert de données vers un tiers. Les cours déposés et les quiz générés ne quittent jamais l'infrastructure de l'établissement.
- **Reproductibilité** : l'ensemble du système démarre par un unique `docker compose up`, sur un poste de développement standard (laptop 16 Go RAM), sans installation manuelle de dépendances.
- **Découplage frontend / backend** : une API REST stricte (DRF) sépare l'application React de la logique métier Django, autorisant des évolutions indépendantes.
- **Abstraction du fournisseur LLM** : la génération de quiz repose sur une *factory* multi-fournisseurs, isolant le cœur métier des spécificités de chaque moteur d'inférence.
- **Performance maîtrisée** : un objectif de génération d'un quiz en moins de 60 secondes encadre les choix techniques, la latence CPU d'un LLM local étant un enjeu réel.

Les principes directeurs sont la **simplicité** (un MVP F1-F6 must-have avant toute sophistication), la **traçabilité des décisions** (tout changement de fournisseur LLM passe par un ADR — Architecture Decision Record) et la **défense en profondeur** (validation des entrées, durcissement contre l'injection de prompt, isolation des conteneurs).

## 2. Vue de contexte

La vue de contexte (niveau 1 du modèle C4) situe EduTutor IA parmi ses acteurs et systèmes externes. Deux acteurs humains interagissent avec la plateforme : l'**étudiant** (persona primaire, qui révise ses cours) et l'**administrateur** (qui configure le fournisseur LLM et l'application). Une persona secondaire émergente, l'**enseignant** (« Mme Lefèvre »), oriente la conception des prompts métier mais ne dispose pas encore d'interface dédiée.

[[DIAGRAMME: c4-contexte.svg]]
*Figure 1 — Vue de contexte C4 : acteurs et systèmes externes d'EduTutor IA.*

Les systèmes externes mobilisés sont le fournisseur d'inférence (Ollama local par défaut, ou un fournisseur cloud en option : Gemini, Groq, Cerebras, Mistral, OpenRouter, OpenAI, Anthropic) et le service d'envoi d'emails transactionnels (Brevo en SMTP, ou backend console en développement). La proposition de valeur — ancrage pédagogique, prompts pensés pour les enseignants, données souveraines — se distingue des concurrents directs (Wilgo, Leo, Quizlet AI, Khanmigo, Notion AI) par le choix par défaut d'une IA locale.

## 3. Vue conteneurs

La vue conteneurs (niveau 2 C4) décrit les unités déployables et leurs protocoles d'échange. Le système est composé de quatre conteneurs orchestrés par Docker Compose.

[[DIAGRAMME: c4-conteneurs.svg]]
*Figure 2 — Vue conteneurs C4 : frontend, backend, base de données et moteur d'inférence.*

| Conteneur | Rôle | Technologie | Communication |
|-----------|------|-------------|---------------|
| `apocalipssi-2026-frontend` | SPA servie au navigateur | React 18 + Vite + TypeScript | HTTP/REST vers le backend |
| `apocalipssi-2026-backend` | API métier, authentification, orchestration LLM | Django 5 + DRF (Python 3.11+) | HTTP vers Ollama, SQL vers PostgreSQL, SMTP vers Brevo |
| `apocalipssi-2026-postgres` | Persistance des données | PostgreSQL 16 | SQL (réseau interne) |
| `apocalipssi-2026-ollama` | Inférence LLM locale | Ollama (Llama 3.1 8B) | HTTP (API Ollama) |

Le frontend ne communique qu'avec le backend ; il ne dialogue jamais directement avec la base ni avec le moteur d'inférence. Le backend est le seul point d'orchestration : il valide les requêtes, applique les règles métier, appelle le LLM via la *factory*, et persiste les résultats.

## 4. Cas d'utilisation

Les cas d'utilisation se répartissent entre deux acteurs : l'étudiant et l'administrateur.

[[DIAGRAMME: cas-utilisation.svg]]
*Figure 3 — Diagramme des cas d'utilisation des deux acteurs.*

| Acteur | Cas d'utilisation |
|--------|-------------------|
| Étudiant | S'inscrire / se connecter par email ; valider son email ; réinitialiser son mot de passe ; gérer son profil (modifier, supprimer le compte) ; déposer un cours (PDF ≤ 5 Mo ou texte ≥ 200 caractères) ; générer un quiz de 10 QCM ; passer le quiz ; consulter son score /10 et le détail ; consulter l'historique ; voir le tableau de bord de progression ; réviser ses erreurs ; basculer en mode sombre |
| Administrateur | Configurer le fournisseur LLM et l'application ; gérer les utilisateurs (activer/désactiver, rôle, supprimer) ; insérer / réinitialiser des données |

Le périmètre MVP must-have couvre les fonctionnalités F1 à F6 : authentification, saisie de cours, génération de 10 QCM, correction, score et historique.

## 5. Vues dynamiques — séquences

Trois scénarios critiques sont détaillés par des diagrammes de séquence.

### 5.1 Authentification par email

L'authentification repose sur l'email comme identifiant unique de l'utilisateur Django. À l'inscription, un `Profile` est créé (OneToOne) avec `email_verified = false` ; un email de validation est envoyé via Brevo. La connexion délivre un token d'authentification que le frontend joint aux requêtes ultérieures.

[[DIAGRAMME: sequence-authentification.svg]]
*Figure 4 — Séquence d'authentification : inscription, validation d'email et connexion.*

### 5.2 Génération d'un quiz

L'étudiant dépose un cours ; le backend extrait le texte (pypdf pour un PDF), construit le prompt métier, appelle le fournisseur LLM via la *factory*, parse la réponse en 10 objets `Question` et persiste le `Quiz`. L'objectif de latence est inférieur à 60 secondes.

[[DIAGRAMME: sequence-generation-quiz.svg]]
*Figure 5 — Séquence de génération d'un quiz à partir d'un cours.*

### 5.3 Soumission et correction

L'étudiant renseigne, pour chaque question, un `selected_index`. Le backend compare aux `correct_index`, calcule le score sur 10, le persiste sur le `Quiz` et renvoie le détail question par question pour la révision des erreurs.

[[DIAGRAMME: sequence-soumission-correction.svg]]
*Figure 6 — Séquence de soumission et de correction d'un quiz.*

## 6. Modèle de données

Le modèle de données s'organise autour de l'utilisateur, de ses quiz et des questions associées, complété par deux singletons de configuration.

[[DIAGRAMME: classes-modele-donnees.svg]]
*Figure 7 — Diagramme de classes du modèle de données.*

[[DIAGRAMME: mcd-base-donnees.svg]]
*Figure 8 — Modèle conceptuel de données (MCD) de la base PostgreSQL.*

| Entité | Champ | Type / contrainte | Description |
|--------|-------|-------------------|-------------|
| **User** (Django) | email | unique, identifiant | Identifiant de connexion |
| | password | hash | Mot de passe haché |
| | is_active / is_staff | booléen | Statut et rôle |
| **Profile** | user | OneToOne → User | Profil étendu |
| | email_verified | booléen | Email validé ou non |
| | created_at | datetime | Date de création |
| **Quiz** | user | FK → User | Propriétaire du quiz |
| | title | texte | Titre du quiz |
| | source_text | texte | Texte source du cours |
| | score | entier /10, nullable | Score obtenu (null avant passage) |
| | created_at / updated_at | datetime | Horodatage |
| **Question** | quiz | FK → Quiz | Quiz parent |
| | index | entier 1..10 | Numéro de la question |
| | prompt | texte | Énoncé de la question |
| | options | JSON (4 chaînes) | Les quatre propositions |
| | correct_index | entier 0..3 | Indice de la bonne réponse |
| | selected_index | entier 0..3, nullable | Réponse de l'étudiant |
| **LLMConfig** | (singleton) | — | Configuration du fournisseur |
| | backend / model | texte | Fournisseur et modèle actifs |
| | api_keys | JSON | Clés par fournisseur |
| | ollama_host / timeout | texte / entier | Hôte Ollama et délai |
| **SiteConfig** | (singleton) | — | Configuration applicative |
| | app_name | texte | Nom de l'application |
| | allow_signups | booléen | Inscriptions ouvertes ou non |
| | require_email_verification | booléen | Validation d'email obligatoire |
| | bannière | texte | Message d'information global |

Les cardinalités principales : un `User` possède un `Profile` (1:1) et plusieurs `Quiz` (1:N) ; un `Quiz` regroupe exactement 10 `Question` (1:N). `LLMConfig` et `SiteConfig` sont des singletons (une seule ligne en base).

## 7. Vue composants

À l'intérieur du conteneur backend, la logique est découpée en quatre applications Django, chacune responsable d'un domaine fonctionnel cohérent.

[[DIAGRAMME: composants.svg]]
*Figure 9 — Vue des composants internes du backend Django.*

| Application | Responsabilité | Modèles |
|-------------|----------------|---------|
| `accounts` | Authentification par email, profils, validation d'email, réinitialisation de mot de passe | `Profile` (+ `User` Django) |
| `quizzes` | Cycle de vie des quiz : génération, passage, correction, historique | `Quiz`, `Question` |
| `llm` | Configuration et *factory* multi-fournisseurs, construction des prompts, parsing | `LLMConfig` |
| `administration` | Back-office : configuration applicative, gestion des utilisateurs et des données | `SiteConfig` |

L'application `quizzes` dépend de `llm` pour la génération mais ne connaît aucun détail du fournisseur sous-jacent : elle invoque une interface unique fournie par la *factory*. La documentation de l'API est générée automatiquement (Swagger via drf-spectacular).

## 8. Vue de déploiement

Le déploiement cible est un poste de développement unique (laptop 16 Go RAM), où Docker Compose orchestre les quatre conteneurs sur un réseau interne partagé. Seuls les ports du frontend et du backend sont exposés à l'hôte ; PostgreSQL et Ollama restent confinés au réseau Docker.

[[DIAGRAMME: deploiement-docker.svg]]
*Figure 10 — Vue de déploiement Docker Compose sur poste de développement.*

La contrainte de 16 Go de RAM conditionne le choix de Llama 3.1 8B, modèle suffisamment compact pour tenir en mémoire aux côtés des autres conteneurs tout en restant pertinent pour la génération de QCM. L'inférence s'exécute sur CPU par défaut, d'où l'enjeu de latence encadré par l'objectif de 60 secondes.

## 9. Flux d'activité — génération d'un quiz

Le flux de génération illustre les points de décision et de validation appliqués entre le dépôt du cours et la persistance du quiz.

[[DIAGRAMME: activite-generation-quiz.svg]]
*Figure 11 — Flux d'activité de la génération d'un quiz.*

Les contrôles clés sont : validation du dépôt (PDF ≤ 5 Mo **ou** texte ≥ 200 caractères) ; extraction du texte par pypdf si nécessaire ; construction du prompt métier ; appel LLM avec gestion du timeout ; validation structurelle de la réponse (10 questions, 4 options, `correct_index` valide) ; persistance. En cas de réponse malformée ou de dépassement de délai, une stratégie de repli renvoie une erreur exploitable à l'utilisateur plutôt qu'un quiz incomplet.

## 10. Choix technologiques justifiés

| Couche | Technologie retenue | Justification | Alternative écartée |
|--------|---------------------|---------------|---------------------|
| Backend | Django 5 + DRF (Python 3.11+) | Écosystème mature, admin intégré, ORM robuste, sérialisation REST native | FastAPI (moins d'outillage intégré) |
| Frontend | React 18 + Vite + TypeScript | Typage fort, build rapide (Vite), large écosystème | Vue (compétences équipe orientées React) |
| Base de données | PostgreSQL 16 | Robustesse, support JSON natif (champ `options`), transactions ACID | SQLite (insuffisant en concurrence) |
| Conteneurisation | Docker + Docker Compose | Reproductibilité, démarrage par une commande | Installation manuelle (non reproductible) |
| Inférence IA | Ollama / Llama 3.1 8B (local) | Gratuit, souverain, RGPD by design, tient en 16 Go | API cloud par défaut (fuite de données, coût) |
| Extraction PDF | pypdf | Pure Python, sans dépendance système lourde | Outils OCR (surdimensionnés pour PDF texte) |
| Emails | Brevo (SMTP) / console en dev | Transactionnel fiable, bascule console en local | Service propriétaire opaque |
| Documentation API | Swagger (drf-spectacular) | Génération automatique depuis le schéma DRF | Documentation manuelle (dérive) |

## 11. Sécurité et RGPD

La conformité RGPD est traitée *by design*, ancrée dans les choix d'architecture plutôt qu'ajoutée a posteriori :

- **Données souveraines** : l'inférence par défaut sur Ollama local garantit que les cours déposés et les quiz générés ne sont transmis à aucun tiers. Le recours à un fournisseur cloud est un choix explicite, documenté par ADR.
- **Authentification** : identifiant = email, mots de passe hachés par Django, validation d'email obligatoire pilotée par `Profile.email_verified` et `SiteConfig.require_email_verification`. Les requêtes API sont authentifiées par token.
- **Minimisation et droit à l'effacement** : l'étudiant peut modifier son profil et supprimer son compte ; la suppression entraîne celle des quiz et questions associés (cascade).
- **Défense contre l'injection de prompt** : le texte du cours est traité comme une donnée non fiable. Le prompt métier isole l'entrée utilisateur, des instructions système contraignent strictement le format de sortie attendu, et la réponse du LLM est validée structurellement (10 questions, 4 options, indices valides) avant toute persistance. Une réponse non conforme est rejetée plutôt qu'enregistrée.
- **Isolation** : PostgreSQL et Ollama ne sont pas exposés hors du réseau Docker interne ; seuls le frontend et le backend ouvrent des ports.

## 12. Architecture multi-fournisseurs LLM et stratégie ADR

Le cœur du découplage IA est une *factory* (application `llm`) qui instancie le client d'inférence à partir de `LLMConfig`. Le code métier de `quizzes` ne dépend que d'une interface unique de génération ; le fournisseur effectif est résolu à l'exécution.

| Catégorie | Fournisseurs | Usage |
|-----------|-------------|-------|
| Local (défaut) | Ollama (Llama 3.1 8B) | Production souveraine, RGPD, gratuit |
| Free tier | Gemini, Groq, Cerebras, Mistral, OpenRouter | Accélération / repli, à coût nul |
| Premium | OpenAI, Anthropic | Qualité supérieure, payant |
| Mock | — | Tests et développement déterministes |

Tout changement de fournisseur est une décision d'architecture : il est consigné dans un **ADR** (Architecture Decision Record) documentant le contexte, les options envisagées, la décision et ses conséquences (notamment l'impact RGPD d'un passage vers un fournisseur cloud). Cette discipline garantit la traçabilité des arbitrages souveraineté / performance / coût et protège le principe par défaut d'IA locale d'une dérive non documentée.

## 13. Perspectives d'évolution (Release 2)

Le MVP (F1-F6) une fois stabilisé, plusieurs axes d'évolution sont envisagés :

- **Interface enseignant** : matérialiser la persona « Mme Lefèvre » par un espace dédié (création de quiz pour une classe, suivi de cohorte), capitalisant sur les prompts métier déjà pensés pour les enseignants.
- **Accélération de l'inférence** : support GPU optionnel, mise en cache des générations, ou bascule automatique vers un fournisseur free tier en cas de dépassement de l'objectif de 60 secondes.
- **Enrichissement pédagogique** : niveaux de difficulté paramétrables, explications générées pour chaque réponse, formats de questions complémentaires.
- **Analytique de progression** : tableaux de bord enrichis, recommandation des chapitres à réviser, export des résultats.
- **Industrialisation** : passage d'un déploiement poste unique à un environnement serveur, CI/CD, observabilité (journalisation, métriques de latence LLM).

Chaque évolution touchant au fournisseur LLM ou au traitement des données personnelles devra faire l'objet d'un ADR, conformément à la stratégie définie en section 12.
