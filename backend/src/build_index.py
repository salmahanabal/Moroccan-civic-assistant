"""Construit l'index vectoriel à partir de data/processed/chunks.jsonl.

Commande (depuis le dossier backend) : python -m src.build_index

Le premier lancement télécharge le modèle d'embeddings (plusieurs centaines de Mo),
puis calcule le vecteur des ~2 000 chunks : prévoir quelques minutes sur CPU.
"""

import json
import sys
import time

from src import config, embeddings, vectorstore


def load_chunks() -> list[dict]:
    """Lit le fichier JSONL produit par make_chunks (un chunk par ligne)."""
    with open(config.CHUNKS_FILE, encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    chunks = load_chunks()
    print(f"{len(chunks)} chunks à indexer avec le modèle {config.EMBEDDING_MODEL}")

    started = time.time()
    vectors = embeddings.embed_passages([chunk["text"] for chunk in chunks])
    print(f"Vecteurs calculés en {time.time() - started:.0f} s")

    # reset=True : on repart d'une collection vide, pour ne jamais avoir de doublons
    collection = vectorstore.get_collection(reset=True)
    vectorstore.add_chunks(collection, chunks, vectors)
    print(f"Index construit : {collection.count()} chunks dans {config.CHROMA_DIR}")


if __name__ == "__main__":
    main()
