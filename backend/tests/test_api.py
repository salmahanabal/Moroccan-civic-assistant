"""Tests de l'API (main.py) : /health et /chat.

La recherche et le LLM sont remplacés par de fausses fonctions, et l'index est
une fausse collection : aucun modèle n'est chargé, aucune clé d'API n'est utilisée.
"""

import pytest
from fastapi.testclient import TestClient

import main
from src import generator

FAKE_RESULT = {
    "answer": "Le vote est un droit personnel et un devoir national [1].",
    "language": "fr",
    "found": True,
    "sources": [
        {"id": 1, "file": "constitution_2011_fr.pdf", "page": 10, "excerpt": "Sont électeurs...", "url": "https://exemple.ma/c", "score": 0.88}
    ],
    "duration_seconds": 1.2,
}


class FakeCollection:
    def count(self):
        return 2049


@pytest.fixture
def client():
    # Sans « with », le démarrage (chargement du vrai modèle) n'est pas exécuté
    main.app.dependency_overrides[main.get_collection] = lambda: FakeCollection()
    main.limiter.reset()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_health_returns_ok_and_chunk_count(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "chunks": 2049}


def test_chat_with_valid_question_returns_answer_and_sources(client, monkeypatch):
    monkeypatch.setattr(main.rag, "answer_question", lambda question, theme=None, retrieve_fn=None: FAKE_RESULT)
    response = client.post("/chat", json={"question": "Qui peut voter ?"})
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["language"] == "fr"
    assert body["sources"][0]["file"] == "constitution_2011_fr.pdf"
    assert body["sources"][0]["page"] == 10
    assert "duration_seconds" not in body  # champ interne, non exposé


def test_chat_with_empty_question_returns_422(client):
    response = client.post("/chat", json={"question": "   "})
    assert response.status_code == 422
    assert "vide" in response.text


def test_chat_with_too_long_question_returns_422(client):
    response = client.post("/chat", json={"question": "a" * 501})
    assert response.status_code == 422
    assert "500" in response.text


def test_chat_without_question_field_returns_422(client):
    assert client.post("/chat", json={}).status_code == 422


def test_chat_returns_503_with_readable_message_when_llm_is_down(client, monkeypatch):
    def broken(question, theme=None, retrieve_fn=None):
        raise generator.LLMUnavailableError("secret technique : quota")

    monkeypatch.setattr(main.rag, "answer_question", broken)
    response = client.post("/chat", json={"question": "Une question ?"})
    assert response.status_code == 503
    assert "momentanément indisponible" in response.json()["detail"]
    assert "quota" not in response.text  # aucune trace technique pour l'utilisateur


def test_chat_is_rate_limited_per_ip(client, monkeypatch):
    monkeypatch.setattr(main.rag, "answer_question", lambda question, theme=None, retrieve_fn=None: FAKE_RESULT)
    statuses = [client.post("/chat", json={"question": "Question ?"}).status_code for _ in range(12)]
    assert statuses[:10] == [200] * 10
    assert 429 in statuses[10:]


def test_cors_allows_the_frontend_origin_only(client):
    allowed = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
    refused = client.get("/health", headers={"Origin": "http://site-inconnu.example"})
    assert "access-control-allow-origin" not in refused.headers
