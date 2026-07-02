import csv
import os
import re
import time
from pathlib import Path

import ollama


# ==================================================
# CONFIGURATION
# ==================================================

FICHIER_COURS = r"C:\Users\Inf\Desktop\ProjetApocalippsi\CorpusCours.txt"

DOSSIER_SORTIE = "qcm"

PROMPTS_VARIABLES = [
    "Le QCM ne doit plus être sur napoléon mais sur le machine learning et privilégier les questions de compréhension.",
    "Le QCM doit être facile et destiné à des lycéens.",
    "Le QCM doit être sur la langue francaise",
    "Le QCM doit privilégier les questions de compréhension.",
    "Le QCM doit être de niveau universitaire.",
]

PROMPT_BASE = """
Cours :

{cours}


À partir du cours ci-dessous, génère un QCM de 10 questions.

Contraintes :
- 4 propositions par question.
- Une seule bonne réponse.
- Indique la bonne réponse après chaque question.
- Ajoute une courte explication.
- Le QCM doit être en francais
- Le QCM doit être sur napoléon.

Consigne supplémentaire :
{consigne}

"""


# ==================================================
# OUTILS
# ==================================================

def nettoyer_nom(texte):
    texte = texte.lower()
    texte = re.sub(r'[^a-z0-9]+', '_', texte)
    return texte[:40]


def charger_cours():
    with open(FICHIER_COURS, "r", encoding="utf-8") as f:
        return f.read()


def recuperer_modeles():

    data = ollama.list()

    modeles = []

    for model in data["models"]:
        nom = model.get("model") or model.get("name")
        modeles.append(nom)

    return modeles


def sauvegarder_reponse(modele, consigne, temps, texte):

    dossier = Path(DOSSIER_SORTIE) / nettoyer_nom(consigne)

    dossier.mkdir(parents=True, exist_ok=True)

    nom_modele = modele.replace(":", "_").replace("/","_")

    chemin = dossier / f"{nom_modele}.txt"

    with open(chemin, "w", encoding="utf-8") as f:

        f.write(f"Modèle : {modele}\n")
        f.write(f"Temps : {temps:.2f} secondes\n")
        f.write(f"Consigne : {consigne}\n")
        f.write("=" * 80 + "\n\n")

        f.write(texte)

    return chemin


def ajouter_csv(modele, consigne, temps, texte):

    chemin_csv = Path(DOSSIER_SORTIE) / "resultats.csv"

    fichier_existe = chemin_csv.exists()

    with open(chemin_csv, "a", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        if not fichier_existe:
            writer.writerow([
                "modele",
                "consigne",
                "temps_secondes",
                "nb_caracteres"
            ])

        writer.writerow([
            modele,
            consigne,
            round(temps, 2),
            len(texte)
        ])


# ==================================================
# TEST
# ==================================================

def tester_modele(modele, cours, consigne):

    print(f"\n[{modele}]")
    print(f"Consigne : {consigne}")

    prompt = PROMPT_BASE.format(
        cours=cours,
        consigne=consigne
    )

    debut = time.perf_counter()

    response = ollama.chat(
        model=modele,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    temps = time.perf_counter() - debut

    texte = response["message"]["content"]

    sauvegarder_reponse(
        modele,
        consigne,
        temps,
        texte
    )

    ajouter_csv(
        modele,
        consigne,
        temps,
        texte
    )

    print(
        f"{temps:.2f}s | "
        f"{len(texte)} caractères"
    )


# ==================================================
# MAIN
# ==================================================

def main():

    os.makedirs(DOSSIER_SORTIE, exist_ok=True)

    cours = charger_cours()

    modeles = recuperer_modeles()

    print("\nModèles détectés :")

    for m in modeles:
        print("-", m)

    print("\nDébut des tests...\n")

    for consigne in PROMPTS_VARIABLES:

        print("=" * 80)
        print(consigne)
        print("=" * 80)

        for modele in modeles:

            try:
                tester_modele(
                    modele,
                    cours,
                    consigne
                )

            except Exception as e:
                print(f"Erreur {modele} : {e}")

    print("\nTous les tests sont terminés !")


if __name__ == "__main__":
    main()