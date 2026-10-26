"""Chef d'orchestre du RAG : answer_question() enchaîne toutes les étapes de la requête.

Langue -> recherche des chunks -> refus si rien d'assez proche -> LLM -> sources.
C'est cette fonction que l'API (main.py) appelle à chaque question.
"""

import re
import time
from collections.abc import Callable

from src import config, generator, guards, prompts, query_rewriter, retriever
from src.language import detect_language

CITATION = re.compile(r"\[(\d+)\]")


def build_sources(chunks: list[dict], answer: str) -> list[dict]:
    """Prépare la liste des sources à renvoyer : fichier, page, extrait, lien, score.

    On ne garde que les extraits que le modèle a cités ([1], [3]...). S'il n'en
    a cité aucun, on garde tous les extraits fournis : une réponse a toujours
    au moins une source (mesure de succès du PRD).
    """
    cited = {int(number) for number in CITATION.findall(answer)}
    selected = [
        (number, chunk) for number, chunk in enumerate(chunks, start=1) if number in cited
    ] or list(enumerate(chunks, start=1))
    return [
        {
            "id": number,
            "file": chunk["file"],
            "page": chunk["page"],
            "excerpt": chunk["text"][: config.EXCERPT_CHARS],
            "url": chunk["url"],
            "score": round(chunk["score"], 3),
        }
        for number, chunk in selected
    ]


def refusal(kind: str, language: str, duration: float) -> dict:
    """Réponse de refus poli (sans source) : « pas dans mes documents » ou « pas d'opinion »."""
    return {
        "answer": prompts.REFUSAL_MESSAGES[kind][language],
        "language": language,
        "found": False,
        "sources": [],
        "duration_seconds": round(duration, 2),
    }


def answer_question(
    question: str,
    theme: str | None = None,
    retrieve_fn: Callable[..., list[dict]] = retriever.retrieve,
    generate_fn: Callable[[str, str], str] = generator.generate_answer,
    rewrite_fn: Callable[[str], list[str]] = query_rewriter.rewrite_query,
) -> dict:
    """Répond à une question avec ses sources.

    retrieve_fn, generate_fn et rewrite_fn peuvent être remplacées dans les tests, pour
    ne pas avoir besoin du vrai modèle d'embeddings ni du vrai LLM.
    """
    started = time.time()
    language = detect_language(question)

    # Filtres rapides, avant toute recherche : avis politique, langue non prise en charge
    if guards.looks_like_opinion_request(question):
        return refusal("opinion", language, time.time() - started)
    if guards.is_unsupported_language(question):
        return refusal("unsupported_language", language, time.time() - started)

    # Question à plusieurs volets : on la découpe en questions simples pour que chaque volet
    # retrouve ses propres passages (si le découpage échoue, la recherche reste classique)
    sub_queries = rewrite_fn(question) if config.QUERY_REWRITING else []
    if sub_queries:
        chunks = retrieve_fn(question, theme=theme, sub_queries=sub_queries)
    else:
        chunks = retrieve_fn(question, theme=theme)
    if not retriever.has_answer(chunks):
        # Aucun passage assez proche : on ne dérange même pas le LLM (FR-7)
        return refusal("no_answer", language, time.time() - started)

    raw_answer = generate_fn(prompts.SYSTEM_PROMPT, prompts.build_user_prompt(question, language, chunks))

    if prompts.NO_ANSWER in raw_answer:
        return refusal("no_answer", language, time.time() - started)
    if prompts.OPINION in raw_answer:
        return refusal("opinion", language, time.time() - started)

    return {
        "answer": raw_answer,
        "language": language,
        "found": True,
        "sources": build_sources(chunks, raw_answer),
        "duration_seconds": round(time.time() - started, 2),
    }
