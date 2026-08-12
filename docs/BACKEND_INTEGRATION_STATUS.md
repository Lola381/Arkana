# Backend Integration Status

> **Status:** Phase 3 (FastAPI & RAG Generation) Pending
> **Last Updated:** 2026-07-25

This document outlines the current progress, mappings, and integration readiness of the **Echolore** backend engine with the **Arkana** frontend. For full architectural diagrams, please see [ARCHITECTURE.md](../ARCHITECTURE.md) and [INTEGRATION_PLAN.md](./INTEGRATION_PLAN.md).

---

## 1. Purpose of Echolore
Echolore is the dedicated data engineering, semantic search, and AI Retrieval-Augmented Generation (RAG) backend for Arkana. While Arkana handles the cinematic user interface, 3D modals, and authentication via Node.js/MongoDB, Echolore is responsible for providing the live, dynamic data that populates those interfaces.

## 2. Current Backend Progress
The Echolore backend is highly mature regarding data acquisition and structuring, but currently lacks an HTTP interface.

- **Phase 1 (Extractors):** 100% Complete. 
- **Phase 2 (Loaders & Embedders):** 100% Complete. Data has been successfully extracted, cleaned, and embedded into PostgreSQL and Qdrant (3,826 heritage sites).
- **Phase 3 (FastAPI & RAG):** 0% Complete. The API server does not yet exist.
- **Phase 4 (Frontend Integration):** 0% Complete. Arkana is currently using hardcoded mock data.

## 3. Available Backend Features
The following capabilities are fully implemented in Echolore and are ready to be served:
- **Relational Data:** `heritage_sites` and `site_images` in PostgreSQL.
- **Geospatial Queries:** PostGIS is configured, enabling distance queries and map bounding box queries (`ST_MakeEnvelope`).
- **Vector Search:** Qdrant `arkana_corpus` is fully populated with 768-dimensional embeddings generated via `all-mpnet-base-v2`.
- **RAG Retrieval:** `ingestion/retrieval/retriever.py` successfully retrieves context and citations for any semantic query.

## 4. Planned APIs
These endpoints will be built in Echolore (FastAPI, Port 8000). Arkana's Node.js server (Port 5000) will proxy them.

- `GET /api/heritage/sites` - List and filter heritage sites.
- `GET /api/heritage/sites/:id` - Fetch detailed metadata by UUID.
- `GET /api/map/bounds` - Fetch sites within a specific map bounding box (PostGIS).
- `POST /api/chat/ask` - Submit a query to Gemini with RAG context from Qdrant.

For a full list of planned Arkana gateway endpoints, see [API.md](../API.md).

## 5. Data Model Mapping
When integrating, the backend `HeritageSite` model must be serialized to match Arkana's current prop expectations.

| Arkana Expects | Echolore Provides | Transformation |
|----------------|-------------------|----------------|
| `id` | `site_id` | UUID to String |
| `title` | `name` | None |
| `type` / `artForm` | `category` | Enum mapping |
| `period` | `historical_era` | Append `historical_start_year` |
| `description` | `short_summary` | None |
| `image` | `images` array | Extract first `url` |
| `region` | `location.state` | None |
| `coordinates` | `coordinates` (WKB) | Convert PostGIS to `{lat, lng}` |

## 6. Integration Phases
1. **Scaffold FastAPI & HTTP Layer:** Build the core FastAPI application connected to PostgreSQL and Qdrant.
2. **Read-Only Data Integration:** Implement `GET /sites` and update Arkana's `Browse.jsx` to fetch real data instead of `artifacts.js`.
3. **RAG Pipeline Integration:** Implement `POST /chat` with Gemini. Ensure the JSON output schema perfectly matches Arkana's `geoData` and `insightCard` requirements.
4. **Map & Geospatial:** Implement `GET /map/bounds` to dynamically load map pins in `AskArkana.jsx`.

## 7. Current Blockers
- **Strict JSON Schema:** The Arkana frontend Map relies on the AI returning perfectly formatted `geoData` objects. Gemini must be strictly prompted to avoid JSON hallucination, which would crash the Leaflet map.
- **Image Hosting:** Echolore uses Wikimedia Commons URLs. Arkana must ensure its `<img />` tags and `LiquidImage.jsx` components support these external domains securely.

## 8. Integration Readiness
**Score: 70%**
The most difficult engineering tasks (data extraction, cleanup, schema design, and vector embedding) are completely finished. The remaining work is standard API development (FastAPI) and frontend data fetching.

## 9. Remaining Work
- [ ] Initialize `main.py` (FastAPI) in Echolore.
- [ ] Define Pydantic response models matching the table above.
- [ ] Write SQLAlchemy queries for the endpoints.
- [ ] Connect `retriever.py` output to the Gemini API SDK.
- [ ] Refactor Arkana frontend components to use `fetch()` or React Query instead of static array imports.
