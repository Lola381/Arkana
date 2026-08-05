# Module 8 — Evaluation / ML Metrics

## Purpose
The Evaluation module establishes observability and quantitative metrics for the Arkana RAG pipeline. It utilizes LLM-as-a-judge patterns to evaluate real-time faithfulness (preventing AI hallucinations), provides automated CI/CD gating for retrieval precision against a golden test set, and captures holistic query telemetry (latency, context usage, refusal rates) for downstream dashboarding.

## Files
- `ai/ai/evaluation/faithfulness_judge.py`
  - *Contains `FaithfulnessJudge`, `RetrievalEvaluator`, and `MetricsLogger`.*

## Entry Points
- `FaithfulnessJudge.evaluate()` & `evaluate_batch()`
- `RetrievalEvaluator.run_retrieval_evaluation()`
- `MetricsLogger.log_query()` & `flush()`

## Inputs
- **Evaluator:** `query`, `response`, and retrieved `chunks`.
- **Retrieval Test:** A `GoldenTestItem` containing `query`, `expected_source_doc_ids`, and optional `tribe` context.

## Outputs
Returns unified metric schemas:
```python
{
    "faithfulness": 0.95,
    "relevance": 0.88,
    "reasoning": "All claims directly backed by excerpt 1."
}
```

## Current Architecture
The `ArkanaPipeline` orchestrator dynamically proxies successful text generation cycles into the evaluation module asynchronously.
- The **Faithfulness Judge** dispatches the generated output back to the LLM (e.g., Groq) instructed with a rigorous rubric (`JUDGE_PROMPT`).
- The **Retrieval Evaluator** simulates complex queries against hybrid embeddings and strictly calculates Precision@3 against hand-curated baseline documents.
- The **Metrics Logger** acts as a resilient buffer, aggregating query latency and LLM scores in-memory until safely flushing batch `INSERT` statements to the PostgreSQL analytics database.

## Final Implementation
1. The web user receives their generated token stream, finalizing the prompt.
2. `pipeline.py` calculates total query latency.
3. A strict GC-protected background task (`_run_evaluation`) is spawned.
4. The background task fetches faithfulness and relevance scores from the LLM judge.
5. The unified data (latency, query, metadata, scores) is safely atomically buffered by the `MetricsLogger`.
6. Once the buffer hits 100 queries, it seamlessly writes the telemetry to PostgreSQL.

## Implemented Improvements
### 1. Unified Metric Ingestion
- **Problem:** `pipeline.py` was generating double rows per query. It fired a telemetry task immediately (with 0.0 scores) and then fired an evaluation task that logged a secondary telemetry event (with 0 latency).
- **Root Cause:** Fragmented `create_task()` orchestrations.
- **Implementation:** Consolidated to a single `_run_evaluation` task that sequentially tracks real latency, awaits the LLM judge, and dispatches a unified atomic `INSERT` payload.
- **Impact:** Fixed severe telemetry database corruption. Analytics now accurately portray both latency and model accuracy.

### 2. Task Reference Protection
- **Problem:** `asyncio.create_task()` fire-and-forget logic risked spontaneous evaluation aborts.
- **Root Cause:** The Python Garbage Collector culls tasks holding only weak references if memory runs tight.
- **Implementation:** Deployed a `self._background_tasks = set()` reference cache, mapping strong references via `add_done_callback(discard)`.
- **Impact:** Zero risk of lost metrics under heavy production loads.

### 3. Batch Concurrency and OOM Limits
- **Problem:** `evaluate_batch` unbounded network calls triggered HTTP 429 rate limits. Database outages caused infinite metric buffer growth (OOM).
- **Implementation:** Initialized an `asyncio.Semaphore(10)` rate limiter. Enforced a hard buffer truncation (`[-5000:]`) in `MetricsLogger.flush`.
- **Impact:** Hardened production resilience.

## Deferred Improvements
- **Grafana / Observability Dashboards**
  - **Future owner:** DevOps
  - **Reason:** Connecting PostgreSQL metrics tables to visual dashboards is a deployment infrastructure concern.
- **Nightly CI Automation**
  - **Future owner:** CI/CD Architecture
  - **Reason:** Triggering `RetrievalEvaluator.run_retrieval_evaluation_sync()` on pull requests requires GitHub Actions definitions outside the python codebase.

## AI Notes
- **Safe refactors:** Tuning the internal weights or prompt text in `JUDGE_PROMPT`.
- **Things that must never change:** Modifying `MetricsLogger.flush` to use an `asyncio.Lock()`. The current pattern of swapping the list reference (`records = self.buffer; self.buffer = []`) is explicitly lock-free and thread-safe in asyncio. Adding a Lock could create unnecessary deadlocks.
