"""Tests de l'appel au LLM (src/generator.py) : aucune requête réelle n'est envoyée."""

import io
import json
import urllib.error

import pytest

from src import generator


def fake_urlopen(outcomes):
    """Remplace urllib.request.urlopen : renvoie ou lève, dans l'ordre, ce que contient la liste."""
    calls = []

    def urlopen(request, timeout=None):
        calls.append({"url": request.full_url, "headers": dict(request.header_items()), "body": json.loads(request.data), "timeout": timeout})
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return io.BytesIO(json.dumps(outcome).encode("utf-8"))

    urlopen.calls = calls
    return urlopen


def reply(text):
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


def http_error(code):
    return urllib.error.HTTPError("https://exemple", code, "erreur", {}, io.BytesIO(b"{}"))


@pytest.fixture(autouse=True)
def configured(monkeypatch):
    monkeypatch.setattr(generator.config, "LLM_API_KEY", "cle-de-test")
    monkeypatch.setattr(generator.config, "LLM_MODELS", ["modele-a", "modele-b"])


def use(monkeypatch, outcomes):
    urlopen = fake_urlopen(outcomes)
    monkeypatch.setattr(generator.urllib.request, "urlopen", urlopen)
    return urlopen


def test_successful_call_returns_stripped_text_from_the_first_model(monkeypatch):
    urlopen = use(monkeypatch, [reply("  Réponse de test [1].  ")])
    assert generator.generate_answer("système", "question") == "Réponse de test [1]."
    assert len(urlopen.calls) == 1
    assert "modele-a" in urlopen.calls[0]["url"]


def test_api_key_is_sent_in_a_header_never_in_the_url(monkeypatch):
    urlopen = use(monkeypatch, [reply("ok")])
    generator.generate_answer("système", "question")
    assert "cle-de-test" not in urlopen.calls[0]["url"]
    assert urlopen.calls[0]["headers"]["X-goog-api-key"] == "cle-de-test"


def test_system_prompt_and_question_are_sent(monkeypatch):
    urlopen = use(monkeypatch, [reply("ok")])
    generator.generate_answer("RÈGLES", "QUESTION")
    body = urlopen.calls[0]["body"]
    assert body["systemInstruction"]["parts"][0]["text"] == "RÈGLES"
    assert body["contents"][0]["parts"][0]["text"] == "QUESTION"


def test_quota_exhausted_model_falls_back_to_the_next_one(monkeypatch):
    urlopen = use(monkeypatch, [http_error(429), reply("Réponse du second modèle")])
    assert generator.generate_answer("système", "question") == "Réponse du second modèle"
    assert "modele-a" in urlopen.calls[0]["url"] and "modele-b" in urlopen.calls[1]["url"]


def test_timeout_falls_back_to_the_next_model(monkeypatch):
    use(monkeypatch, [TimeoutError("trop lent"), reply("ok")])
    assert generator.generate_answer("système", "question") == "ok"


def test_empty_answer_falls_back_to_the_next_model(monkeypatch):
    use(monkeypatch, [reply("   "), reply("ok")])
    assert generator.generate_answer("système", "question") == "ok"


def test_all_models_failing_raises_a_readable_error(monkeypatch):
    use(monkeypatch, [http_error(429), http_error(503)])
    with pytest.raises(generator.LLMUnavailableError):
        generator.generate_answer("système", "question")


def test_refused_api_key_stops_immediately(monkeypatch):
    urlopen = use(monkeypatch, [http_error(403), reply("ne doit pas être appelé")])
    with pytest.raises(generator.LLMUnavailableError):
        generator.generate_answer("système", "question")
    assert len(urlopen.calls) == 1


def test_thinking_parts_are_ignored(monkeypatch):
    data = {"candidates": [{"content": {"parts": [{"text": "réflexion interne", "thought": True}, {"text": "Réponse finale"}]}}]}
    use(monkeypatch, [data])
    assert generator.generate_answer("système", "question") == "Réponse finale"


def test_quick_call_uses_a_short_timeout_and_falls_back(monkeypatch):
    monkeypatch.setattr(generator.config, "QUICK_CALL_BUDGET_SECONDS", 8)
    urlopen = use(monkeypatch, [TimeoutError("trop lent"), reply("sous-question")])
    assert generator.generate_quick("système", "question") == "sous-question"
    assert all(call["timeout"] <= 8 for call in urlopen.calls)  # jamais le délai de 20 s d'une vraie réponse


def test_quick_call_gives_up_when_its_time_budget_is_spent(monkeypatch):
    monkeypatch.setattr(generator.config, "QUICK_CALL_BUDGET_SECONDS", 0)
    urlopen = use(monkeypatch, [reply("ne doit pas être appelé")])
    with pytest.raises(generator.LLMUnavailableError):
        generator.generate_quick("système", "question")
    assert urlopen.calls == []


def test_missing_api_key_raises_an_error(monkeypatch):
    monkeypatch.setattr(generator.config, "LLM_API_KEY", "")
    with pytest.raises(generator.LLMUnavailableError):
        generator.generate_answer("système", "question")
