"""Choix de l'extrait montré pour chaque source : la phrase du passage qui répond le mieux.

Avant, on montrait les premiers caractères du passage, qui ne contiennent pas toujours la réponse.
Ici, on cherche dans le passage la phrase qui partage le plus de mots (et de nombres) avec la réponse
et la question, puis on la renvoie avec sa position pour que l'interface la surligne.

Si aucun mot n'est commun (par exemple une réponse en français qui cite un texte arabe), on ne devine
pas : on garde le début du passage, sans surlignage.
"""

import math
import re
import unicodedata

from src import config

CITATION = re.compile(r"\[\d+\]")
WORD = re.compile(r"\w+")
SENTENCE_END = re.compile(r"(?<=[.!?؟؛])\s+")   # fin de phrase (point français ou arabe, « ؟ », « ؛ »)
CLAUSE_END = re.compile(r"(?<=[,،:;])\s+")      # pour couper les phrases trop longues
MIN_MATCHES = 2                                 # mots communs minimum (sauf si un nombre correspond)

DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
ARABIC_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"})
ARABIC_PREFIXES = ("وال", "بال", "لل", "ال")

_RAW_STOPWORDS = """
le la les l un une des du de d et ou en à au aux a est sont être que qui quoi quel quelle quels quelles dans par pour
sur avec sans ce cet cette ces se sa son ses leur leurs il elle ils elles on ne pas plus où comment combien peut
peuvent faut doit doivent faire fait aussi ainsi alors donc mais si car sous entre vers chez dont lui eux y
في من على إلى الى عن أن ان إن هو هي هذا هذه ذلك التي الذي الذين ما ماذا كيف كم هل لا لم لن قد كان كل أو او و ثم بعد قبل
عند مع بين إذا اذا حيث أي
"""


def _normalize(word: str) -> str:
    """Minuscules, sans accents ni voyelles arabes, chiffres arabes -> chiffres, formes de lettres unifiées."""
    word = word.lower().translate(DIGITS)
    word = "".join(char for char in unicodedata.normalize("NFD", word) if unicodedata.category(char) != "Mn")
    return word.translate(ARABIC_LETTERS)


STOPWORDS = {_normalize(word) for word in _RAW_STOPWORDS.split()}


def stem(word: str) -> str | None:
    """Racine grossière d'un mot (ses 5 premières lettres) ; None pour un mot vide de sens."""
    word = _normalize(word)
    if word.isdigit():
        return word if len(word) >= 2 else None     # un nombre d'un seul chiffre est trop banal
    if len(word) < 3 or word in STOPWORDS:
        return None
    for prefix in ARABIC_PREFIXES:                  # « الحكومة » et « حكومة » doivent se rejoindre
        if word.startswith(prefix) and len(word) - len(prefix) >= 3:
            word = word[len(prefix):]
            break
    return None if word in STOPWORDS else word[:5]


def stems_of(text: str) -> set[str]:
    return {root for root in (stem(word) for word in WORD.findall(CITATION.sub(" ", text))) if root}


def split_spans(text: str, max_chars: int) -> list[tuple[int, int]]:
    """Découpe le texte en phrases (début, fin) ; une phrase plus longue que max_chars est recoupée aux virgules."""
    spans, start = [], 0
    for match in SENTENCE_END.finditer(text):
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(text)))

    refined = []
    for start, end in spans:
        if end - start <= max_chars:
            refined.append((start, end))
            continue
        cut = start
        for match in CLAUSE_END.finditer(text, start, end):
            refined.append((cut, match.start()))
            cut = match.end()
        refined.append((cut, end))
    return [(start, end) for start, end in refined if text[start:end].strip()]


def best_excerpt(text: str, answer: str, question: str = "", max_chars: int = config.EXCERPT_CHARS) -> dict:
    """Extrait à montrer pour un passage : {"excerpt", "highlight_start", "highlight_end"}.

    L'extrait commence à la phrase qui répond le mieux et dure au plus max_chars caractères ;
    highlight_start / highlight_end encadrent cette phrase (None si aucune phrase ne se détache).
    """
    text = " ".join(text.split())                    # espaces et retours à la ligne ramenés à un seul espace
    fallback = {"excerpt": text[:max_chars], "highlight_start": None, "highlight_end": None}
    wanted = stems_of(answer) | stems_of(question)
    if not wanted:
        return fallback

    spans = split_spans(text, max_chars)
    sentence_stems = [stems_of(text[start:end]) for start, end in spans]
    frequency: dict[str, int] = {}
    for roots in sentence_stems:
        for root in roots:
            frequency[root] = frequency.get(root, 0) + 1

    best_index, best_score = None, 0.0
    for index, roots in enumerate(sentence_stems):
        matched = wanted & roots
        has_number = any(root.isdigit() for root in matched)
        if len(matched) < MIN_MATCHES and not has_number:
            continue
        # un mot rare dans le passage compte plus qu'un mot qui revient partout ; un nombre commun compte double
        weight = sum(math.log(1 + len(spans) / frequency[root]) * (2 if root.isdigit() else 1) for root in matched)
        score = weight / math.sqrt(len(roots))      # on évite de favoriser une phrase juste parce qu'elle est longue
        if score > best_score:
            best_index, best_score = index, score
    if best_index is None:
        return fallback

    start, end = spans[best_index]
    return {
        "excerpt": text[start : start + max_chars],
        "highlight_start": 0,
        "highlight_end": min(end, start + max_chars) - start,
    }
