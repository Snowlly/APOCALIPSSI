"""Sérialiseurs pour les endpoints LLM (génération de quiz)."""

from rest_framework import serializers


class GenerateQuizSerializer(serializers.Serializer):
    """Input pour POST /api/llm/generate-quiz/.

    Soit `pdf` (file) soit `source_text` (str ≥ 200 chars). Un des deux est
    requis.
    """

    title = serializers.CharField(max_length=200)
    pdf = serializers.FileField(required=False)
    source_text = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs: dict) -> dict:
        pdf = attrs.get("pdf")
        source_text = (attrs.get("source_text") or "").strip()

        if not pdf and not source_text:
            raise serializers.ValidationError(
                "Fournir soit `pdf`, soit `source_text` (≥ 200 caractères)."
            )

        if not pdf and len(source_text) < 200:
            raise serializers.ValidationError(
                {
                    "source_text": "Doit faire au moins 200 caractères.",
                }
            )

        if pdf and not pdf.name.lower().endswith(".pdf"):
            raise serializers.ValidationError({"pdf": "Seuls les fichiers .pdf sont acceptés."})

        return attrs
