# Cross-Repository Integration Audit: Arkana & Echolore

> **Audit Date:** 2026-07-25
> **Auditor:** Senior Frontend Architect & Backend Integration Engineer
> **Subject:** Readiness Assessment for Phase 3 Echolore Backend Integration

## 1. Executive Summary

This report analyzes the integration readiness between the two core repositories forming the platform:
- **Arkana (Frontend):** A highly polished React 19 SPA featuring cinematic UI, 3D modals, and map visualizations. Currently relies entirely on static, hardcoded data (`artifacts.js`, `chatResponses.js`).
- **Echolore (Backend):** A robust Python-based data engineering pipeline and retrieval engine. It has successfully extracted, deduplicated, and embedded a sample of 3,826 heritage sites into PostgreSQL (with PostGIS) and Qdrant. 

The primary finding is that **Echolore's Phase 1 & Phase 2 data engineering is 100% complete and highly successful**, but the Phase 3 HTTP API layer (FastAPI) and RAG integration (Gemini) are currently missing.

## 2. Maturity Assessment

| Domain | Status | Maturity Score | Details |
|--------|--------|----------------|---------|
| **Frontend UI** | Very High | 90% | Cinematic animations, map integration, and responsive layout are fully built. |
| **Frontend API Integration** | None | 0% | No HTTP client exists for data. Everything is synchronously loaded from static files. |
| **Backend ETL Pipeline** | Very High | 100% | Phase 1 (Extractors) & Phase 2 (Loaders/Embedders) are fully complete and verified on a 3-state sample. |
| **Backend Vector/Retrieval** | High | 90% | Embeddings generated. Qdrant is populated. `HeritageRetriever` works locally via CLI. |
| **Backend HTTP/API** | None | 0% | FastAPI server does not exist. No REST endpoints have been implemented. Gemini API is not yet wired to the RAG context. |

## 3. Architecture Comparison

- **Frontend Expectations:** The frontend expects a REST API providing fast, paginated JSON responses and complex, pre-formatted GeoJSON/Map events from the AI chat.
- **Backend Reality:** The backend is currently a suite of CLI scripts that populate databases. The core data layer (PostgreSQL + PostGIS) is perfectly suited to meet frontend expectations (e.g., PostGIS can easily handle the map bounds queries), but the HTTP translation layer (FastAPI) is missing.

## 4. Documentation Comparison

- **Frontend (Arkana):** Excellent UI documentation and component structure. The API documentation (`API.md`) has been updated to reflect the planned Echolore endpoints.
- **Backend (Echolore):** Exceptional engineering documentation. `PROJECT_STATUS_REPORT.md` and `BACKEND_IMPLEMENTATION_OVERVIEW.md` provide an accurate, up-to-date record of what is complete and what is missing.

## 5. API Capabilities vs Expectations

| Frontend Expectation | Backend Capability (Echolore) | Gap to Resolve |
|----------------------|-------------------------------|----------------|
| `GET /api/heritage/sites` | Can be fulfilled by PostgreSQL `heritage_sites` table with B-tree indexes. | Needs FastAPI route & SQLAlchemy query. |
| `GET /api/heritage/sites/:id` | Can be fulfilled by `site_id` (UUID) lookup. | Needs FastAPI route. |
| `POST /api/chat/ask` | `ingestion.retrieval.retriever` exists. | Needs FastAPI route & Gemini API call implementation. |
| `GET /api/map/bounds` | Can be fulfilled by PostGIS `ST_MakeEnvelope` on `coordinates`. | Needs FastAPI route. |
| `POST /api/identify` | No image recognition pipeline exists in Echolore. | Major gap (Future phase). |

## 6. Exact Frontend ↔ Backend Field Mappings

To seamlessly integrate without modifying the frontend UI components heavily, the FastAPI endpoints must serialize the backend `HeritageSite` model into the format expected by the frontend.

| Arkana Frontend Expects | Echolore Backend Source (`heritage_sites`) | Transformation Required |
|-------------------------|--------------------------------------------|-------------------------|
| `id` (String) | `site_id` (UUID) | Cast UUID to String |
| `title` (String) | `name` (String) | None |
| `type` / `artForm` | `category` (String) | Map Enums (e.g., `fort` -> `Fort`) |
| `period` / `timePeriod`| `historical_era` + `historical_start_year` | Combine into string (e.g., "Mughal (1500)") |
| `description` (String) | `short_summary` or `description` | Truncate if rendering in grid |
| `image` (String URL) | `images` array (from `site_images`) | Extract `images[0].url` |
| `region` (String) | `state` (String) | None |
| `coordinates` (Map) | `coordinates` (PostGIS `GEOGRAPHY`) | Convert WKB to `{lat, lng}` |

### AI Chat Response Mappings
The Arkana chat UI expects a very specific payload. When Echolore's FastAPI hits Gemini, the prompt must enforce this schema:
- `text`: Gemini's generated answer.
- `citation`: Extracted from Echolore's `source_url` or `citations` array.
- `insightCard`: Constructed from retrieved PostgreSQL metadata (`name`, `historical_era`, image).
- `geoData`: Must be extracted from the retrieved site's PostGIS `coordinates`.

## 7. Existing Backend Features (DO NOT REBUILD)

The following backend components **already exist** in Echolore and must be utilized directly:
1. **Database Schema:** Do not design a new database. Use the existing `docker/postgres/init.sql`.
2. **Data Ingestion:** Do not write scrapers. The extractors (`wikidata`, `wikipedia`, `unesco`) are complete.
3. **Embeddings/Qdrant:** The 768-dim `all-mpnet-base-v2` embeddings are already in Qdrant. Do not re-embed.
4. **Retrieval Logic:** Use `ingestion/retrieval/retriever.py` to fetch context. It already handles query embedding and Qdrant similarity search.

## 8. Required Integration Changes

### Backend Changes Required (Echolore)
1. **Scaffold FastAPI:** Create `main.py` and routers.
2. **Implement `GET /sites`:** Query PostgreSQL, apply filters (`state`, `category`), paginate, and return the mapped JSON.
3. **Implement RAG Endpoint (`POST /chat`):** 
   - Call existing `retriever.py` to get context.
   - Inject context into a Gemini prompt.
   - Force Gemini to return JSON that matches the frontend's expected format.
4. **Database Migration Tooling:** Introduce SQLAlchemy ORM models to match the existing SQL schema.

### Frontend Changes Required (Arkana)
1. **API Service Layer:** Replace static imports (`import { BROWSE_ARTIFACTS } ...`) with a data fetching library (e.g., React Query or basic `fetch` in `useEffect`).
2. **Dynamic Routing:** Update `App.jsx` to use `/artifact/:id` and fetch site details based on the UUID parameter.
3. **Image Loading:** Update frontend to handle Wikimedia Commons URLs instead of Google CDN URLs.

## 9. Technical Debt & Risks

- **Risk - Chat Schema Strictness:** The frontend map relies on the LLM generating perfectly formatted `geoData` objects. If Gemini hallucinates the JSON structure, the Leaflet map will crash.
- **Debt - Authentication:** Arkana's Node.js backend handles auth via MongoDB, but Echolore uses PostgreSQL for site data. A split-brain database situation exists. *(Recommendation: Keep Auth in Node/Mongo for now, proxy heritage requests to Echolore).*
- **Debt - Hardcoded Entities:** The frontend `Culture.jsx` is hardcoded to "Warli". Dynamic fetching for culture profiles is needed.

## 10. Conclusion

The most complex data engineering and UI tasks are entirely finished. The remaining integration work consists purely of writing the HTTP 'glue' (FastAPI endpoints and React `fetch` calls) to connect the two excellent halves. See [BACKEND_INTEGRATION_STATUS.md](./BACKEND_INTEGRATION_STATUS.md) for the exact phase-by-phase timeline.
