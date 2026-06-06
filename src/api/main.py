"""NeuralRAG FastAPI Gateway"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Literal
import time, structlog
from prometheus_client import Counter, Histogram, make_asgi_app

logger = structlog.get_logger(__name__)
app = FastAPI(title="NeuralRAG API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/metrics", make_asgi_app())

QUERY_LATENCY = Histogram("neuralrag_query_latency_seconds", "Query latency", ["search_mode"])
QUERY_COUNTER = Counter("neuralrag_queries_total", "Total queries", ["collection"])
INGEST_COUNTER = Counter("neuralrag_ingestions_total", "Ingestion counter", ["status"])

class IngestRequest(BaseModel):
    url: str
    collection: str
    chunk_strategy: Literal["semantic","recursive","sliding_window"] = "semantic"
    metadata: Optional[dict] = None

class QueryRequest(BaseModel):
    question: str
    collection: str
    top_k: int = 5
    search_mode: Literal["hybrid","dense","sparse"] = "hybrid"
    use_cache: bool = True

class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]
    latency_ms: float
    cache_hit: bool
    search_mode: str

@app.post("/ingest", status_code=202)
async def ingest(req: IngestRequest, bg: BackgroundTasks):
    from src.ingestion.worker import ingest_document_task
    task = ingest_document_task.delay(req.url, req.collection, {}, req.metadata)
    INGEST_COUNTER.labels(status="queued").inc()
    return {"task_id": task.id, "status": "queued"}

@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    from src.search.hybrid import HybridSearchEngine
    from src.cache.semantic_cache import SemanticCache
    start = time.time()
    QUERY_COUNTER.labels(collection=req.collection).inc()
    cache = SemanticCache()
    cached = await cache.get(req.question)
    if req.use_cache and cached:
        latency_ms = (time.time()-start)*1000
        QUERY_LATENCY.labels(search_mode="cache").observe(latency_ms/1000)
        return QueryResponse(cache_hit=True, latency_ms=latency_ms, **cached)
    engine = HybridSearchEngine()
    results = await engine.search(req.question, req.collection, req.top_k, req.search_mode)
    answer = await _generate(req.question, results)
    latency_ms = (time.time()-start)*1000
    QUERY_LATENCY.labels(search_mode=req.search_mode).observe(latency_ms/1000)
    resp = {"answer": answer, "sources": results, "search_mode": req.search_mode}
    await cache.set(req.question, resp)
    return QueryResponse(cache_hit=False, latency_ms=latency_ms, **resp)

@app.get("/health")
async def health(): return {"status":"ok","version":"1.0.0"}

async def _generate(question: str, contexts: list) -> str:
    from openai import AsyncOpenAI
    client = AsyncOpenAI()
    ctx = "\n\n".join([c.get("payload",{}).get("text","") for c in contexts])
    r = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role":"system","content":"Answer based only on the provided context. Be concise."},
            {"role":"user","content":f"Context:\n{ctx}\n\nQuestion: {question}"}
        ], temperature=0)
    return r.choices[0].message.content
