# Technical Compatibility Report

This report evaluates the compatibility between the active AI/RAG module implementation and the backend repository ingestion format, detailing configurations, schema structures, and integration recommendations.

---

## 1. Vector Database Configuration

| Configuration Parameter | Text Chunk Collection | Visual / Image Collection |
| :--- | :--- | :--- |
| **Vector DB Used** | **Qdrant** (Dense) & **PostgreSQL** (Sparse) | **Qdrant** |
| **Server Version** | Unspecified / not dockerized in compose stack | Unspecified / not dockerized in compose stack |
| **Client Library Version** | Omitted / unpinned in [`requirements.txt`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/requirements.txt) | Omitted / unpinned in [`requirements.txt`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/requirements.txt) |
| **Collection Name** | `arkana_corpus` | `arkana_images` |
| **Vector Dimension** | `768` | `512` |
| **Distance Metric** | `COSINE` | `COSINE` |
| **Collection Creation Configuration** | `VectorParams(size=768, distance=Distance.COSINE)` | `VectorParams(size=512, distance=Distance.COSINE)` |

---

## 2. Embedding Pipeline

*   **Embedding Model Names**:
    *   **Text Retrieve Dense**: `sentence-transformers/all-mpnet-base-v2` (initialized in [`embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/embedding/embedder.py))
    *   **Semantic Boundary Chunking**: `all-MiniLM-L6-v2` (initialized in [`semantic_chunker.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/chunking/semantic_chunker.py))
    *   **CLIP Image Encoder**: `ViT-B/32` (initialized in [`clip_embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/visual/clip_embedder.py))
*   **Embedding Dimensions**:
    *   `768` (Text retrieval)
    *   `384` (Boundary check)
    *   `512` (Image encoder)
*   **Normalization Settings**:
    *   **Text**: Checked automatically during the `model.encode` routine.
    *   **CLIP**: Explicitly normalized via: `image_features /= image_features.norm(dim=-1, keepdim=True)`
*   **Batch Processing Logic**:
    *   Text embeddings are generated in batches of `batch_size = 32` (defined in `EmbeddingConfig`).
    *   Qdrant upserts are written in batches of `100` points (defined in [`embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/embedding/embedder.py#L113-L125)).

---

## 3. Payload Schema

### A. Text Collection (`arkana_corpus`)
```json
{
  "chunk_id": "string (UUID v4)",
  "doc_id": "string",
  "chunk_index": "integer",
  "text": "string",
  "token_count": "integer",
  "tribe_name": "string / null",
  "region": "string / null",
  "time_period_start": "integer / null",
  "time_period_end": "integer / null",
  "institution": "string / null",
  "source_title": "string",
  "source_url": "string / null"
}
```

### B. Image Collection (`arkana_images`)
```json
{
  "artifact_id": "string",
  "tribe_name": "string / null",
  "style": "string / null",
  "institution": "string / null",
  "title": "string / null",
  "image_url": "string",
  "period": "string / null",
  "region": "string / null"
}
```

---

## 4. Retrieval Interface

*   **How Vectors are Searched**: Dense vectors are searched via `QdrantClient.search()` in the [`Embedder`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/embedding/embedder.py#L206) class. Results are combined with PostgreSQL FTS sparse outputs in [`rrf_fusion.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/retrieval/rrf_fusion.py) using the Reciprocal Rank Fusion (RRF) algorithm:
    $$\text{RRF Score} = \sum_{m \in M} \frac{1}{k + \text{rank}_m + 1}$$
*   **Search Parameters**:
    *   `query` (`str`): Natural language search prompt.
    *   `filters` (`dict`): Attribute filters mapping key values (e.g., `{"tribe_name": "Warli"}`).
    *   `top_k` (`int`): Limits returned fused context windows.
*   **Top-K Values**: `dense_top_k = 20`, `sparse_top_k = 20`, returning a final merged list capped at `fused_top_k = 20` (reranked to `top_n = 4` by the Cross-Encoder).
*   **Filtering Support**:
    *   **Qdrant**: Supports strict payload filters built via `Filter(must=[FieldCondition(...)])` matching exactly.
    *   **PostgreSQL**: Uses a raw SQL `WHERE` clause containing keyword query checks and optional tribe name constraint checks.
*   **Input/Output Formats**:
    *   **Input**: `user_query: str`, `map_context: Dict[str, Any]` (converted to filters).
    *   **Output**: List of dictionaries containing RRF scores, IDs, and payload metadata dictionary lists:
        ```python
        List[Dict[str, Any]] # e.g. [{"chunk": {...}, "rrf_score": float, "chunk_id": str}]
        ```

---

## 5. Compatibility Analysis with the Target Backend

### A) Can backend embeddings directly enter this Qdrant collection?
**No.** Although both use a vector dimension of `768`, the backend embeddings are produced by `paraphrase-multilingual-mpnet-base-v2`, whereas the active RAG pipeline collection (`arkana_corpus`) relies on `sentence-transformers/all-mpnet-base-v2`. Mixing vectors from different base models in the same search space is incompatible and will fail to yield meaningful search matches.

### B) Are metadata fields compatible?
**Partially.** Both schemas share basic concepts (indexing, URLs, parent site identity), but key nomenclature and field structures mismatch.

### C) What fields need mapping?

| Backend Ingestion Schema Field | Active AI Qdrant Schema Target Field | Mapping / Conversion Requirement |
| :--- | :--- | :--- |
| `site_id` | `doc_id` | Exact string copy. |
| `site_name` | `source_title` | Name of the heritage site. |
| `parent_section` | `source_title` (or new payload field) | Needs concatenation (e.g. `"{site_name} - {parent_section}"`) or needs to be added as a new key in Qdrant payload. |
| `chunk_index` | `chunk_index` | Exact integer match. |
| `historical_era` | `time_period_start` / `time_period_end` | Must be parsed from text ranges (e.g., `"1200 CE"` -> `1200`). |
| `category` | *(Stored in PostgreSQL only)* | Excluded from the active Qdrant metadata schema payload. |
| `state` | `region` | Exact string representation of the state/UT. |
| `source_url` | `source_url` | Exact string copy. |
| **(Missing on Backend)** | `text` | The raw chunk text content must be mapped and stored inside Qdrant as `text`. |
| **(Missing on Backend)** | `token_count` | Calculated during ETL process using character length boundaries. |
| **(Missing on Backend)** | `tribe_name`, `institution` | Must be parsed from source metadata attributes. |

### D) Any breaking changes required?
1.  **Embedding Model Standardisation**: The backend must switch to `sentence-transformers/all-mpnet-base-v2` or the AI RAG config (`PipelineConfig.embedding_model`) must update to `paraphrase-multilingual-mpnet-base-v2` to align vector generation.
2.  **Infrastructure Updates**: The backend container config [`docker-compose.yml`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/docker-compose.yml) must run a Qdrant container on host port `6333` and remove or reallocate ChromaDB (currently on port `8001`).
3.  **Indexing Script Rewrites**: The backend ingestion scripts ([`scripts/loader.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/scripts/loader.py)) must be updated to load chunk payloads into Qdrant using the `qdrant-client` APIs instead of SQL-only database loading.

### E) Recommended Integration Strategy
1.  **Standardise on `all-mpnet-base-v2`**: Align backend ETL pipelines to use `all-mpnet-base-v2` since the RAG chunking similarity thresholds and evaluation test metrics are already calibrated around it.
2.  **Add Qdrant to Docker Stack**: Add `qdrant/qdrant` to `docker-compose.yml` mapped to port `6333:6333` and verify container health.
3.  **Implement a Transformation Middleware**: Build a mapping utility class inside the ingestion pipeline to parse backend records into standard `TextChunk` format containing both PostgreSQL-compatible columns and Qdrant-compliant payload models before vector storage.
