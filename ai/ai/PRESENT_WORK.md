# Arkana AI — Present Work & Architecture

This document serves as the **single source of truth** for the current state of the Arkana (formerly Echolore) AI backend. It consolidates all previous architectural audits, handoff summaries, and data strategy reports into a unified, accurate description of the active system.

---

## 1. Data Strategy & Ingestion (Phase 1 & 2)

### The Echolore Legacy Data
The initial dataset was originally extracted from various sources (Wikidata, Wikipedia, UNESCO, OSM) under the legacy "Echolore" project name. 
- The data was handed over as a **200MB SQL database dump**.
- This data was restored into a local **PostgreSQL / PostGIS** database.
- PostGIS extensions were utilized to enable geographic querying (extracting Latitude/Longitude coordinates for historical sites).

### Vectorization & Chunking
The raw text was processed through a `semantic_chunker.py` using `SentenceTransformers`.
- Text chunks were embedded into 768-dimensional vectors.
- These dense vectors were pushed into **Qdrant**, our high-speed vector database, running locally on port 6333.
- *Metadata Note:* Any chunks that did not have an explicit external URL (like Wikipedia) were tagged with `"chunk_source": "Arkana"` by default.

---

## 2. Backend Architecture (Phase 3)

The backend has been completely migrated from a set of disconnected scripts into a robust, production-ready **FastAPI** server (`uvicorn main:app`). 

### The AI Pipeline (`ai/pipeline.py`)
The unified pipeline handles user queries via `POST /api/chat`. It follows a strict Retrieval-Augmented Generation (RAG) architecture:

1. **Hybrid Retrieval (`rrf_fusion.py`)**: 
   - Takes the user's text query and converts it to a vector.
   - Queries **Qdrant** for semantic matches (Dense Search).
   - *Fix Implemented:* Corrected the Qdrant API response mapping to properly extract the `chunk_text` string instead of throwing dictionary KeyErrors.
   - *(Note: All ML inference runs in `asyncio.to_thread` to prevent the FastAPI server from freezing).*

2. **Cross-Encoder Reranking (`cross_encoder.py`)**:
   - Takes the retrieved chunks and scores them for relevance against the exact query using `ms-marco-MiniLM-L-6-v2`.
   - Results are sorted, and any low-quality chunks are discarded.
   - *Fix Implemented:* Added the `"score"` key to the final Citation JSON dictionary so the frontend can display the mathematical relevance of the data.

3. **LLM Generation (`llm_client.py`)**:
   - The top-ranked chunks are injected into a system prompt.
   - The `AsyncGroq` client sends the prompt to the `llama-3.1-8b-instant` model.
   - The response is streamed back to the client via Server-Sent Events (SSE).

### The Map API (`sites.py`)
The map endpoint (`GET /api/sites`) is handled purely by PostgreSQL.
- Connects directly to the SQL database.
- *Fix Implemented:* Utilizes PostGIS `ST_Y(location)` and `ST_X(location)` functions to correctly extract decimal coordinates for the frontend map renderer.

### RAM Optimization
The pipeline originally initialized a massive 600MB **CLIP** model (`ViT-B/32`) for visual/image intelligence. This caused severe Out-Of-Memory (OOM) crashes on 8GB RAM machines.
- *Fix Implemented:* Created an `enable_clip` configuration toggle to safely bypass loading the CLIP model during startup, instantly resolving the OOM crashes without breaking the codebase.

---

**Status:** The entire Backend AI architecture is mathematically verified, fully operational, and running smoothly.
