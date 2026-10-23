"""Pose une question au RAG depuis le terminal.

Exemple (depuis le dossier backend) :
    python -m src.ask "À partir de quel âge peut-on voter ?"
"""

import argparse
import sys

from src import generator, rag


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Pose une question à l'assistant.")
    parser.add_argument("question", help="la question, entre guillemets")
    parser.add_argument("--theme", default=None, help="limiter la recherche à un thème")
    arguments = parser.parse_args()

    try:
        result = rag.answer_question(arguments.question, theme=arguments.theme)
    except generator.LLMUnavailableError as error:
        print(f"Le modèle n'est pas disponible : {error}")
        sys.exit(1)

    print(result["answer"])
    print(f"\n(langue : {result['language']} | trouvée : {result['found']} | {result['duration_seconds']} s)")
    for source in result["sources"]:
        print(f"  [{source['id']}] {source['file']} | page {source['page']} | score {source['score']}")
        print(f"      {source['excerpt'][:120].replace(chr(10), ' ')}...")


if __name__ == "__main__":
    main()
