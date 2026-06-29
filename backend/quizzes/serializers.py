"""Sérialiseurs pour Quiz et Question."""

from rest_framework import serializers

from .models import Question, Quiz


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["index", "prompt", "options", "correct_index"]


class QuestionPublicSerializer(serializers.ModelSerializer):
    """Version sans la bonne réponse — pour exposer le quiz à l'étudiant
    sans tricher (utilisée par K3 frontend si besoin)."""

    class Meta:
        model = Question
        fields = ["index", "prompt", "options"]


class QuizSerializer(serializers.ModelSerializer):
    """Renvoie un quiz complet avec ses 10 questions (incluant correct_index)."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "source_text", "score", "created_at", "questions"]
        read_only_fields = ["id", "created_at"]


class QuizSummarySerializer(serializers.ModelSerializer):
    """Version compacte pour la liste d'historique."""

    nb_questions = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ["id", "title", "score", "nb_questions", "created_at"]

    def get_nb_questions(self, obj: Quiz) -> int:
        return obj.questions.count()


class AnswerItemSerializer(serializers.Serializer):
    """Une réponse fournie par l'utilisateur."""

    index = serializers.IntegerField(min_value=1, max_value=10)
    selected_index = serializers.IntegerField(min_value=0, max_value=3)


class SubmitAnswersSerializer(serializers.Serializer):
    """POST /api/quizzes/<id>/answer/ — 10 réponses attendues."""

    answers = AnswerItemSerializer(many=True)

    def validate_answers(self, value):
        if len(value) != 10:
            raise serializers.ValidationError(f"10 réponses attendues, {len(value)} reçues.")
        indices = sorted(a["index"] for a in value)
        if indices != list(range(1, 11)):
            raise serializers.ValidationError("Les indices doivent couvrir 1..10 sans doublon.")
        return value
