# ARKANA + ECHOLORE — Integration Plan

> **Last updated**: 2026-07-25  
> **Status**: Pre-integration. Documentation and planning phase.  
> **Purpose**: Single source of truth for the relationship between ARKANA (application layer)
> and Echolore (data & AI layer). Read this before implementing any new features.

---

## 1. What Each Repository Does

### ARKANA (`github.com/Lola381/Arkana`)

The **application layer**. This is what users see.

| Responsibility | Status |
|---|---|
| React 19 frontend (all pages, animations, maps) | Complete (demo-ready) |
| User authentication (JWT, bcrypt, HTTP-only cookies) | Complete |
| MongoDB user storage | Complete |
| Leaflet map with GeoJSON polygon rendering | Complete |
| Artifact browse + filter UI | Complete (hardcoded data) |
| AI chat interface | Complete (simulated mock) |
| Live heritage data API | Not implemented |
| Live RAG AI backend | Not implemented |

### Echolore (`github.com/Arjit-14/Echolore`)

The **data and AI layer**. This is what powers the content.

| Responsibility | Status |
|---|---|
| Data ingestion — Wikidata, Wikipedia, UNESCO, OSM | Complete |
| ETL — normalise, deduplicate, enrich | Complete |
| PostgreSQL + PostGIS (3,826 sites, 516 images) | Complete |
| Text chunking for RAG | Complete (Phase 2) |
| Vector embedding (`scripts/embedder.py`) | Complete (Phase 2 - 3,826 records) |
| Qdrant `arkana_corpus` collection | Complete (Phase 2 - 3,826 records) |
| FastAPI retrieval endpoints | Not yet implemented |
| Gemini LLM integration | Not yet implemented |
| Redis caching | Not yet implemented |

---

## 2. Current Architecture (What Exists Today)

```
Browser
  │
  ▼
React SPA (Vite, port 5173)
  │
  │  /api/* proxy
  ▼
Node.js / Express (port 5000)
  │
  ├── /api/auth/*     ← JWT authentication (IMPLEMENTED)
  └── /api/health     ← Health check (IMPLEMENTED)
  │
  ▼
MongoDB Atlas
  └── users collection
```

**AI chat today**: `useArkanaChat.js` runs entirely in the browser. It matches keywords
against `chatResponses.js` (hardcoded). No backend call is made for AI responses.

**Heritage data today**: `src/data/artifacts.js` is a static JavaScript file with
approximately 40 hardcoded artifact records.

---

## 3. Target Architecture (What Will Exist After Integration)

```
Browser
  │
  ▼
React SPA (Vite — static CDN in production)
  │
  │  REST calls
  ▼
Node.js / Express (ARKANA backend — API gateway)
  │
  ├── /api/auth/*          ← JWT auth (MongoDB or PostgreSQL)
  ├── /api/heritage/sites  ← Proxy → Echolore FastAPI
  └── /api/chat/ask        ← Proxy → Echolore FastAPI
            │
            ▼
       Echolore FastAPI (Python, port 8000)
            │
            ├── GET  /api/sites          ← PostgreSQL + PostGIS query
            ├── GET  /api/sites/:id      ← PostgreSQL site detail
            ├── POST /api/chat           ← Qdrant → Gemini → citations + geoData
            └── GET  /api/map/bounds     ← PostgreSQL polygon data
                      │
                      ├── PostgreSQL + PostGIS (3,826+ heritage sites)
                      ├── Qdrant (arkana_corpus — text embeddings)
                      ├── Redis (query cache)
                      └── Google Gemini API (LLM generation)
```

---

## 4. Key Overlaps to Resolve

### Overlap 1: Frontend duplication in Echolore
Echolore's `src/` directory is a copy of ARKANA's frontend (`package.json` names are identical).
**ARKANA is the canonical frontend.** Echolore's `src/` should be removed when the Echolore team
is ready.

### Overlap 2: Gemini API used in two places
`server.py` (ARKANA, legacy) calls Gemini directly.
Echolore will call Gemini as part of the RAG pipeline.
**Resolution**: All Gemini usage consolidates into Echolore's FastAPI. ARKANA backend proxies,
it does not call Gemini directly.

### Overlap 3: server.py vs. backend/
ARKANA has two servers: a legacy Flask `server.py` and the canonical Node.js `backend/`.
**Resolution**: `server.py` is marked legacy. The Node.js backend is the only active server.

### Overlap 4: Hardcoded data vs. live database
ARKANA's `src/data/artifacts.js` (~40 records) will be replaced by live calls to
Echolore's `/api/sites` endpoint when that endpoint is available.

---

## 5. Integration Steps (Ordered)

### Step 1 — Echolore: FastAPI (2-3 weeks)
- Build FastAPI with: `GET /api/sites`, `GET /api/sites/:id`, `POST /api/chat`, `GET /api/map/bounds`
- Implement Redis caching and `slowapi` rate limiting
- **Deliverable**: Live service at `http://echolore:8000`

### Step 2 — ARKANA: Add Proxy Routes, Remove server.py (1-2 weeks)
- Add `ECHOLORE_API_URL` to `backend/.env`
- Add proxy routes: `/api/heritage/sites`, `/api/chat/ask`
- Add `authMiddleware` on chat endpoint
- Delete `server.py` from active use
- **Deliverable**: ARKANA backend is the single API gateway

### Step 3 — ARKANA Frontend: Replace Hardcoded Data (2-3 weeks)
- Create `src/services/api.js`
- Replace `artifacts.js` imports with `useEffect` fetches
- Replace `useArkanaChat.js` mock with real streaming API call
- Add loading states and error boundaries
- **Deliverable**: All frontend data is live

### Step 4 — Database: Migrate MongoDB → PostgreSQL (1-2 weeks)
- Alembic migration: `users`, `chat_sessions`, `chat_messages` tables
- Rewrite `auth.controller.js` for PostgreSQL
- Remove `mongoose`
- **Deliverable**: Single database (PostgreSQL + Qdrant)

### Step 5 — DevOps: Docker + CI/CD (1-2 weeks)
- Full `docker-compose.yml` (6 services)
- GitHub Actions: lint + test + build + deploy
- **Deliverable**: Reproducible development environment

---

## 6. Component Ownership

| Component | Owner | Notes |
|---|---|---|
| React frontend | ARKANA | Canonical. Do not duplicate in Echolore. |
| Node.js backend | ARKANA | API gateway. Auth + proxy. |
| Authentication (JWT) | ARKANA | Complete. |
| Heritage data ETL | Echolore | Complete (Phases 1 & 2). |
| PostgreSQL heritage database | Echolore | 3,826 sites loaded. |
| Qdrant embeddings | Echolore | Complete (3,826 records). |
| FastAPI data service | Echolore | Not yet built. |
| Gemini LLM integration | Echolore | Not yet built. |
| Leaflet map rendering | ARKANA | Uses data from Echolore via API. |
| Documentation | ARKANA | This `docs/` directory. |

---

## 7. API Contract (To Be Defined)

This section will be populated when Echolore builds its FastAPI endpoints.
The contract must be agreed between both teams before Step 3 begins.

Required endpoints (minimum):

```
GET  /api/sites
     ?region=  &period=  &category=  &q=  &limit=  &offset=
     Returns: [{id, name, state, coordinates, category, period, image_url, qid}]

GET  /api/sites/:id
     Returns: full site detail including Wikipedia text, coordinates, UNESCO status

POST /api/chat
     Body: {query: string, session_id?: string}
     Returns: {text: string, citations: [{title, url, qid}], geoData: {center, zoom, polygon, pins}}

GET  /api/map/bounds
     ?qid= (comma-separated)
     Returns: {features: GeoJSON FeatureCollection}
```

---

## 8. Environment Variables

### ARKANA (`backend/.env`) — current
```
PORT=5000
MONGO_URI=<mongodb connection string>
JWT_SECRET=<secret>
ACCESS_TOKEN_SECRET=<secret>
REFRESH_TOKEN_SECRET=<secret>
GEMINI_API_KEY=<key>           # Will move to Echolore after integration
```

### ARKANA (`backend/.env`) — after integration, add:
```
ECHOLORE_API_URL=http://localhost:8000
```

### Echolore (`.env`) — current
```
POSTGRES_USER=<user>
POSTGRES_PASSWORD=<password>
POSTGRES_DB=<db>
QDRANT_URL=http://localhost:6333
GEMINI_API_KEY=<key>
```

---

*This document is evidence-based. All current status claims are verified from repository
source files as of 2026-07-25. See `docs/LEGACY_ARCHIVE/` for historical audit reports.*
