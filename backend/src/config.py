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
MIN_CHUNK_CHARS = 50    # un chunk plus court est ignoré (souvent un titre isolé)

# --- Nettoyage du texte ---
MIN_PAGES_FOR_HEADER_DETECTION = 5   # en dessous, on ne cherche pas d'en-têtes répétés
REPEATED_LINE_RATIO = 0.3            # ligne présente sur plus de 30 % des pages = en-tête ou pied de page

# Texte arabe sain, servant de vocabulaire de référence pour réparer les mots abîmés
# par la police de certains PDF (voir cleaning.repair_arabic_ligatures)
ARABIC_REFERENCE_FILE = "constitution_2011_ar.pdf"

# --- Embeddings (configuration A ; C = "BAAI/bge-m3") ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"
EMBEDDING_BATCH_SIZE = 32   # nombre de chunks calculés en même temps (plus petit = moins de mémoire)

# --- Recherche ---
TOP_K = 5               # nombre de chunks retrouvés par question
# Sous ce score, on considère qu'il n'y a pas de réponse dans le corpus.
# Mesuré en Phase 3 sur 16 questions : hors sujet <= 0,79 ; questions du corpus >= 0,84.
# Valeur provisoire, à recalibrer à l'évaluation (Phase 5) avec 30 questions.
SCORE_THRESHOLD = 0.82

# --- Base vectorielle ---
COLLECTION_NAME = "demarches_maroc"

# --- Génération (le nom du modèle sera fixé en Phase 4) ---
MAX_TOKENS = 600        # borne la longueur de la réponse du LLM (coût)
MAX_QUESTION_LENGTH = 500
