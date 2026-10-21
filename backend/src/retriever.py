"""Récupération des chunks les plus proches d'une question (FR-4).

Si même le meilleur chunk est trop peu proche (score sous le seuil du fichier
config.py), on considère que la réponse n'est pas dans le corpus : c'est ce
qui permet de refuser de répondre au lieu d'inventer (FR-7).
"""

from collections.abc import Callable

from src import config, embeddings, vectorstore


def retrieve(
    question: str,
    top_k: int = config.TOP_K,
    theme: str | None = None,
    collection=None,
    embed_fn: Callable[[str], list[float]] = embeddings.embed_query,
) -> list[dict]:
    """Renvoie les top_k chunks les plus proches de la question, du meilleur au moins bon.

    embed_fn est le calcul du vecteur de la question : on peut le remplacer
    dans les tests, pour ne pas avoir à charger le vrai modèle.
    """
    collection = collection or vectorstore.get_collection()
    return vectorstore.search(collection, embed_fn(question), top_k=top_k, theme=theme)


def has_answer(results: list[dict], threshold: float = config.SCORE_THRESHOLD) -> bool:
    """Vrai si le meilleur chunk est assez proche de la question pour tenter une réponse."""
    return bool(results) and results[0]["score"] >= threshold
