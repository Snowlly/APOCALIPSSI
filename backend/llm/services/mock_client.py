"""
Mock LLM — utile pour les tests / dev sans Ollama.

Génère 10 questions plausibles à partir des premiers mots du source_text.
Activé via : LLM_BACKEND=mock dans le .env
"""

import random

from .base import LLMClient


class MockLLMClient(LLMClient):
    """Génère des QCM déterministes (seed sur le texte) — pour tests."""

    def generate_quiz(self, source_text: str, title: str) -> list[dict]:
        # Seed déterministe — même texte → mêmes QCM (utile en tests)
        rng = random.Random(hash(source_text) % 2**31)
        words = [w for w in source_text.split() if len(w) > 3][:30]
        if not words:
            words = ["concept", "notion", "élément", "principe", "exemple", "définition"]

        questions: list[dict] = []
        for i in range(1, 11):
            word = words[i % len(words)] if words else f"point{i}"
            correct_idx = rng.randint(0, 3)
            options = [
                f"Réponse A à propos de '{word}'",
                f"Réponse B à propos de '{word}'",
                f"Réponse C à propos de '{word}'",
                f"Réponse D à propos de '{word}'",
            ]
            options[correct_idx] = f"✓ Bonne réponse mock pour '{word}' (question {i})"
            questions.append(
                {
                    "prompt": f"[MOCK Q{i}] D'après le cours « {title} », quelle affirmation est correcte sur « {word} » ?",
                    "options": options,
                    "correct_index": correct_idx,
                }
            )
        return questions
