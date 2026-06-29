"""
Commande `python manage.py seed`
--------------------------------
Insère un user de test + 2 quizz d'exemple pour démarrer rapidement.

Identifiants après seed :
    Username : test
    Email    : test@apocal.local
    Password : motdepasse123
"""

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from quizzes.models import Question, Quiz


class Command(BaseCommand):
    help = "Insère 1 utilisateur de test et 2 quizz d'exemple."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="test",
            defaults={"email": "test@apocal.local", "first_name": "Test", "last_name": "User"},
        )
        if created:
            user.set_password("motdepasse123")
            user.save()
            self.stdout.write(self.style.SUCCESS("✅ User 'test' créé."))
        else:
            self.stdout.write("ℹ️  User 'test' existe déjà.")

        # Supprime les quizz existants du user test pour éviter les doublons
        Quiz.objects.filter(user=user).delete()

        # Quiz 1
        quiz1 = Quiz.objects.create(
            user=user,
            title="Histoire — la Révolution française",
            source_text=(
                "La Révolution française débute en 1789 avec la prise de la Bastille "
                "le 14 juillet. Elle marque la fin de l'Ancien Régime et l'établissement "
                "d'une république. Robespierre incarne la période de la Terreur."
            ),
            score=8,
        )
        questions_1 = [
            (
                "En quelle année débute la Révolution française ?",
                ["1789", "1799", "1815", "1848"],
                0,
            ),
            (
                "Quel événement marque le début de la Révolution ?",
                [
                    "La prise de la Bastille",
                    "Le sacre de Napoléon",
                    "La fronde",
                    "Le serment du jeu de paume",
                ],
                0,
            ),
            (
                "Quel personnage incarne la Terreur ?",
                ["Napoléon", "Robespierre", "Louis XVI", "Danton"],
                1,
            ),
            (
                "Quelle date marque la prise de la Bastille ?",
                ["14 juillet 1789", "1 mai 1789", "11 novembre 1789", "5 octobre 1789"],
                0,
            ),
            (
                "Quelle est la conséquence politique majeure ?",
                [
                    "Restauration monarchique",
                    "Création d'une république",
                    "Création de l'Empire",
                    "Fédération européenne",
                ],
                1,
            ),
            (
                "Comment s'appelle la période d'avant la Révolution ?",
                ["Ancien Régime", "Moyen Âge", "Renaissance", "Lumières"],
                0,
            ),
            (
                "Quelle déclaration majeure est adoptée en 1789 ?",
                [
                    "Déclaration d'indépendance",
                    "Déclaration des droits de l'homme",
                    "Code Napoléon",
                    "Constitution de l'an III",
                ],
                1,
            ),
            (
                "Quel roi régnait au début de la Révolution ?",
                ["Louis XV", "Louis XVI", "Louis XIV", "Louis XVIII"],
                1,
            ),
            (
                "Quel symbole nait avec la Révolution ?",
                ["Le drapeau tricolore", "L'aigle impériale", "La fleur de lys", "L'hermine"],
                0,
            ),
            (
                "Comment se termine officiellement l'Ancien Régime ?",
                [
                    "Avec l'abdication",
                    "Avec la prise de la Bastille",
                    "Avec le coup d'État du 18 brumaire",
                    "Avec l'exécution de Louis XVI",
                ],
                3,
            ),
        ]
        for i, (prompt, options, correct) in enumerate(questions_1, start=1):
            Question.objects.create(
                quiz=quiz1, index=i, prompt=prompt, options=options, correct_index=correct
            )

        # Quiz 2
        quiz2 = Quiz.objects.create(
            user=user,
            title="Informatique — Bases du Web",
            source_text=(
                "HTTP est un protocole client-serveur. HTML structure les pages, "
                "CSS les met en forme, JavaScript ajoute du comportement. Le navigateur "
                "interprète ces trois langages côté client."
            ),
            score=None,  # pas encore passé
        )
        questions_2 = [
            (
                "Quel protocole sert à transporter les pages web ?",
                ["HTTP", "FTP", "SMTP", "SSH"],
                0,
            ),
            ("Quel langage structure une page web ?", ["CSS", "HTML", "JavaScript", "SQL"], 1),
            ("Quel langage met en forme une page ?", ["HTML", "CSS", "PHP", "Python"], 1),
            (
                "Où s'exécute JavaScript par défaut ?",
                ["Côté serveur", "Côté client", "Sur la DB", "Dans le BIOS"],
                1,
            ),
            ("Quel est le port HTTP standard ?", ["21", "22", "80", "443"], 2),
            (
                "Quel format de fichier est interprété par le navigateur ?",
                ["HTML", "DOCX", "EXE", "ZIP"],
                0,
            ),
            (
                "Quel élément encadre le titre principal d'une page HTML ?",
                ["<title>", "<h1>", "<header>", "<main>"],
                1,
            ),
            (
                "À quoi sert HTTPS par rapport à HTTP ?",
                ["Plus rapide", "Plus sécurisé", "Plus économique", "Plus joli"],
                1,
            ),
            ("Quel terme désigne l'arbre des éléments HTML ?", ["DOM", "BOM", "CSSOM", "DTD"], 0),
            (
                "Quel outil ouvre une page web ?",
                ["Navigateur", "Compilateur", "Serveur SMTP", "Console SQL"],
                0,
            ),
        ]
        for i, (prompt, options, correct) in enumerate(questions_2, start=1):
            Question.objects.create(
                quiz=quiz2, index=i, prompt=prompt, options=options, correct_index=correct
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Quiz '{quiz1.title}' créé avec {quiz1.questions.count()} questions."
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Quiz '{quiz2.title}' créé avec {quiz2.questions.count()} questions."
            )
        )
        self.stdout.write(self.style.SUCCESS("\n🎉 Seed terminé."))
        self.stdout.write("   Connectez-vous : test / motdepasse123")
