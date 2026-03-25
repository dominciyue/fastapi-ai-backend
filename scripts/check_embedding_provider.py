import asyncio
import json

from app.core.config import get_settings
from app.services.llm_client import OpenAICompatibleClient


async def main() -> None:
    settings = get_settings()
    client = OpenAICompatibleClient()
    is_mock = client._use_mock_embedding_mode()
    embeddings = await client.embed(["embedding health check"])
    vector = embeddings[0]

    print(
        json.dumps(
            {
                "mode": "mock" if is_mock else "real",
                "embedding_base_url": client._embedding_base_url,
                "embedding_model": settings.embedding_model,
                "configured_dimension": settings.embedding_dimension,
                "returned_dimension": len(vector),
                "sample": vector[:5],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
