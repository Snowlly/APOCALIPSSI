"""Tests de l'app administration (Lot 8)."""

import pytest
from django.contrib.auth.models import User
from django.test import override_settings
from rest_framework.test import APIClient

from administration.models import SiteConfig
from llm.models import LLMConfig

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client() -> APIClient:
    admin = User.objects.create_user(
        username="admin@test.com",
        email="admin@test.com",
        password="motdepasse123",
        is_staff=True,
    )
    c = APIClient()
    c.force_authenticate(user=admin)
    return c


@pytest.fixture
def user_client() -> APIClient:
    u = User.objects.create_user(
        username="lambda@test.com",
        email="lambda@test.com",
        password="motdepasse123",
    )
    c = APIClient()
    c.force_authenticate(user=u)
    return c


# --- Permissions ---


def test_admin_endpoints_require_staff(user_client):
    assert user_client.get("/api/admin/stats/").status_code == 403
    assert user_client.get("/api/admin/users/").status_code == 403
    assert user_client.get("/api/admin/llm-config/").status_code == 403


def test_public_site_config_is_open():
    r = APIClient().get("/api/site-config/")
    assert r.status_code == 200
    assert "app_name" in r.data
    assert "allow_signups" in r.data


# --- Config du site ---


def test_site_config_patch(admin_client):
    r = admin_client.patch(
        "/api/admin/site-config/", {"app_name": "QuizTeam", "allow_signups": False}, format="json"
    )
    assert r.status_code == 200
    assert r.data["app_name"] == "QuizTeam"
    assert SiteConfig.load().allow_signups is False


def test_allow_signups_false_blocks_signup(admin_client):
    admin_client.patch("/api/admin/site-config/", {"allow_signups": False}, format="json")
    r = APIClient().post(
        "/api/accounts/signup/",
        {"email": "new@test.com", "password": "motdepasse123"},
        format="json",
    )
    assert r.status_code == 403


# --- Config LLM ---


def test_llm_config_get_lists_providers_and_masks_keys(admin_client):
    r = admin_client.get("/api/admin/llm-config/")
    assert r.status_code == 200
    keys = {p["key"] for p in r.data["providers"]}
    assert {"ollama", "gemini", "groq", "mock"}.issubset(keys)
    assert "api_keys_set" in r.data
    assert "api_key" not in r.data["effective"]  # jamais la clé en clair


def test_llm_config_patch_sets_backend_and_key(admin_client):
    r = admin_client.patch(
        "/api/admin/llm-config/",
        {"backend": "groq", "api_keys": {"groq": "secret-key"}},
        format="json",
    )
    assert r.status_code == 200
    cfg = LLMConfig.load()
    assert cfg.backend == "groq"
    assert cfg.api_keys.get("groq") == "secret-key"
    assert r.data["api_keys_set"]["groq"] is True  # marquée comme définie
    # La clé ne doit jamais ressortir en clair dans la réponse.
    assert "secret-key" not in str(r.data)


def test_llm_config_rejects_unknown_backend(admin_client):
    r = admin_client.patch("/api/admin/llm-config/", {"backend": "inexistant"}, format="json")
    assert r.status_code == 400


# --- Gestion des utilisateurs ---


def test_admin_can_deactivate_user(admin_client):
    target = User.objects.create_user(username="t@test.com", email="t@test.com", password="x")
    r = admin_client.patch(f"/api/admin/users/{target.id}/", {"is_active": False}, format="json")
    assert r.status_code == 200
    target.refresh_from_db()
    assert target.is_active is False


def test_admin_cannot_modify_self(admin_client):
    me = User.objects.get(email="admin@test.com")
    r = admin_client.patch(f"/api/admin/users/{me.id}/", {"is_active": False}, format="json")
    assert r.status_code == 400


def test_admin_can_delete_user(admin_client):
    target = User.objects.create_user(username="d@test.com", email="d@test.com", password="x")
    r = admin_client.delete(f"/api/admin/users/{target.id}/")
    assert r.status_code == 204
    assert not User.objects.filter(id=target.id).exists()


# --- Stats ---


def test_stats(admin_client):
    r = admin_client.get("/api/admin/stats/")
    assert r.status_code == 200
    assert r.data["users_total"] >= 1
    assert "quizzes_total" in r.data


# --- Exigence de validation d'email sur la génération de quiz ---


@override_settings(LLM_BACKEND="mock")
def test_require_email_verification_blocks_generation(admin_client, user_client):
    admin_client.patch(
        "/api/admin/site-config/", {"require_email_verification": True}, format="json"
    )
    # user_client n'a pas d'email vérifié -> génération refusée
    r = user_client.post(
        "/api/llm/generate-quiz/", {"title": "X", "source_text": "x" * 200}, format="multipart"
    )
    assert r.status_code == 403
