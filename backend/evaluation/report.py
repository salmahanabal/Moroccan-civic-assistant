"""Fabrique le tableau comparatif des configurations en lisant les fichiers results*.csv.

    python -m evaluation.report

Chaque ligne du tableau vient d'un fichier de résultats : aucun chiffre n'est écrit à la main.
Les colonnes d'exactitude, de fidélité et de refus restent vides tant que le fichier ne contient
pas les notes (ou les mesures) correspondantes.
"""

import csv
import statistics
import sys

from src import config


def read_results(path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def percent(values: list[int]) -> str:
    return f"{100 * sum(values) / len(values):.0f} % ({sum(values)}/{len(values)})" if values else "—"


def row_for(path) -> dict:
    rows = read_results(path)
    in_corpus = [r for r in rows if r["type"] != "hors_corpus"]
    hits = [int(r["hit_at_5"]) for r in in_corpus if r["hit_at_5"] != ""]
    refusals = [int(r["refus_correct"]) for r in rows if r["refus_correct"] != ""]
    accuracy = [int(r["note_exactitude"]) for r in in_corpus if r["note_exactitude"] != ""]
    faithfulness = [int(r["note_fidelite"]) for r in rows if r["note_fidelite"] != ""]
    durations = [float(r["duree_s"]) for r in rows if r["duree_s"] != ""]
    return {
        "fichier": path.name,
        "config": rows[0]["config"],
        "hit": percent(hits),
        "refus": percent(refusals),
        "exactitude": f"{statistics.mean(accuracy):.2f} / 2" if accuracy else "—",
        "fidelite": percent(faithfulness),
        "latence": f"{statistics.mean(durations):.1f} s" if durations else "—",
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    files = sorted(config.EVAL_DIR.glob("results*.csv"))
    rows = [row_for(path) for path in files]
    print("| Fichier de résultats | Configuration | Hit rate@5 | Refus correct | Exactitude | Fidélité | Latence |")
    print("|---|---|---|---|---|---|---|")
    for r in rows:
        print(f"| `{r['fichier']}` | {r['config']} | {r['hit']} | {r['refus']} | {r['exactitude']} | {r['fidelite']} | {r['latence']} |")


if __name__ == "__main__":
    main()
