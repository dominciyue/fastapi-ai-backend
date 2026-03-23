from app.core.config import get_settings


def chunk_text(text: str) -> list[str]:
    settings = get_settings()
    normalized = " ".join(text.split())
    if not normalized:
        return []

    step = max(settings.chunk_size - settings.chunk_overlap, 1)
    chunks: list[str] = []
    for start in range(0, len(normalized), step):
        chunk = normalized[start : start + settings.chunk_size]
        if chunk:
            chunks.append(chunk)
    return chunks
