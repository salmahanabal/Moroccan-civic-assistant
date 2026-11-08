"""Tableau « avant / après les corrections » sur les trois jeux de questions, lu dans les fichiers de résultats.

    python -m evaluation.compare_runs

Chaque chiffre vient d'un fichier results*.csv (réponses du système) et d'un fichier judge_results*.csv
(notes du juge LLM) : rien n'est écrit à la main. Pour pouvoir comparer « avant » et « après » sur le même
pied, l'exactitude et la fidélité sont celles du JUGE dans les deux cas (la notation manuelle du jeu de départ
n'existe que pour l'ancien système ; elle reste dans results.csv).
"""

import csv
import statistics
import sys

from src import config

# (jeu, état, fichier de résultats, fichier du juge)
RUNS = [
    ("Jeu de départ (30 questions)", "avant", "results.csv", "judge_results.csv"),
    ("Jeu de départ (30 questions)", "après", "results_set1_after.csv", "judge_results_set1_after.csv"),
    ("Jeu de réglage (45 questions)", "avant", "results_set2.csv", "judge_results_set2.csv"),
    ("Jeu de réglage (45 questions)", "après", "results_set2_after.csv", "judge_results_set2_after.csv"),
    ("Jeu de test final (36 questions)", "avant", "results_set3_before.csv", "judge_results_set3_before.csv"),
    ("Jeu de test final (36 questions)", "après", "results_set3_after.csv", "judge_results_set3_after.csv"),
]


def read_csv(path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def summarize_run(results: list[dict], judge: list[dict]) -> dict:
    """Chiffres d'un passage du système sur un jeu de questions."""
    in_corpus = [row for row in results if row["type"] != "hors_corpus"]
    out_corpus = [row for row in results if row["type"] == "hors_corpus"]
    scores = [int(row["judge_exactitude"]) for row in judge if row["type"] != "hors_corpus" and row["judge_exactitude"] != ""]
    faithful = [int(row["judge_fidelite"]) for row in judge if row["judge_fidelite"] != ""]
    durations = [float(row["duree_s"]) for row in results if row["duree_s"] != ""]
    return {
        "hit": (sum(int(row["hit_at_5"]) for row in in_corpus if row["hit_at_5"] != ""), len(in_corpus)),
        "refus_correct": (sum(int(row["refus_correct"]) for row in out_corpus if row["refus_correct"] != ""), len(out_corpus)),
        # le système a répondu « pas dans mes documents » alors que la question porte sur le corpus
        "refus_a_tort": (sum(1 for row in in_corpus if row["found"] == "False"), len(in_corpus)),
        "exactitude": statistics.mean(scores) if scores else None,
        "fidelite": (sum(faithful), len(faithful)),
        "latence": statistics.mean(durations) if durations else None,
    }


def format_row(set_name: str, state: str, summary: dict) -> str:
    def ratio(pair):
        done, total = pair
        return f"{100 * done / total:.0f} % ({done}/{total})" if total else "—"

    accuracy = f"{summary['exactitude']:.2f} / 2" if summary["exactitude"] is not None else "—"
    latency = f"{summary['latence']:.1f} s" if summary["latence"] is not None else "—"
    return (f"| {set_name} | {state} | {ratio(summary['hit'])} | {ratio(summary['refus_correct'])} | {ratio(summary['refus_a_tort'])} "
            f"| {accuracy} | {ratio(summary['fidelite'])} | {latency} |")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    print("| Jeu | Système | Hit rate@5 | Refus correct (hors corpus) | Refus à tort (corpus) | Exactitude (juge) | Fidélité (juge) | Latence |")
    print("|---|---|---|---|---|---|---|---|")
    for set_name, state, results_file, judge_file in RUNS:
        results_path, judge_path = config.EVAL_DIR / results_file, config.EVAL_DIR / judge_file
        if not (results_path.exists() and judge_path.exists()):
            continue
        print(format_row(set_name, state, summarize_run(read_csv(results_path), read_csv(judge_path))))


if __name__ == "__main__":
    main()
