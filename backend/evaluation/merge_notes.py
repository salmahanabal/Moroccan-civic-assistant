"""Recopie tes notes (fichier mes_notes.csv téléchargé depuis NOTATION.html) dans results.csv.

    python -m evaluation.merge_notes                      cherche mes_notes.csv dans backend/evaluation
    python -m evaluation.merge_notes chemin/vers/mes_notes.csv

Le script ne CHOISIT aucune note : il recopie seulement celles que tu as saisies, et refuse
toute valeur hors des barèmes (exactitude 0, 1 ou 2 ; fidélité 0 ou 1).
"""

import csv
import sys

from src import config

RESULTS_FILE = config.EVAL_DIR / "results.csv"
DEFAULT_NOTES = config.EVAL_DIR / "mes_notes.csv"
ALLOWED = {"note_exactitude": {"0", "1", "2"}, "note_fidelite": {"0", "1"}}


def read_csv(path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main(notes_path=None) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    notes_path = notes_path or (DEFAULT_NOTES if len(sys.argv) < 2 else sys.argv[1])
    notes = {row["id"]: row for row in read_csv(notes_path)}
    rows = read_csv(RESULTS_FILE)

    merged = 0
    for row in rows:
        note = notes.get(row["id"])
        if not note:
            continue
        for column, allowed in ALLOWED.items():
            value = (note.get(column) or "").strip()
            if value and value not in allowed:
                raise SystemExit(f"Question {row['id']} : « {value} » n'est pas une note valable pour {column}.")
            if value:
                row[column] = value
        if (note.get("commentaire") or "").strip():
            row["commentaire"] = note["commentaire"].strip()
        merged += 1

    with open(RESULTS_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    missing = [
        r["id"] for r in rows
        if not r["note_fidelite"] or (r["type"] != "hors_corpus" and not r["note_exactitude"])
    ]
    print(f"{merged} lignes mises à jour dans {RESULTS_FILE.name}.")
    if missing:
        print("Il manque encore des notes pour les questions :", ", ".join(sorted(set(missing), key=int)))
    else:
        print("Toutes les notes sont là. Lance maintenant : python -m evaluation.run_eval --summary")


if __name__ == "__main__":
    main()
