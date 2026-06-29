from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    ResendVerificationView,
    SignupView,
    VerifyEmailView,
)

urlpatterns = [
    # Authentification de base
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", MeView.as_view(), name="me"),
    # Validation d'email (lien reçu par email)
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
    # Réinitialisation de mot de passe (mot de passe oublié)
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"
    ),
    # Profil (modifier / changer mot de passe / supprimer le compte)
    path("profile/", ProfileView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
]
