"""Tests de la recopie des notes (evaluation/merge_notes.py) : le script ne doit jamais inventer une note."""

import csv

import pytest

from evaluation import merge_notes

COLUMNS = ["id", "type", "note_exactitude", "note_fidelite", "commentaire"]


def write(path, rows, columns):
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


@pytest.fixture
def files(tmp_path, monkeypatch):
    results = tmp_path / "results.csv"
    write(results, [
        {"id": "1", "type": "simple", "note_exactitude": "", "note_fidelite": "", "commentaire": ""},
        {"id": "2", "type": "hors_corpus", "note_exactitude": "", "note_fidelite": "", "commentaire": ""},
    ], COLUMNS)
    monkeypatch.setattr(merge_notes, "RESULTS_FILE", results)
    return results, tmp_path / "mes_notes.csv"


def read(path):
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def test_notes_are_copied_as_typed(files):
    results, notes = files
    write(notes, [{"id": "1", "note_exactitude": "2", "note_fidelite": "1", "commentaire": "Très bien"},
                  {"id": "2", "note_exactitude": "", "note_fidelite": "1", "commentaire": ""}],
          ["id", "note_exactitude", "note_fidelite", "commentaire"])
    merge_notes.main(notes)
    rows = read(results)
    assert (rows[0]["note_exactitude"], rows[0]["note_fidelite"], rows[0]["commentaire"]) == ("2", "1", "Très bien")
    assert (rows[1]["note_exactitude"], rows[1]["note_fidelite"]) == ("", "1")


def test_invalid_note_is_refused_and_results_stay_untouched(files):
    results, notes = files
    before = results.read_text(encoding="utf-8-sig")
    write(notes, [{"id": "1", "note_exactitude": "5", "note_fidelite": "1", "commentaire": ""}],
          ["id", "note_exactitude", "note_fidelite", "commentaire"])
    with pytest.raises(SystemExit):
        merge_notes.main(notes)
    assert results.read_text(encoding="utf-8-sig") == before


def test_missing_notes_are_never_filled_in(files, capsys):
    results, notes = files
    write(notes, [{"id": "1", "note_exactitude": "", "note_fidelite": "", "commentaire": ""}],
          ["id", "note_exactitude", "note_fidelite", "commentaire"])
    merge_notes.main(notes)
    assert read(results)[0]["note_exactitude"] == ""
    assert "Il manque encore des notes" in capsys.readouterr().out
