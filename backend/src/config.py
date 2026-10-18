"""Paramètres centralisés du projet (NFR-4).

Tous les réglages qu'on veut comparer à l'évaluation sont ici,
et nulle part ailleurs dans le code.
"""

from pathlib import Path

# --- Chemins (calculés à partir de l'emplacement de ce fichier) ---
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

RAW_DIR = ROOT_DIR / "data" / "raw"                      # PDF du corpus
PROCESSED_DIR = ROOT_DIR / "data" / "processed"          # résultats intermédiaires
SOURCES_CSV = ROOT_DIR / "data" / "sources.csv"          # registre des documents
CHUNKS_FILE = PROCESSED_DIR / "chunks.jsonl"             # chunks après découpage
CHROMA_DIR = BACKEND_DIR / "chroma_db"                   # index vectoriel persistant
EVAL_DIR = BACKEND_DIR / "evaluation"                    # questions et résultats

# --- Découpage en chunks (configuration A ; B = 1200 / 200) ---
CHUNK_SIZE = 800        # taille d'un chunk, en caractères
CHUNK_OVERLAP = 150     # chevauchement entre deux chunks consécutifs

# --- Embeddings (configuration A ; C = "BAAI/bge-m3") ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# --- Recherche ---
TOP_K = 5               # nombre de chunks retrouvés par question
SCORE_THRESHOLD = 0.5   # valeur provisoire : sera calibrée en Phase 3/5

# --- Base vectorielle ---
COLLECTION_NAME = "demarches_maroc"

# --- Génération (le nom du modèle sera fixé en Phase 4) ---
MAX_TOKENS = 600        # borne la longueur de la réponse du LLM (coût)
MAX_QUESTION_LENGTH = 500
