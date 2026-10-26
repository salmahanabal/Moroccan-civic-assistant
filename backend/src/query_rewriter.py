"""Découpage d'une question à plusieurs volets en questions simples (amélioration de la Phase 5).

Une question comme « Comment sont choisis les députés, et qui devient chef du gouvernement ? »
parle de deux textes différents. Son vecteur est un mélange des deux sujets et ne ressemble
bien à aucun des deux : les bons passages arrivent trop loin dans la recherche.
On demande donc au LLM de la découper en questions courtes et complètes ; la recherche est
ensuite faite pour chacune (voir retriever.retrieve). Le LLM ne sert ICI qu'à reformuler pour
chercher : il ne voit aucun extrait et sa sortie n'est jamais montrée à l'utilisateur.
"""

import re
from collections.abc import Callable

from src import generator

MAX_SUB_QUESTIONS = 3
MAX_SUB_QUESTION_CHARS = 200
MIN_QUESTION_CHARS = 30   # une question très courte n'a qu'un seul volet

# Signes d'une question à plusieurs volets : « et », virgule, « ou », ou deux interrogatifs arabes reliés par « و »
MULTI_PART = re.compile(r"\s(?:et|ou)\s|,|،|\sو(?:ما|من|كيف|هل|كم|أين|متى|لماذا)")

REWRITE_PROMPT = (
    "Tu aides un moteur de recherche dans des textes juridiques marocains. On te donne une question "
    "d'utilisateur. Si elle contient plusieurs questions distinctes, découpe-la en 2 ou 3 questions "
    "courtes et AUTONOMES (chacune reprend le sujet complet, sans pronom ni ellipse). Si elle ne "
    "contient qu'une seule question, renvoie-la telle quelle. Garde la langue de la question. "
    "Réponds uniquement par les questions, une par ligne, sans numéro ni commentaire. "
    "N'ajoute aucune information qui n'est pas dans la question."
)


def needs_rewrite(question: str) -> bool:
    """Vrai si la question semble avoir plusieurs volets (sinon on économise un appel au LLM)."""
    return len(question) >= MIN_QUESTION_CHARS and bool(MULTI_PART.search(question))


def parse_sub_questions(raw: str, question: str) -> list[str]:
    """Nettoie la réponse du LLM : une question par ligne, sans doublon ni numéro, 3 au maximum."""
    sub_questions: list[str] = []
    for line in raw.splitlines():
        text = line.strip().lstrip("-•*0123456789.) ").strip()
        text = text[:MAX_SUB_QUESTION_CHARS]
        if len(text) < 10 or text.startswith("[["):
            continue
        if text.casefold() == question.strip().casefold() or text in sub_questions:
            continue
        sub_questions.append(text)
    return sub_questions[:MAX_SUB_QUESTIONS]


def rewrite_query(question: str, generate_fn: Callable[[str, str], str] = generator.generate_quick) -> list[str]:
    """Renvoie les sous-questions, ou une liste vide (= recherche normale) si le découpage échoue.

    Un LLM indisponible ou un quota épuisé ne doit jamais empêcher de répondre : on se
    rabat alors sur la recherche classique avec la question d'origine.
    """
    if not needs_rewrite(question):
        return []
    try:
        raw = generate_fn(REWRITE_PROMPT, question)
    except generator.LLMUnavailableError:
        return []
    return parse_sub_questions(raw, question)
