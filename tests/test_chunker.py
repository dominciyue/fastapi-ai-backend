from app.services.chunker import chunk_text


def test_chunk_text_splits_long_text() -> None:
    text = "A" * 2500
    chunks = chunk_text(text)
    assert len(chunks) >= 2
    assert all(chunks)
