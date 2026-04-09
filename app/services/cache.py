import json
from functools import lru_cache
from hashlib import sha256

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.schemas.retrieval import RetrievalHit


class RetrievalCache:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: Redis | None = None

    def _get_client(self) -> Redis:
        if self._client is None:
            self._client = Redis.from_url(
                self.settings.redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
        return self._client

    def _key(self, query: str, top_k: int, rerank: bool) -> str:
        digest = sha256(f"{query}:{top_k}:{rerank}".encode()).hexdigest()
        return f"retrieval:{digest}"

    def get_search_hits(self, query: str, top_k: int, rerank: bool) -> list[RetrievalHit] | None:
        if not self.settings.enable_retrieval_cache:
            return None

        try:
            payload = self._get_client().get(self._key(query, top_k, rerank))
        except RedisError:
            return None

        if not payload:
            return None

        return [RetrievalHit.model_validate(item) for item in json.loads(payload)]

    def set_search_hits(
        self,
        query: str,
        top_k: int,
        rerank: bool,
        hits: list[RetrievalHit],
    ) -> None:
        if not self.settings.enable_retrieval_cache:
            return

        payload = json.dumps([hit.model_dump(mode="json") for hit in hits])
        ttl = self.settings.retrieval_cache_ttl_seconds

        try:
            self._get_client().set(self._key(query, top_k, rerank), payload, ex=ttl)
        except RedisError:
            return


@lru_cache
def get_retrieval_cache() -> RetrievalCache:
    return RetrievalCache()
