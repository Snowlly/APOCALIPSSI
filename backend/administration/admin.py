"""Enregistrement dans le Django admin (utile en complément de l'UI React)."""

from django.contrib import admin

from .models import SiteConfig


@admin.register(SiteConfig)
class SiteConfigAdmin(admin.ModelAdmin):
    list_display = (
        "app_name",
        "allow_signups",
        "require_email_verification",
        "banner_enabled",
        "updated_at",
    )
