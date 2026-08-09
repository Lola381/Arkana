# Module 1 — Semantic Chunker

## Purpose
The Semantic Chunker is responsible for partitioning unstructured historical text into boundary-aware semantic chunks. It identifies natural topic shifts using sentence-level cosine similarity to ensure that resultant chunks represent coherent thoughts.

The module enforces strict token limits and applies sliding-window token overlap to preserve contextual continuity between adjacent chunks. It operates entirely in memory and is decoupled from database ingestion logic.

## Files
- `ai/ai/chunking/semantic_chunker.py`
- `ai/ai/chunking/test_chunker_edge_cases.py`

## Entry Points
- `SemanticChunker.chunk_document(text, doc_id, metadata, source)`
- `SemanticChunker.chunk_documents_batch(documents, source)`

## Inputs
Accepts raw string data alongside structural metadata.
- `text`: `str` (Raw document text)
- `doc_id`: `str` (Unique identifier from Echolore)
- `metadata`: `Dict[str, Any]` (Requires keys: `title`, `tribe_name`, `region`, `url`, `institution`, `time_period_start`, `time_period_end`)
- `source`: `str` (Identifier used for dynamic threshold calibration)

## Outputs
Returns `List[Dict[str, Any]]` representing the chunks.
Schema:
```python
{
    "chunk_id": str(uuid4),
    "doc_id": str,
    "chunk_index": int,
    "text": str,
    "token_count": int,
    "tribe_name": str,
    "region": str,
    "time_period_start": str,
    "time_period_end": str,
    "institution": str,
    "source_title": str,
    "source_url": str
}
```

## Current Architecture
The chunker employs a dual-model paradigm. It uses `sentence-transformers/all-MiniLM-L6-v2` solely for fast, lightweight boundary detection (calculating cosine similarity between adjacent sentences). However, it uses a dedicated `transformers.AutoTokenizer` instances matching the downstream embedder (`sentence-transformers/all-mpnet-base-v2`) to enforce hard token limits and overlap lengths, preventing OOM errors in subsequent pipeline stages.

## Final Implementation
1. **Cleaning:** Strips source-specific noise (e.g., page numbers, uppercase fragments).
2. **Tokenization:** Splits text into sentences via `nltk.sent_tokenize`.
3. **Similarity Calculation:** Embeds sentences via `all-MiniLM-L6-v2`. Computes adjacent cosine similarities (`numpy.dot`). Boundaries are marked where similarity drops below `similarity_threshold`.
4. **Chunk Assembly:** Sentences between boundaries are joined.
5. **Token Enforcement:** Token limits are verified via `AutoTokenizer`. If a chunk exceeds `effective_max_tokens` (`max_tokens - overlap_tokens`), it is forcibly split.
6. **Orphan Management:** Chunks falling below `min_tokens` are retained in an accumulator and merged into the subsequent boundary segment to prevent data loss.
7. **Overlap:** The exact token IDs of the last `overlap_tokens` from chunk *N* are decoded and prepended to chunk *N+1*.

## Implemented Improvements
### 1. Accurate Tokenization
- **Problem:** Chunk sizes exceeded downstream context windows, causing silent truncation during embedding.
- **Root Cause:** Token length was roughly approximated using `len(text) // 4` and string splitting.
- **Implementation:** Imported `AutoTokenizer` configured strictly to the Embedder's target model (`all-mpnet-base-v2`). Replaced approximations with `.encode()` and `.decode()` logic.
- **Impact:** Exact token guarantees. Downstream OOM/truncation risks are eliminated.

### 2. Orphan/Small Chunk Data Loss
- **Problem:** Semantic boundaries frequently yielded trailing chunks smaller than `min_tokens` which were silently discarded.
- **Root Cause:** The `create_chunks_from_boundaries` loop lacked state persistence to carry small chunks forward into the next iteration.
- **Implementation:** Introduced an `orphan_sentences` accumulator that carries undersized chunks forward and prepends them to the next segment.
- **Impact:** Guarantees 100% data retention from extraction to embedding.

### 3. Overlap Limit Violation
- **Problem:** Chunks perfectly split at `max_tokens` exceeded limits after `overlap_tokens` were prepended.
- **Root Cause:** Splitting logic ignored overlap margins.
- **Implementation:** Replaced static `max_tokens` with dynamic `effective_max_tokens` (subtracting `overlap_tokens` for all chunks after index 0).
- **Impact:** Strictly maintains the 512-token ceiling across the entire array.

## Important Design Decisions
- **Dual-Model Decoupling:** Boundary detection uses a fast 384-dimensional model, while token counting explicitly uses the 768-dimensional model's tokenizer. Do not couple these; using the 768d model for boundary detection is computationally wasteful.
- **Metadata Persistence:** Every chunk maintains a full copy of the parent document's metadata. This is non-negotiable for downstream hybrid retrieval filtering.

## Assumptions
- CPU infrastructure has sufficient memory to hold both the `SentenceTransformer` pipeline and the standalone `AutoTokenizer` concurrently.
- Input data relies on traditional punctuation rules suitable for `nltk.sent_tokenize`.

## Known Limitations
- The entire execution flow is heavily CPU-bound and synchronous.
- The `source_thresholds` dictionary is hardcoded into the `__init__` constructor rather than externalized.

## Integration Points
- **Upstream:** Called by Indexing Bridge / ETL scripts parsing Echolore PostgreSQL dumps.
- **Downstream:** Outputs are fed directly to `Embedder.process_and_index()`.

## Breaking Changes
**Rebuild Required:** Because token boundary calculation, overlap injection, and orphan retention logic were fundamentally altered, previous text chunking outputs are incompatible. All existing `rag_chunks` tables in PostgreSQL and `arkana_corpus` collections in Qdrant must be wiped and rebuilt from Echolore.

## Future Improvements
- **Deferred:** Offload `chunk_document()` execution to `asyncio.to_thread()` or a `ProcessPoolExecutor` when integrating with FastAPI to prevent blocking the async event loop.
- **Deferred:** Extract `source_thresholds` dictionary into `ChunkConfig` or environment configuration.

## AI Notes
- **Safe to refactor:** NLTK integration; dynamic threshold calibration methods.
- **Do not change:** The `Dict` schema returned by `_create_chunk`. Upstream and downstream systems tightly couple to this schema.
- **Dependencies:** `sentence-transformers`, `transformers`, `nltk`, `numpy`.
- **Things future modules should assume:** Token counts returned in the chunk metadata are exact, precise representations for `all-mpnet-base-v2` and will never exceed the configured maximums.
