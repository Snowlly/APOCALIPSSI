"""
Endpoints d'administration (Lot 8). Tous réservés aux comptes staff
(`IsAdminUser`), sauf l'endpoint PUBLIC de config du site.

    GET   /api/site-config/                  — (public) nom app, bannière, inscriptions
    GET   /api/admin/stats/                  — vue d'ensemble
    GET   /api/admin/site-config/            — lire la config du site
    PATCH /api/admin/site-config/            — modifier la config du site
    GET   /api/admin/llm-config/             — config LLM + fournisseurs + aide
    PATCH /api/admin/llm-config/             — modifier la config LLM
    GET   /api/admin/users/?q=...            — liste + recherche d'utilisateurs
    PATCH /api/admin/users/<id>/             — activer/désactiver, rôle, email vérifié
    DELETE /api/admin/users/<id>/            — supprimer un compte
    POST  /api/admin/users/<id>/resend-verification/ — renvoyer l'email de validation
    POST  /api/admin/seed/                   — insérer des données de démo
    POST  /api/admin/reset-data/             — VIDER la base (destructif, confirmé)
"""

import logging

from django.contrib.auth.models import User
from django.core.management import call_command
from django.db.models import Avg, Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.emails import EmailError, send_verification_email
from accounts.models import get_or_create_profile
from llm.models import LLMConfig
from llm.providers import PROVIDERS
from quizzes.models import Question, Quiz

from .models import SiteConfig
from .serializers import (
    AdminUserSerializer,
    AdminUserUpdateSerializer,
    LLMConfigUpdateSerializer,
    SiteConfigPublicSerializer,
    SiteConfigSerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public : config minimale du site (le front s'y adapte)
# ---------------------------------------------------------------------------


class PublicSiteConfigView(APIView):
    """Config PUBLIQUE : nom de l'app, bannière, inscriptions ouvertes."""

    permission_classes = [AllowAny]

    @extend_schema(responses={200: SiteConfigPublicSerializer})
    def get(self, request):
        return Response(SiteConfigPublicSerializer(SiteConfig.load()).data)


# ---------------------------------------------------------------------------
# Config du site (admin)
# ---------------------------------------------------------------------------


class SiteConfigAdminView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: SiteConfigSerializer})
    def get(self, request):
        return Response(SiteConfigSerializer(SiteConfig.load()).data)

    @extend_schema(request=SiteConfigSerializer, responses={200: SiteConfigSerializer})
    def patch(self, request):
        serializer = SiteConfigSerializer(SiteConfig.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ---------------------------------------------------------------------------
# Config LLM (admin) — choix fournisseur + modèle + clés + AIDE par fournisseur
# ---------------------------------------------------------------------------


class LLMConfigAdminView(APIView):
    permission_classes = [IsAdminUser]

    def _providers_payload(self) -> list[dict]:
        """Liste des fournisseurs avec leur aide (pour l'UI)."""
        return [
            {
                "key": p.key,
                "label": p.label,
                "cloud": p.cloud,
                "paid": p.paid,
                "needs_key": p.needs_key,
                "default_model": p.default_model,
                "help": p.help,
                "keys_url": p.keys_url,
            }
            for p in PROVIDERS.values()
        ]

    def _serialize(self, cfg: LLMConfig) -> dict:
        from llm.services.factory import resolve_active

        # On NE renvoie JAMAIS les clés en clair : seulement « définie ou non ».
        api_keys_set = {k: bool((cfg.api_keys or {}).get(k)) for k in PROVIDERS}
        return {
            "backend": cfg.backend,
            "model": cfg.model,
            "ollama_host": cfg.ollama_host,
            "timeout": cfg.timeout,
            "api_keys_set": api_keys_set,
            "providers": self._providers_payload(),
            "effective": resolve_active(),  # ce qui sera RÉELLEMENT utilisé (repli .env)
        }

    @extend_schema(responses={200: OpenApiResponse(description="Config LLM + fournisseurs")})
    def get(self, request):
        payload = self._serialize(LLMConfig.load())
        # Ne pas exposer la clé effective en clair non plus.
        payload["effective"].pop("api_key", None)
        return Response(payload)

    @extend_schema(
        request=LLMConfigUpdateSerializer,
        responses={200: OpenApiResponse(description="Config LLM mise à jour")},
    )
    def patch(self, request):
        serializer = LLMConfigUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "backend" in data and data["backend"] and data["backend"] not in PROVIDERS:
            return Response(
                {"backend": [f"Fournisseur inconnu : {data['backend']}."]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cfg = LLMConfig.load()
        if "backend" in data:
            cfg.backend = data["backend"]
        if "model" in data:
            cfg.model = data["model"]
        if "ollama_host" in data:
            cfg.ollama_host = data["ollama_host"]
        if "timeout" in data:
            cfg.timeout = data["timeout"]

        # Fusion des clés : valeur vide => on EFFACE la clé du fournisseur.
        if "api_keys" in data:
            keys = dict(cfg.api_keys or {})
            for provider, value in data["api_keys"].items():
                if value:
                    keys[provider] = value
                else:
                    keys.pop(provider, None)
            cfg.api_keys = keys

        cfg.save()
        payload = self._serialize(cfg)
        payload["effective"].pop("api_key", None)
        return Response(payload)


# ---------------------------------------------------------------------------
# Gestion des utilisateurs (admin)
# ---------------------------------------------------------------------------


class AdminUserListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: AdminUserSerializer(many=True)})
    def get(self, request):
        q = (request.query_params.get("q") or "").strip()
        qs = User.objects.all().order_by("-date_joined")
        if q:
            qs = qs.filter(
                Q(email__icontains=q)
                | Q(username__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
        qs = qs[:200]  # garde-fou : on plafonne (sinon ajouter une vraie pagination)
        return Response(AdminUserSerializer(qs, many=True).data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _guard(self, request, target: User) -> Response | None:
        """Empêche les actions dangereuses (auto-sabotage, toucher un superuser)."""
        if target.id == request.user.id:
            return Response(
                {"detail": "Vous ne pouvez pas modifier/supprimer votre propre compte ici."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target.is_superuser and not request.user.is_superuser:
            return Response(
                {"detail": "Action interdite sur un super-administrateur."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    @extend_schema(request=AdminUserUpdateSerializer, responses={200: AdminUserSerializer})
    def patch(self, request, pk: int):
        target = get_object_or_404(User, pk=pk)
        blocked = self._guard(request, target)
        if blocked:
            return blocked

        serializer = AdminUserUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if "is_active" in data:
            target.is_active = data["is_active"]
        if "is_staff" in data:
            target.is_staff = data["is_staff"]
        if "is_active" in data or "is_staff" in data:
            target.save(update_fields=["is_active", "is_staff"])
        if "email_verified" in data:
            profile = get_or_create_profile(target)
            profile.email_verified = data["email_verified"]
            profile.save(update_fields=["email_verified"])

        return Response(AdminUserSerializer(target).data)

    @extend_schema(responses={204: OpenApiResponse(description="Utilisateur supprimé")})
    def delete(self, request, pk: int):
        target = get_object_or_404(User, pk=pk)
        blocked = self._guard(request, target)
        if blocked:
            return blocked
        target.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminUserResendVerificationView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: OpenApiResponse(description="Email renvoyé")})
    def post(self, request, pk: int):
        target = get_object_or_404(User, pk=pk)
        try:
            send_verification_email(target)
        except EmailError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({"detail": f"Email de validation renvoyé à {target.email}."})


# ---------------------------------------------------------------------------
# Vue d'ensemble + opérations base
# ---------------------------------------------------------------------------


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: OpenApiResponse(description="Statistiques globales")})
    def get(self, request):
        users = User.objects.all()
        quizzes = Quiz.objects.all()
        taken = quizzes.filter(score__isnull=False)
        return Response(
            {
                "users_total": users.count(),
                "users_active": users.filter(is_active=True).count(),
                "users_staff": users.filter(is_staff=True).count(),
                "quizzes_total": quizzes.count(),
                "quizzes_taken": taken.count(),
                "average_score": (
                    round(taken.aggregate(a=Avg("score"))["a"], 1) if taken.exists() else None
                ),
                "questions_total": Question.objects.count(),
            }
        )


class AdminSeedView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: OpenApiResponse(description="Données de démo insérées")})
    def post(self, request):
        try:
            call_command("seed")
        except Exception as exc:  # noqa: BLE001 (on renvoie un message lisible)
            logger.exception("Echec du seed")
            return Response(
                {"detail": f"Echec du seed : {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({"detail": "Données de démo insérées (voir la commande seed)."})


class AdminResetDataView(APIView):
    """⚠️ DESTRUCTIF : vide les données. Protégé par confirmation + mot de passe."""

    permission_classes = [IsAdminUser]

    @extend_schema(responses={200: OpenApiResponse(description="Base réinitialisée")})
    def post(self, request):
        # Double confirmation : phrase exacte + mot de passe de l'admin.
        if request.data.get("confirm") != "RESET":
            return Response(
                {"detail": 'Confirmation manquante (envoyez confirm = "RESET").'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        password = request.data.get("password") or ""
        if not request.user.check_password(password):
            return Response(
                {"detail": "Mot de passe administrateur incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        include_users = bool(request.data.get("include_users"))

        # 1) Tous les quiz (et leurs questions en cascade).
        nb_quizzes = Quiz.objects.count()
        Quiz.objects.all().delete()

        nb_users = 0
        if include_users:
            # On NE supprime jamais les super-admins ni l'admin courant.
            victims = User.objects.filter(is_superuser=False).exclude(pk=request.user.pk)
            nb_users = victims.count()
            victims.delete()

        logger.warning(
            "[ADMIN] reset-data par %s : %s quiz, %s users supprimés",
            request.user.email,
            nb_quizzes,
            nb_users,
        )
        return Response(
            {
                "detail": "Base réinitialisée.",
                "deleted_quizzes": nb_quizzes,
                "deleted_users": nb_users,
            }
        )
