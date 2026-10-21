"""Découpage du texte en chunks (étape 3 du pipeline, exigence FR-2).

Un chunk est un morceau de texte de taille limitée. On les chevauche : la fin
d'un chunk est répétée au début du suivant, pour qu'une information coupée
entre deux morceaux reste lisible dans au moins l'un des deux.
"""

import re
from bisect import bisect_right
from pathlib import Path

from src import config

# Fin de phrase (français et arabe) suivie d'un espace
SENTENCE_END = re.compile(r"[.!?؟؛:;]\s")


def find_cut_point(text: str, start: int, end: int) -> int:
    """Cherche le meilleur endroit pour couper entre start et end.

    Ordre de préférence : fin de paragraphe, puis fin de phrase, puis espace.
    On ne cherche que dans la seconde moitié du chunk, pour éviter des
    chunks trop courts.
    """
    window_start = start + (end - start) // 2
    window = text[window_start:end]

    last_paragraph_break = window.rfind("\n")
    if last_paragraph_break != -1:
        return window_start + last_paragraph_break + 1

    sentence_ends = list(SENTENCE_END.finditer(window))
    if sentence_ends:
        return window_start + sentence_ends[-1].end()

    last_space = window.rfind(" ")
    if last_space != -1:
        return window_start + last_space + 1
    return end  # aucun espace : on coupe net


def split_text(text: str, chunk_size: int, overlap: int) -> list[tuple[int, str]]:
    """Découpe un texte et renvoie une liste de (position de départ, chunk)."""
    if overlap >= chunk_size // 2:
        raise ValueError("Le chevauchement doit rester inférieur à la moitié de la taille d'un chunk.")

    chunks: list[tuple[int, str]] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            end = find_cut_point(text, start, end)

        piece = text[start:end]
        stripped = piece.strip()
        if stripped:
            offset = start + (len(piece) - len(piece.lstrip()))
            chunks.append((offset, stripped))
        if end >= len(text):
            break

        # Le chunk suivant recule de « overlap » caractères, sans couper un mot en deux
        next_start = max(end - overlap, start + 1)
        while next_start < end and not text[next_start - 1].isspace():
            next_start += 1
        start = next_start
    return chunks


def chunk_document(
    pages: list[str],
    document: dict,
    chunk_size: int = config.CHUNK_SIZE,
    overlap: int = config.CHUNK_OVERLAP,
) -> list[dict]:
    """Découpe un document entier et rattache chaque chunk à sa page.

    On assemble d'abord toutes les pages en un seul texte (une phrase peut
    continuer d'une page à l'autre), puis on retrouve la page où chaque
    chunk COMMENCE grâce à la position de départ de chaque page.
    """
    full_text = ""
    page_starts: list[int] = []   # position de début de chaque page dans full_text
    page_numbers: list[int] = []  # numéro de page correspondant
    for number, text in enumerate(pages, start=1):
        if not text.strip():
            continue
        page_starts.append(len(full_text))
        page_numbers.append(number)
        full_text += text + "\n"

    file_stem = Path(document["file"]).stem
    chunks = []
    for start, piece in split_text(full_text, chunk_size, overlap):
        if len(piece) < config.MIN_CHUNK_CHARS:
            continue
        page = page_numbers[bisect_right(page_starts, start) - 1]
        chunks.append(
            {
                "chunk_id": f"{file_stem}_{len(chunks):04d}",
                "file": document["file"],
                "page": page,
                "theme": document["theme"],
                "language": document["language"],
                "url": document["url"],
                "text": piece,
            }
        )
    return chunks
