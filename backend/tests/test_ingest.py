"""Tests de l'extraction des PDF (src/ingest.py).

On fabrique de vrais petits PDF dans un dossier temporaire (tmp_path) : les
tests n'ont donc pas besoin des 18 vrais documents du corpus.
"""

import pymupdf

from src import ingest


def make_pdf(path, page_texts):
    """Crée un PDF avec une page par texte de la liste."""
    document = pymupdf.open()
    for text in page_texts:
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(path)
    document.close()


def test_extract_pdf_pages_returns_one_text_per_page(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    make_pdf(pdf_path, ["Bonjour page un", "Bonjour page deux"])
    pages = ingest.extract_pdf_pages(pdf_path)
    assert len(pages) == 2
    assert "page un" in pages[0]
    assert "page deux" in pages[1]


def test_ingest_all_reads_registry_and_attaches_metadata(tmp_path):
    make_pdf(tmp_path / "loi_test_fr.pdf", ["Texte de la loi"])
    registry = tmp_path / "sources.csv"
    registry.write_text(
        "fichier,url,theme,langue,organisme,date_telechargement\n"
        "loi_test_fr.pdf,https://exemple.ma/loi.pdf,elections,fr,SGG,2026-10-18\n",
        encoding="utf-8",
    )
    documents = ingest.ingest_all(csv_path=registry, raw_dir=tmp_path)
    assert len(documents) == 1
    assert documents[0]["file"] == "loi_test_fr.pdf"
    assert documents[0]["theme"] == "elections"
    assert documents[0]["language"] == "fr"
    assert documents[0]["url"] == "https://exemple.ma/loi.pdf"
    assert "Texte de la loi" in documents[0]["pages"][0]


def test_ingest_all_skips_missing_pdf_without_crashing(tmp_path):
    registry = tmp_path / "sources.csv"
    registry.write_text(
        "fichier,url,theme,langue,organisme,date_telechargement\n"
        "absent.pdf,https://exemple.ma/a.pdf,elections,fr,SGG,2026-10-18\n",
        encoding="utf-8",
    )
    assert ingest.ingest_all(csv_path=registry, raw_dir=tmp_path) == []
