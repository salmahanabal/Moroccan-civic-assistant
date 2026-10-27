"""Vérifie que l'extrait montré pour chaque source contient bien la réponse (ancien extrait contre nouveau).

    python -m evaluation.check_excerpts            pose les questions du corpus au vrai système (consomme du quota LLM)
    python -m evaluation.check_excerpts --report   résume le dernier fichier excerpts_check.csv

Pour chaque source citée, on regarde quelle part des mots de la réponse qui se trouvent dans le passage
apparaît aussi dans l'extrait montré (« couverture »). C'est une mesure approchée (mots communs), pas un
jugement humain. On compare : le début du passage sur 200 caractères (l'ancien extrait), sur 300 caractères
(même longueur que le nouveau) et la phrase choisie par src/excerpt.py.
"""

import argparse
import csv
import time

from evaluation.llm_judge import read_csv
from src import config, excerpt, generator, rag, retriever

QUESTIONS_FILE = config.EVAL_DIR / "questions.csv"
OUTPUT_FILE = config.EVAL_DIR / "excerpts_check.csv"
COLUMNS = ["question_id", "type", "source_id", "file", "page", "same_language", "reachable_terms",
           "coverage_start_200", "coverage_start_300", "coverage_new", "highlighted", "excerpt_new"]
OLD_EXCERPT_CHARS = 200


def term_coverage(answer: str, chunk_text: str, shown_text: str) -> tuple[int, float | None]:
    """(nombre de mots de la réponse présents dans le passage, part d'entre eux visibles dans le texte montré).

    La part vaut None si aucun mot de la réponse n'est dans le passage (cas d'une autre langue) :
    il n'y a alors rien à retrouver, la mesure n'a pas de sens.
    """
    reachable = excerpt.stems_of(answer) & excerpt.stems_of(chunk_text)
    if not reachable:
        return 0, None
    return len(reachable), len(reachable & excerpt.stems_of(shown_text)) / len(reachable)


def run(pause: float) -> None:
    questions = [row for row in read_csv(QUESTIONS_FILE) if row["type"] != "hors_corpus"]
    captured: dict = {}

    def spy_retrieve(text, theme=None, sub_queries=None):
        captured["chunks"] = retriever.retrieve(text, theme=theme, sub_queries=sub_queries)
        return captured["chunks"]

    rows = []
    for question in questions:
        try:
            result = rag.answer_question(question["question"], retrieve_fn=spy_retrieve)
        except generator.LLMUnavailableError as error:
            print(f"Arrêt à la question {question['id']} (quota ou panne) : {error}")
            break
        for source in result["sources"]:
            chunk = captured["chunks"][source["id"] - 1]
            reachable, new_coverage = term_coverage(result["answer"], chunk["text"], source["excerpt"])
            _, start_200 = term_coverage(result["answer"], chunk["text"], chunk["text"][:OLD_EXCERPT_CHARS])
            _, start_300 = term_coverage(result["answer"], chunk["text"], chunk["text"][: config.EXCERPT_CHARS])
            same_language = result["language"] == ("ar" if source["file"].endswith("_ar.pdf") else "fr")
            rows.append({
                "question_id": question["id"], "type": question["type"], "source_id": source["id"], "file": source["file"],
                "page": source["page"], "same_language": int(same_language), "reachable_terms": reachable,
                "coverage_start_200": "" if start_200 is None else round(start_200, 3),
                "coverage_start_300": "" if start_300 is None else round(start_300, 3),
                "coverage_new": "" if new_coverage is None else round(new_coverage, 3),
                "highlighted": int(source["highlight_start"] is not None),
                "excerpt_new": source["excerpt"].replace("\n", " "),
            })
        print(f"question {question['id']:>2} : {len(result['sources'])} source(s)")
        time.sleep(pause)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} sources écrites dans {OUTPUT_FILE.name}")


def report() -> None:
    rows = read_csv(OUTPUT_FILE)
    print(f"{len(rows)} sources citées (25 questions du corpus)\n")
    for label, subset in (("même langue que la réponse", [r for r in rows if r["same_language"] == "1"]),
                          ("autre langue que la réponse", [r for r in rows if r["same_language"] == "0"])):
        measured = [r for r in subset if r["coverage_new"] != ""]
        print(f"{label} : {len(subset)} sources, dont {len(measured)} mesurables, "
              f"{sum(int(r['highlighted']) for r in subset)} avec phrase surlignée")
        if measured:
            for name, column in (("début du passage, 200 caractères (ancien)", "coverage_start_200"),
                                 ("début du passage, 300 caractères", "coverage_start_300"),
                                 ("phrase choisie (nouveau)", "coverage_new")):
                values = [float(r[column]) for r in measured]
                complete = sum(value == 1.0 for value in values)
                print(f"   {name:45} couverture moyenne {100 * sum(values) / len(values):3.0f} %   "
                      f"réponse entièrement visible : {complete}/{len(values)}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare l'ancien et le nouvel extrait des sources")
    parser.add_argument("--report", action="store_true", help="résumé du dernier fichier excerpts_check.csv")
    parser.add_argument("--pause", type=float, default=4.0, help="secondes d'attente entre deux questions")
    arguments = parser.parse_args()
    if arguments.report:
        import sys
        sys.stdout.reconfigure(encoding="utf-8")
        report()
    else:
        run(arguments.pause)


if __name__ == "__main__":
    main()
