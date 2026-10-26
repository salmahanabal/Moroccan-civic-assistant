"""Tests du découpage des questions à plusieurs volets (src/query_rewriter.py et retriever.interleave).

Le LLM est remplacé par de fausses fonctions : aucun quota n'est consommé.
"""

from src import generator, query_rewriter, retriever


def make_chunk(file: str, page: int, text: str, score: float) -> dict:
    return {"file": file, "page": page, "text": text, "url": "", "score": score}


def test_simple_questions_do_not_call_the_llm():
    assert query_rewriter.needs_rewrite("Qui nomme le chef du gouvernement ?") is False
    assert query_rewriter.needs_rewrite("Oui ?") is False
    assert query_rewriter.needs_rewrite("ما هي اللغات الرسمية في المملكة المغربية؟") is False


def test_multi_part_questions_are_detected_in_french_and_arabic():
    assert query_rewriter.needs_rewrite("Que faut-il pour voter et comment demande-t-on à être inscrit ?") is True
    assert query_rewriter.needs_rewrite("Comment sont choisis les députés, qui devient chef du gouvernement ?") is True
    assert query_rewriter.needs_rewrite("كم عدد أعضاء مجلس النواب وكيف يتم انتخابهم في المغرب؟") is True


def test_rewrite_returns_clean_sub_questions():
    def fake_llm(system_prompt, user_prompt):
        return "1. Que faut-il pour voter au Maroc ?\n- Comment s'inscrire sur les listes électorales ?\n\n"

    result = query_rewriter.rewrite_query("Que faut-il pour voter et comment s'inscrire ?", generate_fn=fake_llm)
    assert result == ["Que faut-il pour voter au Maroc ?", "Comment s'inscrire sur les listes électorales ?"]


def test_rewrite_drops_duplicates_special_words_and_extra_lines():
    question = "Que faut-il pour voter et comment s'inscrire ?"

    def fake_llm(system_prompt, user_prompt):
        return "\n".join([question, "[[NO_ANSWER]]", "Sous-question numéro un ?", "Sous-question numéro un ?",
                          "Sous-question numéro deux ?", "Sous-question numéro trois ?", "Sous-question numéro quatre ?"])

    result = query_rewriter.rewrite_query(question, generate_fn=fake_llm)
    assert result == ["Sous-question numéro un ?", "Sous-question numéro deux ?", "Sous-question numéro trois ?"]


def test_rewrite_falls_back_silently_when_the_llm_is_unavailable():
    def broken(system_prompt, user_prompt):
        raise generator.LLMUnavailableError("quota épuisé")

    assert query_rewriter.rewrite_query("Que faut-il pour voter et comment s'inscrire ?", generate_fn=broken) == []


def test_rewrite_does_not_call_the_llm_for_a_simple_question():
    def never_called(system_prompt, user_prompt):
        raise AssertionError("Le LLM ne devait pas être appelé")

    assert query_rewriter.rewrite_query("Qui nomme le chef du gouvernement ?", generate_fn=never_called) == []


def test_interleave_gives_each_list_its_places_and_removes_duplicates():
    list_a = [make_chunk("a.pdf", 1, "a1", 0.9), make_chunk("a.pdf", 2, "a2", 0.8), make_chunk("a.pdf", 3, "a3", 0.7)]
    list_b = [make_chunk("b.pdf", 1, "b1", 0.6), make_chunk("a.pdf", 1, "a1", 0.9), make_chunk("b.pdf", 2, "b2", 0.5)]
    merged = retriever.interleave([list_a, list_b], top_k=4)
    # a1 est présent dans les deux listes : il n'est gardé qu'une fois ; chaque liste a sa place
    assert {(c["file"], c["page"]) for c in merged} == {("a.pdf", 1), ("a.pdf", 2), ("a.pdf", 3), ("b.pdf", 1)}
    assert len(merged) == 4
    assert [c["score"] for c in merged] == sorted((c["score"] for c in merged), reverse=True)


def test_interleave_keeps_the_best_chunk_first():
    first = [make_chunk("a.pdf", 1, "a1", 0.9)]
    second = [make_chunk("b.pdf", 1, "b1", 0.95)]
    assert retriever.interleave([first, second], top_k=5)[0]["file"] == "b.pdf"
