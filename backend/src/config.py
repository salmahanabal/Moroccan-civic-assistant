"""Paramètres centralisés du projet (NFR-4).

Tous les réglages qu'on veut comparer à l'évaluation sont ici,
et nulle part ailleurs dans le code.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# --- Chemins (calculés à partir de l'emplacement de ce fichier) ---
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent

# Charge les variables secrètes du fichier backend/.env (jamais publié sur Git)
load_dotenv(BACKEND_DIR / ".env")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# --- Variantes de configuration (comparaison A / B / C, Phase 5) ---
# Par défaut (variable RAG_VARIANT absente) c'est la configuration A. Pour tester une autre
# configuration SANS écraser l'index actuel, on lance les commandes avec des variables
# d'environnement, par exemple :  RAG_VARIANT=B RAG_CHUNK_SIZE=1200 RAG_CHUNK_OVERLAP=200
# Chaque variante écrit dans ses propres fichiers (chunks_B.jsonl, chroma_db_B, results_B.csv).
VARIANT = os.getenv("RAG_VARIANT", "")
FILE_SUFFIX = f"_{VARIANT}" if VARIANT else ""

RAW_DIR = ROOT_DIR / "data" / "raw"                      # PDF du corpus
PROCESSED_DIR = ROOT_DIR / "data" / "processed"          # résultats intermédiaires
SOURCES_CSV = ROOT_DIR / "data" / "sources.csv"          # registre des documents
CHUNKS_FILE = PROCESSED_DIR / f"chunks{FILE_SUFFIX}.jsonl"   # chunks après découpage
CHROMA_DIR = BACKEND_DIR / f"chroma_db{FILE_SUFFIX}"         # index vectoriel persistant
EVAL_DIR = BACKEND_DIR / "evaluation"                    # questions et résultats

# --- Découpage en chunks (configuration A : 800 / 150 ; B : 1200 / 200) ---
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "800"))        # taille d'un chunk, en caractères
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))  # chevauchement entre deux chunks consécutifs
MIN_CHUNK_CHARS = 50    # un chunk plus court est ignoré (souvent un titre isolé)

# --- Nettoyage du texte ---
MIN_PAGES_FOR_HEADER_DETECTION = 5   # en dessous, on ne cherche pas d'en-têtes répétés
REPEATED_LINE_RATIO = 0.3            # ligne présente sur plus de 30 % des pages = en-tête ou pied de page

# Texte arabe sain, servant de vocabulaire de référence pour réparer les mots abîmés
# par la police de certains PDF (voir cleaning.repair_arabic_ligatures)
ARABIC_REFERENCE_FILE = "constitution_2011_ar.pdf"

# --- Embeddings ---
# Comparaison faite en Phase 5 sur 17 documents (hit rate@5) : e5-base 72 %, bge-m3 84 %.
# bge-m3 est donc le modèle retenu. (Pour retester e5 : RAG_EMBEDDING_MODEL=intfloat/multilingual-e5-base)
EMBEDDING_MODEL = os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-m3")
EMBEDDING_BATCH_SIZE = 32   # nombre de chunks calculés en même temps (plus petit = moins de mémoire)

# --- Recherche ---
TOP_K = 5               # nombre de chunks retrouvés par question
# Places réservées (sur TOP_K) aux meilleurs chunks de l'AUTRE langue que la question.
# 0 = recherche classique. Voir retriever.retrieve pour l'explication.
# Mesuré sur les 35 documents avec bge-m3 (hit rate@5) : 0 place = 76 %, 2 places = 84 %, 3 places = 84 %.
OTHER_LANGUAGE_SLOTS = int(os.getenv("RAG_OTHER_SLOTS", "2"))
# Sous ce score, on considère qu'il n'y a pas de réponse dans le corpus.
# Échelle de bge-m3 sur 35 documents : meilleur score des questions du corpus >= 0,60 ;
# questions hors sujet simples entre 0,37 et 0,50 (une question proche, comme « passeport », monte à 0,58).
# Le seuil reste volontairement bas (peu de refus à tort) : c'est le LLM qui refuse les cas limites.
SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.50"))  # chaque modèle a sa propre échelle de scores

# --- Base vectorielle ---
COLLECTION_NAME = "civic_maroc"

# --- Génération de la réponse (LLM) ---
LLM_PROVIDER = "gemini"
# Modèles essayés dans l'ordre : si l'un est saturé ou a épuisé son quota du jour (le palier gratuit
# est limité PAR MODÈLE), on passe au suivant. Mesuré en Phase 4 : ~2 s pour les deux premiers.
LLM_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"]
LLM_THINKING_LEVEL = "low"       # le modèle « réfléchit » peu : plus rapide, moins de tokens
# Borne la longueur de la réponse (coût). La réflexion interne compte dans cette limite :
# une valeur trop basse coupe la réponse en plein milieu d'une phrase.
MAX_TOKENS = 1500
LLM_TIMEOUT_SECONDS = 20         # au-delà, on abandonne ce modèle et on passe au suivant
MAX_QUESTION_LENGTH = 500
EXCERPT_CHARS = 200              # longueur de l'extrait de chaque source renvoyé à l'utilisateur

# --- API ---
RATE_LIMIT = "10/minute"         # par adresse IP : protège le quota gratuit contre les abus
# Adresses du frontend autorisées par le CORS (séparées par des virgules dans .env)
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]
