"""Tests du découpage en chunks (src/chunking.py)."""

import pytest

from src import chunking

SENTENCES = " ".join(f"Phrase numéro {i} du texte de test." for i in range(80))


def test_chunks_never_exceed_chunk_size():
    chunks = chunking.split_text(SENTENCES, chunk_size=300, overlap=50)
    assert all(len(piece) <= 300 for _, piece in chunks)


def test_chunks_overlap():
    chunks = chunking.split_text(SENTENCES, chunk_size=300, overlap=50)
    # Le début de chaque chunk réapparaît dans la fin du précédent
    for (_, previous), (_, following) in zip(chunks, chunks[1:]):
        assert following[:20] in previous


def test_chunks_cut_on_sentence_end_when_possible():
    chunks = chunking.split_text(SENTENCES, chunk_size=300, overlap=50)
    assert all(piece.endswith(".") for _, piece in chunks[:-1])


def test_short_text_gives_a_single_chunk():
    chunks = chunking.split_text("Un texte court.", chunk_size=800, overlap=150)
    assert chunks == [(0, "Un texte court.")]


def test_no_empty_chunks_and_no_lost_text():
    chunks = chunking.split_text(SENTENCES, chunk_size=300, overlap=50)
    assert all(piece.strip() for _, piece in chunks)
    # Chaque phrase du texte de départ se retrouve dans au moins un chunk
    for i in range(80):
        assert any(f"Phrase numéro {i} du" in piece for _, piece in chunks)


def test_overlap_too_large_raises_an_error():
    with pytest.raises(ValueError):
        chunking.split_text("abc def", chunk_size=100, overlap=60)


def test_chunk_document_assigns_pages_and_metadata():
    document = {"file": "loi_test_fr.pdf", "theme": "elections", "language": "fr", "url": "https://exemple.ma/doc.pdf"}
    pages = [
        "Première page. " * 30,
        "Deuxième page. " * 30,
        "Troisième page. " * 30,
    ]
    chunks = chunking.chunk_document(pages, document, chunk_size=200, overlap=30)
    assert chunks[0]["page"] == 1
    assert chunks[-1]["page"] == 3
    assert {chunk["page"] for chunk in chunks} == {1, 2, 3}
    assert chunks[0]["chunk_id"] == "loi_test_fr_0000"
    assert chunks[0]["theme"] == "elections"
    assert chunks[0]["url"] == "https://exemple.ma/doc.pdf"


def test_chunk_document_skips_empty_pages_and_tiny_chunks():
    document = {"file": "x.pdf", "theme": "t", "language": "ar", "url": ""}
    chunks = chunking.chunk_document(["", "   ", "Un petit titre"], document)
    assert chunks == []  # moins de MIN_CHUNK_CHARS caractères
