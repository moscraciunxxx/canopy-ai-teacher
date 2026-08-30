from src.retrieve import LexicalRetriever, chunk_markdown


def test_chunking_preserves_heading_context() -> None:
    chunks = chunk_markdown(
        "# Solving equations\nSubtract the same number from both sides.\n\n"
        "## Worked example\n2x + 3 = 11."
    )

    assert chunks
    assert any("Solving equations" in chunk["section"] for chunk in chunks)
    assert any("2x + 3 = 11" in chunk["text"] for chunk in chunks)


def test_lexical_retriever_ranks_relevant_chunk() -> None:
    chunks = [
        {"chunk_id": "a", "section": "Inverse operations", "text": "Subtract 3 from both sides."},
        {"chunk_id": "b", "section": "Vocabulary", "text": "A variable represents an unknown value."},
    ]
    retriever = LexicalRetriever(chunks)
    results = retriever.search("subtract both sides", top_k=1)

    assert results[0]["chunk_id"] == "a"
