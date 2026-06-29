"""
Commande `python manage.py bootstrap_demo`
------------------------------------------
Crée (de façon IDEMPOTENTE) les 3 comptes de démonstration par défaut, plus des
quiz d'exemple pour le compte utilisateur. Conçue pour tourner à CHAQUE démarrage
du backend (dev ET prod) : elle ne réinitialise JAMAIS un mot de passe déjà
changé, ni n'écrase un quiz existant.

Comptes créés (login = email ; chacun peut changer login/mot de passe ensuite
depuis son espace profil) :
    user@apocal.local  / userdemo2026   -> utilisateur standard
    staff@apocal.local / staffdemo2026  -> staff (back-office /api/admin/)
    admin@apocal.local / admindemo2026  -> superuser (Django /admin/)

Les quiz d'exemple (Agile/Scrum, Droit du numérique, ITIL) sont lus depuis le
fichier `demo_quizzes.json` situé à côté de cette commande.
"""

import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import get_or_create_profile
from quizzes.models import Question, Quiz

QUIZ_DATA_FILE = Path(__file__).resolve().parent / "demo_quizzes.json"
# Comptes étudiants/enseignante SCÉNARISÉS (Léa en révision, Kevin qui bloque en
# maths → score faible alimentant Dashboard/Révision, Mme Lefèvre + quiz « hallucinant »
# préfigurant J3). Une part du récit portée par la donnée, pas seulement l'animation.
STUDENT_DATA_FILE = Path(__file__).resolve().parent / "demo_students.json"

DEFAULT_ACCOUNTS = [
    {
        "email": "user@apocal.local",
        "password": "userdemo2026",
        "first_name": "Démo",
        "last_name": "Utilisateur",
        "is_staff": False,
        "is_superuser": False,
        "with_quizzes": True,
    },
    {
        "email": "staff@apocal.local",
        "password": "staffdemo2026",
        "first_name": "Démo",
        "last_name": "Staff",
        "is_staff": True,
        "is_superuser": False,
        "with_quizzes": False,
    },
    {
        "email": "admin@apocal.local",
        "password": "admindemo2026",
        "first_name": "Démo",
        "last_name": "Admin",
        "is_staff": True,
        "is_superuser": True,
        "with_quizzes": False,
    },
]


class Command(BaseCommand):
    help = "Crée les 3 comptes de démo par défaut (idempotent) + quiz d'exemple."

    @transaction.atomic
    def handle(self, *args, **options):
        for acc in DEFAULT_ACCOUNTS:
            user = self._ensure_account(acc)
            if acc.get("with_quizzes"):
                self._ensure_quizzes(user)
        self._ensure_scenario_students()
        self.stdout.write(self.style.SUCCESS("bootstrap_demo : terminé."))

    def _ensure_account(self, acc):
        """Crée le compte s'il n'existe pas. Idempotent : ne touche pas un compte
        existant (donc ne réinitialise pas un mot de passe déjà modifié)."""
        user, created = User.objects.get_or_create(
            username=acc["email"],
            defaults={
                "email": acc["email"],
                "first_name": acc.get("first_name", ""),
                "last_name": acc.get("last_name", ""),
                "is_staff": acc.get("is_staff", False),
                "is_superuser": acc.get("is_superuser", False),
            },
        )
        if created:
            user.set_password(acc["password"])
            user.save()
            profile = get_or_create_profile(user)
            profile.email_verified = True
            profile.save(update_fields=["email_verified"])
            self.stdout.write(self.style.SUCCESS(f"  + compte créé : {acc['email']}"))
        else:
            self.stdout.write(f"  = compte déjà présent : {acc['email']}")
        return user

    def _ensure_quizzes(self, user):
        """Charge les quiz de démo et les attache à l'utilisateur (sans doublon)."""
        if not QUIZ_DATA_FILE.exists():
            self.stdout.write(self.style.WARNING(f"  ! fichier quiz absent : {QUIZ_DATA_FILE}"))
            return

        data = json.loads(QUIZ_DATA_FILE.read_text(encoding="utf-8"))
        for qz in data:
            quiz, created = Quiz.objects.get_or_create(
                user=user,
                title=qz["title"],
                defaults={"source_text": qz.get("source_text", ""), "score": None},
            )
            if not created:
                continue  # quiz déjà présent -> on n'écrase pas
            for i, question in enumerate(qz["questions"], start=1):
                Question.objects.create(
                    quiz=quiz,
                    index=i,
                    prompt=question["prompt"],
                    options=question["options"],
                    correct_index=question["correct_index"],
                )
            count = len(qz["questions"])
            self.stdout.write(self.style.SUCCESS(f"  + quiz créé : {qz['title']} ({count} Q)"))

    def _ensure_scenario_students(self):
        """Crée les comptes étudiants/enseignante scénarisés + leurs quiz (avec
        score et réponses ratées), pour que la donnée porte une part du récit
        (Dashboard, Révision des erreurs, préfiguration J3). Idempotent."""
        if not STUDENT_DATA_FILE.exists():
            self.stdout.write(
                self.style.WARNING(f"  ! fichier étudiants absent : {STUDENT_DATA_FILE}")
            )
            return
        students = json.loads(STUDENT_DATA_FILE.read_text(encoding="utf-8"))
        for st in students:
            user = self._ensure_account(st)
            self._ensure_scenario_quizzes(user, st.get("quizzes", []))

    def _ensure_scenario_quizzes(self, user, quizzes):
        """Quiz scénarisés : score (/10) et selected_index (réponse donnée) pris
        en compte, sans doublon (on n'écrase pas un quiz existant)."""
        for qz in quizzes:
            quiz, created = Quiz.objects.get_or_create(
                user=user,
                title=qz["title"],
                defaults={"source_text": qz.get("source_text", ""), "score": qz.get("score")},
            )
            if not created:
                continue
            for i, question in enumerate(qz["questions"], start=1):
                Question.objects.create(
                    quiz=quiz,
                    index=i,
                    prompt=question["prompt"],
                    options=question["options"],
                    correct_index=question["correct_index"],
                    selected_index=question.get("selected_index"),
                )
            self.stdout.write(
                self.style.SUCCESS(
                    f"  + quiz scénarisé : {qz['title']} ({len(qz['questions'])} Q, score={qz.get('score')})"
                )
            )
