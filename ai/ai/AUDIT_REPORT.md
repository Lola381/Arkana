# Arkana AI Audit Report

This report presents a read-only technical audit of the `ai/` folder and its architecture, modules, configurations, data flows, and integration readiness.

---

## 1. File Inventory & Functional Descriptions

The active AI code is stored in the root of the `ai/` directory and its module folders. The `ai/backend/` folder contains historical ETL scripts, schemas, checkpoints, and a prototype frontend shell.

### A. Core AI Module Files (`ai/`)

| File Path | Component | Functional Description |
| :--- | :--- | :--- |
| [`ai/pipeline.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/pipeline.py) | **Unified Pipeline** | The main entry point for the application. Integrates all components (chunking, embedding, retrieval, reranking, generation, NER, visual identification, and evaluation). Exposes functions for FastAPI/TM3 backend integrations. |
| [`ai/verify_models.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/verify_models.py) | **Sanity Verification** | Developer verification script. Loads and tests embedding dimensions, cross-encoder scoring, CPU-bound CLIP, spaCy NER, and Groq LLM API connectivity. |
| [`ai/chunking/semantic_chunker.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/chunking/semantic_chunker.py) | **Chunking** | Implements semantic boundary detection. Computes cosine similarity between adjacent sentences using a SentenceTransformer model and splits documents. Applies source-specific calibration thresholds and overlaps. |
| [`ai/embedding/embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/embedding/embedder.py) | **Embedding & DB client** | Generates text embeddings and indexes them to Qdrant (dense search) and PostgreSQL (sparse BM25 metadata search). Contains dense and sparse query routines. |
| [`ai/retrieval/rrf_fusion.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/retrieval/rrf_fusion.py) | **Hybrid Retrieval** | Combines Qdrant dense vector search results and PostgreSQL BM25 sparse search results using the Reciprocal Rank Fusion (RRF) algorithm. |
| [`ai/reranking/cross_encoder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/reranking/cross_encoder.py) | **Reranking** | Scores retrieved query-chunk pairs using a Cross-Encoder transformer model. Filters out low-scoring candidates and sorts the remainder to return the top $N$ context windows. |
| [`ai/generation/llm_client.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/generation/llm_client.py) | **LLM Groq Client** | Interface for Groq completions API. Houses streaming, non-streaming, and LLM-as-judge faithfulness validation requests using the Llama 3.1 model. |
| [`ai/generation/prompt_builder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/generation/prompt_builder.py) | **Prompt Engineering** | Formulates constraints for the LLM system prompt: strict citation structures, grounding rules, and history limits. Formats citation metadata return payloads. |
| [`ai/ner/entity_extractor.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/ner/entity_extractor.py) | **Named Entity Extraction** | Runs spaCy entity matching. Maps GPE (locations), dates, and exact names to tribe/region records. Emits synchronization events (`MAP_HIGHLIGHT`, `MAP_PAN`, `TIMELINE_SEEK`). |
| [`ai/visual/clip_embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/visual/clip_embedder.py) | **Visual Intelligence** | Generates image vectors with CLIP. Implements zero-shot art style classification and visual search over similar artifact pictures indexed inside Qdrant. |
| [`ai/evaluation/faithfulness_judge.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/evaluation/faithfulness_judge.py) | **Evaluation & Logging** | Evaluates faithfulness of generations, runs retrieval precision checks against a golden test set (`golden_test_set.json`), and logs telemetry to PostgreSQL. |

---

### B. Backend and Supporting Files (`ai/backend/`)

- [`ai/backend/PROJECT_STATUS_REPORT.md`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/PROJECT_STATUS_REPORT.md): Authority report on completed data validation (Phase 1) and PostgreSQL loading progress (Phase 2).
- [`ai/backend/README.md`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/README.md): Merged architecture guide and local deployment setup instruction.
- [`ai/backend/handoff_summary.md`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/handoff_summary.md): Handoff summary for transitioning team members; records Wikidata state corrections and data.gov.in deprioritization.
- [`ai/backend/docker-compose.yml`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/docker-compose.yml): Declares Postgres/PostGIS, Redis, and ChromaDB containers.
- [`ai/backend/requirements.txt`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/requirements.txt): Legacy python dependency configurations.
- [`ai/backend/scripts/pipeline.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/scripts/pipeline.py): Orchestrates raw checkpoint ingestion, deduplication, and enrichment outputting to a JSONL file.
- [`ai/backend/scripts/loader.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/scripts/loader.py): Inserts the enriched JSONL heritage sites data and image references into PostgreSQL.
- [`ai/backend/ingestion/config.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/ingestion/config.py): Ingestion config parameters (Postgres connection, Wikidata state QIDs, quality weights).
- [`ai/backend/ingestion/validate.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/ingestion/validate.py): Diagnostic runner verifying Wikidata, Wikipedia, UNESCO, and OSM source API connectivity.
- [`ai/backend/ingestion/models/heritage_schema.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/ingestion/models/heritage_schema.py): Master schema definition (`HeritageSite`) using Pydantic v2.
- [`ai/backend/ingestion/transformers/`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/ingestion/transformers/): House normalization, fuzzy deduplication, and cross-source metadata enrichment logics.
- [`ai/backend/ingestion/utils/`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/ingestion/utils/): Holds rate-limited async HTTP client, parent-child text chunker (`chunker.py`), and JSON logger.
- [`ai/backend/src/`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/src/): Prototype React application (Explore map, Browse filters, static artifact profiles).

---

## 2. Module Completion Status

| Module | Status | Associated Implementation |
| :--- | :--- | :--- |
| **Chunking** | **Complete** | In `ai/chunking/semantic_chunker.py`, using SentenceTransformers-based cosine similarity boundary calculations. |
| **Embedding** | **Complete** | In `ai/embedding/embedder.py`, using `all-mpnet-base-v2` for dense embeddings and asyncpg metadata updates. |
| **Retrieval** | **Complete** | In `ai/retrieval/rrf_fusion.py`, combining dense (Qdrant) and sparse (Postgres) ranks via Reciprocal Rank Fusion. |
| **Reranking** | **Complete** | In `ai/reranking/cross_encoder.py`, with `ms-marco-MiniLM-L-6-v2` for semantic query-chunk comparison. |
| **Generation** | **Complete** | In `ai/generation/llm_client.py` and `ai/generation/prompt_builder.py`, calling the Groq API (Llama 3.1) with system instructions. |
| **NER** | **Complete** | In `ai/ner/entity_extractor.py`, using spaCy `en_core_web_sm` and mapping rules. |
| **Visual** | **Complete** | In `ai/visual/clip_embedder.py`, using CLIP `ViT-B/32` for image search and style classification. |
| **Evaluation** | **Complete** | In `ai/evaluation/faithfulness_judge.py`, housing LLM-as-judge and precision CI gates. |
| **Pipeline** | **Complete** | In `ai/pipeline.py`, defining the unified `ArkanaPipeline` coordinator. |

---

## 3. Vector Database & Initialization

- **Vector Database**: **Qdrant** is used for dense vector retrieval of text chunks and image embeddings. **PostgreSQL** serves as the sparse (BM25) text retriever.
- **Initialization Locations**:
  - The Qdrant client is instantiated inside the `Embedder` constructor in [`ai/embedding/embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/embedding/embedder.py#L35-L42):
    ```python
    self.qdrant = QdrantClient(url=self.config.qdrant_url)
    ```
    This client is then shared with the visual index in [`ai/pipeline.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/pipeline.py#L157):
    ```python
    self.clip_embedder = CLIPEmbedder(clip_config, qdrant_client=self.embedder.qdrant)
    ```
  - Upon initialization, `Embedder` calls `_ensure_collection()` which checks if the default collection `arkana_corpus` (Cosine distance, 768 dimensions) exists, creating it if necessary.
  - Similarly, the `CLIPEmbedder` initializes its visual search collection `arkana_images` (Cosine distance, 512 dimensions) inside `_ensure_collection()` in [`ai/visual/clip_embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/visual/clip_embedder.py#L221-L235).

---

## 4. Embedding Models

1. **Text Chunk Search**: `sentence-transformers/all-mpnet-base-v2` (dimension: 768).
2. **Semantic Boundary Detection**: `all-MiniLM-L6-v2` (used in `SemanticChunker` to compute cosine similarity between adjacent sentence embeddings).
3. **Image Classification & Search**: OpenAI's CLIP `ViT-B/32` (dimension: 512, used in `CLIPEmbedder`).

---

## 5. LLM Configuration & Calling Mechanism

- **LLM Model**: `llama-3.1-8b-instant` served by the **Groq API**.
- **Calling Interface**:
  - Initialized inside `LLMClient` via:
    ```python
    self.client = Groq(api_key=api_key)
    ```
  - **Streaming**: Calls `self.client.chat.completions.create` with `stream=True` in `generate_streaming()`, yielding token segments as they arrive.
  - **Non-Streaming**: Calls `self.client.chat.completions.create` with `stream=False` in `generate_complete()`.
  - **LLM-as-a-judge Evaluation**: Done via `evaluate_faithfulness()`, which submits a custom JSON formatting template prompting the model to grade the query context on `faithfulness` (0-1) and `relevance` (0-1) scores.
- **System Prompt Rules**: Defined in `ai/generation/prompt_builder.py`. Employs strict RAG rules:
  1. Answer **ONLY** using provided source excerpts.
  2. If info is absent, respond with exactly: `"This information is not currently in the Arkana archive."`
  3. End factual claims with the citation: `[Source: {institution} — {source_title}]`.
  4. Never speculate or mention that it is an AI or looking up details.

---

## 6. Chunking Strategy

### Active Strategy (Semantic Chunking)
Defined in [`ai/chunking/semantic_chunker.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/chunking/semantic_chunker.py):
- **Splitting**: NLTK's `sent_tokenize` splits the document into sentences.
- **Boundary Detection**: Cosine similarity is computed between adjacent sentence vectors using `all-MiniLM-L6-v2`. A boundary is established if similarity falls below the threshold.
- **Threshold Calibration**: Source-dependent thresholds:
  - `map_academy`: 0.65
  - `ignca`: 0.55
  - `museums_of_india`, `asi`, `internet_archive`, `europeana`: 0.60
- **Boundaries & Fallback**: Capped by token counts (approximated as 4 chars/token):
  - `min_tokens`: 150
  - `max_tokens`: 512
  - If a semantic block exceeds `max_tokens`, it is recursively sub-split by word bounds.
- **Overlap**: `overlap_tokens` (default 50) is prepended to each subsequent chunk from the end of the previous chunk text.

### Legacy Strategy (Section-Aware parent-child chunking)
Defined in [`ai/backend/ingestion/utils/chunker.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/ingestion/utils/chunker.py):
- splits Wikipedia articles by header markers (`==Section==`).
- Creates child chunks using 500-token sliding windows with 15% overlap.
- Skips boilerplate sections (e.g., "See Also", "References").

---

## 7. Supported Data Sources

The ingestion pipeline and chunker configurations support the following primary data sources:
1. **Wikidata SPARQL**: For generating core heritage site entities, coordinates, categories, and QIDs.
2. **Wikipedia API**: For long-form descriptions and related historical/cultural entities.
3. **UNESCO Open Data API v3**: Ground truth for India's 44 World Heritage Sites.
4. **OSM Overpass API**: Supplementary coordinate enrichment.
5. **Calibrated Chunker Sources**: Extractor patterns specifically calibrate thresholds for `map_academy`, `ignca`, `museums_of_india`, `asi`, `internet_archive`, and `europeana`.
6. *Note on data.gov.in*: This source was investigated in Phase 1 and **permanently deprioritized** due to poor data enrichment quality and API access issues.

---

## 8. Unified Pipeline Entry Points (FastAPI/TM3 API)

Exposed in [`ai/pipeline.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/pipeline.py):

```python
async def query(
    user_query: str,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    map_context: Optional[Dict[str, Any]] = None,
    db_pool=None
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main RAG query pipeline. Streams tokens, citations, map events (NER), 
    and insight cards to FastAPI routers.
    """

async def identify_image(
    image_path: str, 
    db_pool=None
) -> Dict[str, Any]:
    """
    Visual identification pipeline. Classifies style, searches for similar 
    artifacts in Qdrant, and builds a context-aware RAG query.
    """

async def run_retrieval_evaluation(
    db_pool=None
) -> Dict[str, Any]:
    """
    Retrieval evaluation entry point. Runs precision@3 validation on the 
    golden test set for CI/CD gates.
    """

def chunk_and_index_documents(
    documents: List[Dict[str, Any]], 
    source: str = "default", 
    db_pool=None
) -> Dict[str, int]:
    """
    Document ingestion entry point. Chunks documents semantically, 
    generates embeddings, and indexes them in Qdrant and PostgreSQL.
    """
```

---

## 9. Missing Components / Not Yet Started

1. **FastAPI Web Server Layer**: The API routers (`app/main.py` or equivalent) that route HTTP/SSE requests to these pipeline functions are missing.
2. **Indexing Orchestrator script**: There is no script/task that reads all records from PostgreSQL, chunks them, generates vectors, and populates the Qdrant database. The database is empty by default until a load run is developed.
3. **Local Image Cache Manager**: The image search indexes URLs on-the-fly (`embed_image_from_url`). There is no local downloader or local image file server.
4. **Authentication backend**: Login routes, JWT generation, and session management are not implemented in the Python backend (only mocked on the frontend).

---

## 10. Risks & Conflicts (ChromaDB vs. Qdrant)

There is a misalignment between the legacy ingestion design and the new active AI pipeline:

- **Vector Database Discrepancy**:
  - The legacy backend infrastructure ([`ai/backend/docker-compose.yml`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/backend/docker-compose.yml)) and documents assume **ChromaDB** running on port 8000 as the vector database.
  - The new active RAG implementation ([`ai/embedding/embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/embedding/embedder.py) and [`ai/visual/clip_embedder.py`](file:///c:/Users/NILESH/Documents/CHRIST/Trimester%204/arkana/ai/visual/clip_embedder.py)) exclusively uses **Qdrant** (port 6333) via the `qdrant_client` library.
  - **Risk**: Attempting to launch the backend stack using the existing Docker Compose setup will fail to initialize the AI pipeline because Qdrant is not running.
- **Port Conflict (FastAPI vs. ChromaDB)**:
  - ChromaDB is configured to run on port 8000.
  - FastAPI applications conventionally also run on port 8000.
  - **Risk**: If the developer launches a FastAPI app to serve the AI pipeline on port 8000, it will conflict with ChromaDB. Switching to Qdrant (port 6333) avoids this, but ChromaDB must be disabled or moved to port 8001.
- **Query & Payload Filtering Differences**:
  - The active hybrid retriever uses Qdrant's payload filters (`FieldCondition`, `MatchValue`, `Filter`) to implement metadata filtering matching the interactive map's context (e.g., `tribe_name`).
  - **Risk**: ChromaDB uses a completely different query filter API (`where`, `where_document` maps) and does not natively match Qdrant's schema. Swapping the backend back to ChromaDB would require major code rewrites in the retrieval and embedding modules.
- **Embedding Model Misalignment**:
  - Legacy planning documentation references `paraphrase-multilingual-mpnet-base-v2` for text vectorization.
  - The active AI code expects `sentence-transformers/all-mpnet-base-v2` (dimension 768).
  - **Risk**: Generating embeddings using different models or dimensions between the ETL stage and search stage will lead to mismatched search logic and zero retrieval hits.
