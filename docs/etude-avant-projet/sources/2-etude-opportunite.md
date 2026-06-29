# Étude d'opportunité — EduTutor IA

## 1. Contexte et objet du document

Ce document constitue l'étude d'opportunité du projet **EduTutor IA**, plateforme web de révision par quiz QCM générés par intelligence artificielle à partir des supports de cours de l'étudiant (PDF ou texte saisi). Il vise à éclairer la décision d'engagement (Go / No-Go) en confrontant l'idée au marché, à la concurrence et aux conditions économiques de viabilité.

EduTutor IA se positionne comme une startup edtech française dont la singularité repose sur un choix d'architecture structurant : une **IA exécutée localement** (modèle Llama 3.1 8B via Ollama), gage de souveraineté des données et de conformité RGPD *by design*, complétée par une architecture multi-fournisseurs activable à la demande.

## 2. Contexte marché

Le marché des outils d'aide à la révision assistés par IA connaît une croissance forte et soutenue depuis l'arrivée des grands modèles de langage grand public (fin 2022). Trois dynamiques structurent ce contexte.

**Une demande étudiante en forte expansion.** Les usages d'IA générative se sont massivement diffusés dans l'enseignement supérieur. Les étudiants de BTS, Licence et Master utilisent désormais ces outils non plus seulement pour produire du contenu, mais pour s'auto-évaluer, structurer leurs révisions et combler leurs lacunes. La génération automatique de QCM à partir de leurs propres supports répond à un besoin concret : transformer un cours passif en exercice actif (apprentissage par récupération, ou *retrieval practice*, dont l'efficacité pédagogique est largement documentée).

**Une offre encore fragmentée et anglo-saxonne.** Les solutions dominantes (Quizlet, Khanmigo) sont américaines, pensées pour un marché et un système éducatif différents, et reposent quasi systématiquement sur des LLM cloud propriétaires. L'offre francophone, réellement ancrée dans les pratiques pédagogiques nationales, reste embryonnaire.

**Une pression réglementaire et de confiance croissante.** Le RGPD, le futur cadre européen sur l'IA (*AI Act*) et la sensibilité particulière des données éducatives (souvent rattachées à des mineurs ou à des établissements publics) font de la conformité un critère d'achat de plus en plus différenciant, notamment pour la cible secondaire « enseignant / établissement ». Les solutions transférant systématiquement les contenus vers des serveurs hors UE deviennent un point de friction juridique et politique.

Ce triple contexte — demande en hausse, offre peu localisée, exigence de conformité — dessine une fenêtre d'opportunité crédible pour une solution française, pédagogiquement ancrée et souveraine.

## 3. Analyse concurrentielle

Le tableau ci-dessous confronte EduTutor IA aux cinq solutions de référence identifiées sur le segment de la révision et de l'assistance pédagogique par IA.

| Solution | Positionnement | IA locale / cloud | RGPD / souveraineté | Cible principale | Modèle de prix |
|---|---|---|---|---|---|
| **Wilgo** | Assistant de révision IA francophone, fiches et quiz | Cloud (LLM tiers) | Hébergement UE, données envoyées au cloud | Étudiant secondaire / supérieur | Freemium + abonnement |
| **Leo** | Tuteur conversationnel IA, accompagnement scolaire | Cloud | Variable selon fournisseur LLM | Élève / étudiant | Freemium / abonnement |
| **Quizlet AI** | Flashcards et quiz, leader historique massifié | Cloud (propriétaire) | Données hors UE (acteur US) | Étudiant mondial (volume) | Freemium + Quizlet Plus |
| **Khanmigo** | Tuteur IA adossé à Khan Academy, socle pédagogique fort | Cloud (GPT) | Données hors UE (acteur US) | Élève / enseignant (K-12) | Abonnement / institutionnel |
| **Notion AI** | Productivité augmentée, génération de contenu transverse | Cloud | Données hors UE (acteur US) | Knowledge workers, étudiants avancés | Add-on payant sur abonnement |
| **EduTutor IA** | Révision QCM à partir des cours de l'étudiant, ancrage pédagogique FR | **Local par défaut** (Ollama / Llama 3.1 8B), multi-fournisseurs optionnel | **RGPD by design, données souveraines** (traitement local) | Étudiant du supérieur FR (BTS/Licence/Master) ; enseignant | Gratuit en local ; pistes freemium |

*Tableau 1 — Comparatif concurrentiel d'EduTutor IA.*

Lecture du tableau. Les acteurs établis se distinguent par leur volume d'usage et la richesse de leurs contenus, mais partagent deux dépendances : un traitement systématiquement *cloud* et, pour les leaders, un hébergement hors Union européenne. EduTutor IA n'a aucune chance de rivaliser sur le volume ou la notoriété à court terme ; sa différenciation se construit sur deux axes que les concurrents ne couvrent pas simultanément : **le traitement local souverain** et **l'ancrage pédagogique francophone** via des prompts métier pensés pour des enseignants.

## 4. Analyse SWOT

L'analyse SWOT synthétise les facteurs internes (forces / faiblesses) et externes (opportunités / menaces) conditionnant la réussite du projet.

| **Forces (internes)** | **Faiblesses (internes)** |
|---|---|
| • IA **locale par défaut** : souveraineté, RGPD *by design*, coût d'inférence nul. <br>• Architecture **multi-fournisseurs** (Ollama, Gemini, Groq, Cerebras, Mistral, OpenRouter, premium) gouvernée par ADR : flexibilité et réversibilité. <br>• Stack moderne et maîtrisée (Django 5 / DRF, React 18 + Vite + TS, PostgreSQL 16, Docker). <br>• Ancrage pédagogique réel : prompts métier conçus pour les enseignants. <br>• Périmètre MVP clair et resserré (F1-F6). | • **Latence CPU** d'un LLM local : objectif < 60 s par quiz, exigeant sur un poste 16 Go RAM. <br>• Qualité de génération du modèle 8B en deçà des modèles cloud de pointe. <br>• Notoriété et base d'utilisateurs nulles au démarrage. <br>• Périmètre fonctionnel volontairement restreint (QCM uniquement, 10 questions). <br>• Dépendance à la qualité d'extraction PDF (pypdf). |
| **Opportunités (externes)** | **Menaces (externes)** |
| • Demande étudiante en forte croissance pour l'auto-évaluation par IA. <br>• Exigence RGPD / *AI Act* croissante, surtout côté enseignants et établissements. <br>• Offre francophone souveraine peu occupée. <br>• Cible secondaire « enseignant » (persona Mme Lefèvre) ouvrant un marché B2B/B2I. <br>• Démocratisation des LLM open-weight performants et légers. | • Concurrents établis (Quizlet, Khanmigo) aux moyens considérables. <br>• Possibilité que les leaders ajoutent une option « UE / souveraine ». <br>• Progrès rapide des LLM cloud creusant l'écart de qualité. <br>• Sensibilité prix d'une cible étudiante. <br>• Évolution réglementaire pouvant imposer des contraintes supplémentaires. |

*Tableau 2 — Matrice SWOT d'EduTutor IA.*

## 5. Positionnement et proposition de valeur différenciante

EduTutor IA se positionne sur l'intersection de trois attentes rarement satisfaites simultanément : **personnalisation** (les quiz sont générés à partir des cours réels de l'étudiant, et non d'un catalogue générique), **souveraineté** (le traitement par défaut reste sur la machine, sans transfert des contenus vers un tiers) et **pertinence pédagogique** (prompts métier conçus avec une logique enseignante).

La proposition de valeur se formule ainsi :

> *« Transformez vos propres cours en quiz d'entraînement en moins d'une minute, sans que vos données ne quittent votre poste, avec une IA pensée par et pour des enseignants. »*

Les piliers différenciants, par rapport au comparatif de la section 3 :

- **Données souveraines.** Le traitement local (Ollama / Llama 3.1 8B) élimine le transfert de contenus de cours vers un cloud tiers — argument décisif face aux solutions US et levier de confiance auprès des enseignants et établissements.
- **Coût d'inférence nul en mode local.** L'absence de facturation à la requête autorise un usage illimité côté étudiant et un modèle économique non strictement indexé sur le coût d'API.
- **Réversibilité technique.** L'architecture multi-fournisseurs, encadrée par des ADR, permet de basculer vers un LLM cloud (Gemini, Groq, Mistral, premium…) sans réécrire l'application — utile pour des cas premium ou des contextes sans GPU/CPU suffisant.
- **Ancrage métier.** Les prompts orientés pédagogie produisent des QCM exploitables (10 questions, 4 options, une bonne réponse) directement alignés sur une logique d'évaluation formative.

[[DIAGRAMME: cas-utilisation.svg]]
*Figure 1 — Cas d'utilisation : périmètre fonctionnel couvert pour les acteurs Étudiant et Administrateur.*

## 6. Cibles et personas

| Persona | Profil | Besoin clé | Attente envers EduTutor IA |
|---|---|---|---|
| **Cible primaire — l'étudiant** | Étudiant du supérieur (BTS, Licence, Master) qui révise ses propres cours | S'auto-évaluer rapidement, identifier ses lacunes, réviser ses erreurs | Génération immédiate de QCM depuis un PDF/texte, score /10, historique et progression |
| **Cible secondaire — l'enseignant (« Mme Lefèvre »)** | Enseignante souhaitant proposer des quiz à ses élèves, attentive à la conformité | Produire des évaluations formatives fiables sans exposer les contenus | IA souveraine, prompts pédagogiquement solides, contrôle des données |

*Tableau 3 — Personas cibles d'EduTutor IA.*

La cible primaire (étudiant) porte l'adoption du MVP (fonctionnalités F1-F6 : authentification, saisie de cours, génération de 10 QCM, correction, score, historique). La cible secondaire (enseignant) constitue un relais de croissance émergent et l'angle de différenciation le plus défendable face aux acteurs cloud généralistes, tout en ouvrant une porte vers un futur marché B2B/institutionnel.

## 7. Pistes de modèle économique

À ce stade d'avant-projet, plusieurs pistes coexistent ; aucune n'est figée. Le choix de l'IA locale (coût d'inférence nul) offre une latitude que n'ont pas les concurrents indexés sur le coût d'API.

| Piste | Principe | Avantages | Limites |
|---|---|---|---|
| **Open source / communautaire** | Application publique sur GitHub, auto-hébergeable | Adoption, contributions, crédibilité souveraine | Pas de revenu direct |
| **Freemium étudiant** | Gratuit en local, fonctions avancées payantes (analytics, formats de questions, export) | Faible barrière d'entrée, conversion progressive | Conversion incertaine sur cible étudiante sensible au prix |
| **Premium IA cloud** | Option payante basculant vers un LLM cloud premium (qualité supérieure, sans GPU local) | Monétise l'architecture multi-fournisseurs existante | Réintroduit un coût d'API et une dépendance externe |
| **B2B / établissements** | Licence ou déploiement pour établissements (cible Mme Lefèvre) | Souveraineté = argument fort en B2I, panier plus élevé | Cycle de vente long, exigences contractuelles |

*Tableau 4 — Pistes de modèle économique.*

La trajectoire la plus cohérente combine un **socle gratuit / open source** (acquisition et crédibilité souveraine) avec une **piste B2B / établissements** à moyen terme, où l'argument de souveraineté est le plus valorisé. Le mode *premium cloud* reste une option opportuniste, secondaire au regard de l'identité « locale » du produit.

## 8. Analyse coûts / bénéfices qualitative

| Dimension | Coûts / efforts | Bénéfices attendus |
|---|---|---|
| **Technique** | Maîtrise de la latence LLM local (< 60 s sur 16 Go RAM) ; intégration Ollama ; orchestration Docker (postgres, ollama, backend, frontend) | Stack moderne et réversible ; coût d'inférence nul ; déploiement reproductible (`docker compose up`) |
| **Données / conformité** | Conception RGPD *by design* ; gestion vérification email, suppression de compte | Argument de confiance décisif ; conformité comme avantage concurrentiel, non comme contrainte |
| **Produit** | Périmètre MVP resserré (QCM 10 questions) ; qualité de génération à éprouver | Time-to-value court ; proposition de valeur claire et démontrable |
| **Marché** | Notoriété nulle ; coût d'acquisition à construire | Fenêtre francophone souveraine peu disputée ; double cible étudiant + enseignant |
| **Financier** | Pas de revenu immédiat ; modèle à valider | Coûts opérationnels faibles (pas d'API à la requête en local) ; plusieurs pistes ouvertes |

*Tableau 5 — Analyse coûts / bénéfices qualitative.*

Le profil coûts/bénéfices est favorable sur le plan opérationnel (coûts d'inférence et d'hébergement maîtrisés grâce au local) et stratégique (différenciation souveraine et pédagogique). Le principal poste de risque est technique — la latence d'un LLM local sur CPU — et fait l'objet d'un objectif explicite et mesurable (< 60 s par quiz), donc traçable dès le MVP.

## 9. Recommandation : Go / No-Go

**Recommandation : GO**, sur un périmètre MVP resserré (fonctionnalités must-have F1-F6) et avec une vigilance prioritaire sur la latence de génération.

Les arguments en faveur du Go :

1. **Une fenêtre marché crédible.** Demande étudiante en croissance, offre francophone souveraine peu occupée, exigence de conformité montante : les trois conditions d'une opportunité réelle sont réunies.
2. **Une différenciation défendable et non triviale à copier.** Le couple *IA locale souveraine* + *ancrage pédagogique francophone* n'est couvert par aucun concurrent du comparatif simultanément ; il est cohérent avec un futur marché enseignant / établissement.
3. **Un risque maîtrisable et borné.** Le principal risque (latence LLM local) est identifié, mesurable (objectif < 60 s) et localisé techniquement ; il ne remet pas en cause la faisabilité globale, démontrée par une stack et une architecture déjà définies.
4. **Un coût d'engagement contenu.** Périmètre MVP clair, coûts opérationnels faibles en mode local, déploiement reproductible par Docker : l'investissement initial reste proportionné au potentiel.

Conditions et points de vigilance attachés au Go :

- **Valider l'objectif de latence** (< 60 s par quiz sur poste 16 Go RAM) dès les premières itérations : c'est le critère go/no-go technique de fait.
- **Mesurer la qualité pédagogique** des QCM générés par le modèle 8B local, et activer la bascule multi-fournisseurs (via ADR) si l'écart de qualité est rédhibitoire.
- **Tester l'appétence de la cible secondaire enseignant** au plus tôt, car elle porte la différenciation la plus durable.
- **Différer les décisions de monétisation** : prioriser l'adoption et la preuve de valeur avant tout choix de modèle économique définitif.

En synthèse, EduTutor IA présente un rapport opportunité / risque favorable, adossé à un positionnement différenciant clair et à un périmètre maîtrisé. La décision recommandée est un **Go conditionné** à la validation continue de la latence de génération et de la qualité pédagogique des quiz.
