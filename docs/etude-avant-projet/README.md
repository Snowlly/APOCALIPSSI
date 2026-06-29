# Dossier d'avant-projet — EduTutor IA

Documentation **héritée de la première équipe** : étude amont du projet, fournie
comme contexte et comme **modèle de qualité professionnelle**. À lire, et à faire
évoluer si votre repriorisation l'exige.

> 🧭 Ces documents sont **en amont** du cadrage agile : ils n'y substituent pas
> vos 7 artefacts (Vision Board, personas, story map…), ils les éclairent.

## Contenu

| Élément | Chemin | Rôle |
|---|---|---|
| Sources Markdown | `sources/*.md` | Texte éditable des 4 documents (source de vérité) |
| Documents Word | `docx/*.docx` | Générés depuis les sources, à exporter en PDF |
| Diagrammes (code) | `diagrammes/*.mmd` | Code **Mermaid** des 11 diagrammes (éditable) |
| Diagrammes (images) | `diagrammes/img/*.png` `*.svg` | Rendus, embarqués dans les `.docx` |
| Générateur | `generate.py` | Markdown → Word (python-docx) |

Les **4 documents** : 1) Expression de besoin · 2) Étude d'opportunité ·
3) Étude de faisabilité · 4) Dossier d'architecture technique.

## Régénérer les documents Word

```bash
pip install python-docx
cd docs/etude-avant-projet
python generate.py        # -> docx/*.docx (diagrammes embarqués)
```

## Régénérer / modifier un diagramme

Le code source est dans `diagrammes/*.mmd` (Mermaid). Pour produire les images :

- **En ligne** : copier le contenu d'un `.mmd` dans <https://mermaid.live>, exporter en SVG/PNG dans `diagrammes/img/`.
- **En ligne de commande** (Node) :
  ```bash
  npm i -g @mermaid-js/mermaid-cli
  mmdc -i diagrammes/cas-utilisation.mmd -o diagrammes/img/cas-utilisation.png
  ```

Puis relancez `python generate.py` pour réintégrer les images dans les `.docx`.

## Produire les PDF (pour le site)

Ouvrez chaque `.docx` et **Exporter en PDF** (Word ou LibreOffice). Déposez les
PDF dans le **repo du site** sous `assets/docs/` ; ils sont consultables sur la
page « Étude d'avant-projet ».

## Note

Le répertoire `prompts/` (prompts de génération des diagrammes) est **exclu du
dépôt** (`.gitignore`) : il est réservé au formateur et n'est pas destiné aux
étudiants pour l'instant.
