"""Tests de la mesure du hit rate (evaluation/run_eval.py)."""

from evaluation import run_eval


def test_single_expected_file_must_be_in_the_top5():
    assert run_eval.is_hit("a.pdf", ["x.pdf", "a.pdf"])
    assert not run_eval.is_hit("a.pdf", ["x.pdf", "y.pdf"])


def test_two_texts_question_needs_both_files():
    assert run_eval.is_hit("a.pdf;b.pdf", ["b.pdf", "a.pdf", "z.pdf"])
    assert not run_eval.is_hit("a.pdf;b.pdf", ["a.pdf", "z.pdf"])


def test_equivalent_versions_are_alternatives():
    # La même loi existe en arabe et en français : l'une OU l'autre suffit
    assert run_eval.is_hit("loi_ar.pdf|loi_fr.pdf", ["loi_fr.pdf"])
    assert run_eval.is_hit("loi_ar.pdf|loi_fr.pdf;const_fr.pdf", ["loi_ar.pdf", "const_fr.pdf"])
    assert not run_eval.is_hit("loi_ar.pdf|loi_fr.pdf;const_fr.pdf", ["loi_ar.pdf"])


def test_empty_expectation_is_never_a_hit():
    assert not run_eval.is_hit("", ["a.pdf"])
