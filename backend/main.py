"""API FastAPI de l'assistant (Phase 6, exigences FR-8 et section 7 du PRD).

Deux routes :
    GET  /health  vérifie que l'API tourne et que l'index est chargé
    POST /chat    répond à une question, avec ses sources

Lancement (depuis le dossier backend) :  uvicorn main:app --reload
Page de test automatique :               http://localhost:8000/docs
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from schemas import ChatRequest, ChatResponse, HealthResponse
from src import config, embeddings, generator, rag, retriever, vectorstore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("rag-api")

# Limite le nombre de requêtes par adresse IP (protège le quota gratuit de l'API du LLM)
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Au démarrage : charge l'index et le modèle UNE SEULE FOIS, pas à chaque question."""
    app.state.collection = vectorstore.get_collection()
    embeddings.get_model()
    logger.info("Index chargé : %d chunks", app.state.collection.count())
    yield


app = FastAPI(
    title="Assistant civique marocain",
    description="Répond en français et en arabe aux questions sur la Constitution, les élections et les institutions, avec ses sources.",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS : seules les adresses du frontend listées dans ALLOWED_ORIGINS peuvent appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


def get_collection(request: Request):
    """Fournit la collection ChromaDB chargée au démarrage (remplaçable dans les tests)."""
    return request.app.state.collection


@app.get("/health", response_model=HealthResponse)
def health(collection=Depends(get_collection)) -> dict:
    """Vérifie que l'API tourne et que l'index contient des chunks."""
    return {"status": "ok", "chunks": collection.count()}


@app.post("/chat", response_model=ChatResponse)
@limiter.limit(config.RATE_LIMIT)
def chat(request: Request, payload: ChatRequest, collection=Depends(get_collection)) -> dict:
    """Répond à une question. Une question vide ou trop longue renvoie une erreur 422."""
    started = time.time()

    def retrieve_with_loaded_index(question: str, theme: str | None = None) -> list[dict]:
        return retriever.retrieve(question, theme=theme, collection=collection)

    try:
        result = rag.answer_question(payload.question, theme=payload.theme, retrieve_fn=retrieve_with_loaded_index)
    except generator.LLMUnavailableError as error:
        logger.error("LLM indisponible : %s", error)
        # Message lisible pour l'utilisateur : jamais de trace technique
        raise HTTPException(
            status_code=503,
            detail="Le service de réponse est momentanément indisponible. Réessayez dans quelques instants.",
        ) from error

    # Journal : durée, nombre de sources, found. On n'écrit JAMAIS le texte de la question (NFR-7).
    logger.info(
        "chat langue=%s found=%s sources=%d duree=%.2fs",
        result["language"], result["found"], len(result["sources"]), time.time() - started,
    )
    return result
