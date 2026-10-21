"""Extraction du texte des PDF (étape 1 du pipeline, exigence FR-1).

On lit le registre data/sources.csv, puis on ouvre chaque PDF avec PyMuPDF
et on récupère le texte page par page, avec les métadonnées du document
(fichier, thème, langue, URL d'origine).
"""

import csv
from pathlib import Path

import pymupdf

from src import config


def load_sources(csv_path: Path = config.SOURCES_CSV) -> list[dict]:
    """Lit le registre des documents : une ligne du CSV = un dictionnaire."""
    with open(csv_path, encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def extract_pdf_pages(pdf_path: Path) -> list[str]:
    """Renvoie le texte brut de chaque page d'un PDF (une chaîne par page)."""
    with pymupdf.open(pdf_path) as document:
        return [page.get_text() for page in document]


def ingest_all(
    csv_path: Path = config.SOURCES_CSV, raw_dir: Path = config.RAW_DIR
) -> list[dict]:
    """Lit tous les PDF du registre et renvoie une liste de documents.

    Chaque document est un dictionnaire : file, theme, language, url, pages.
    Un PDF absent du dossier est signalé puis ignoré (on ne plante pas).
    """
    documents = []
    for source in load_sources(csv_path):
        pdf_path = raw_dir / source["fichier"]
        if not pdf_path.exists():
            print(f"ATTENTION : fichier introuvable, ignoré : {pdf_path.name}")
            continue
        documents.append(
            {
                "file": source["fichier"],
                "theme": source["theme"],
                "language": source["langue"],
                "url": source["url"],
                "pages": extract_pdf_pages(pdf_path),
            }
        )
    return documents
