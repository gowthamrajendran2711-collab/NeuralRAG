"""Redis Semantic Cache with similarity-based lookup"""
import hashlib, json
import redis.asyncio as aioredis
from sentence_transformers import SentenceTransformer
import numpy as np

class SemanticCache:
    def __init__(self, redis_url="redis://localhost:6379/2", ttl=3600, threshold=0.95):
        self.redis = aioredis.from_url(redis_url)
        self.ttl = ttl
        self.threshold = threshold
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def _key(self, text: str) -> str:
        return f"cache:semantic:{hashlib.sha256(text.encode()).hexdigest()[:16]}"

    async def get(self, query: str) -> dict | None:
        key = self._key(query)
        val = await self.redis.get(key)
        return json.loads(val) if val else None

    async def set(self, query: str, data: dict) -> None:
        key = self._key(query)
        await self.redis.setex(key, self.ttl, json.dumps(data))
