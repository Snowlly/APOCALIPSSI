"""Sérialiseurs de l'app administration (Lot 8)."""

from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.models import get_or_create_profile

from .models import SiteConfig


class SiteConfigSerializer(serializers.ModelSerializer):
    """Config du site — version admin (tous les champs modifiables)."""

    class Meta:
        model = SiteConfig
        fields = [
            "app_name",
            "allow_signups",
            "require_email_verification",
            "banner_enabled",
            "banner_message",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class SiteConfigPublicSerializer(serializers.ModelSerializer):
    """Config du site — version PUBLIQUE (ce que le front a le droit de connaître)."""

    class Meta:
        model = SiteConfig
        fields = ["app_name", "allow_signups", "banner_enabled", "banner_message"]


class AdminUserSerializer(serializers.ModelSerializer):
    """Vue admin d'un utilisateur (lecture)."""

    email_verified = serializers.SerializerMethodField()
    quiz_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "is_active",
            "is_staff",
            "is_superuser",
            "email_verified",
            "quiz_count",
        ]
        read_only_fields = fields

    def get_email_verified(self, obj) -> bool:
        return get_or_create_profile(obj).email_verified

    def get_quiz_count(self, obj) -> int:
        return obj.quizzes.count()


class AdminUserUpdateSerializer(serializers.Serializer):
    """Champs modifiables par un admin sur un utilisateur."""

    is_active = serializers.BooleanField(required=False)
    is_staff = serializers.BooleanField(required=False)
    email_verified = serializers.BooleanField(required=False)


class LLMConfigUpdateSerializer(serializers.Serializer):
    """Entrée pour modifier la config LLM depuis l'admin.

    `api_keys` est un dict {provider: clé}. Une valeur vide ("") EFFACE la clé du
    fournisseur ; une valeur absente la laisse inchangée.
    """

    backend = serializers.CharField(required=False, allow_blank=True)
    model = serializers.CharField(required=False, allow_blank=True)
    ollama_host = serializers.CharField(required=False, allow_blank=True)
    timeout = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    api_keys = serializers.DictField(
        child=serializers.CharField(allow_blank=True),
        required=False,
    )
