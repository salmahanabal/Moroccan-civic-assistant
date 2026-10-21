"""Nettoyage du texte extrait des PDF (étape 2 du pipeline).

Règle d'or : on ne change JAMAIS le sens du texte et on ne traduit rien.
On enlève seulement le « bruit » : caractères parasites, numéros de page,
en-têtes et pieds de page répétés, sauts de ligne au milieu des phrases.
"""

import re
import unicodedata
from collections import Counter

from src import config

TATWEEL = "ـ"  # trait d'allongement décoratif de l'arabe (ex. « الفصـل »)

# Caractères invisibles (marques de sens de lecture, espaces de largeur nulle...)
INVISIBLE_CHARS = dict.fromkeys(
    map(ord, "​‌‍‎‏‪‫‬‭‮⁦⁧⁨⁩﻿"),
    None,
)

# Une ligne qui ne contient qu'un numéro de page : « 12 », « - 12 - », « – 3 –»
PAGE_NUMBER_LINE = re.compile(r"^\s*[-–—]?\s*\d{1,4}\s*[-–—]?\s*$")

# Début d'un article ou d'un titre : on ne le colle jamais à la ligne précédente
SECTION_START = re.compile(
    r"^(Article|ARTICLE|Chapitre|CHAPITRE|Titre|TITRE|Section|SECTION|الفصل|المادة|الباب|الجزء|الفرع)\b"
)

# Signes qui marquent la fin d'une phrase (français et arabe)
SENTENCE_END = ".:;!?؟؛…"


def normalize_unicode(text: str) -> str:
    """Remet les caractères dans leur forme standard.

    Certains PDF écrivent l'arabe avec des « formes de présentation » : ça
    s'affiche bien, mais pour l'ordinateur ce ne sont pas les vraies lettres
    (une recherche de « راميد » ne trouvait rien). La normalisation NFKC règle ça.
    """
    text = unicodedata.normalize("NFKC", text)
    text = text.replace(TATWEEL, "")
    return text.translate(INVISIBLE_CHARS)


# --- Réparation des ligatures arabes sorties à l'envers -----------------------
# Dans certains PDF (polices « Sakkal Majalla »...), les lettres liées « لا »,
# « لأ », « لم » sont enregistrées dans l'autre sens : on lit « املادة » au lieu
# de « المادة ». C'est le fichier PDF lui-même qui est ainsi : on répare le texte.

ARABIC_WORD = re.compile("[ء-ي]+")

# Règle A : en début de mot, « ا » + (ا أ إ آ م) + « ل » devient « ا » + « ل » + lettre.
# Préfixes acceptés : و ف ب (pas ك, sinon « كاملة » = « complète » serait cassé).
ARTICLE_LIGATURE = re.compile(
    "(?<![ء-ي])([وفب]?)ا([اأإآم])ل"
)

# Règle B : paires « lettre + lam » qui peuvent être une ligature inversée
SWAPPABLE_PAIRS = ("ال", "أل", "إل", "آل")


# Un « ؟ » collé entre deux lettres (« سيا؟سي ») est un parasite d'extraction : un vrai
# point d'interrogation est toujours suivi d'un espace ou d'une ponctuation.
STRAY_QUESTION_MARK = re.compile("(?<=[ء-ي])؟(?=[ء-ي])")


def remove_stray_question_marks(text: str) -> str:
    """Supprime les « ؟ » parasites situés au milieu d'un mot arabe."""
    return STRAY_QUESTION_MARK.sub("", text)


def fix_article_ligature(text: str) -> str:
    """Règle A : remet « ل » avant la lettre suivante au début des mots (املادة -> المادة)."""
    return ARTICLE_LIGATURE.sub(lambda m: m.group(1) + "ال" + m.group(2), text)


def build_arabic_vocabulary(pages: list[str]) -> set[str]:
    """Ensemble des mots arabes d'un texte sain (sert de dictionnaire de référence)."""
    return set(ARABIC_WORD.findall(" ".join(pages)))


def _swapped_variants(word: str) -> list[str]:
    """Toutes les versions d'un mot où une ou plusieurs paires « lettre + lam » sont inversées."""
    positions = [i for i in range(len(word) - 1) if word[i : i + 2] in SWAPPABLE_PAIRS][:5]
    variants = []
    for mask in range(1, 2 ** len(positions)):
        chosen = [positions[k] for k in range(len(positions)) if mask >> k & 1]
        if any(b - a < 2 for a, b in zip(chosen, chosen[1:])):
            continue  # deux paires qui se chevauchent : impossible
        letters = list(word)
        for i in chosen:
            letters[i], letters[i + 1] = letters[i + 1], letters[i]
        variants.append((len(chosen), "".join(letters)))
    return [variant for _, variant in sorted(variants)]  # les corrections les plus légères d'abord


def repair_arabic_ligatures(text: str, vocabulary: set[str]) -> str:
    """Règle B : répare un mot SEULEMENT s'il est inconnu et que sa version corrigée est connue.

    Exemple : « خالل » n'est pas dans le vocabulaire de référence, mais « خلال »
    y est : on remplace. Un mot déjà connu n'est jamais modifié.
    """

    def repair(match: re.Match) -> str:
        word = match.group(0)
        if word in vocabulary:
            return word
        for variant in _swapped_variants(word):
            if variant in vocabulary:
                return variant
        return word

    return ARABIC_WORD.sub(repair, text)


def remove_page_numbers(text: str) -> str:
    """Supprime les lignes qui ne contiennent qu'un numéro de page."""
    lines = [line for line in text.split("\n") if not PAGE_NUMBER_LINE.match(line)]
    return "\n".join(lines)


def _line_signature(line: str) -> str:
    """Forme comparable d'une ligne : les chiffres deviennent « # ».

    Ainsi « BULLETIN OFFICIEL No 6284 » et « BULLETIN OFFICIEL No 6285 »
    sont reconnus comme la même ligne répétée.
    """
    return re.sub(r"\d+", "#", line.strip())


def remove_repeated_lines(pages: list[str]) -> list[str]:
    """Supprime les en-têtes et pieds de page qui se répètent sur beaucoup de pages.

    On ne regarde que les 2 premières et les 2 dernières lignes de chaque page,
    et on ne touche jamais aux débuts d'articles.
    """
    if len(pages) < config.MIN_PAGES_FOR_HEADER_DETECTION:
        return pages

    def edge_positions(lines: list[str]) -> set[int]:
        """Positions (numéros de ligne) des 2 premières et 2 dernières lignes non vides."""
        non_empty = [i for i, line in enumerate(lines) if line.strip()]
        return set(non_empty[:2] + non_empty[-2:])

    split_pages = [page.split("\n") for page in pages]

    counts = Counter()
    for lines in split_pages:
        # Un ensemble (set) : une ligne compte une seule fois par page
        counts.update({_line_signature(lines[i]) for i in edge_positions(lines)})

    repeated = {
        signature
        for signature, count in counts.items()
        if count / len(pages) >= config.REPEATED_LINE_RATIO
    }

    cleaned_pages = []
    for lines in split_pages:
        edges = edge_positions(lines)
        kept = [
            line
            for i, line in enumerate(lines)
            if not (
                i in edges
                and _line_signature(line) in repeated
                and not SECTION_START.match(line.strip())
            )
        ]
        cleaned_pages.append("\n".join(kept))
    return cleaned_pages


def reflow_lines(text: str) -> str:
    """Recolle les lignes coupées au milieu d'une phrase, en gardant les paragraphes.

    Dans un PDF, chaque ligne visuelle se termine par un saut de ligne, même
    au milieu d'une phrase. On garde un saut de ligne seulement après la fin
    d'une phrase ou avant un nouvel article. Les mots coupés par un tiret
    en fin de ligne (« fonc- tionnement ») sont recollés.
    """
    paragraphs: list[str] = []
    current = ""
    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if current and SECTION_START.match(line):
            paragraphs.append(current)
            current = ""
        if current.endswith("-") and line[0].islower():
            current = current[:-1] + line  # mot coupé : on recolle sans espace
        elif current:
            current += " " + line
        else:
            current = line
        if line[-1] in SENTENCE_END:
            paragraphs.append(current)
            current = ""
    if current:
        paragraphs.append(current)
    return "\n".join(re.sub(r"[ \t]+", " ", paragraph) for paragraph in paragraphs)


def clean_document(pages: list[str], arabic_vocabulary: set[str] | None = None) -> list[str]:
    """Applique tout le nettoyage à la liste des pages d'un document.

    Si un vocabulaire arabe de référence est fourni, on répare aussi les
    ligatures inversées au milieu des mots (règle B).
    """
    pages = [remove_stray_question_marks(normalize_unicode(page)) for page in pages]
    pages = [fix_article_ligature(page) for page in pages]
    if arabic_vocabulary:
        pages = [repair_arabic_ligatures(page, arabic_vocabulary) for page in pages]
    pages = remove_repeated_lines(pages)
    pages = [remove_page_numbers(page) for page in pages]
    return [reflow_lines(page) for page in pages]
