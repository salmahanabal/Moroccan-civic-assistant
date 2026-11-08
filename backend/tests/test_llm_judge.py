"""Tests du LLM juge (evaluation/llm_judge.py) : calcul du kappa et lecture de la réponse du juge."""

import pytest

from evaluation import llm_judge


def test_kappa_on_a_classic_example():
    # 50 éléments : 20 « oui/oui », 15 « non/non », 5 et 10 désaccords -> accord 0,70, hasard 0,50, kappa 0,40
    first = [1] * 20 + [1] * 5 + [0] * 10 + [0] * 15
    second = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
    assert llm_judge.cohen_kappa(first, second, [0, 1]) == pytest.approx(0.4)


def test_perfect_agreement_gives_one():
    notes = [0, 1, 2, 2, 1, 0]
    assert llm_judge.cohen_kappa(notes, notes, [0, 1, 2]) == pytest.approx(1.0)
    assert llm_judge.cohen_kappa(notes, notes, [0, 1, 2], weighted=True) == pytest.approx(1.0)


def test_kappa_is_zero_when_one_rater_always_gives_the_same_note():
    # accord brut de 80 %, mais le kappa vaut 0 : c'est le « paradoxe du kappa »
    always_one = [1] * 10
    other = [1] * 8 + [0] * 2
    assert llm_judge.cohen_kappa(always_one, other, [0, 1]) == pytest.approx(0.0)


def test_kappa_is_undefined_when_both_raters_always_give_the_same_note():
    assert llm_judge.cohen_kappa([1] * 10, [1] * 10, [0, 1]) is None


def test_weighted_kappa_penalises_a_big_gap_more_than_a_small_one():
    first = [0, 1, 2, 2, 0, 1]
    small_gap = [0, 1, 1, 2, 0, 1]   # un écart de 1 point
    big_gap = [0, 1, 0, 2, 0, 1]     # un écart de 2 points sur la même question
    assert llm_judge.cohen_kappa(first, small_gap, [0, 1, 2], weighted=True) > llm_judge.cohen_kappa(
        first, big_gap, [0, 1, 2], weighted=True
    )


def test_confusion_matrix_rows_are_the_first_rater():
    matrix = llm_judge.confusion_matrix([2, 2, 1], [2, 1, 1], [0, 1, 2])
    assert matrix == [[0, 0, 0], [0, 1, 0], [0, 1, 1]]


def test_parse_valid_judgement():
    result = llm_judge.parse_judgement('Voici : {"exactitude": 2, "fidelite": 1, "raison": "ok"}', out_of_corpus=False)
    assert result == {"exactitude": 2, "fidelite": 1, "raison": "ok"}


def test_out_of_corpus_ignores_the_exactitude():
    result = llm_judge.parse_judgement('{"exactitude": 2, "fidelite": 1, "raison": "refus poli"}', out_of_corpus=True)
    assert result["exactitude"] is None and result["fidelite"] == 1


@pytest.mark.parametrize("text", ["pas de json", '{"exactitude": 5, "fidelite": 1}', '{"exactitude": 2, "fidelite": 3}', '{"exactitude": 2}', "{casse"])
def test_unusable_judgements_are_rejected(text):
    assert llm_judge.parse_judgement(text, out_of_corpus=False) is None


def test_judge_prompt_contains_the_four_blocks_but_no_notes():
    row = {"type": "simple", "question": "Q ?", "reponse_attendue": "ATTENDU", "reponse_systeme": "REPONSE",
           "note_exactitude": "2", "note_fidelite": "1"}
    prompt = llm_judge.build_judge_prompt(row, [{"title": "doc.pdf, page 3", "text": "TEXTE"}])
    for expected in ("Q ?", "ATTENDU", "REPONSE", "doc.pdf, page 3", "TEXTE"):
        assert expected in prompt
    assert "note_exactitude" not in prompt


def test_summary_counts_in_corpus_scores_and_ignores_refusals():
    rows = [
        {"id": "1", "type": "simple", "judge_exactitude": "2", "judge_fidelite": "1"},
        {"id": "2", "type": "simple", "judge_exactitude": "1", "judge_fidelite": "1"},
        {"id": "3", "type": "arabe", "judge_exactitude": "2", "judge_fidelite": "0"},
        {"id": "4", "type": "hors_corpus", "judge_exactitude": "", "judge_fidelite": "1"},
    ]
    result = llm_judge.summarize_judgements(rows)
    assert result["questions_corpus"] == 3
    assert result["repartition"] == {0: 0, 1: 1, 2: 2}
    assert result["moyenne"] == pytest.approx(5 / 3)
    assert (result["fidelite"], result["fidelite_sur"]) == (3, 4)
    assert result["par_type"]["simple"] == {"questions": 2, "moyenne": 1.5}


def test_compare_runs_summary_counts_hits_wrong_refusals_and_judge_scores():
    from evaluation import compare_runs

    results = [
        {"type": "simple", "hit_at_5": "1", "refus_correct": "", "found": "True", "duree_s": "2.0"},
        {"type": "simple", "hit_at_5": "0", "refus_correct": "", "found": "False", "duree_s": "4.0"},
        {"type": "hors_corpus", "hit_at_5": "", "refus_correct": "1", "found": "False", "duree_s": "1.0"},
    ]
    judge = [
        {"type": "simple", "judge_exactitude": "2", "judge_fidelite": "1"},
        {"type": "simple", "judge_exactitude": "0", "judge_fidelite": "1"},
        {"type": "hors_corpus", "judge_exactitude": "", "judge_fidelite": "1"},
    ]
    summary = compare_runs.summarize_run(results, judge)
    assert summary["hit"] == (1, 2) and summary["refus_correct"] == (1, 1) and summary["refus_a_tort"] == (1, 2)
    assert summary["exactitude"] == 1.0 and summary["fidelite"] == (3, 3) and summary["latence"] == pytest.approx(7 / 3)
    assert "| Jeu 9 | après | 50 % (1/2) | 100 % (1/1) | 50 % (1/2) | 1.00 / 2 | 100 % (3/3) | 2.3 s |" == compare_runs.format_row("Jeu 9", "après", summary)
