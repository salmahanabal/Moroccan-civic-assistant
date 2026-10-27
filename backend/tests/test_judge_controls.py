"""Tests de la fabrication des mauvaises réponses (evaluation/judge_controls.py), sans appeler le juge."""

import pytest

from evaluation import judge_controls
from src import prompts


def make_rows(count=12):
    rows = []
    for i in range(1, count + 1):
        rows.append({
            "id": str(i), "type": "simple", "langue": "fr" if i % 3 else "ar", "question": f"Question {i} ?",
            "reponse_attendue": "attendu", "reponse_systeme": f"La Chambre compte {390 + i} membres [1].",
            "sources_citees": f"doc{i}.pdf p.{i}",
        })
    rows.append({"id": "99", "type": "hors_corpus", "langue": "fr", "question": "Hors sujet ?", "reponse_attendue": "",
                 "reponse_systeme": "Je n'ai pas trouvé.", "sources_citees": ""})
    return rows


def test_controls_are_reproducible_and_never_use_out_of_corpus_questions():
    first = judge_controls.make_controls(make_rows(), seed=1, per_kind=4)
    second = judge_controls.make_controls(make_rows(), seed=1, per_kind=4)
    assert [c["control_id"] for c in first] == [c["control_id"] for c in second]
    assert all(c["base_id"] != "99" for c in first)
    assert {c["kind"] for c in first} == {"autre_question", "chiffre_modifie", "invention", "refus_a_tort"}
    assert len(first) == 16


def test_original_rows_are_not_modified():
    rows = make_rows()
    before = [dict(row) for row in rows]
    judge_controls.make_controls(rows, per_kind=4)
    assert rows == before


def test_swapped_answer_comes_from_another_question_in_the_same_language():
    rows = make_rows()
    by_id = {row["id"]: row for row in rows}
    for control in judge_controls.make_controls(rows, per_kind=6):
        if control["kind"] != "autre_question":
            continue
        other = by_id[control["swap_id"]]
        assert control["swap_id"] != control["base_id"]
        assert other["langue"] == by_id[control["base_id"]]["langue"]
        assert control["row"]["reponse_systeme"] == other["reponse_systeme"]
        assert control["row"]["question"] == by_id[control["base_id"]]["question"]


def test_wrong_refusal_has_no_source_and_uses_the_official_message():
    for control in judge_controls.make_controls(make_rows(), per_kind=3):
        if control["kind"] == "refus_a_tort":
            language = control["row"]["langue"]
            assert control["row"]["reponse_systeme"] == prompts.REFUSAL_MESSAGES["no_answer"][language]
            assert control["row"]["sources_citees"] == ""


def test_invented_sentence_is_added_after_the_real_answer():
    for control in judge_controls.make_controls(make_rows(), per_kind=3):
        if control["kind"] == "invention":
            assert control["row"]["reponse_systeme"].endswith(judge_controls.INVENTED_SENTENCE[control["row"]["langue"]])


def test_alter_number_changes_a_number_but_not_a_citation_marker():
    assert judge_controls.alter_number("La Chambre compte 395 membres [12].") == "La Chambre compte 402 membres [12]."
    assert judge_controls.alter_number("Aucun nombre ici [1][25].") is None


@pytest.mark.parametrize("kind, exactitude, fidelite, expected", [
    ("autre_question", 0, 1, True), ("autre_question", 2, 1, False),
    ("chiffre_modifie", 2, 0, True), ("chiffre_modifie", 1, 1, True), ("chiffre_modifie", 2, 1, False),
    ("invention", 2, 0, True), ("invention", 0, 1, False),
    ("refus_a_tort", 0, 1, True), ("refus_a_tort", 1, 1, False),
])
def test_detection_rules(kind, exactitude, fidelite, expected):
    assert judge_controls.is_detected(kind, exactitude, fidelite) is expected
