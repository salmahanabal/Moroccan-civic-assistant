"""Tests du nettoyage du texte (src/cleaning.py)."""

from src import cleaning


def test_normalize_unicode_converts_arabic_presentation_forms():
    # « مرحبا » écrit avec des formes de présentation (lettres initiales, finales...)
    presentation_forms = "ﻣﺮﺣﺒﺎ"
    standard_letters = "مرحبا"
    assert cleaning.normalize_unicode(presentation_forms) == standard_letters


def test_normalize_unicode_removes_tatweel_and_invisible_characters():
    # Le tatweel (ـ) allonge la lettre sans changer le mot ; ‏ est invisible
    assert cleaning.normalize_unicode("الفصـل‏") == "الفصل"


def test_remove_page_numbers_keeps_real_text():
    text = "Premier paragraphe.\n12\n- 13 -\nDeuxième paragraphe."
    assert cleaning.remove_page_numbers(text) == "Premier paragraphe.\nDeuxième paragraphe."


def test_remove_page_numbers_keeps_numbers_inside_sentences():
    text = "La loi n° 29-11 date de 2011."
    assert cleaning.remove_page_numbers(text) == text


def test_remove_repeated_lines_removes_header_but_keeps_body():
    # 6 pages avec le même en-tête (seul le numéro change) et un corps différent
    pages = [f"BULLETIN OFFICIEL No {6280 + i}\nTexte unique de la page {chr(65 + i)}.\nSuite du texte." for i in range(6)]
    cleaned = cleaning.remove_repeated_lines(pages)
    assert all("BULLETIN OFFICIEL" not in page for page in cleaned)
    assert all("Texte unique" in page for page in cleaned)


def test_remove_repeated_lines_never_removes_article_headings():
    # « Article 1 », « Article 2 »... se ressemblent une fois les chiffres masqués
    pages = [f"Article {i}\nContenu de l'article {chr(65 + i)} qui est différent.\nFin." for i in range(6)]
    cleaned = cleaning.remove_repeated_lines(pages)
    assert all(page.startswith("Article") for page in cleaned)


def test_remove_repeated_lines_does_nothing_on_short_documents():
    pages = ["En-tête\nTexte A.", "En-tête\nTexte B."]
    assert cleaning.remove_repeated_lines(pages) == pages


def test_reflow_lines_joins_broken_sentences():
    text = "Le Parlement vote\nles lois et contrôle\nle Gouvernement."
    assert cleaning.reflow_lines(text) == "Le Parlement vote les lois et contrôle le Gouvernement."


def test_reflow_lines_repairs_hyphenated_words():
    assert cleaning.reflow_lines("le fonc-\ntionnement du Parlement.") == "le fonctionnement du Parlement."


def test_reflow_lines_keeps_one_paragraph_per_article():
    text = "Article 1\nLe Maroc est une monarchie.\nArticle 2\nLa souveraineté appartient à la nation."
    paragraphs = cleaning.reflow_lines(text).split("\n")
    assert paragraphs[0] == "Article 1 Le Maroc est une monarchie."
    assert paragraphs[1].startswith("Article 2")


def test_clean_document_runs_every_step():
    pages = ["Texte avec espaces   multiples\net lignes coupées.", "Autre page.\n5"]
    cleaned = cleaning.clean_document(pages)
    assert cleaned[0] == "Texte avec espaces multiples et lignes coupées."
    assert cleaned[1] == "Autre page."
