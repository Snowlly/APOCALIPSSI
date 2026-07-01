import os
import time
from pathlib import Path
import ollama


# ==========================================
# CONFIGURATION
# ==========================================

FICHIER_COURS = r"C:\Users\Inf\Desktop\ProjetApocalippsi\Cours1.txt"
DOSSIER_SORTIE = "qcm"

PROMPT = """
À partir du cours ci-dessous, génère un QCM de 10 questions.

Contraintes :
- 4 propositions par question.
- Une seule bonne réponse.
- Indique la bonne réponse après chaque question.
- Ajoute une courte explication.

Cours :

{cours}
"""


# ==========================================
# FONCTIONS
# ==========================================

def charger_cours():
    with open(FICHIER_COURS, "r", encoding="utf-8") as f:
        return f.read()


def recuperer_modeles():
    data = ollama.list()

    # Compatible avec plusieurs versions d'Ollama
    modeles = []

    for model in data["models"]:
        nom = model.get("model") or model.get("name")
        modeles.append(nom)

    return modeles


def sauvegarder_reponse(modele, temps, contenu):

    os.makedirs(DOSSIER_SORTIE, exist_ok=True)

    nom_fichier = modele.replace(":", "_") + ".txt"

    chemin = Path(DOSSIER_SORTIE) / nom_fichier

    with open(chemin, "w", encoding="utf-8") as f:

        f.write(f"Modèle : {modele}\n")
        f.write(f"Temps d'exécution : {temps:.2f} secondes\n")
        f.write("=" * 80 + "\n\n")
        f.write(contenu)

    print(f"Résultat sauvegardé : {chemin}")


def tester_modele(modele, cours):

    print(f"\n=== Test de {modele} ===")

    debut = time.perf_counter()

    response = ollama.chat(
        model=modele,
        messages=[
            {
                "role": "user",
                "content": PROMPT.format(cours=cours)
            }
        ]
    )

    fin = time.perf_counter()

    temps_execution = fin - debut

    contenu = response["message"]["content"]

    print(f"Temps : {temps_execution:.2f} secondes")

    sauvegarder_reponse(
        modele,
        temps_execution,
        contenu
    )


# ==========================================
# PROGRAMME PRINCIPAL
# ==========================================

def main():

    cours = charger_cours()

    modeles = recuperer_modeles()

    print("\nModèles détectés :")

    for m in modeles:
        print(f" - {m}")

    choix = input(
        "\nTester tous les modèles ? (o/n) : "
    ).lower()

    if choix == "o":

        for modele in modeles:
            try:
                tester_modele(modele, cours)

            except Exception as e:
                print(f"Erreur avec {modele} : {e}")

    else:

        modele = input("Nom du modèle : ")

        tester_modele(modele, cours)


if __name__ == "__main__":
    main()