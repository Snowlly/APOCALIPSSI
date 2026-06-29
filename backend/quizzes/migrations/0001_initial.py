"""Migration initiale pour les modèles Quiz et Question.

Générée manuellement pour que `docker compose up` fonctionne immédiatement
sans avoir à lancer `makemigrations` au préalable.
"""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Quiz",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(help_text="Titre du cours / quiz (saisi ou déduit).", max_length=200)),
                ("source_text", models.TextField(help_text="Texte source utilisé pour la génération (extrait PDF ou saisie).")),
                ("score", models.IntegerField(blank=True, help_text="Score /10 obtenu lors de la dernière tentative (None si pas encore passé).", null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(help_text="Propriétaire du quiz.", on_delete=django.db.models.deletion.CASCADE, related_name="quizzes", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Quiz",
                "verbose_name_plural": "Quizz",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("index", models.PositiveIntegerField(help_text="Position de la question dans le quiz (1 à 10).")),
                ("prompt", models.TextField(help_text="Énoncé de la question.")),
                ("options", models.JSONField(help_text="Liste des 4 options (chaînes). Ex : ['Paris', 'Londres', 'Madrid', 'Berlin']")),
                ("correct_index", models.PositiveSmallIntegerField(help_text="Index (0 à 3) de la bonne réponse dans `options`.")),
                ("quiz", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to="quizzes.quiz")),
            ],
            options={
                "verbose_name": "Question",
                "verbose_name_plural": "Questions",
                "ordering": ["index"],
                "unique_together": {("quiz", "index")},
            },
        ),
    ]
