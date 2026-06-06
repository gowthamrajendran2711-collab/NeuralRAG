"""Tests for HybridSearchEngine"""
import pytest
from unittest.mock import AsyncMock, patch
from src.search.hybrid import HybridSearchEngine

@pytest.fixture
def engine():
    with patch("src.search.hybrid.QdrantClient"):
        return HybridSearchEngine()

def test_rrf_combine_basic(engine):
    dense = [{"id": "a", "score": 0.9}, {"id": "b", "score": 0.8}]
    sparse = [{"id": "b", "score": 0.7}, {"id": "c", "score": 0.6}]
    result = engine._rrf_combine(dense, sparse, top_k=3)
    assert len(result) <= 3
    # doc "b" appears in both lists, should rank higher
    ids = [r["id"] for r in result]
    assert "b" in ids

def test_rrf_combine_empty(engine):
    result = engine._rrf_combine([], [], top_k=5)
    assert result == []

@pytest.mark.asyncio
async def test_search_mode_dispatch(engine):
    engine._dense_search = AsyncMock(return_value=[{"id": "x"}])
    engine._sparse_search = AsyncMock(return_value=[])
    await engine.search("test query", "my_collection", mode="dense")
    engine._dense_search.assert_called_once()
    engine._sparse_search.assert_not_called()
