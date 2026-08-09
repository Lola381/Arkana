# Module 4 — Reranker (Cross-Encoder)

## Purpose
The Reranker evaluates and strictly scores query-chunk candidate pairs retrieved by the hybrid search engine (Module 3). By utilizing a heavy semantic cross-encoder model (`ms-marco-MiniLM-L-6-v2`), it evaluates the query and chunk simultaneously to maximize contextual relevance, discards low-quality historical matches, and returns a tightly truncated, highly accurate list for context augmentation.

## Files
- `ai/ai/reranking/cross_encoder.py`
- `ai/ai/reranking/test_reranker_fixes.py`

## Entry Points
- `CrossEncoderReranker.rerank(query, candidates, top_n)` (async)

## Inputs
- `query`: `str` (Raw text query)
- `candidates`: `List[Dict[str, Any]]` (List of dictionaries output from the Retriever, specifically containing a `"chunk"` dictionary which contains the `"text"`)
- `top_n`: `int` (Optional override for maximum returned chunks)

## Outputs
Schema:
```python
[
    {
        "chunk": Dict[str, Any], # Raw chunk metadata + text
        "rrf_score": float,      # Computed Reciprocal Rank Fusion score (carried over)
        "chunk_id": str,         # Unique Echolore document UUID (carried over)
        "rerank_score": float    # Appended cross-encoder confidence score
    }
]
```

## Current Architecture
The Reranker loads a HuggingFace Cross-Encoder model synchronously into memory upon instantiation. Upon receiving a list of candidate dictionaries from the Retriever, it constructs string pairs and executes heavy CPU/GPU-bound tensor predictions. It strictly filters out candidates that fail to meet the absolute relevance floor threshold and aggressively truncates the final sorted array to prevent overwhelming the downstream LLM context window.

## Final Implementation
1. `rerank()` accepts the query and an array of retriever candidates.
2. If candidates exist, it unpacks them into `(query, chunk_text)` tuples.
3. It offloads `self.reranker.predict(...)` to a background worker thread via `asyncio.to_thread()` to prevent blocking the async event loop.
4. Instead of mutating the original inputs, it deep-copies the candidate dictionaries and attaches the new `rerank_score` float natively.
5. Candidates are sorted descending by this new cross-encoder score.
6. A hard filter strips any candidate with a `rerank_score` below `-5.0`.
7. The sorted array is truncated to `top_n` (default 4) and returned.

## Implemented Improvements
### 1. Asynchronous Thread Offloading
- **Problem:** `self.reranker.predict()` is purely CPU/GPU-bound. Executing it synchronously froze the encompassing event loop (FastAPI/TM3) for hundreds of milliseconds per query, destroying concurrent request handling.
- **Root Cause:** Direct synchronous invocation inside an async pipeline.
- **Implementation:** Wrapped the prediction engine in `await asyncio.to_thread(...)`. Updated all upstream callers (`pipeline.py`, `faithfulness_judge.py`) to safely `await self.reranker.rerank(...)`.
- **Impact:** Complete restoration of ASGI server concurrency with zero latency penalties to neighboring web traffic.

### 2. Deletion of `rerank_with_details()`
- **Problem:** A redundant diagnostic method possessed zero internal callers but contained a fatal serialization bug (`np.mean` returned an un-serializable `numpy.float64` scalar).
- **Root Cause:** Abandoned diagnostic code.
- **Implementation:** Permanently removed the method.
- **Impact:** Cleared technical debt and eliminated a hazardous serialization bomb.

### 3. Absolute State Immutability
- **Problem:** The reranker historically attached the `rerank_score` directly to the memory addresses of the dictionaries passed to it from the Retriever. 
- **Root Cause:** Standard Python mutable list logic.
- **Implementation:** Upgraded the assignment block to generate clean `.copy()` dict clones before attaching new data.
- **Impact:** Ensures structural integrity. If upstream modules or caches retain pointers to the Retriever output, they will not experience silent data mutations.

## Important Design Decisions
- **Immutable Mathematics & Model Selection:** The specific string `"cross-encoder/ms-marco-MiniLM-L-6-v2"` and the cutoff threshold of `-5.0` remain completely unchanged. Modifying these directly impacts contextual accuracy.
- **Truncation Philosophy:** The module intentionally bottlenecks the data flow (`top_n=4`) to prevent the LLM context window from being flooded by distractor chunks.

## Assumptions
- The candidate payload strictly conforms to the schema output by `reciprocal_rank_fusion` (Module 3).
- Fast tensor operations rely on the internal `batch_size=32` setting during inference.

## Known Limitations
- The 22MB cross-encoder weights are loaded synchronously into RAM during class instantiation (`__init__`), slightly delaying container startup time.

## Integration Points
- **Upstream:** Called exclusively by the pipeline orchestrator (`ai/ai/pipeline.py`) and evaluators (`ai/ai/evaluation/faithfulness_judge.py`).
- **Downstream:** Feeds the tightly filtered array directly into the Prompt Builder (Module 5).

## Breaking Changes
- **API Migration:** Any caller interacting with `CrossEncoderReranker.rerank()` MUST be updated to `await`.
- **Database Stability:** No PostgreSQL or Qdrant rebuild is required. This module executes dynamically in RAM.

## Future Improvements
- **Startup Model Warmup / Singleton Management**
  - **Future owner:** FastApi Layer / App Orchestration
  - **Target module:** Module 9 (API / FastApi)
  - **Reason:** Model loading blocks heavily during `__init__`. The API layer should own instantiating this dependency safely on application startup rather than lazy-loading it synchronously during a request pipeline.

## AI Notes
- **Safe refactors:** Modifying internal batch sizes or thread-dispatching mechanics.
- **Things that must never change:** Outputting mutated input objects (Immutability must be maintained). Output schema must remain uniform dictionaries.
- **Public interfaces:** `async def rerank(...)` is the absolute and singular integration gateway.

---

## Deferred Improvement Tracker

| Improvement | Future Owner | Target Module | Status |
| ----------- | ------------ | ------------- | ------ |
| Wrap CPU-bound chunker in `ProcessPoolExecutor` | Indexing Bridge / API | Module 10 (ETL) | Pending |
| Move chunker `source_thresholds` to config | Indexing Bridge / Config | Module 10 (ETL) | Pending |
| Two-phase commit / rollback (Storage consistency) | Indexing Bridge | Module 10 (ETL) | Pending |
| Startup Model Warmup / Singleton Management | API / FastApi Layer | Module 9 (API) | Pending |
