# Arkana AI — Future Work & Roadmap

This document outlines the upcoming phases of development for the Arkana AI architecture, primarily focusing on Frontend Integration (Phase 4) and future ML optimizations.

---

## 1. Phase 4: Frontend Integration (React/Next.js)

The Backend API is fully operational. The immediate next step is mapping the frontend UI to consume the FastAPI endpoints.

### API Consumption
- **Map API**: The frontend Map component needs to fetch `GET /api/sites` to plot the `latitude` and `longitude` markers for historical sites.
- **Chat UI**: The AI Chat interface must connect to `POST /api/chat` and handle **Server-Sent Events (SSE)** to stream the AI's response token-by-token.

### Citation Badge Mapping
The AI backend currently returns JSON citations containing a `"chunk_source"` key. The frontend UI must map these strings to visual badges:
- If `"chunk_source": "Wikipedia"`, display a globe icon and hyperlink.
- If `"chunk_source": "Arkana"`, display a gold "Arkana Verified / Internal Lore" badge.

---

## 2. Future Optimizations (Phase 5+)

### Re-enabling Visual Intelligence (CLIP)
The pipeline currently has the 600MB `ViT-B/32` CLIP model disabled via the `enable_clip = False` config toggle to prevent OOM crashes on 8GB RAM machines.
- **Goal:** Once the application is deployed to a cloud server with 16GB+ RAM, set `enable_clip = True`. This will instantly re-enable the Image Identification RAG pipeline without requiring any code rewrites.

### Data Provenance Enhancement
During Phase 2 (Ingestion), the legacy data scripts stripped some original source URLs and defaulted them to `"Arkana"`.
- **Goal:** If exact provenance is required, we must step backward, modify the scraping scripts to strictly preserve external URLs, and wipe/re-ingest the Qdrant database to replace the `"Arkana"` tags with the true external links.

### Evaluation Framework
The pipeline currently stubs the `golden_test_set.json` evaluation logic.
- **Goal:** Populate the golden test set with 50-100 verified Q&A pairs to mathematically benchmark the Reranker and LLM accuracy over time.
