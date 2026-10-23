"""Tests des filtres avant recherche (src/guards.py) et de leur branchement dans rag.py."""

import csv

import pytest

from src import config, guards, prompts, rag


def never_called(*args, **kwargs):
    raise AssertionError("Cette étape ne devait pas être exécutée")


@pytest.mark.parametrize(
    "question",
    [
        "Que penses-tu du Roi ?",
        "Quel est ton avis sur ce parti ?",
        "Pour qui dois-je voter aux prochaines élections ?",
        "Pour quel parti dois-je voter ?",
        "Quel est le meilleur parti politique du Maroc ?",
        "Quel parti choisir ?",
        "À ton avis, qui mérite de gagner ?",
        "ما رأيك في هذا الحزب؟",
        "لمن يجب أن أصوت في الانتخابات القادمة؟",
        "ما هو أفضل حزب في المغرب؟",
    ],
)
def test_opinion_requests_are_detected(question):
    assert guards.looks_like_opinion_request(question)


@pytest.mark.parametrize(
    "question",
    [
        "Qui choisit le chef du gouvernement ?",
        "À quoi servent les partis politiques ?",
        "Comment peut-on créer un parti politique ?",
        "Quel est le rôle du Parlement ?",
        "Pour quelle durée les députés sont-ils élus ?",
        "ما هو دور رئيس الحكومة؟",
        "كيف يمكن تأسيس حزب سياسي؟",
    ],
)
def test_legitimate_questions_are_not_mistaken_for_opinion_requests(question):
    assert not guards.looks_like_opinion_request(question)


def test_none_of_the_reference_questions_is_wrongly_filtered():
    # Les 30 questions de référence : seules les 5 questions hors corpus peuvent être des demandes d'avis
    with open(config.EVAL_DIR / "questions.csv", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 30
    for row in rows:
        if row["type"] != "hors_corpus":
            assert not guards.looks_like_opinion_request(row["question"]), row["question"]
            assert not guards.is_unsupported_language(row["question"]), row["question"]


def test_english_questions_are_detected():
    assert guards.is_unsupported_language("Who appoints the head of government in Morocco?")
    assert guards.is_unsupported_language("What are the official languages of the Kingdom of Morocco?")


@pytest.mark.parametrize(
    "question",
    [
        "Parlement rôle",
        "Quelles langues sont officielles au Maroc ?",
        "Combien de juges siègent à la Cour constitutionnelle et pour combien de temps ?",
        "ما هي اللغات الرسمية في المملكة المغربية؟",
        "???",
        "a",
        "",
    ],
)
def test_french_arabic_and_short_questions_are_never_marked_as_unsupported(question):
    assert not guards.is_unsupported_language(question)


def test_opinion_request_is_refused_before_search_and_llm():
    result = rag.answer_question("Pour quel parti dois-je voter ?", retrieve_fn=never_called, generate_fn=never_called)
    assert result["found"] is False
    assert result["sources"] == []
    assert result["answer"] == prompts.REFUSAL_MESSAGES["opinion"]["fr"]


def test_arabic_opinion_request_gets_the_arabic_message():
    result = rag.answer_question("لمن يجب أن أصوت؟", retrieve_fn=never_called, generate_fn=never_called)
    assert result["language"] == "ar"
    assert result["answer"] == prompts.REFUSAL_MESSAGES["opinion"]["ar"]


def test_english_question_is_refused_with_a_bilingual_message():
    result = rag.answer_question("Who appoints the head of government in Morocco?", retrieve_fn=never_called, generate_fn=never_called)
    assert result["found"] is False
    assert "français" in result["answer"] and "العربية" in result["answer"]
