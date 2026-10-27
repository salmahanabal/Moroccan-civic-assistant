"""Forme des données échangées avec l'API (modèles Pydantic).

Pydantic vérifie automatiquement les données reçues : une question vide ou trop
longue est refusée avec une erreur 422 claire, sans écrire de code de contrôle.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from src import config


class ChatRequest(BaseModel):
    """Ce que l'interface envoie : la question, et éventuellement un thème."""

    question: str = Field(description="La question de l'utilisateur (1 à 500 caractères).")
    theme: str | None = Field(default=None, description="Thème pour limiter la recherche (facultatif).")

    @field_validator("question")
    @classmethod
    def question_must_be_valid(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("La question ne peut pas être vide.")
        if len(value) > config.MAX_QUESTION_LENGTH:
            raise ValueError(f"La question ne doit pas dépasser {config.MAX_QUESTION_LENGTH} caractères.")
        return value


class Source(BaseModel):
    """Un passage de document officiel utilisé pour répondre."""

    id: int
    file: str
    page: int
    excerpt: str
    # Position (dans excerpt) de la phrase qui répond le mieux, à surligner ; None si aucune ne se détache
    highlight_start: int | None = None
    highlight_end: int | None = None
    url: str
    score: float


class ChatResponse(BaseModel):
    """Ce que l'API renvoie : la réponse, sa langue, et ses sources."""

    answer: str
    language: Literal["fr", "ar"]
    found: bool
    sources: list[Source]


class HealthResponse(BaseModel):
    """Réponse de /health : l'API tourne et l'index contient des chunks."""

    status: str
    chunks: int
