"""Affiche 5 chunks au hasard (3 en français, 2 en arabe) pour les relire à la main.

Commande (depuis le dossier backend) : python -m src.sample_chunks
Le résultat est aussi écrit dans data/processed/sample_chunks.txt : ouvre ce
fichier dans VS Code pour lire l'arabe correctement (la console l'affiche mal).
"""

import json
import random
import sys

from src import config


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with open(config.CHUNKS_FILE, encoding="utf-8") as file:
        chunks = [json.loads(line) for line in file]

    french = [chunk for chunk in chunks if chunk["language"] == "fr"]
    arabic = [chunk for chunk in chunks if chunk["language"] == "ar"]
    selection = random.sample(french, 3) + random.sample(arabic, 2)

    lines = []
    for chunk in selection:
        lines.append(
            f"=== {chunk['file']} | page {chunk['page']} | {chunk['theme']} | {chunk['language']} "
            f"| {len(chunk['text'])} caractères"
        )
        lines.append(chunk["text"])
        lines.append("")
    report = "\n".join(lines)

    print(report)
    sample_path = config.PROCESSED_DIR / "sample_chunks.txt"
    sample_path.write_text(report, encoding="utf-8")
    print(f"(copie enregistrée dans {sample_path})")


if __name__ == "__main__":
    main()
