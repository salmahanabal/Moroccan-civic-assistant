"""Tests du stockage vectoriel et de la récupération (src/vectorstore.py et src/retriever.py).

On utilise de petits vecteurs à 3 nombres inventés : pas besoin du vrai modèle.
Les trois chunks pointent chacun dans une direction différente (x, y ou z).
"""

import pytest

from src import embeddings, retriever, vectorstore

CHUNKS = [
    {"chunk_id": "a_0000", "file": "a.pdf", "page": 1, "theme": "elections", "language": "fr", "url": "u1", "text": "Texte sur le vote."},
    {"chunk_id": "b_0000", "file": "b.pdf", "page": 2, "theme": "partis_politiques", "language": "fr", "url": "u2", "text": "Texte sur les partis."},
    {"chunk_id": "c_0000", "file": "c.pdf", "page": 3, "theme": "constitution", "language": "ar", "url": "u3", "text": "نص عن الدستور."},
]
VECTORS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]


@pytest.fixture
def collection(tmp_path):
    client = vectorstore.get_client(tmp_path / "chroma")
    collection = vectorstore.get_collection(client, reset=True)
    vectorstore.add_chunks(collection, CHUNKS, VECTORS)
    return collection


def test_collection_counts_the_added_chunks(collection):
    assert collection.count() == 3


def test_search_returns_closest_chunk_first_with_metadata(collection):
    results = vectorstore.search(collection, [0.9, 0.1, 0.0], top_k=3)
    assert results[0]["file"] == "a.pdf"
    assert results[0]["page"] == 1
    assert results[0]["theme"] == "elections"
    assert results[0]["url"] == "u1"
    assert results[0]["text"] == "Texte sur le vote."
    assert results[0]["score"] > results[1]["score"] > results[2]["score"]


def test_identical_vector_has_a_score_close_to_one(collection):
    results = vectorstore.search(collection, [0.0, 1.0, 0.0], top_k=1)
    assert results[0]["file"] == "b.pdf"
    assert results[0]["score"] == pytest.approx(1.0, abs=1e-4)


def test_search_can_be_limited_to_a_theme(collection):
    results = vectorstore.search(collection, [1.0, 0.0, 0.0], top_k=3, theme="constitution")
    assert [result["file"] for result in results] == ["c.pdf"]


def test_search_can_be_limited_to_a_language(collection):
    results = vectorstore.search(collection, [1.0, 0.0, 0.0], top_k=3, language="ar")
    assert [result["file"] for result in results] == ["c.pdf"]


def test_search_can_combine_theme_and_language_filters(collection):
    assert [r["file"] for r in vectorstore.search(collection, [0, 0, 1.0], top_k=3, theme="constitution", language="ar")] == ["c.pdf"]
    assert vectorstore.search(collection, [0, 0, 1.0], top_k=3, theme="constitution", language="fr") == []


def test_balanced_retrieval_reserves_slots_for_the_other_language(tmp_path):
    # 5 chunks français très proches de la question, 3 chunks arabes un peu moins proches
    chunks, vectors = [], []
    for number in range(5):
        chunks.append({"chunk_id": f"fr_{number}", "file": f"fr_{number}.pdf", "page": 1, "theme": "t", "language": "fr", "url": "u", "text": "fr"})
        vectors.append([1.0, 0.01 * number, 0.0])
    for number in range(3):
        chunks.append({"chunk_id": f"ar_{number}", "file": f"ar_{number}.pdf", "page": 1, "theme": "t", "language": "ar", "url": "u", "text": "ar"})
        vectors.append([0.6, 0.01 * number, 0.8])
    collection = vectorstore.get_collection(vectorstore.get_client(tmp_path / "chroma"), reset=True)
    vectorstore.add_chunks(collection, chunks, vectors)

    def ask(slots):
        return retriever.retrieve("Une question en français ?", top_k=5, collection=collection,
                                  embed_fn=lambda q: [1.0, 0.0, 0.0], other_language_slots=slots)

    classic = ask(0)
    assert [r["language"] for r in classic] == ["fr"] * 5  # sans réglage : seulement du français
    balanced = ask(2)
    assert sorted(r["language"] for r in balanced) == ["ar", "ar", "fr", "fr", "fr"]
    assert [r["score"] for r in balanced] == sorted((r["score"] for r in balanced), reverse=True)


def test_reset_gives_an_empty_collection(tmp_path):
    client = vectorstore.get_client(tmp_path / "chroma")
    first = vectorstore.get_collection(client, reset=True)
    vectorstore.add_chunks(first, CHUNKS, VECTORS)
    second = vectorstore.get_collection(client, reset=True)
    assert second.count() == 0


def test_retrieve_uses_the_given_embedding_function(collection):
    results = retriever.retrieve("une question", top_k=2, collection=collection, embed_fn=lambda question: [0.0, 0.0, 1.0])
    assert results[0]["file"] == "c.pdf"
    assert len(results) == 2


def test_has_answer_depends_on_the_best_score():
    assert retriever.has_answer([{"score": 0.82}, {"score": 0.4}], threshold=0.7) is True
    assert retriever.has_answer([{"score": 0.55}], threshold=0.7) is False
    assert retriever.has_answer([], threshold=0.7) is False


def test_e5_models_get_query_and_passage_prefixes():
    assert embeddings.get_prefix("query", "intfloat/multilingual-e5-base") == "query: "
    assert embeddings.get_prefix("passage", "intfloat/multilingual-e5-base") == "passage: "
    assert embeddings.get_prefix("query", "BAAI/bge-m3") == ""
