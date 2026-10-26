"""Tests du chef d'orchestre (src/rag.py) et des prompts (src/prompts.py).

La recherche et le LLM sont remplacés par de fausses fonctions : ces tests ne
consomment ni le quota de la clé d'API ni le vrai modèle d'embeddings.
"""

import pytest

from src import generator, prompts, rag

CHUNKS = [
    {"text": "Sont électeurs les citoyens majeurs. " * 20, "file": "loi_57_11.pdf", "page": 4, "url": "https://exemple.ma/a", "score": 0.90},
    {"text": "Les partis politiques concourent à l'expression de la volonté des électeurs.", "file": "constitution.pdf", "page": 7, "url": "https://exemple.ma/b", "score": 0.85},
    {"text": "Le Parlement comprend deux Chambres.", "file": "constitution.pdf", "page": 9, "url": "https://exemple.ma/b", "score": 0.84},
]


def fake_retrieve(chunks):
    return lambda question, theme=None: chunks


def never_called(system_prompt, user_prompt):
    raise AssertionError("Le LLM ne devait pas être appelé")


def test_detect_language():
    assert rag.detect_language("À partir de quel âge peut-on voter ?") == "fr"
    assert rag.detect_language("ما هو دور رئيس الحكومة؟") == "ar"
    assert rag.detect_language("12345 ?") == "fr"


def test_answer_with_sources_keeps_only_cited_extracts():
    result = rag.answer_question(
        "Qui peut voter ?",
        retrieve_fn=fake_retrieve(CHUNKS),
        generate_fn=lambda system, user: "Les citoyens majeurs peuvent voter [1][3].",
    )
    assert result["found"] is True
    assert result["language"] == "fr"
    assert [source["id"] for source in result["sources"]] == [1, 3]
    assert result["sources"][0]["file"] == "loi_57_11.pdf"
    assert result["sources"][0]["page"] == 4
    assert len(result["sources"][0]["excerpt"]) == 200  # extrait coupé à 200 caractères


def test_answer_without_citation_keeps_all_extracts_as_sources():
    result = rag.answer_question(
        "Qui peut voter ?",
        retrieve_fn=fake_retrieve(CHUNKS),
        generate_fn=lambda system, user: "Les citoyens majeurs.",
    )
    assert result["found"] is True
    assert len(result["sources"]) == 3  # une réponse a toujours au moins une source


def test_low_score_refuses_without_calling_the_llm():
    weak = [{**CHUNKS[0], "score": 0.30}]  # nettement sous le seuil de config.py
    result = rag.answer_question("Recette de gâteau ?", retrieve_fn=fake_retrieve(weak), generate_fn=never_called)
    assert result["found"] is False
    assert result["sources"] == []
    assert result["answer"] == prompts.REFUSAL_MESSAGES["no_answer"]["fr"]


def test_no_answer_keyword_from_the_llm_becomes_a_polite_refusal():
    result = rag.answer_question(
        "Quelle est la capitale ?",
        retrieve_fn=fake_retrieve(CHUNKS),
        generate_fn=lambda system, user: prompts.NO_ANSWER,
    )
    assert result["found"] is False
    assert result["sources"] == []


def test_opinion_keyword_gives_the_neutrality_message_in_arabic():
    result = rag.answer_question(
        "لأي حزب يجب أن أصوت؟",
        retrieve_fn=fake_retrieve(CHUNKS),
        generate_fn=lambda system, user: prompts.OPINION,
    )
    assert result["found"] is False
    assert result["language"] == "ar"
    assert result["answer"] == prompts.REFUSAL_MESSAGES["opinion"]["ar"]


def test_llm_error_is_not_hidden():
    def broken(system_prompt, user_prompt):
        raise generator.LLMUnavailableError("quota")

    with pytest.raises(generator.LLMUnavailableError):
        rag.answer_question("Question ?", retrieve_fn=fake_retrieve(CHUNKS), generate_fn=broken)


def test_multi_part_question_is_searched_with_its_sub_questions():
    received = {}

    def fake_retrieve(question, theme=None, sub_queries=None):
        received["sub_queries"] = sub_queries
        return CHUNKS

    result = rag.answer_question(
        "Que faut-il pour voter et comment s'inscrire ?",
        retrieve_fn=fake_retrieve,
        generate_fn=lambda system, user: "Il faut être majeur [1].",
        rewrite_fn=lambda question: ["Que faut-il pour voter ?", "Comment s'inscrire ?"],
    )
    assert result["found"] is True
    assert received["sub_queries"] == ["Que faut-il pour voter ?", "Comment s'inscrire ?"]


def test_question_without_sub_questions_keeps_the_classic_search_call():
    result = rag.answer_question(
        "Qui peut voter ?",
        retrieve_fn=fake_retrieve(CHUNKS),  # n'accepte pas sub_queries : ne doit pas en recevoir
        generate_fn=lambda system, user: "Les citoyens majeurs [1].",
        rewrite_fn=lambda question: [],
    )
    assert result["found"] is True


def test_user_prompt_contains_numbered_extracts_and_language():
    prompt = prompts.build_user_prompt("Question ?", "ar", CHUNKS)
    assert "Langue de la question : arabe" in prompt
    assert "[1] (document : loi_57_11.pdf, page 4)" in prompt
    assert "[3] (document : constitution.pdf, page 9)" in prompt


def test_system_prompt_forbids_opinions_and_inventions():
    assert "neutre" in prompts.SYSTEM_PROMPT
    assert prompts.NO_ANSWER in prompts.SYSTEM_PROMPT
    assert prompts.OPINION in prompts.SYSTEM_PROMPT
