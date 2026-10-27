"""Test du LLM juge avec de MAUVAISES réponses fabriquées exprès (« contrôles négatifs »).

    python -m evaluation.judge_controls             fabrique les mauvaises réponses et les fait noter par le juge
    python -m evaluation.judge_controls --report    dit combien de mauvaises réponses le juge a attrapées

Pourquoi : sur de bonnes réponses, un juge qui donne 2 à tout serait d'accord avec toi sans savoir repérer
une erreur. Ici, chaque réponse est abîmée d'une façon connue ; on sait donc ce que le juge DOIT trouver.
Les copies abîmées vivent seulement dans judge_controls.csv : results.csv et tes notes ne sont pas modifiés.

Quatre sortes de défauts :
  autre_question  la réponse d'une autre question (fidèle à ses sources, mais ne répond pas à la question) -> exactitude < 2
  chiffre_modifie un chiffre de la réponse est remplacé par un autre                                      -> exactitude < 2 ou fidélité 0
  invention       une phrase inventée est ajoutée à une bonne réponse                                      -> fidélité 0
  refus_a_tort    l'assistant refuse alors que la réponse existe                                           -> exactitude 0
"""

import argparse
import csv
import random
import re
import sys
import time

from evaluation.llm_judge import judge_row, read_csv
from src import config, generator, prompts, vectorstore

RESULTS_FILE = config.EVAL_DIR / "results.csv"
CONTROLS_FILE = config.EVAL_DIR / "judge_controls.csv"
CONTROL_COLUMNS = ["control_id", "kind", "base_id", "swap_id", "judge_exactitude", "judge_fidelite", "judge_model", "judge_raison", "detected"]
SEED = 42
PER_KIND = 8   # nombre de réponses abîmées pour chaque sorte de défaut

INVENTED_SENTENCE = {
    "fr": " Cette règle a été instaurée par la loi n° 99-999 de 1987 et s'applique aussi aux associations étrangères.",
    "ar": " وقد تم إقرار هذه القاعدة بموجب القانون رقم 99.999 لسنة 1987 وتسري أيضا على الجمعيات الأجنبية.",
}
NUMBER = re.compile(r"(?<![\[\d])\d{2,4}(?![\]\d])")   # un nombre de 2 à 4 chiffres qui n'est pas une citation [12]


def alter_number(answer: str) -> str | None:
    """Remplace le premier nombre de la réponse par un autre (+7) ; None s'il n'y en a aucun."""
    match = NUMBER.search(answer)
    if not match:
        return None
    return answer[: match.start()] + str(int(match.group()) + 7) + answer[match.end():]


def make_controls(rows: list[dict], seed: int = SEED, per_kind: int = PER_KIND) -> list[dict]:
    """Fabrique les réponses abîmées à partir des vraies réponses des questions du corpus."""
    rng = random.Random(seed)
    candidates = [row for row in rows if row["type"] != "hors_corpus" and row["reponse_systeme"]]
    controls: list[dict] = []

    def add(kind: str, base: dict, answer: str, sources: str, swap_id: str = "") -> None:
        controls.append({
            "control_id": f"{kind}-{base['id']}", "kind": kind, "base_id": base["id"], "swap_id": swap_id,
            "row": {**base, "reponse_systeme": answer, "sources_citees": sources},
        })

    # 1. la réponse d'une autre question de la même langue (le texte ne trahit pas la langue)
    for base in rng.sample(candidates, min(per_kind, len(candidates))):
        others = [r for r in candidates if r["id"] != base["id"] and r["langue"] == base["langue"]
                  and r["question"] != base["question"]]
        other = rng.choice(others)
        add("autre_question", base, other["reponse_systeme"], other["sources_citees"], swap_id=other["id"])

    # 2. un chiffre modifié (seulement dans les réponses qui contiennent un nombre)
    with_number = [r for r in candidates if alter_number(r["reponse_systeme"])]
    for base in rng.sample(with_number, min(per_kind, len(with_number))):
        add("chiffre_modifie", base, alter_number(base["reponse_systeme"]), base["sources_citees"])

    # 3. une phrase inventée ajoutée à la fin
    for base in rng.sample(candidates, min(per_kind, len(candidates))):
        add("invention", base, base["reponse_systeme"] + INVENTED_SENTENCE[base["langue"]], base["sources_citees"])

    # 4. un refus alors que la réponse existe (un vrai refus ne cite aucune source)
    for base in rng.sample(candidates, min(per_kind, len(candidates))):
        add("refus_a_tort", base, prompts.REFUSAL_MESSAGES["no_answer"][base["langue"]], "")
    return controls


def is_detected(kind: str, exactitude: int | None, fidelite: int) -> bool:
    """Le juge a-t-il repéré le défaut connu de cette sorte de mauvaise réponse ?"""
    if kind == "autre_question":
        return exactitude is not None and exactitude < 2
    if kind == "chiffre_modifie":
        return (exactitude is not None and exactitude < 2) or fidelite == 0
    if kind == "invention":
        return fidelite == 0
    if kind == "refus_a_tort":
        return exactitude == 0
    raise ValueError(kind)


def run_controls(pause: float) -> None:
    from evaluation.make_scoring_page import cited_passages

    rows = read_csv(RESULTS_FILE)
    by_id = {row["id"]: row for row in rows}
    controls = make_controls(rows)
    done = {row["control_id"] for row in read_csv(CONTROLS_FILE)} if CONTROLS_FILE.exists() else set()
    todo = [c for c in controls if c["control_id"] not in done]
    print(f"{len(controls)} mauvaises réponses fabriquées, {len(done)} déjà jugées, {len(todo)} à juger.")
    if not todo:
        return

    collection = vectorstore.get_collection()
    new_file = not CONTROLS_FILE.exists()
    with open(CONTROLS_FILE, "a", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=CONTROL_COLUMNS, lineterminator="\n")
        if new_file:
            writer.writeheader()
        for control in todo:
            row = control["row"]
            # le juge voit les passages que l'assistant aurait cités (ceux de l'autre question pour « autre_question »)
            source_row = by_id[control["swap_id"]] if control["swap_id"] else row
            passages = cited_passages(source_row["question"], row["sources_citees"], collection) if row["sources_citees"] else []
            try:
                outcome = judge_row(row, passages)
            except generator.LLMUnavailableError as error:
                print(f"Arrêt à {control['control_id']} (quota ou panne) : {error}\nRelance plus tard : le script reprend ici.")
                return
            if not outcome:
                print(f"[{control['control_id']}] réponse du juge inutilisable, ignorée (relance possible).")
                continue
            judgement, model = outcome
            detected = is_detected(control["kind"], judgement["exactitude"], judgement["fidelite"])
            writer.writerow({
                "control_id": control["control_id"], "kind": control["kind"], "base_id": control["base_id"],
                "swap_id": control["swap_id"],
                "judge_exactitude": "" if judgement["exactitude"] is None else judgement["exactitude"],
                "judge_fidelite": judgement["fidelite"], "judge_model": model, "judge_raison": judgement["raison"],
                "detected": int(detected),
            })
            file.flush()
            print(f"{control['control_id']:22} exactitude={judgement['exactitude']} fidélité={judgement['fidelite']} -> {'attrapé' if detected else 'MANQUÉ'}")
            time.sleep(pause)


def report() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    rows = read_csv(CONTROLS_FILE)
    labels = {
        "autre_question": "réponse d'une autre question (attendu : exactitude < 2)",
        "chiffre_modifie": "chiffre modifié (attendu : exactitude < 2 ou fidélité 0)",
        "invention": "phrase inventée ajoutée (attendu : fidélité 0)",
        "refus_a_tort": "refus à tort (attendu : exactitude 0)",
    }
    total = caught = 0
    for kind, description in labels.items():
        subset = [r for r in rows if r["kind"] == kind]
        if not subset:
            continue
        found = sum(int(r["detected"]) for r in subset)
        total, caught = total + len(subset), caught + found
        print(f"{description}\n   attrapées : {found}/{len(subset)} = {100 * found / len(subset):.0f} %")
        for r in subset:
            if r["detected"] == "0":
                print(f"   manquée : {r['control_id']} (exactitude={r['judge_exactitude']}, fidélité={r['judge_fidelite']}) — {r['judge_raison']}")
    if total:
        print(f"\nTOTAL : {caught}/{total} mauvaises réponses attrapées = {100 * caught / total:.0f} %")


def main() -> None:
    parser = argparse.ArgumentParser(description="Contrôles négatifs du LLM juge")
    parser.add_argument("--report", action="store_true", help="résumé des mauvaises réponses attrapées")
    parser.add_argument("--pause", type=float, default=4.0, help="secondes d'attente entre deux appels")
    arguments = parser.parse_args()
    report() if arguments.report else run_controls(arguments.pause)


if __name__ == "__main__":
    main()
