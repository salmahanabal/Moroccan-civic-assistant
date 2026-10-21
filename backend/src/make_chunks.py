"""Lance les trois premières étapes du pipeline et écrit data/processed/chunks.jsonl.

Commande (depuis le dossier backend) : python -m src.make_chunks
Format JSONL : un chunk par ligne, sous forme d'objet JSON.
"""

import json
import sys

from src import chunking, cleaning, config, ingest


def load_arabic_vocabulary(documents: list[dict]) -> set[str] | None:
    """Construit le vocabulaire arabe de référence à partir d'un texte sain (la Constitution)."""
    reference = next((doc for doc in documents if doc["file"] == config.ARABIC_REFERENCE_FILE), None)
    if reference is None:
        print("ATTENTION : texte arabe de référence introuvable, pas de réparation des ligatures.")
        return None
    # On applique d'abord la règle A pour ne pas mettre de mots abîmés dans le vocabulaire
    pages = [
        cleaning.fix_article_ligature(cleaning.remove_stray_question_marks(cleaning.normalize_unicode(page)))
        for page in reference["pages"]
    ]
    return cleaning.build_arabic_vocabulary(pages)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # pour que la console Windows affiche les accents
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    documents = ingest.ingest_all()
    arabic_vocabulary = load_arabic_vocabulary(documents)

    total_chunks = 0
    with open(config.CHUNKS_FILE, "w", encoding="utf-8") as output:
        for document in documents:
            pages = cleaning.clean_document(document["pages"], arabic_vocabulary)
            chunks = chunking.chunk_document(pages, document)
            for chunk in chunks:
                # ensure_ascii=False : on garde l'arabe et les accents lisibles dans le fichier
                output.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            total_chunks += len(chunks)
            print(f"{document['file']}: {len(document['pages'])} pages -> {len(chunks)} chunks")

    print(f"\nTotal : {total_chunks} chunks écrits dans {config.CHUNKS_FILE}")


if __name__ == "__main__":
    main()
