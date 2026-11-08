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
    sub_queries: list[str] | None = None,
) -> list[dict]:
    """Renvoie les top_k chunks les plus proches de la question, du meilleur au moins bon.

    Un modèle multilingue préfère les textes écrits dans la langue de la question : une
    question en français ramène surtout des textes français, même si la réponse est dans
    une loi écrite en arabe. Pour y remédier, au moins other_language_slots places sur les top_k
    sont garanties aux meilleurs chunks de l'AUTRE langue (0 = recherche classique). C'est un
    MINIMUM : si les meilleurs chunks sont tous dans l'autre langue, ils gardent leurs places.

    Pour une question à plusieurs volets, sub_queries contient les questions simples tirées
    de la question (voir query_rewriter) : on cherche pour chacune, puis on mélange les listes
    « un à tour de rôle » pour que chaque volet ait ses places parmi les top_k.

    embed_fn est le calcul du vecteur de la question : on peut le remplacer
    dans les tests, pour ne pas avoir à charger le vrai modèle.
    """
    collection = collection or vectorstore.get_collection()
    slots = config.OTHER_LANGUAGE_SLOTS if other_language_slots is None else other_language_slots
    slots = min(slots, top_k - 1)  # au moins une place reste pour la langue de la question

    language = detect_language(question)  # la langue de la question d'origine, pas celle d'une reformulation
    other = "ar" if language == "fr" else "fr"

    def search_one(text: str) -> list[dict]:
        vector = embed_fn(text)
        best = vectorstore.search(collection, vector, top_k=top_k, theme=theme)
        if slots <= 0:
            return best
        best_other = vectorstore.search(collection, vector, top_k=slots, theme=theme, language=other)
        return reserve_slots(best, best_other, slots, other)

    results = search_one(question)
    if not sub_queries:
        return results
    return interleave([results] + [search_one(text) for text in sub_queries], top_k, slots, other)


def chunk_key(chunk: dict) -> tuple[str, int, str]:
    return (chunk["file"], chunk["page"], chunk["text"][:60])


def reserve_slots(selected: list[dict], other_language_chunks: list[dict], slots: int, other: str) -> list[dict]:
    """Garantit au moins `slots` chunks de la langue `other` parmi `selected` (rangés du meilleur au moins bon).

    Si le minimum n'est pas atteint, les meilleurs chunks de l'autre langue (other_language_chunks)
    prennent la place des DERNIERS chunks de la langue de la question. Si le minimum est déjà atteint,
    rien ne change : un texte écrit uniquement dans l'autre langue n'est donc jamais plafonné.
    Le résultat est trié par score (le premier chunk reste le plus proche, ce que has_answer attend).
    """
    selected = list(selected)
    missing = slots - sum(1 for chunk in selected if chunk["language"] == other)
    if missing > 0:
        present = {chunk_key(chunk) for chunk in selected}
        additions = [chunk for chunk in other_language_chunks if chunk_key(chunk) not in present][:missing]
        for _ in additions:
            for index in range(len(selected) - 1, -1, -1):
                if selected[index]["language"] != other:
                    del selected[index]
                    break
        selected += additions
    return sorted(selected, key=lambda chunk: chunk["score"], reverse=True)


def interleave(lists: list[list[dict]], top_k: int, slots: int = 0, other: str | None = None) -> list[dict]:
    """Prend le meilleur chunk de chaque liste, puis le deuxième de chaque liste, etc. (sans doublon).

    Si slots > 0, au moins `slots` chunks de la langue `other` sont garantis dans le résultat (voir
    reserve_slots) : sans cela, les chunks de l'autre langue, moins bien notés, ne passaient jamais
    la coupe quand on mélangeait plusieurs listes. Le résultat est trié par score.
    """
    seen: set[tuple[str, int, str]] = set()
    merged: list[dict] = []
    leftovers: list[dict] = []   # les chunks non retenus, dans l'ordre du tour de table
    for rank in range(max(len(chunks) for chunks in lists)):
        for chunks in lists:
            if rank >= len(chunks):
                continue
            chunk = chunks[rank]
            key = chunk_key(chunk)
            if key in seen:
                continue
            seen.add(key)
            (merged if len(merged) < top_k else leftovers).append(chunk)
    if slots > 0 and other:
        return reserve_slots(merged, [chunk for chunk in leftovers if chunk["language"] == other], slots, other)
    return sorted(merged, key=lambda chunk: chunk["score"], reverse=True)


def has_answer(results: list[dict], threshold: float = config.SCORE_THRESHOLD) -> bool:
    """Vrai si le meilleur chunk est assez proche de la question pour tenter une réponse."""
    return bool(results) and results[0]["score"] >= threshold
