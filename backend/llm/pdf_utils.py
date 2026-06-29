"""Utilitaires de parsing de PDF.

On utilise `pypdf` (léger, sans dépendance OCR — les PDF scannés ne marchent
pas, c'est une limitation acceptée du MVP. L'OCR pourra être ajouté dans
les pistes Release 2 par les équipes).
"""

import io

import pypdf

MAX_PDF_SIZE_BYTES = 5 * 1024 * 1024  # 5 Mo


class PDFError(Exception):
    """Erreur lors du parsing PDF."""


def extract_text_from_pdf(file_obj) -> str:
    """Extrait le texte d'un fichier PDF.

    Args:
        file_obj: file-like object (request.FILES['pdf']) ou bytes.

    Returns:
        Texte concaténé de toutes les pages, séparé par des sauts de ligne.

    Raises:
        PDFError: si le fichier dépasse 5 Mo, est corrompu, ou contient
                  uniquement des images (texte vide).
    """
    if hasattr(file_obj, "size") and file_obj.size > MAX_PDF_SIZE_BYTES:
        raise PDFError(f"PDF trop volumineux (> {MAX_PDF_SIZE_BYTES // (1024*1024)} Mo).")

    try:
        # pypdf accepte aussi des bytes — on enveloppe au besoin
        if isinstance(file_obj, bytes | bytearray):
            file_obj = io.BytesIO(file_obj)
        reader = pypdf.PdfReader(file_obj)
    except Exception as exc:
        raise PDFError(f"Impossible d'ouvrir le PDF : {exc}") from exc

    if reader.is_encrypted:
        raise PDFError("Le PDF est protégé par mot de passe.")

    pages_text = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            pages_text.append(text)

    full_text = "\n\n".join(pages_text).strip()
    if not full_text:
        raise PDFError(
            "Aucun texte extractible (PDF scanné ou vide). " "L'OCR n'est pas inclus dans le MVP."
        )

    return full_text
