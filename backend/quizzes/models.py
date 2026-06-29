"""
Modèles métier d'EduTutor IA.

Un Quiz appartient à un utilisateur ; il contient le texte source du cours
(extrait du PDF ou collé en clair) et 10 Questions (QCM avec 4 options et
1 bonne réponse).
"""

from django.conf import settings
from django.db import models


class Quiz(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quizzes",
        help_text="Propriétaire du quiz.",
    )
    title = models.CharField(max_length=200, help_text="Titre du cours / quiz (saisi ou déduit).")
    source_text = models.TextField(
        help_text="Texte source utilisé pour la génération (extrait PDF ou saisie).",
    )
    score = models.IntegerField(
        null=True,
        blank=True,
        help_text="Score /10 obtenu lors de la dernière tentative (None si pas encore passé).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Quiz"
        verbose_name_plural = "Quizz"

    def __str__(self) -> str:
        return f"{self.title} — {self.user.username}"


class Question(models.Model):
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    index = models.PositiveIntegerField(
        help_text="Position de la question dans le quiz (1 à 10).",
    )
    prompt = models.TextField(help_text="Énoncé de la question.")
    options = models.JSONField(
        help_text="Liste des 4 options (chaînes). Ex : ['Paris', 'Londres', 'Madrid', 'Berlin']",
    )
    correct_index = models.PositiveSmallIntegerField(
        help_text="Index (0 à 3) de la bonne réponse dans `options`.",
    )
    # [Lot 6 — Révision des erreurs] Dernière réponse donnée par l'utilisateur.
    # None = pas encore répondu. On stocke la DERNIÈRE tentative pour pouvoir
    # lister les questions ratées (selected_index != correct_index).
    selected_index = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Dernier index (0 à 3) choisi par l'utilisateur (None si pas répondu).",
    )

    class Meta:
        ordering = ["index"]
        unique_together = [("quiz", "index")]
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self) -> str:
        return f"Q{self.index} — {self.prompt[:50]}…"
