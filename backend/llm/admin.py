"""Enregistrement de la config LLM dans le Django admin."""

from django.contrib import admin

from .models import LLMConfig


@admin.register(LLMConfig)
class LLMConfigAdmin(admin.ModelAdmin):
    list_display = ("backend", "model", "updated_at")
