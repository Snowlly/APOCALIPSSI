# Étude de faisabilité — EduTutor IA

## 1. Objet et périmètre du document

La présente étude de faisabilité évalue la viabilité du projet **EduTutor IA**, plateforme web de révision par quiz QCM générés par intelligence artificielle à partir des cours déposés par l'étudiant (PDF ou texte). Elle examine quatre dimensions — technique, organisationnelle, économique et risques — afin de fonder une recommandation argumentée avant le lancement de la phase de réalisation.

Le périmètre couvre le **MVP must-have F1-F6** : authentification par email, saisie de cours, génération de 10 QCM, correction, score sur 10 et historique. Les fonctionnalités secondaires (tableau de bord de progression, mode sombre, back-office administrateur) sont prises en compte au titre des dépendances techniques mais ne conditionnent pas le go/no-go.

La cible primaire est l'**étudiant du supérieur** (BTS, Licence, Master) qui révise ses propres cours ; une cible secondaire émergente est l'**enseignant** (persona « Mme Lefèvre »). La proposition de valeur différenciante repose sur des prompts métier pensés pour les enseignants, un ancrage pédagogique réel et une **conformité RGPD by design** assurée par le recours à une IA locale et des données souveraines, face à des concurrents tels que Wilgo, Leo, Quizlet AI, Khanmigo ou Notion AI.

## 2. Faisabilité technique

### 2.1 Stack retenue

L'architecture cible est une application web découplée, entièrement conteneurisée, exécutable sur un poste de développement standard via une seule commande `docker compose up`.

| Couche | Technologie | Version | Justification |
|---|---|---|---|
| Backend | Django + Django REST Framework | Django 5, Python 3.11+ | Maturité, ORM robuste, écosystème, productivité sur le temps court |
| Frontend | React + Vite + TypeScript | React 18 | Typage statique, build rapide, DX moderne |
| Base de données | PostgreSQL | 16 | Fiabilité transactionnelle, support natif du type JSON (options de QCM) |
| Conteneurisation | Docker + Docker Compose | — | Reproductibilité, isolation des services, lancement unifié |
| IA | Ollama (Llama 3.1 8B) | local | Gratuité, souveraineté, conformité RGPD |
| Extraction PDF | pypdf | — | Extraction texte pure Python, sans dépendance système lourde |
| Emails | Brevo (SMTP) / console en dev | — | Vérification d'email, réinitialisation de mot de passe |
| Documentation API | Swagger via drf-spectacular | — | Contrat d'API auto-documenté |

Le backend est organisé en quatre applications Django à responsabilités claires : `accounts` (authentification par email, modèle `Profile.email_verified`), `quizzes` (modèles `Quiz` et `Question`), `llm` (configuration et factory multi-fournisseurs) et `administration` (`SiteConfig`, back-office).

[[DIAGRAMME: composants.svg]]
*Figure 1 — Vue des composants applicatifs et de leurs interactions.*

### 2.2 Choix de l'IA : Ollama local par défaut vs cloud

Le cœur technique d'EduTutor IA est la génération de QCM. Deux options structurantes s'opposent : un LLM **local** (Ollama, Llama 3.1 8B) ou un LLM **cloud** (API tierces). Le choix retenu privilégie le local par défaut, pour trois raisons :

- **Conformité RGPD et souveraineté** : aucun contenu de cours étudiant ne quitte le périmètre d'exécution. C'est l'argument différenciant central de la proposition de valeur.
- **Coût** : Ollama est gratuit à l'usage, ce qui supprime tout coût marginal par quiz généré.
- **Indépendance** : pas de dépendance à un fournisseur externe, pas de risque de coupure d'API ou de variation tarifaire.

Pour ne pas verrouiller le projet sur cette seule option, l'application `llm` implémente une **architecture multi-fournisseurs** via une factory : Ollama (défaut), Gemini, Groq, Cerebras, Mistral et OpenRouter en *free tier* ; OpenAI et Anthropic en mode *premium* payant ; un fournisseur *mock* pour les tests. La configuration est centralisée dans le singleton `LLMConfig` (champs `backend`, `model`, `api_keys` JSON, `ollama_host`, `timeout`). **Tout changement de fournisseur par défaut doit passer par un ADR** (Architecture Decision Record), notamment celui motivé par la latence (cf. §5).

### 2.3 Intégration et flux de génération

L'orchestration s'appuie sur Docker Compose, qui instancie quatre conteneurs : `apocalipssi-2026-postgres`, `apocalipssi-2026-ollama`, `apocalipssi-2026-backend` et `apocalipssi-2026-frontend`. Le backend communique avec Ollama via HTTP (`ollama_host`) et persiste les quiz dans PostgreSQL.

[[DIAGRAMME: deploiement-docker.svg]]
*Figure 2 — Topologie de déploiement Docker Compose des quatre conteneurs.*

Le flux nominal de génération de quiz enchaîne : extraction du texte source (pypdf si PDF, sinon texte saisi ≥ 200 caractères), construction du prompt métier, appel au LLM, parsing de la réponse en 10 objets `Question` (chacun avec `prompt`, `options` = JSON de 4 chaînes, `correct_index` 0..3) et persistance du `Quiz` rattaché à l'utilisateur.

[[DIAGRAMME: sequence-generation-quiz.svg]]
*Figure 3 — Séquence de génération d'un quiz, du dépôt du cours à la persistance des 10 questions.*

### 2.4 Verdict technique

La stack est entièrement composée de briques éprouvées et open source. La seule incertitude technique réelle porte sur la **latence du LLM local sur CPU** (poste 16 Go RAM, objectif < 60 s par quiz), traitée en §5. **Faisabilité technique : élevée, sous réserve de maîtrise de la latence.**

## 3. Faisabilité organisationnelle

### 3.1 Équipe Scrum et rôles

Le projet est conduit selon le cadre **Scrum**, sur une semaine immersive. L'équipe se structure autour des trois responsabilités du cadre.

| Rôle | Mission principale |
|---|---|
| Product Owner | Porte la vision, priorise le backlog (must-have F1-F6 d'abord), valide les incréments |
| Scrum Master | Facilite les cérémonies, lève les obstacles, protège l'équipe des perturbations |
| Équipe de développement | Conçoit, code et teste l'incrément ; auto-organisée et pluridisciplinaire |

### 3.2 Planning de la semaine

| Jour | Phase | Livrable attendu |
|---|---|---|
| J1 (lundi) | Cadrage, conception, Sprint Planning | Backlog priorisé, architecture, artefacts de cadrage |
| J2 (mardi) | Réalisation — socle | Auth (F1), saisie de cours (F2), squelette d'intégration LLM |
| J3 (mercredi 10h00) | Réalisation — cœur | Génération 10 QCM (F3), correction (F4), score (F5) |
| J3-bis (mercredi 14h00) | Réalisation — cœur (double créneau) | RGPD / données personnelles (demande d'accès, souveraineté) |
| J4 (jeudi) | Réalisation — finalisation | Historique (F6), polissage, gestion des perturbations |
| J5 (vendredi) | Recette et soutenance | Démonstration, rétrospective, restitution |

### 3.3 Cérémonies

Le rituel quotidien comprend un **Daily Scrum** (synchronisation courte, 15 min) ouvrant chaque journée. La semaine est cadrée par un **Sprint Planning** (J1), une **Sprint Review** (démonstration de l'incrément, J5) et une **Rétrospective** (amélioration continue, J5). L'évaluation portant prioritairement sur la **réaction agile aux perturbations**, le Scrum Master joue un rôle clé dans la replanification du backlog au fil des aléas injectés.

### 3.4 Verdict organisationnel

Le périmètre MVP est dimensionné pour la durée. La pluridisciplinarité requise (back Python, front TypeScript, conteneurisation, intégration IA) est couverte par une équipe Scrum standard. **Faisabilité organisationnelle : élevée.**

## 4. Faisabilité économique

L'analyse économique compare l'exploitation en IA locale (option retenue) à une exploitation via API cloud, sur la base d'un usage prévisionnel de référence.

| Poste de coût | Infra locale (Ollama) | API cloud (free tier) | API cloud (premium) |
|---|---|---|---|
| Coût d'inférence LLM | 0 € (compute local) | 0 € jusqu'à quota, puis facturation | ~0,15–0,60 € / 1M tokens (variable) |
| Hébergement applicatif | Poste/serveur existant (16 Go RAM) | Idem + dépendance réseau | Idem |
| Base de données PostgreSQL | Incluse (conteneur) | Incluse (conteneur) | Incluse (conteneur) |
| Coût marginal par quiz | ≈ 0 € | 0 € sous quota | quelques centimes |
| Données quittant le périmètre | Non (souverain) | Oui | Oui |
| Risque de coût à l'échelle | Nul | Plafond de quota | Croît avec l'usage |

Sur le périmètre du projet, l'option **Ollama local est la plus économique** : coût d'inférence nul, aucun abonnement, aucun coût marginal par quiz. Les seuls coûts résiduels sont le matériel (poste laptop 16 Go RAM, déjà disponible) et le temps humain de développement. Les fournisseurs cloud en *free tier* constituent un plan de repli sans coût immédiat, mais introduisent une dépendance externe et une rupture de la souveraineté des données. **Faisabilité économique : favorable, l'option locale minimisant les coûts récurrents.**

## 5. Analyse des risques

[[DIAGRAMME: activite-generation-quiz.svg]]
*Figure 4 — Activité de génération d'un quiz, point de concentration des risques de latence et de parsing.*

| # | Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|---|
| R1 | **Latence du LLM local > 60 s** sur CPU (poste 16 Go RAM) | Élevée | Majeur | **ADR** dédié : repli sur un fournisseur cloud *free tier* (Groq/Gemini) via la factory `llm` ; timeout configurable dans `LLMConfig` ; feedback UX (état « génération en cours ») |
| R2 | Réponse LLM mal formée (parsing en 10 `Question` échoue) | Moyenne | Majeur | Prompt strict + validation du schéma JSON ; retry borné ; fournisseur `mock` pour tests déterministes |
| R3 | Non-conformité RGPD (fuite de contenu de cours) | Faible | Critique | IA locale par défaut (données souveraines) ; suppression de compte ; minimisation des données ; ADR obligatoire avant tout passage cloud |
| R4 | Dépassement du périmètre / temps court | Moyenne | Majeur | Priorisation stricte F1-F6 ; backlog géré par le PO ; replanification agile |
| R5 | Saturation mémoire (Ollama + 3 conteneurs sur 16 Go) | Moyenne | Modéré | Choix d'un modèle 8B ; limites de ressources Docker ; surveillance |
| R6 | Indisponibilité d'un fournisseur cloud (si bascule) | Faible | Modéré | Architecture multi-fournisseurs ; retour au local |

Le risque **R1 (latence)** est identifié comme le risque technique majeur du projet. La latence d'inférence d'un modèle 8B sur CPU peut dépasser l'objectif des 60 secondes. La décision de basculer vers un fournisseur cloud — modifiant la promesse de souveraineté — doit impérativement être tracée par un **ADR**, qui documentera le contexte, les options, la décision et ses conséquences sur la conformité RGPD (R3).

## 6. Matrice RACI

R = Réalise, A = Approuve (responsable final), C = Consulté, I = Informé.

| Activité | Product Owner | Scrum Master | Équipe Dev | Formateur/Client |
|---|---|---|---|---|
| Priorisation du backlog | A/R | C | C | I |
| Architecture & choix de stack | C | I | A/R | I |
| Décision LLM local vs cloud (ADR) | A | C | R | C |
| Développement F1-F6 | I | I | A/R | — |
| Conformité RGPD | A | C | R | C |
| Animation des cérémonies | C | A/R | I | I |
| Gestion des perturbations | C | A/R | R | I |
| Recette et démonstration | A | C | R | I |

## 7. Conclusion et recommandation

Les quatre dimensions analysées convergent vers une **faisabilité globale favorable** :

- **Technique** : stack mature, intégralement conteneurisée, lancement par `docker compose up` ; seule la latence du LLM local constitue un point de vigilance, couvert par une architecture multi-fournisseurs et un ADR de repli.
- **Organisationnelle** : périmètre MVP dimensionné pour une semaine, cadre Scrum adapté à la gestion des perturbations.
- **Économique** : l'option Ollama local supprime tout coût d'inférence et de licence, avec un coût marginal par quiz quasi nul.
- **Risques** : maîtrisables, le risque majeur (latence < 60 s) disposant d'une mitigation claire et tracée.

**Recommandation : GO.** Le projet EduTutor IA est jugé faisable sur la durée de la semaine immersive, sur le périmètre MVP F1-F6. Deux conditions de succès sont posées : (1) valider en début de J2 la latence réelle d'Ollama sur le poste cible et, le cas échéant, déclencher l'ADR de bascule cloud *free tier* ; (2) préserver la conformité RGPD comme invariant de conception, toute dérogation devant être formellement documentée. La proposition de valeur — IA locale, données souveraines, ancrage pédagogique — reste le fil directeur du go/no-go.
