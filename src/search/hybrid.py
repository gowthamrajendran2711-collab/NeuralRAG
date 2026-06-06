"""Hybrid BM25 + Dense Search with Reciprocal Rank Fusion"""
from qdrant_client import QdrantClient

class HybridSearchEngine:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=qdrant_url, timeout=300)
        self.bm25_weight = 0.3
        self.dense_weight = 0.7

    async def search(self, query: str, collection: str, top_k: int = 10, mode: str = "hybrid") -> list:
        if mode == "hybrid":
            return await self._hybrid_search(query, collection, top_k)
        elif mode == "dense":
            return await self._dense_search(query, collection, top_k)
        return await self._sparse_search(query, collection, top_k)

    async def _hybrid_search(self, query, collection, top_k):
        dense = await self._dense_search(query, collection, top_k * 2)
        sparse = await self._sparse_search(query, collection, top_k * 2)
        return self._rrf_combine(dense, sparse, top_k)

    def _rrf_combine(self, dense, sparse, top_k, k=60):
        """Reciprocal Rank Fusion reranking."""
        scores = {}
        for rank, doc in enumerate(dense):
            scores[doc["id"]] = scores.get(doc["id"], 0) + self.dense_weight / (k + rank + 1)
        for rank, doc in enumerate(sparse):
            scores[doc["id"]] = scores.get(doc["id"], 0) + self.bm25_weight / (k + rank + 1)
        all_docs = {d["id"]: d for d in dense + sparse}
        ranked = sorted(scores, key=scores.get, reverse=True)[:top_k]
        return [all_docs[i] for i in ranked if i in all_docs]

    async def _dense_search(self, query, collection, top_k): return []
    async def _sparse_search(self, query, collection, top_k): return []
