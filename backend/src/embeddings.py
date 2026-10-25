"""Transformation du texte en vecteurs (étape 4 du pipeline, exigence FR-3).

Le modèle est multilingue : le français et l'arabe vivent dans le même espace de
vecteurs. C'est ce qui permet de poser une question en arabe et de retrouver un
passage écrit en français (et inversement).
"""

from functools import lru_cache

import torch
from sentence_transformers import SentenceTransformer

from src import config


def get_prefix(kind: str, model_name: str = config.EMBEDDING_MODEL) -> str:
    """Préfixe à ajouter devant le texte avant de le transformer en vecteur.

    Les modèles de la famille « e5 » ont été entraînés avec « query: » devant
    les questions et « passage: » devant les textes à retrouver. Sans ce
    préfixe, la qualité de la recherche baisse. Le modèle bge-m3 n'en a pas besoin.
    """
    if "e5" in model_name.lower():
        return "query: " if kind == "query" else "passage: "
    return ""


@lru_cache(maxsize=1)
def get_model(model_name: str = config.EMBEDDING_MODEL) -> SentenceTransformer:
    """Charge le modèle une seule fois (le chargement est lent : plusieurs secondes).

    S'il y a une carte graphique NVIDIA utilisable, le calcul est environ dix fois plus rapide.
    On y charge alors le modèle en « demi-précision » (float16) : il occupe deux fois moins de
    mémoire graphique (indispensable avec 4 Go) pour une qualité pratiquement identique.
    Sans carte graphique (Docker, hébergeur gratuit), tout se passe comme avant, sur le processeur.
    """
    if torch.cuda.is_available():
        return SentenceTransformer(model_name, device="cuda", model_kwargs={"torch_dtype": torch.float16})
    return SentenceTransformer(model_name)


def embed_passages(texts: list[str], show_progress: bool = True) -> list[list[float]]:
    """Calcule le vecteur de chaque chunk (les vecteurs sont normalisés : longueur 1)."""
    prefix = get_prefix("passage")
    vectors = get_model().encode(
        [prefix + text for text in texts],
        batch_size=config.EMBEDDING_BATCH_SIZE,
        normalize_embeddings=True,
        show_progress_bar=show_progress,
    )
    return vectors.tolist()


def embed_query(question: str) -> list[float]:
    """Calcule le vecteur d'une question."""
    vector = get_model().encode(get_prefix("query") + question, normalize_embeddings=True)
    return vector.tolist()
