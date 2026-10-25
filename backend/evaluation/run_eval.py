"""Évaluation chiffrée du RAG (Phase 5, exigence FR-10).

Deux commandes, à lancer depuis le dossier backend :

    python -m evaluation.run_eval             pose les 30 questions et écrit results.csv
    python -m evaluation.run_eval --summary   calcule les chiffres à partir de results.csv

Calculé automatiquement : hit rate@5, refus correct, latence.
À remplir À LA MAIN dans results.csv (colonnes vides) : note_exactitude (0, 1 ou 2)
et note_fidelite (0 ou 1). Seules les notes que tu saisis comptent.
"""

import argparse
import csv
import statistics
import sys
import time

from src import config, generator, rag, retriever

QUESTIONS_FILE = config.EVAL_DIR / "questions.csv"
RESULTS_FILE = config.EVAL_DIR / f"results{config.FILE_SUFFIX}.csv"  # results.csv, results_B.csv...

COLUMNS = [
    "id", "question", "langue", "type", "reponse_attendue", "fichier_attendu", "page_attendue",
    "config", "found", "reponse_systeme", "sources_citees", "top5_fichiers", "meilleur_score",
    "hit_at_5", "refus_correct", "duree_s", "erreur",
    "note_exactitude", "note_fidelite", "commentaire",
]


def read_csv(path) -> list[dict]:
    # utf-8-sig : le fichier est enregistré avec une « signature » pour qu'Excel lise bien l'arabe
    with open(path, encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def is_hit(expected: str, top5_files: list[str]) -> bool:
    """Le ou les documents attendus sont-ils dans les 5 chunks retrouvés ?

    « ; » sépare les documents qui doivent TOUS apparaître (question à deux textes) ;
    « | » sépare des équivalents dont UN SEUL suffit (même loi en français et en arabe).
    """
    groups = [group.split("|") for group in expected.split(";") if group]
    return bool(groups) and all(any(name in top5_files for name in group) for group in groups)


def no_llm_generate(system_prompt: str, user_prompt: str) -> str:
    """Faux LLM pour tester la recherche seule : ne consomme aucun quota."""
    return "(réponse non générée : mode --no-llm)"


def evaluate_question(question: dict, label: str, pause: float, use_llm: bool = True) -> dict:
    """Pose une question au système et mesure le résultat."""
    retrieved: dict[str, list[dict]] = {}

    def spy_retrieve(text, theme=None):
        """Même recherche que d'habitude, mais on garde les 5 chunks pour le hit rate."""
        retrieved["chunks"] = retriever.retrieve(text, theme=theme)
        return retrieved["chunks"]

    generate_fn = generator.generate_answer if use_llm else no_llm_generate
    result, error = None, ""
    for attempt in range(3):  # le LLM peut refuser temporairement (trop de requêtes)
        try:
            result = rag.answer_question(question["question"], retrieve_fn=spy_retrieve, generate_fn=generate_fn)
            error = ""
            break
        except generator.LLMUnavailableError as exc:
            error = str(exc)
            time.sleep(30 * (attempt + 1))
    if use_llm:
        time.sleep(pause)

    top5 = [chunk["file"] for chunk in retrieved.get("chunks", [])]
    is_out_of_corpus = question["type"] == "hors_corpus"

    row = {column: "" for column in COLUMNS}
    row.update({key: question[key] for key in ("id", "question", "langue", "type", "reponse_attendue", "fichier_attendu", "page_attendue")})
    row["config"] = label
    row["top5_fichiers"] = ";".join(top5)
    row["meilleur_score"] = round(retrieved["chunks"][0]["score"], 3) if retrieved.get("chunks") else ""
    row["erreur"] = error
    if result:
        row["found"] = result["found"]
        row["reponse_systeme"] = result["answer"]
        row["sources_citees"] = ";".join(f"{s['file']} p.{s['page']}" for s in result["sources"])
        if use_llm:
            row["duree_s"] = result["duration_seconds"]  # sans LLM, ce temps ne mesurerait que la recherche
        if is_out_of_corpus and use_llm:
            # Sans LLM, personne ne peut refuser : cette mesure n'aurait aucun sens
            row["refus_correct"] = 1 if not result["found"] else 0
    if not is_out_of_corpus and question["fichier_attendu"]:
        # hit rate@5 : le fichier attendu apparaît-il parmi les 5 chunks retrouvés ?
        row["hit_at_5"] = 1 if is_hit(question["fichier_attendu"], top5) else 0
    return row


def run(label: str, pause: float, use_llm: bool = True) -> None:
    questions = read_csv(QUESTIONS_FILE)
    rows = []
    for number, question in enumerate(questions, start=1):
        row = evaluate_question(question, label, pause, use_llm)
        rows.append(row)
        print(f"[{number}/{len(questions)}] {question['type']:12} found={row['found']!s:5} hit={row['hit_at_5']!s:1} "
              f"{row['duree_s']!s:>5}s  {question['question'][:60]}")
    with open(RESULTS_FILE, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nRésultats écrits dans {RESULTS_FILE}")
    if not use_llm:
        # Échelle des scores de CE modèle : sert à choisir un seuil de refus adapté
        best_in = [float(r["meilleur_score"]) for r in rows if r["type"] != "hors_corpus" and r["meilleur_score"] != ""]
        best_out = [float(r["meilleur_score"]) for r in rows if r["type"] == "hors_corpus" and r["meilleur_score"] != ""]
        print(f"Scores du meilleur chunk : questions du corpus min {min(best_in):.3f} | hors corpus max {max(best_out):.3f}")
    else:
        print("À toi : remplis note_exactitude (0, 1, 2) et note_fidelite (0, 1), puis lance --summary.")


def mean_or_none(values: list[float]):
    return statistics.mean(values) if values else None


def summary() -> None:
    """Calcule les chiffres du tableau d'évaluation à partir de results.csv (et de tes notes)."""
    rows = read_csv(RESULTS_FILE)
    in_corpus = [r for r in rows if r["type"] != "hors_corpus"]
    out_corpus = [r for r in rows if r["type"] == "hors_corpus"]

    hits = [int(r["hit_at_5"]) for r in in_corpus if r["hit_at_5"] != ""]
    refusals = [int(r["refus_correct"]) for r in out_corpus if r["refus_correct"] != ""]
    durations = [float(r["duree_s"]) for r in rows if r["duree_s"] != ""]
    accuracy = [int(r["note_exactitude"]) for r in in_corpus if r["note_exactitude"] != ""]
    faithfulness = [int(r["note_fidelite"]) for r in rows if r["note_fidelite"] != ""]

    print(f"Configuration : {rows[0]['config']}")
    print(f"Hit rate@5            : {sum(hits)}/{len(hits)} = {100 * sum(hits) / len(hits):.0f} %  (cible >= 80 %)")
    if refusals:
        print(f"Refus correct         : {sum(refusals)}/{len(refusals)} = {100 * sum(refusals) / len(refusals):.0f} %  (cible >= 80 %)")
    if durations:
        print(f"Latence moyenne       : {statistics.mean(durations):.1f} s  (cible < 10 s)")
    if accuracy:
        print(f"Exactitude moyenne    : {statistics.mean(accuracy):.2f} / 2 sur {len(accuracy)} notes  (cible >= 1,4)")
    else:
        print("Exactitude moyenne    : à calculer quand tu auras noté (colonne note_exactitude)")
    if faithfulness:
        print(f"Fidélité              : {100 * sum(faithfulness) / len(faithfulness):.0f} % sur {len(faithfulness)} notes  (cible >= 90 %)")
    else:
        print("Fidélité              : à calculer quand tu auras noté (colonne note_fidelite)")
    for kind in ("simple", "combinee", "arabe"):
        subset = [int(r["hit_at_5"]) for r in in_corpus if r["type"] == kind and r["hit_at_5"] != ""]
        if subset:
            print(f"  hit rate@5 {kind:9}: {sum(subset)}/{len(subset)}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Évalue le RAG sur les questions de référence.")
    parser.add_argument("--summary", action="store_true", help="calcule les chiffres à partir de results.csv")
    parser.add_argument("--label", default="A", help="nom de la configuration testée (A, B, C...)")
    parser.add_argument("--pause", type=float, default=4.0, help="secondes d'attente entre deux questions")
    parser.add_argument("--no-llm", action="store_true", help="teste seulement la recherche (aucun appel au LLM)")
    parser.add_argument("--output", default=None, help="nom du fichier de résultats (défaut : results.csv)")
    arguments = parser.parse_args()
    if arguments.output:
        global RESULTS_FILE
        RESULTS_FILE = config.EVAL_DIR / arguments.output
    if arguments.summary:
        summary()
    else:
        run(arguments.label, arguments.pause, use_llm=not arguments.no_llm)


if __name__ == "__main__":
    main()
