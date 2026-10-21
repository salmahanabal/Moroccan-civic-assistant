"""Teste la recherche : affiche les chunks les plus proches d'une question.

Exemples (depuis le dossier backend) :
    python -m src.search "À partir de quel âge peut-on voter ?"
    python -m src.search "كيف يتم تأسيس حزب سياسي؟" --top-k 3
    python -m src.search "Quel est le meilleur parti ?" --theme elections
"""

import argparse
import sys

from src import config, retriever


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Recherche les chunks les plus proches d'une question.")
    parser.add_argument("question", help="la question, entre guillemets")
    parser.add_argument("--top-k", type=int, default=config.TOP_K, help="nombre de chunks à afficher")
    parser.add_argument("--theme", default=None, help="limiter la recherche à un thème (ex. elections)")
    arguments = parser.parse_args()

    results = retriever.retrieve(arguments.question, top_k=arguments.top_k, theme=arguments.theme)
    for rank, result in enumerate(results, start=1):
        print(f"[{rank}] score {result['score']:.3f} | {result['file']} | page {result['page']} | {result['theme']}")
        print("    " + result["text"][:300].replace("\n", " ") + "...")
        print()

    verdict = "réponse possible" if retriever.has_answer(results) else "pas de réponse dans le corpus"
    print(f"Meilleur score : {results[0]['score']:.3f} (seuil {config.SCORE_THRESHOLD}) -> {verdict}")


if __name__ == "__main__":
    main()
