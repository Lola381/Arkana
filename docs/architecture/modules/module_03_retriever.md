# Module 3 — Retriever

## Purpose
The Retriever is a hybrid search engine responsible for executing queries against the embedded historical corpus. It fuses dense semantic vectors (retrieved from Qdrant) with sparse keyword queries (retrieved from PostgreSQL via BM25) to return highly accurate, rank-optimized historical context.

The module strictly orchestrates retrieval. It defers vector embedding to the Embedder (Module 2) and cross-encoder ranking to the Reranker (Module 4).

## Files
- `ai/ai/retrieval/rrf_fusion.py`
- `ai/ai/retrieval/test_retriever_fixes.py`

## Entry Points
- `HybridRetriever.retrieve(query, filters, top_k)` (async)
- `reciprocal_rank_fusion(dense_results, sparse_results, k, top_k)`

## Inputs
- `query`: `str` (Raw text query)
- `filters`: `Dict[str, Any]` (Optional metadata filters, specifically targeting `tribe_name`)
- `top_k`: `int` (Limits the final fused return array)

## Outputs
Schema:
```python
[
    {
        "chunk": Dict[str, Any], # Raw chunk metadata + text
        "rrf_score": float,      # Computed Reciprocal Rank Fusion score
        "chunk_id": str          # Unique Echolore document UUID
    }
]
```

## Current Architecture
The architecture is a true concurrent hybrid search engine. It relies heavily on an injected `Embedder` object to execute the database requests. Upon receiving a query, it simultaneously fires off a dense vector search and a sparse full-text search. The outputs are merged using the RRF algorithm `score = sum(1 / (k + rank))`, which mathematically resolves scoring disparities between fundamentally different database indexing mechanics (Cosine vs BM25).

## Final Implementation
1. `retrieve()` receives a query and optional tribal metadata constraints.
2. The synchronous, CPU-blocking dense search (`embedder.search_dense`) is offloaded to a background worker thread via `asyncio.to_thread()`.
3. The native asynchronous sparse search (`embedder.search_sparse`) is dispatched.
4. `asyncio.gather()` awaits both futures simultaneously, halting execution until both databases return payloads.
5. The resulting dense and sparse arrays are passed to `reciprocal_rank_fusion()`.
6. The algorithm normalizes and aggregates scores, sorts descending, slices at `top_k`, and returns the final payloads.

## Implemented Improvements
### 1. Removal of `retrieve_sync()`
- **Problem:** A redundant synchronous retrieval wrapper silently swallowed database exceptions (`except Exception: sparse_results = []`) and relied on a fatal `asyncio.run()` call.
- **Root Cause:** Artifact of legacy synchronous architecture migrating incompletely to asynchronous pipelines.
- **Implementation:** The `retrieve_sync()` wrapper was permanently deleted. All callers globally are forced to use the fully asynchronous `retrieve()` method.
- **Impact:** Eliminates fatal event loop crashes and prevents infrastructure observability failures caused by silent exception handling.

### 2. True Concurrent Dense + Sparse Retrieval
- **Problem:** Dense and sparse retrieval executed sequentially, inherently doubling the network/CPU latency of every search request.
- **Root Cause:** Synchronous execution of the ML embedding process (`search_dense`) blocked the event loop, preventing the asynchronous `search_sparse` network request from firing until the embedding pipeline finished.
- **Implementation:** Leveraged `asyncio.to_thread()` and `asyncio.gather()` to evaluate both search mechanics in parallel.
- **Impact:** Drastically reduces cumulative search latency while maintaining perfect mathematical parity for downstream modules.

## Important Design Decisions
- **Immutable RRF Mathematics:** The core mathematical formula `1 / (k + rank)` inside `reciprocal_rank_fusion()` remains untouched. The output schema was heavily fortified against modification to preserve compatibility with the Prompt Builder.
- **Async Concurrency Integrity:** Maintaining strict separation between CPU-bound threading and I/O bound async dispatch ensures the overarching event-loop (e.g., FastAPI) is never blocked during expensive ML inference.

## Assumptions
- The instantiated `Embedder` injected into the constructor natively exposes properly typed `search_dense` (sync) and `search_sparse` (async) methods.
- The default `rrf_k` parameter (`60`) provides an optimal normalization curve for this specific historical corpus.

## Known Limitations
- RRF is a naive ranking mechanism. It treats BM25 and Cosine similarity hits with equal weight regardless of query context (e.g. precise year matching). Deeper cross-encoder reranking is deferred to later pipeline stages.

## Integration Points
- **Upstream:** Invoked by TM3 / Prompt Builder pipelines.
- **Downstream:** Calls `Embedder.search_dense()` and `Embedder.search_sparse()` (Module 2). Feeds fused data directly into the `Reranker` (Module 4).

## Breaking Changes
- **API Migration:** Any legacy synchronous scripts must migrate to `await retrieve()`.
- **Database Stability:** Because this module strictly handles execution flow without mutating index structures, **NO PostgreSQL or Qdrant rebuild is required as a result of Module 3.** (However, a rebuild is already scheduled due to Module 1).

## Future Improvements
* **None.**
  * Ranking improvements (like cross-encoder semantic scoring) are intentionally delegated to the dedicated Reranker module (Module 4).

## AI Notes
- **Safe refactors:** Concurrent execution strategies or dependency injection mechanics.
- **Things that must never change:** The output dictionary schema and the structural RRF mathematical ranking logic.
- **Public interfaces:** `HybridRetriever.retrieve()` is the absolute and singular integration gateway.

---

## Deferred Improvement Tracker

| Improvement | Future Owner | Target Module | Status |
| ----------- | ------------ | ------------- | ------ |
| Wrap CPU-bound chunker in `ProcessPoolExecutor` | Indexing Bridge / API | Module 10 (ETL) | Pending |
| Move chunker `source_thresholds` to config | Indexing Bridge / Config | Module 10 (ETL) | Pending |
| Two-phase commit / rollback (Storage consistency) | Indexing Bridge | Module 10 (ETL) | Pending |
