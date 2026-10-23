"""Filtres appliqués AVANT la recherche et le LLM.

Ils repèrent deux cas sans réponse possible : une demande d'avis politique et une
langue non prise en charge. On les refuse tout de suite : c'est plus fiable que de
compter sur le modèle, plus rapide, et cela n'utilise pas le quota du LLM.
Le LLM reste une deuxième ligne de défense (voir prompts.py).
"""

import re

from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

DetectorFactory.seed = 0  # sans cela, langdetect peut donner des résultats différents d'un appel à l'autre

# Formulations qui demandent un AVIS, un vote ou un jugement (français et arabe).
# Volontairement précises : on préfère laisser passer au LLM que refuser une vraie question.
OPINION_PATTERNS = [
    r"\bque penses?[- ]tu\b", r"\bque pensez[- ]vous\b", r"\bqu['’]en penses?[- ]tu\b",
    r"\b(ton|votre) (avis|opinion)\b", r"\bà ton avis\b", r"\bselon toi\b",
    r"\bpour qui (dois|devrais|faut|faudrait|voter|voterais)\b", r"\bpour quel (parti|candidat)\b",
    r"\b(le |la )?(meilleur|pire|mauvais) (parti|politicien|candidat|dirigeant|ministre)\b",
    r"\bquel parti (choisir|soutenir|est le meilleur)\b", r"\b(qui|quel parti) (mérite|devrait gagner)\b",
    r"ما رأيك", r"ما رأيكم", r"في رأيك", r"برأيك", r"لمن (أصوت|يجب أن أصوت|أصوّت)", r"لأي (حزب|مرشح)",
    r"(أفضل|أحسن|أسوأ) (حزب|سياسي|مرشح|وزير)",
]
OPINION_REGEX = re.compile("|".join(OPINION_PATTERNS), re.IGNORECASE)

LATIN_LETTERS = re.compile("[A-Za-zÀ-ÿ]")
MIN_LETTERS_FOR_DETECTION = 20  # en dessous, la détection de langue est trop peu fiable
MIN_ENGLISH_PROBABILITY = 0.9


def looks_like_opinion_request(text: str) -> bool:
    """Vrai si la question demande un avis politique, un conseil de vote ou un jugement."""
    return bool(OPINION_REGEX.search(text))


def is_unsupported_language(text: str) -> bool:
    """Vrai si la question est clairement écrite en anglais (le projet ne gère que le français et l'arabe).

    On ne signale que l'anglais, avec une forte certitude et sur un texte assez long : une
    question française courte ne doit jamais être refusée à tort.
    """
    if len(LATIN_LETTERS.findall(text)) < MIN_LETTERS_FOR_DETECTION:
        return False
    try:
        return any(
            candidate.lang == "en" and candidate.prob >= MIN_ENGLISH_PROBABILITY
            for candidate in detect_langs(text)
        )
    except LangDetectException:
        return False
