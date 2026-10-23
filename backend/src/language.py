"""Détection de la langue d'une question (français ou arabe), utilisée par la recherche et par rag.py."""

import re

ARABIC_LETTERS = re.compile("[؀-ۿ]")


def detect_language(text: str) -> str:
    """Renvoie « ar » si la question contient surtout de l'arabe, sinon « fr »."""
    letters = [char for char in text if char.isalpha()]
    if not letters:
        return "fr"
    arabic = sum(1 for char in letters if ARABIC_LETTERS.match(char))
    return "ar" if arabic / len(letters) > 0.3 else "fr"
