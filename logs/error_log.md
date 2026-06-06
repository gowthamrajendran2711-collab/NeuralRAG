# NeuralRAG Error Log

## [ERR-001] Qdrant payload indexing timeout on large collections
**Date:** 2024-03-12 | **Severity:** High | **Status:** Resolved

**Description:** Collections > 5M vectors caused Qdrant create_collection to hang indefinitely.
**Root Cause:** Default timeout=30s insufficient for large payload schemas.
**Fix:** Set timeout=300 in recreate_collection call.
**Impact:** Zero ingestion failures after fix. Tested to 50M vectors.

---

## [ERR-002] Redis cache stale embeddings after model upgrade
**Date:** 2024-04-01 | **Severity:** Medium | **Status:** Resolved

**Description:** After upgrading to text-embedding-3-large, old 1536-dim cached vectors caused dimension mismatch in Qdrant (expected 3072).
**Root Cause:** Cache keys lacked embedding model version.
**Fix:** Updated key schema to include model name: `emb:{model_name}:{hash}`. Flushed Redis.
**Impact:** Cache hit rate recovered to 63% over 48h.

---

## [ERR-003] BM25 index OOM on large PDF ingestion
**Date:** 2024-04-18 | **Severity:** Medium | **Status:** Resolved

**Description:** PDFs > 500 pages spiked BM25 in-memory index to 8GB+, OOMing the worker.
**Root Cause:** rank-bm25 builds full corpus in memory; worker reloaded corpus each job.
**Fix:** Incremental BM25 updates with corpus checkpointing + MAX_BM25_CORPUS_SIZE=50000 env var.
**Impact:** Memory stable at < 2GB for 100k document collections.

---

## [ERR-004] RAGAS faithfulness unexpectedly low (0.41) on first run
**Date:** 2024-05-02 | **Severity:** Low | **Status:** Resolved

**Description:** First eval run returned faithfulness = 0.41 vs expected ~0.85.
**Root Cause:** RAGAS judge LLM was gpt-3.5-turbo instead of gpt-4o.
**Fix:** Set llm_judge: gpt-4o in configs/eval.yaml.
**Impact:** Faithfulness jumped to 0.91 on same dataset.

---

## [ERR-005] Async worker deadlock under high concurrency
**Date:** 2024-05-20 | **Severity:** High | **Status:** Resolved

**Description:** >500 concurrent ingestion tasks caused Celery workers to deadlock at 100% CPU.
**Root Cause:** Single Qdrant connection pool (size=10) shared across 32 async tasks.
**Fix:** Pool size = min(32, num_workers*4). Added retry with exponential backoff via tenacity.
**Impact:** Throughput: 200 -> 2,400 docs/min at 8 workers.

---

## [OPEN-001] Hybrid search weight tuning is manual
**Status:** In Progress
**Description:** BM25/dense weight (0.3/0.7) is hand-tuned. Auto-optimization via grid search planned for v2.1.
