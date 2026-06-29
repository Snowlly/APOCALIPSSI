"""
Endpoints LLM :
    GET  /api/llm/ping/           — vérifie l'intégration Ollama
    POST /api/llm/generate-quiz/  — génère un quiz à partir d'un PDF ou d'un texte
"""

import requests
from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from quizzes.models import Question, Quiz
from quizzes.serializers import QuizSerializer

from .pdf_utils import PDFError, extract_text_from_pdf
from .serializers import GenerateQuizSerializer
from .services import get_llm_client
from .services.base import LLMError


class PingView(APIView):
    """Vérifie que le backend voit Ollama (ou que le mock répond)."""

    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: OpenApiResponse(description="{ backend, model, ollama_alive, message }")},
        description="Ping LLM — utile pour vérifier l'intégration Ollama.",
    )
    def get(self, _request):
        # Config EFFECTIVE (base prioritaire, repli .env) — Lot 8.
        from .services.factory import resolve_active

        conf = resolve_active()
        backend = conf["backend"]

        if backend == "mock":
            return Response(
                {
                    "backend": "mock",
                    "model": "mock-model",
                    "ollama_alive": False,
                    "message": "Mock LLM actif (choisissez un autre fournisseur dans l'admin).",
                }
            )

        if backend != "ollama":
            # Backend cloud : pas de ping HTTP ici (éviter de consommer du quota).
            return Response(
                {
                    "backend": backend,
                    "model": conf["model"],
                    "message": f"Backend cloud « {backend} » configuré.",
                }
            )

        host = conf["ollama_host"] or settings.OLLAMA_HOST
        model = conf["model"] or settings.OLLAMA_MODEL
        try:
            resp = requests.get(f"{host}/api/tags", timeout=2)
            resp.raise_for_status()
            tags = resp.json().get("models", [])
            target = model.split(":")[0]
            model_present = any(m.get("name", "").startswith(target) for m in tags)
            return Response(
                {
                    "backend": "ollama",
                    "model": model,
                    "ollama_alive": True,
                    "model_loaded": model_present,
                    "message": (
                        "Ollama répond ✓"
                        if model_present
                        else f"Ollama répond mais le modèle {model} n'est pas téléchargé. "
                        "Lancez : make pull-model"
                    ),
                }
            )
        except requests.RequestException as exc:
            return Response(
                {
                    "backend": "ollama",
                    "model": model,
                    "ollama_alive": False,
                    "message": f"Ollama injoignable : {exc}",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


class GenerateQuizView(APIView):
    """Génère un quiz de 10 QCM à partir d'un PDF ou d'un texte collé."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        request=GenerateQuizSerializer,
        responses={201: QuizSerializer},
        description=(
            "Génère 10 QCM à partir d'un cours. Fournir soit `pdf` (multipart) "
            "soit `source_text` (≥ 200 caractères). Le quiz est sauvegardé en "
            "DB et associé à l'utilisateur connecté."
        ),
    )
    def post(self, request):
        # Lot 8 : si l'admin exige un email vérifié, on bloque sinon.
        from accounts.models import get_or_create_profile
        from administration.models import SiteConfig

        if (
            SiteConfig.load().require_email_verification
            and not get_or_create_profile(request.user).email_verified
        ):
            return Response(
                {"detail": "Veuillez confirmer votre adresse email avant de générer un quiz."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = GenerateQuizSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.validated_data["title"]
        pdf_file = serializer.validated_data.get("pdf")
        source_text = (serializer.validated_data.get("source_text") or "").strip()

        # 1. Extraction du texte source
        if pdf_file:
            try:
                source_text = extract_text_from_pdf(pdf_file)
            except PDFError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Appel LLM (Ollama ou Mock)
        try:
            questions_data = get_llm_client().generate_quiz(source_text=source_text, title=title)
        except LLMError as exc:
            return Response(
                {"detail": f"Échec génération LLM : {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 3. Persistance — Quiz + 10 Questions dans une transaction
        from django.db import transaction

        with transaction.atomic():
            quiz = Quiz.objects.create(
                user=request.user,
                title=title,
                source_text=source_text,
            )
            for i, q in enumerate(questions_data, start=1):
                Question.objects.create(
                    quiz=quiz,
                    index=i,
                    prompt=q["prompt"],
                    options=q["options"],
                    correct_index=q["correct_index"],
                )

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)
