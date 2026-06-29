"""
Endpoints quizz :
    GET   /api/quizzes/                — historique du user connecté
    GET   /api/quizzes/<id>/           — détail (avec les 10 questions)
    POST  /api/quizzes/<id>/answer/    — soumet 10 réponses, renvoie le score
"""

from django.db.models import Avg, Count, F, Max
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Question, Quiz
from .serializers import (
    QuizSerializer,
    QuizSummarySerializer,
    SubmitAnswersSerializer,
)


class QuizListView(generics.ListAPIView):
    """Historique des quizz du user connecté."""

    serializer_class = QuizSummarySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user).order_by("-created_at")

    @extend_schema(description="Liste paginée des quizz de l'utilisateur connecté.")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class QuizDetailView(generics.RetrieveAPIView):
    """Détail d'un quiz (les 10 questions complètes)."""

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)


class AnswerQuizView(APIView):
    """Reçoit 10 réponses, calcule le score, met à jour le quiz."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=SubmitAnswersSerializer,
        responses={200: OpenApiResponse(description="{ score, total, details }")},
        description=(
            "Soumet les 10 réponses et reçoit le détail de la correction. "
            "Le score est persisté sur le quiz."
        ),
    )
    def post(self, request, pk: int):
        quiz = get_object_or_404(Quiz, pk=pk, user=request.user)

        serializer = SubmitAnswersSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data["answers"]

        # Index pour lookup rapide
        questions_by_idx = {q.index: q for q in quiz.questions.all()}
        if len(questions_by_idx) != 10:
            return Response(
                {"detail": "Ce quiz n'a pas 10 questions — état incohérent."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        details = []
        score = 0
        for ans in answers:
            q = questions_by_idx[ans["index"]]
            correct = q.correct_index == ans["selected_index"]
            if correct:
                score += 1
            # [Lot 6] On mémorise la réponse choisie pour la révision des erreurs.
            q.selected_index = ans["selected_index"]
            q.save(update_fields=["selected_index"])
            details.append(
                {
                    "index": ans["index"],
                    "selected_index": ans["selected_index"],
                    "correct_index": q.correct_index,
                    "correct": correct,
                }
            )

        quiz.score = score
        quiz.save(update_fields=["score", "updated_at"])

        return Response(
            {
                "score": score,
                "total": 10,
                "details": details,
            }
        )


# ---------------------------------------------------------------------------
# MVP2 — Dashboard de progression (Lot 6)
# ---------------------------------------------------------------------------


class StatsView(APIView):
    """Statistiques de progression de l'utilisateur connecté.

    [Note pédagogique] On agrège côté base de données (Avg, Count, Max…) plutôt
    que de tout charger en Python : c'est plus rapide et ça montre la puissance
    de l'ORM Django. `taken` = quiz réellement passés (score non nul).
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiResponse(description="KPIs + historique des scores")})
    def get(self, request):
        quizzes = Quiz.objects.filter(user=request.user)
        taken = quizzes.filter(score__isnull=False)

        agg = taken.aggregate(avg=Avg("score"), best=Max("score"), nb=Count("id"))
        nb_taken = agg["nb"] or 0

        # Précision globale sur les questions répondues (toutes tentatives confondues).
        answered = Question.objects.filter(quiz__user=request.user, selected_index__isnull=False)
        nb_answered = answered.count()
        nb_correct = answered.filter(selected_index=F("correct_index")).count()

        # Historique chronologique des scores (pour le graphique de progression).
        history = [
            {
                "id": q.id,
                "title": q.title,
                "score": q.score,
                "created_at": q.created_at,
            }
            for q in taken.order_by("created_at")
        ]

        return Response(
            {
                "total_quizzes": quizzes.count(),
                "quizzes_taken": nb_taken,
                "average_score": round(agg["avg"], 1) if agg["avg"] is not None else None,
                "best_score": agg["best"],
                "last_score": history[-1]["score"] if history else None,
                "questions_answered": nb_answered,
                "questions_correct": nb_correct,
                "accuracy": round(100 * nb_correct / nb_answered) if nb_answered else None,
                "history": history,
            }
        )


# ---------------------------------------------------------------------------
# MVP2 — Révision des erreurs (Lot 6)
# ---------------------------------------------------------------------------


class MistakesView(APIView):
    """Liste les questions ratées (dernière réponse incorrecte) de l'utilisateur."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: OpenApiResponse(description="Liste des questions ratées")})
    def get(self, request):
        wrong = (
            Question.objects.filter(quiz__user=request.user, selected_index__isnull=False)
            .exclude(selected_index=F("correct_index"))
            .select_related("quiz")
            .order_by("-quiz__created_at", "index")
        )
        items = [
            {
                "quiz_id": q.quiz_id,
                "quiz_title": q.quiz.title,
                "index": q.index,
                "prompt": q.prompt,
                "options": q.options,
                "correct_index": q.correct_index,
                "selected_index": q.selected_index,
            }
            for q in wrong
        ]
        return Response({"count": len(items), "mistakes": items})
