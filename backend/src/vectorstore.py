"""Stockage et recherche des vecteurs dans ChromaDB (étape 5 du pipeline, FR-3 et FR-4).

ChromaDB est une base de données faite pour retrouver les vecteurs les plus
proches d'un vecteur donné. Elle écrit ses données dans backend/chroma_db/
(dossier hors Git), donc l'index survit quand on éteint l'ordinateur.
"""

from pathlib import Path

import chromadb

from src import config


def get_client(path: Path = config.CHROMA_DIR) -> chromadb.ClientAPI:
    """Ouvre (ou crée) la base ChromaDB persistante."""
    return chromadb.PersistentClient(path=str(path))


def get_collection(client: chromadb.ClientAPI | None = None, reset: bool = False):
    """Renvoie la collection des chunks ; avec reset=True, on repart d'une collection vide.

    « cosine » = on compare les vecteurs par leur angle (le sens), pas par leur longueur.
    """
    client = client or get_client()
    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
        except Exception:  # la collection n'existait pas encore : rien à supprimer
            pass
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def add_chunks(collection, chunks: list[dict], embeddings: list[list[float]], batch_size: int = 500) -> None:
    """Ajoute les chunks (texte + vecteur + métadonnées) par paquets."""
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        collection.add(
            ids=[chunk["chunk_id"] for chunk in batch],
            embeddings=embeddings[start : start + batch_size],
            documents=[chunk["text"] for chunk in batch],
            metadatas=[
                {
                    "file": chunk["file"],
                    "page": chunk["page"],
                    "theme": chunk["theme"],
                    "language": chunk["language"],
                    "url": chunk["url"],
                }
                for chunk in batch
            ],
        )


def search(collection, query_embedding: list[float], top_k: int = config.TOP_K, theme: str | None = None) -> list[dict]:
    """Renvoie les top_k chunks les plus proches, avec leur score de similarité.

    Score = 1 - distance : 1 veut dire « identique », 0 « aucun rapport ».
    Avec theme, la recherche est limitée aux chunks de ce thème (FR-14).
    """
    options = {"where": {"theme": theme}} if theme else {}
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
        **options,
    )
    return [
        {"text": text, "score": 1 - distance, **metadata}
        for text, metadata, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0]
        )
    ]
