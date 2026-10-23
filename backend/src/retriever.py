"""Récupération des chunks les plus proches d'une question (FR-4).

Si même le meilleur chunk est trop peu proche (score sous le seuil du fichier
config.py), on considère que la réponse n'est pas dans le corpus : c'est ce
qui permet de refuser de répondre au lieu d'inventer (FR-7).
"""

from collections.abc import Callable

from src import config, embeddings, vectorstore
from src.language import detect_language


def retrieve(
    question: str,
    top_k: int = config.TOP_K,
    theme: str | None = None,
    collection=None,
    embed_fn: Callable[[str], list[float]] = embeddings.embed_query,
    other_language_slots: int | None = None,
) -> list[dict]:
    """Renvoie les top_k chunks les plus proches de la question, du meilleur au moins bon.

    Un modèle multilingue préfère les textes écrits dans la langue de la question : une
    question en français ramène surtout des textes français, même si la réponse est dans
    une loi écrite en arabe. Pour y remédier, other_language_slots places sur les top_k
    sont réservées aux meilleurs chunks de l'AUTRE langue (0 = recherche classique).

    embed_fn est le calcul du vecteur de la question : on peut le remplacer
    dans les tests, pour ne pas avoir à charger le vrai modèle.
    """
    collection = collection or vectorstore.get_collection()
    slots = config.OTHER_LANGUAGE_SLOTS if other_language_slots is None else other_language_slots
    vector = embed_fn(question)

    if slots <= 0:
        return vectorstore.search(collection, vector, top_k=top_k, theme=theme)

    language = detect_language(question)
    other = "ar" if language == "fr" else "fr"
    same_language = vectorstore.search(collection, vector, top_k=top_k - slots, theme=theme, language=language)
    other_language = vectorstore.search(collection, vector, top_k=slots, theme=theme, language=other)
    return sorted(same_language + other_language, key=lambda chunk: chunk["score"], reverse=True)


def has_answer(results: list[dict], threshold: float = config.SCORE_THRESHOLD) -> bool:
    """Vrai si le meilleur chunk est assez proche de la question pour tenter une réponse."""
    return bool(results) and results[0]["score"] >= threshold
