"""
Sérialiseurs pour l'app accounts.

[Note pédagogique] Choix « email = identifiant » : à l'inscription on ne demande
QUE l'email + le mot de passe ; en interne, username = email. Le login se fait
donc par email. On gère explicitement les doublons d'email avec un message clair.
"""

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password as django_validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import get_or_create_profile


class UserSerializer(serializers.ModelSerializer):
    """Serializer en lecture pour l'utilisateur connecté."""

    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "email_verified",
            "is_staff",
        ]
        read_only_fields = fields

    def get_email_verified(self, obj) -> bool:
        return get_or_create_profile(obj).email_verified


class SignupSerializer(serializers.ModelSerializer):
    """Inscription par EMAIL (identifiant). Le username interne = email."""

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
        help_text="Au moins 8 caractères.",
    )

    class Meta:
        model = User
        fields = ["email", "password", "first_name", "last_name"]
        extra_kwargs = {
            "email": {"required": True, "allow_blank": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        # L'email est l'identifiant -> il doit être unique (sur email ET username).
        if (
            User.objects.filter(email__iexact=value).exists()
            or User.objects.filter(username__iexact=value).exists()
        ):
            raise serializers.ValidationError(
                "Un compte existe déjà avec cet email. Connectez-vous, ou "
                "utilisez « mot de passe oublié » pour le réinitialiser."
            )
        return value

    def validate_password(self, value: str) -> str:
        try:
            django_validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop("password")
        email = validated_data["email"]
        user = User(username=email, **validated_data)  # username = email (identifiant)
        user.set_password(password)
        user.save()
        get_or_create_profile(user)  # profil avec email_verified=False
        return user


class LoginSerializer(serializers.Serializer):
    """Authentification par EMAIL + mot de passe."""

    email = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs: dict) -> dict:
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password")

        # On retrouve l'utilisateur par email (insensible à la casse), puis on
        # authentifie via son username réel. Cela fonctionne aussi pour les
        # comptes anciens dont le username diffère de l'email.
        user_obj = User.objects.filter(email__iexact=email).first()
        username = user_obj.username if user_obj else email

        user = authenticate(
            request=self.context.get("request"), username=username, password=password
        )
        if user is None:
            raise serializers.ValidationError("Email ou mot de passe invalide.")
        if not user.is_active:
            raise serializers.ValidationError("Ce compte est désactivé.")
        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Demande de réinitialisation : juste l'email."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirmation : uid + token (du lien email) + nouveau mot de passe."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    def validate_new_password(self, value: str) -> str:
        try:
            django_validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class EmailVerifySerializer(serializers.Serializer):
    """Validation d'email : le token reçu par email."""

    token = serializers.CharField()


# ---------------------------------------------------------------------------
# Gestion du profil (Lot 4) : modifier ses infos, son mot de passe, supprimer
# ---------------------------------------------------------------------------


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Modification du profil : prénom, nom et email.

    [Note pédagogique] L'email est l'identifiant (username = email en interne).
    Si l'utilisateur change d'email, on doit donc mettre à jour le username ET
    re-demander une validation (email_verified repasse à False). On gère aussi
    le cas du doublon (email déjà pris par quelqu'un d'autre).
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        extra_kwargs = {
            "email": {"required": False},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate_email(self, value: str) -> str:
        value = value.strip().lower()
        # L'email doit rester unique, SAUF s'il s'agit déjà du mien (pas un doublon).
        clash = (
            User.objects.filter(email__iexact=value).exclude(pk=self.instance.pk).exists()
            or User.objects.filter(username__iexact=value).exclude(pk=self.instance.pk).exists()
        )
        if clash:
            raise serializers.ValidationError("Cet email est déjà utilisé par un autre compte.")
        return value

    def update(self, instance: User, validated_data: dict) -> User:
        new_email = validated_data.get("email")
        email_changed = new_email is not None and new_email != instance.email

        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        if new_email is not None:
            instance.email = new_email
            instance.username = new_email  # username = email (identifiant)
        instance.save()

        # Changement d'email -> il faut le re-valider.
        if email_changed:
            profile = get_or_create_profile(instance)
            profile.email_verified = False
            profile.save(update_fields=["email_verified"])
            instance._email_changed = True  # drapeau lu par la vue pour renvoyer un email
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Changement de mot de passe : il faut connaître l'ancien (sécurité)."""

    old_password = serializers.CharField(write_only=True, style={"input_type": "password"})
    new_password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    def validate_old_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value

    def validate_new_password(self, value: str) -> str:
        try:
            django_validate_password(value, user=self.context["request"].user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class DeleteAccountSerializer(serializers.Serializer):
    """Suppression de compte : on confirme par le mot de passe (action destructive)."""

    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate_password(self, value: str) -> str:
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Mot de passe incorrect.")
        return value
