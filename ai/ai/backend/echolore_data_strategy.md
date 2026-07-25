# Echolore — Data Source Validation & Implementation Plan
> **Role**: Senior Data Engineer + AI Systems Architect
> **Phase**: Data Source Validation + Ingestion Pipeline Design
> **Date**: June 2026

---

## Executive Summary

Echolore is a RAG-based heritage knowledge platform for Indian history and cultural sites. The goal of this phase is to rigorously evaluate every proposed data source, design a unified data model, architect a production-grade ingestion pipeline, and deliver a clear feasibility verdict with an actionable roadmap.

**Bottom line up front**: The project is **FEASIBLE WITH SCOPE REDUCTION**. The Wikimedia ecosystem (Wikipedia, Wikidata, Commons) is exceptionally strong and alone can seed 3,000–5,000+ quality Indian heritage records. ASI / government portals are the weakest link — they provide no proper API and their data quality is inconsistent.

---

## Section 1 — API & Data Source Evaluation

### 1.1 Core Required Sources

---

#### 🔵 Source 1: Wikipedia API (MediaWiki Action API + REST API)

| Attribute | Detail |
|---|---|
| **Data Type** | Long-form encyclopedic text, infoboxes, categories, images |
| **API Access** | ✅ Yes — `https://en.wikipedia.org/w/api.php` + REST `https://en.wikipedia.org/api/rest_v1/` |
| **Authentication** | None required for read access. OAuth for writes. Bot credentials for high-volume. |
| **Rate Limits** | 10 req/min (anonymous) → 200 req/min (with proper User-Agent) → Unlimited (bot group). **Max 3 concurrent requests.** |
| **Data Quality** | ⭐⭐⭐⭐ 4/5 — Excellent coverage of major sites; minor sites may be stubs |
| **Integration Ease** | ⭐⭐⭐⭐⭐ 5/5 — `wikipedia-api` Python library is battle-tested |
| **License** | CC BY-SA 4.0 — Free reuse **with attribution** |
| **RAG Suitable** | ✅ YES — Long-form descriptions are ideal corpus text |
| **Realistic Record Count** | ~2,500–4,000 tagged Indian heritage/monument articles |

**Access Strategy:**
```python
# Recommended: Use wikipedia-api or mediawiki-api-talk Python libraries
import wikipediaapi
wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent="Echolore/1.0 (echolore@example.com)"
)
page = wiki.page("Taj Mahal")
```

**Key categories to mine:**
- `Category:Monuments_of_national_importance_in_India`
- `Category:Archaeological_sites_in_India`
- `Category:UNESCO_World_Heritage_Sites_in_India`
- `Category:Hindu_temples_in_India` (and by state)

> [!WARNING]
> As of 2026, anonymous API access has been throttled to **10 req/min**. You **MUST** set a descriptive `User-Agent` header to qualify for the 200 req/min tier. Failure to do so will cause silent rate-limiting that looks like connection issues.

---

#### 🔵 Source 2: Wikidata SPARQL

| Attribute | Detail |
|---|---|
| **Data Type** | Structured knowledge graph: names, coordinates, dates, heritage designations, linked entities |
| **API Access** | ✅ Yes — SPARQL endpoint: `https://query.wikidata.org/sparql` |
| **Authentication** | None required |
| **Rate Limits** | 60 second query timeout; ~600 requests/minute soft cap |
| **Data Quality** | ⭐⭐⭐⭐ 4/5 — Excellent for structured metadata; sparse for minor sites |
| **Integration Ease** | ⭐⭐⭐⭐ 4/5 — `SPARQLWrapper` or `qwikidata` Python libraries |
| **License** | CC0 (Public Domain) — **No restrictions** |
| **RAG Suitable** | ✅ YES — Perfect for structured metadata enrichment and entity linking |
| **Realistic Record Count** | ~5,000–8,000 Indian heritage-related entities |

**Core SPARQL Query (Indian Heritage Sites):**
```sparql
SELECT ?item ?itemLabel ?coords ?inception ?stateLabel ?image ?heritageDesig WHERE {
  ?item wdt:P17 wd:Q668 .  # country = India
  ?item wdt:P31/wdt:P279* wd:Q4989906 .  # instance of monument (or subclass)
  OPTIONAL { ?item wdt:P625 ?coords }
  OPTIONAL { ?item wdt:P571 ?inception }
  OPTIONAL { ?item wdt:P131 ?state }
  OPTIONAL { ?item wdt:P18 ?image }
  OPTIONAL { ?item wdt:P1435 ?heritageDesig }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
LIMIT 5000
```

**This is your backbone source.** Wikidata provides the structured spine; Wikipedia provides the narrative flesh.

---

#### 🔵 Source 3: UNESCO World Heritage Dataset

| Attribute | Detail |
|---|---|
| **Data Type** | Official WH site list: names, coordinates, inscription year, criteria, brief descriptions |
| **API Access** | ✅ Yes — UNESCO DataHub API: `https://data.unesco.org/` (REST API with filters) |
| **Authentication** | None for bulk download; API key optional for advanced queries |
| **Rate Limits** | Not documented; effectively unlimited for batch download |
| **Data Quality** | ⭐⭐⭐⭐⭐ 5/5 — Ground truth authoritative data |
| **Integration Ease** | ⭐⭐⭐⭐⭐ 5/5 — CSV/JSON/GeoJSON/Parquet direct download |
| **License** | CC BY-SA 4.0 |
| **RAG Suitable** | ✅ YES — Short but authoritative; excellent as citation anchor |
| **Realistic Record Count** | 42 Indian UNESCO WH sites (small but high quality) |

**Access Strategy:**
- Download full dataset in JSON/CSV from `https://data.unesco.org/` — no pagination needed
- India has 42 WHS (40 cultural + 2 natural)
- Use as **authoritative anchor records** — every site in this set must be in your corpus

> [!NOTE]
> The UNESCO list is small (42 records for India) but these are your highest-priority records. Every one must be fully enriched from Wikipedia + Wikidata.

---

#### 🔵 Source 4: Wikimedia Commons (Images)

| Attribute | Detail |
|---|---|
| **Data Type** | Images, metadata, license info, author attribution |
| **API Access** | ✅ Yes — `https://commons.wikimedia.org/w/api.php` |
| **Authentication** | None for read; Bot credentials for high-volume |
| **Rate Limits** | Same as Wikipedia API — 200 req/min with User-Agent |
| **Data Quality** | ⭐⭐⭐⭐ 4/5 — Quality varies; major sites have excellent coverage |
| **Integration Ease** | ⭐⭐⭐⭐ 4/5 — Standard MediaWiki API |
| **License** | CC BY / CC BY-SA / Public Domain — **always free; attribution required** |
| **RAG Suitable** | ⚠️ PARTIAL — Images are metadata; use as supplementary asset, not corpus text |
| **Realistic Record Count** | 50,000+ images across Indian heritage categories |

**Priority category:**
```
Category:Monuments_of_national_importance_in_India
```

**Toolforge Heritage API (Bonus):**
```
https://heritage.toolforge.org/api/api.php
```
This community-managed API maps monument identifiers to Wikimedia Commons entries — use it to link sites to their image collections.

> [!IMPORTANT]
> Do NOT download images during the initial ingestion phase. Store image URLs + attribution metadata only. Bulk-download only if you need local thumbnails for the frontend.

---

#### 🔵 Source 5: OpenStreetMap (Overpass API)

| Attribute | Detail |
|---|---|
| **Data Type** | Geospatial: precise coordinates, polygon boundaries, tags, address |
| **API Access** | ✅ Yes — Overpass API: `https://overpass-api.de/api/interpreter` |
| **Authentication** | None |
| **Rate Limits** | 2 concurrent requests; ~10,000 queries/day (soft limit) |
| **Data Quality** | ⭐⭐⭐ 3/5 — Excellent for major sites; gaps in rural/minor monuments |
| **Integration Ease** | ⭐⭐⭐⭐ 4/5 — `overpy` Python library |
| **License** | ODbL (Open Database License) — Free to use; **must credit OSM** |
| **RAG Suitable** | ⚠️ PARTIAL — Geospatial data, not text corpus; use for metadata enrichment |
| **Realistic Record Count** | ~1,500–3,000 tagged heritage nodes/ways in India |

**Overpass Query (All India Heritage):**
```overpassql
[out:json][timeout:60];
area["name"="India"]["admin_level"="2"]->.india;
(
  nwr["historic"~"monument|archaeological_site|heritage|fort|temple"](area.india);
  nwr["tourism"="attraction"]["heritage"](area.india);
);
out center tags;
```

> [!WARNING]
> OSM coverage for India's rural and lesser-known sites is **incomplete**. Do NOT use OSM as a primary source for site discovery. Use it only for coordinate enrichment when Wikidata `P625` is missing.

---

### 1.2 Additional Recommended Sources

---

#### 🟢 Source 6: data.gov.in (India OGD Platform)

| Attribute | Detail |
|---|---|
| **Data Type** | Government datasets: ASI-protected monument lists, state heritage lists, tourism stats |
| **API Access** | ✅ Yes — REST API per dataset; requires free registration + API key |
| **Authentication** | API key (free registration) |
| **Rate Limits** | Not formally documented; generous for low-volume access |
| **Data Quality** | ⭐⭐⭐ 3/5 — Variable; some datasets are poorly maintained CSVs from 2018–2022 |
| **Integration Ease** | ⭐⭐⭐ 3/5 — `datagovindia` Python package simplifies discovery |
| **License** | NGOML (National Government Open Data License) — Free to use with attribution |
| **RAG Suitable** | ⚠️ PARTIAL — Use for structured metadata only; descriptions are minimal |
| **Realistic Record Count** | 3,600+ ASI-protected monument entries (structured CSV) |

**Critical Dataset:**
- "District-wise list of Centrally Protected Monuments" — 3,693 records

**⚠️ Honest Assessment:** Data is often stale (2018 vintage), lacks descriptions, and coordinates are inconsistent. Use as a **coverage checklist** to identify gaps, not as a primary data source.

---

#### 🟢 Source 7: ISRO Bhuvan Geoportal

| Attribute | Detail |
|---|---|
| **Data Type** | Spatial data: monument locations, imagery layers, heritage site polygons |
| **API Access** | ⚠️ Limited — OGC WMS/WFS endpoints; no developer-friendly REST API |
| **Authentication** | None for public layers |
| **Rate Limits** | Not documented |
| **Data Quality** | ⭐⭐⭐ 3/5 — Indicative use only; not official legal boundary data |
| **Integration Ease** | ⭐⭐ 2/5 — WMS requires GIS tooling (geopandas, gdal) |
| **License** | "Indicative purposes only" — Legal ambiguity for production use |
| **RAG Suitable** | ❌ NO — Spatial rasters, not text corpus |

> [!CAUTION]
> Bhuvan explicitly states data is "for visualization and indicative purposes only." Do NOT use it as an authoritative source for coordinates or monument boundaries in a production system without explicit ASI clearance.

---

#### 🟢 Source 8: Internet Archive / Digital Library of India

| Attribute | Detail |
|---|---|
| **Data Type** | Digitized books, manuscripts, historical texts, old travel writing about Indian sites |
| **API Access** | ✅ Yes — Internet Archive API: `https://archive.org/advancedsearch.php` |
| **Authentication** | None for search; S3-like API for downloads |
| **Rate Limits** | Generous; 1 req/sec recommended |
| **Data Quality** | ⭐⭐⭐ 3/5 — High quality for historical depth; variable OCR quality |
| **Integration Ease** | ⭐⭐⭐⭐ 4/5 — `internetarchive` Python library |
| **License** | Mostly Public Domain / CC for pre-1927 works |
| **RAG Suitable** | ✅ YES — Excellent for deep historical context; requires OCR cleaning |
| **Realistic Record Count** | Thousands of relevant books; select carefully |

**Use case**: Augment corpus with historical accounts (e.g., 19th century ASI reports, colonial-era gazetteers) for richer historical context in RAG responses.

---

#### 🟢 Source 9: Wikivoyage API

| Attribute | Detail |
|---|---|
| **Data Type** | Tourist-oriented descriptions, practical info, regional context |
| **API Access** | ✅ Yes — Same MediaWiki API infrastructure as Wikipedia |
| **Authentication** | None |
| **Rate Limits** | Same as Wikipedia |
| **Data Quality** | ⭐⭐⭐ 3/5 — Good practical context; not scholarly |
| **Integration Ease** | ⭐⭐⭐⭐⭐ 5/5 — Identical to Wikipedia API |
| **License** | CC BY-SA 3.0 |
| **RAG Suitable** | ✅ YES — Adds "visitor-friendly" voice to complement Wikipedia's encyclopedic tone |

---

#### 🟢 Source 10: Europeana API (Supplementary)

| Attribute | Detail |
|---|---|
| **Data Type** | European museum records about India (colonial-era art, objects, historical records) |
| **API Access** | ✅ Yes — `https://api.europeana.eu/record/v2/search.json` |
| **Authentication** | API key (free) |
| **Rate Limits** | 10,000 requests/day (free tier) |
| **Data Quality** | ⭐⭐⭐ 3/5 — Excellent for colonial-era records; India-specific coverage is niche |
| **Integration Ease** | ⭐⭐⭐⭐ 4/5 — Clean REST API, well-documented |
| **License** | CC BY / CC0 / In-Copyright (per item) — Must check per record |
| **RAG Suitable** | ⚠️ PARTIAL — Selective use; check license per object |

> [!NOTE]
> Recommended only for Phase 2+. The India-specific corpus here (Mughal-era art, colonial documents) can add unique depth but requires careful per-item license checking.

---

#### 🟢 Source 11: Wikispecies / GBIF (Natural Heritage Sites)

| Attribute | Detail |
|---|---|
| **Data Type** | Species data for natural heritage sites (Kaziranga, Sundarbans, etc.) |
| **API Access** | ✅ Yes — GBIF REST API: `https://api.gbif.org/v1/` |
| **Authentication** | None for read; account for downloads |
| **Rate Limits** | 100 req/min |
| **Data Quality** | ⭐⭐⭐⭐ 4/5 — Authoritative for biodiversity data |
| **Integration Ease** | ⭐⭐⭐⭐ 4/5 — Clean REST API |
| **License** | CC BY 4.0 |
| **RAG Suitable** | ✅ YES — For natural heritage sites only |

---

### 1.3 Source Priority Matrix

| Priority | Source | Effort | Value |
|---|---|---|---|
| **P0 (Must Have)** | Wikipedia API | Low | Highest |
| **P0 (Must Have)** | Wikidata SPARQL | Medium | Highest |
| **P0 (Must Have)** | UNESCO DataHub | Low | High (authoritative) |
| **P1 (High Value)** | Wikimedia Commons | Low | High (images) |
| **P1 (High Value)** | OSM Overpass | Low | High (geo) |
| **P1 (High Value)** | data.gov.in | Medium | Medium (coverage check) |
| **P2 (Nice to Have)** | Internet Archive | High | Medium (historical depth) |
| **P2 (Nice to Have)** | Wikivoyage | Low | Medium |
| **P3 (Later Phase)** | Europeana | Medium | Low-Medium |
| **P3 (Later Phase)** | GBIF | Low | Low (niche) |

---

## Section 2 — Unified Data Model

### 2.1 Heritage Site Schema (Canonical)

```python
{
  # === Identity ===
  "site_id": "echolore_taj_mahal_001",    # Stable internal UUID
  "wikidata_qid": "Q9141",                # Wikidata QID (primary dedup key)
  "wikipedia_title": "Taj Mahal",         # Wikipedia page title
  "osm_id": "relation/5835063",           # OSM reference
  "asi_id": "N-UP-A5",                    # ASI monument number (if available)
  "unesco_id": "252",                     # UNESCO WH site ID (if applicable)

  # === Core Fields ===
  "name": "Taj Mahal",
  "alternate_names": ["Tāj Mahal", "Crown of the Palace"],
  "description": "<long-form text>",       # Primary RAG corpus field (2000–8000 chars)
  "short_summary": "<200-char summary>",   # For UI cards

  # === Location ===
  "location": {
    "state": "Uttar Pradesh",
    "district": "Agra",
    "country": "India",
    "address": "Dharmapuri, Forest Colony, Tajganj, Agra, UP 282001"
  },
  "coordinates": {
    "lat": 27.1751,
    "lon": 78.0421,
    "geohash": "ttyy",
    "source": "wikidata"                   # Coordinate source for trust ranking
  },

  # === Classification ===
  "category": "Mausoleum",                 # Normalized type
  "category_tags": ["UNESCO", "Mughal", "Islamic architecture", "monument"],
  "heritage_status": {
    "is_unesco_whs": true,
    "is_asi_protected": true,
    "asi_type": "centrally_protected_monument",
    "heritage_designations": ["UNESCO World Heritage Site", "ASI-protected"]
  },

  # === History ===
  "historical_period": {
    "era": "Mughal",
    "start_year": 1632,
    "end_year": 1653,
    "certainty": "exact"                   # exact | approximate | unknown
  },
  "commissioned_by": "Shah Jahan",

  # === Assets ===
  "images": [
    {
      "url": "https://upload.wikimedia.org/...",
      "thumbnail_url": "...",
      "license": "CC BY-SA 4.0",
      "author": "Dhirad",
      "source": "wikimedia_commons",
      "commons_filename": "Taj_Mahal.jpg"
    }
  ],

  # === Sources & Citations ===
  "source_urls": {
    "wikipedia": "https://en.wikipedia.org/wiki/Taj_Mahal",
    "wikidata": "https://www.wikidata.org/entity/Q9141",
    "unesco": "https://whc.unesco.org/en/list/252/",
    "osm": "https://www.openstreetmap.org/relation/5835063"
  },
  "citations": ["Wikipedia: Taj Mahal", "UNESCO WH List #252"],

  # === Related Entities ===
  "related_entities": {
    "people": ["Shah Jahan", "Mumtaz Mahal", "Ustad Ahmad Lahori"],
    "locations": ["Agra Fort", "Fatehpur Sikri"],
    "events": ["Construction of Taj Mahal"],
    "topics": ["Mughal architecture", "Islamic art"]
  },

  # === RAG Metadata ===
  "rag_chunks": [],                         # Populated during ingestion
  "embedding_model": "text-embedding-3-small",
  "last_indexed": "2026-06-18T00:00:00Z",

  # === Ingestion Provenance ===
  "data_sources": ["wikipedia", "wikidata", "unesco", "osm"],
  "ingestion_version": "1.0",
  "created_at": "2026-06-18T00:00:00Z",
  "updated_at": "2026-06-18T00:00:00Z",
  "data_quality_score": 0.92               # Computed: % of fields filled
}
```

### 2.2 Source Mapping to Schema

| Schema Field | Primary Source | Fallback Source |
|---|---|---|
| `name` | Wikidata label | Wikipedia title |
| `description` | Wikipedia (full article) | Wikidata description |
| `short_summary` | Wikidata description | Wikipedia intro paragraph |
| `coordinates` | Wikidata P625 | OSM, then Wikipedia infobox |
| `state` | Wikidata P131 | Wikipedia infobox |
| `historical_period` | Wikidata P571/P580 | Wikipedia text (regex extract) |
| `category` | Wikidata P31 → normalized | Wikipedia categories |
| `is_unesco_whs` | UNESCO dataset (authoritative) | Wikidata P1435 |
| `asi_id` | data.gov.in CSV | Wikipedia infobox |
| `images` | Wikimedia Commons API | Wikipedia page images |
| `related_entities` | Wikidata linked entities | Wikipedia links |

### 2.3 Conflict Resolution Policy

```
Priority Ladder (highest wins):
  1. UNESCO DataHub — for WHS status, inscription year, criteria
  2. Wikidata       — for coordinates, classification, dates
  3. Wikipedia      — for names, descriptions, related entities
  4. OSM            — for coordinates ONLY (when P625 missing)
  5. data.gov.in    — for ASI classification ONLY
```

**Specific rules:**
- **Coordinates**: If Wikidata P625 disagrees with OSM by >500m, flag for manual review. Log discrepancy in `coordinate_conflict` field.
- **Names**: Store all variants in `alternate_names`; use Wikidata English label as canonical.
- **Dates**: Always store both raw value and certainty level. Prefer specific dates over century-level.
- **Missing Description**: If Wikipedia article is a stub (<500 chars), mark `description_quality: "stub"` and do NOT create RAG chunks from it. Use Wikidata description as fallback.

### 2.4 Missing Data Strategy

| Field | Action |
|---|---|
| No coordinates | Try OSM → try Wikipedia infobox regex → mark `coords_missing: true` |
| No Wikipedia article | Use Wikidata description only; mark for manual enrichment |
| No images | Proceed without; mark `has_images: false` |
| No dates | Store `historical_period.certainty: "unknown"` |
| Stub description (<500 chars) | Do NOT chunk; store as metadata-only record |

---

## Section 3 — Ingestion Pipeline Architecture

### 3.1 Full ETL Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                    │
│  Wikidata SPARQL  │  Wikipedia API  │  UNESCO CSV  │  OSM Overpass  │
│  Wikimedia Commons│  data.gov.in    │  Wikivoyage  │  Internet Arch │
└──────────┬────────┴────────┬────────┴──────┬───────┴────────┬───────┘
           │                 │               │                │
           ▼                 ▼               ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    EXTRACTION LAYER                                  │
│  - Python async extractors per source                               │
│  - Rate-limit aware (token bucket per source)                       │
│  - Retry logic (exponential backoff + jitter)                       │
│  - Raw output → local JSONL files (checkpointed)                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    NORMALIZATION LAYER                               │
│  - Schema mapping (source fields → canonical schema)                │
│  - Name normalization (Unicode NFKC, diacritics)                    │
│  - Coordinate validation (lat/lon sanity checks)                    │
│  - Date parsing (multiple formats → ISO 8601)                       │
│  - Category normalization (raw Wikidata P31 → site type enum)       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DEDUPLICATION LAYER                               │
│  - Primary key: Wikidata QID (canonical entity ID)                  │
│  - Secondary: (normalized_name, state) fuzzy match (RapidFuzz)      │
│  - Merge strategy: most-complete record wins; conflict logged        │
│  - Output: Deduplicated Pandas DataFrame → Parquet                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ENRICHMENT LAYER                                  │
│  - Cross-source field filling (e.g., add OSM coords if WD missing)  │
│  - Quality scoring (% fields populated → data_quality_score)        │
│  - Image URL resolution (Commons API)                               │
│  - Related entity graph construction                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CHUNKING & EMBEDDING LAYER                        │
│  Strategy: Hybrid Parent-Child Chunking                             │
│  - Parent chunk: Full Wikipedia description (~1000–3000 tokens)     │
│  - Child chunks: Semantic sections (300–500 tokens, 15% overlap)    │
│  - Metadata injected into every chunk (site_id, category, state)   │
│  - Filter: Skip sites with description_quality="stub"              │
│  - Embedding: sentence-transformers/paraphrase-multilingual-mpnet   │
│    (supports English + Hindi transliterations)                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       STORAGE LAYER                                   │
│                                                                       │
│  ┌─────────────────────┐    ┌────────────────────────────────────┐   │
│  │   PostgreSQL (SQL)   │    │   Qdrant (Vector DB)               │   │
│  │  - Master site table │    │  - Child chunk embeddings          │   │
│  │  - Full metadata     │    │  - Payload: site_id, chunk_index,  │   │
│  │  - Source tracking   │    │    state, category, period, source  │   │
│  │  - Update timestamps │    │  - Collections: "heritage_chunks"  │   │
│  │  PostGIS extension   │    │  - Filter-enabled retrieval        │   │
│  │  for geo queries     │    │                                    │   │
│  └─────────────────────┘    └────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 Chunking Strategy (Detailed)

**Recommended: Hierarchical Parent-Child with Semantic Sections**

```
Wikipedia Article → Strip boilerplate → Split by section headers
  └── Parent: Full "History" section (stored in PostgreSQL)
      └── Child 1: "Origins and Construction" (350 tokens → vector)
      └── Child 2: "Architecture" (400 tokens → vector)
      └── Child 3: "Decline and Restoration" (300 tokens → vector)

Each child chunk carries:
  - site_id, site_name, state, category, era
  - parent_section (e.g., "History")
  - chunk_index (for ordering)
  - source_url (for citation)
```

**Chunk Size Guidelines:**

| Content Type | Chunk Size | Strategy |
|---|---|---|
| Wikipedia section (historical narrative) | 400–600 tokens | Recursive character split with headers |
| Wikidata short description | Full text (50–200 tokens) | No chunking needed |
| Internet Archive historical text | 300–500 tokens | Semantic chunking |
| UNESCO criteria text | Full text (100–400 tokens) | No chunking |

**Overlap**: 15% overlap between consecutive chunks of the same article.

### 3.3 Embedding Strategy

**Recommended Model**: `paraphrase-multilingual-mpnet-base-v2` (sentence-transformers)
- Handles English + Hindi transliterations
- Free, self-hosted
- 768 dimensions
- Strong performance on cultural/historical text

**Alternative for later**: `text-embedding-3-small` (OpenAI) — higher quality, costs money.

**Embedding pipeline:**
```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

def embed_chunk(chunk_text: str, metadata: dict) -> dict:
    embedding = model.encode(chunk_text, normalize_embeddings=True)
    return {
        "vector": embedding.tolist(),
        "payload": {
            **metadata,
            "text": chunk_text
        }
    }
```

### 3.4 Vector Database Comparison

| Criterion | Chroma | Qdrant |
|---|---|---|
| **Architecture** | Embedded Python or server mode | Rust-based server (Docker) |
| **Setup Complexity** | `pip install chromadb` — zero config | Docker required |
| **Performance** | Good to 100K vectors | Excellent to 1B+ vectors |
| **Filtering** | Basic metadata filtering | Advanced payload filtering + hybrid search |
| **Persistence** | SQLite-backed | Optimized on-disk with WAL |
| **Horizontal Scale** | Single node | Distributed sharding |
| **Python SDK** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cost** | Free / Open Source | Free / Open Source |
| **Best For** | Rapid prototyping, MVP | Production-ready, scalability |

**Verdict for Echolore (Student Project):**
- **Phase 1–2 (Validation + MVP)**: Use **Chroma** — zero setup friction, perfect for iteration
- **Phase 3+ (If scaling)**: Migrate to **Qdrant** — better filtering by state/category/era

> [!IMPORTANT]
> With ~5,000–10,000 heritage sites and 3–5 chunks each = **25,000–50,000 vectors**. This is well within Chroma's range. Only switch to Qdrant if you need per-state or per-era filtering at scale.

### 3.5 Metadata Storage Decision

**Use PostgreSQL (with PostGIS)**

**Why NOT pure NoSQL:**
- Heritage site data is highly relational (sites ↔ people ↔ events ↔ locations)
- You need geospatial queries (`SELECT * WHERE point within 50km of [lat, lon]`)
- PostGIS provides native geospatial indexing

**Schema:**
```sql
-- Core table
CREATE TABLE heritage_sites (
    site_id UUID PRIMARY KEY,
    wikidata_qid VARCHAR(20) UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    short_summary TEXT,
    state VARCHAR(100),
    district VARCHAR(100),
    coordinates GEOGRAPHY(POINT, 4326),   -- PostGIS
    historical_period_start INT,
    historical_period_end INT,
    category VARCHAR(100),
    is_unesco_whs BOOLEAN DEFAULT FALSE,
    is_asi_protected BOOLEAN DEFAULT FALSE,
    data_quality_score FLOAT,
    data_sources TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Images table
CREATE TABLE site_images (
    id UUID PRIMARY KEY,
    site_id UUID REFERENCES heritage_sites(site_id),
    url TEXT NOT NULL,
    license VARCHAR(100),
    author TEXT,
    source VARCHAR(50)
);

-- Source tracking
CREATE TABLE ingestion_log (
    id UUID PRIMARY KEY,
    site_id UUID REFERENCES heritage_sites(site_id),
    source_name VARCHAR(50),
    raw_data JSONB,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 3.6 Update Strategy

| Scenario | Strategy |
|---|---|
| Initial build | Full batch ingest (all sources, ~1–2 days) |
| Wikidata updates | Weekly incremental via SPARQL `wdt:P813` (last retrieved) |
| Wikipedia updates | Weekly `prop=revisions` check for changed articles |
| UNESCO updates | Annual (list is stable) |
| OSM changes | Monthly OSM planet diff download |
| New site discovered | Trigger-based: add QID → re-run enrichment pipeline for that record |

---

## Section 4 — Feasibility Verdict

### VERDICT: ✅ FEASIBLE WITH SCOPE REDUCTION

**Justification by dimension:**

| Dimension | Assessment |
|---|---|
| **Data Availability** | ✅ STRONG — Wikimedia ecosystem provides 3,000–5,000+ quality records with descriptions, coordinates, and images. UNESCO provides 42 authoritative anchors. |
| **API Reliability** | ✅ STRONG — Wikipedia, Wikidata, and UNESCO are production-grade APIs maintained by major organizations. OSM Overpass is reliable for bulk queries. |
| **Legal Risk** | ✅ LOW — CC BY-SA 4.0 and CC0 dominate. Attribution is required but straightforward. No IP risk from primary sources. |
| **Engineering Complexity** | ⚠️ MODERATE — ETL pipeline, deduplication, chunking, embedding, and dual-database setup requires ~4–6 weeks of focused work for a student team of 2–3. |
| **Government Data** | ⚠️ WEAK — ASI has no API. data.gov.in datasets are stale CSVs. Use only as a supplementary coverage checklist. **Do NOT build any core feature on government APIs.** |

**Required scope reductions:**
1. ❌ Drop ISRO Bhuvan (legal ambiguity + low value)
2. ❌ Drop Europeana for Phase 1 (adds complexity, marginal value)
3. ❌ Do NOT attempt to scrape ASI website (fragile, no permission)
4. ✅ Target 2,000–3,500 records for MVP (not the full 3,693 ASI list)

---

## Section 5 — Implementation Roadmap

### Phase 1: Data Validation Scripts (Week 1–2)

**Goal**: Prove each API works, measure actual record counts, assess quality.

**Tasks:**
- [ ] Write Wikidata SPARQL validation script → export CSV of all Indian heritage entities
- [ ] Write Wikipedia batch fetch test (100 random articles from category) → measure avg. article length, stub rate
- [ ] Download UNESCO full dataset → count Indian sites, check field completeness
- [ ] Write OSM Overpass test query → count heritage nodes, compare with Wikidata
- [ ] Write data.gov.in fetcher → download ASI monument CSV → compare with Wikidata list

**Tools:**
```
Python 3.11+
requests, httpx (async)
SPARQLWrapper, wikipediaapi
overpy (OSM)
pandas, polars (data processing)
pytest (validation assertions)
```

**Deliverable**: `data_validation_report.md` — confirmed record counts, field coverage %, stub rates per source.

**Risk**: Wikidata SPARQL timeout on large queries — use pagination with `OFFSET` or filter by state.

**Time Estimate**: 10–14 days for 2 engineers.

---

### Phase 2: Dataset Building (Week 3–6)

**Goal**: Build the canonical heritage site database with 2,000–4,000 enriched records.

**Tasks:**
- [ ] Build async extraction pipeline (Wikidata → Wikipedia → Commons → OSM)
- [ ] Implement deduplication using Wikidata QID as primary key
- [ ] Implement conflict resolution policy (priority ladder)
- [ ] Build quality scoring function
- [ ] Store enriched records in PostgreSQL (PostGIS)
- [ ] Run full ingestion for all 28 Indian states + UTs
- [ ] Generate quality report: how many records have full description, coords, images?

**Tools:**
```
Python 3.11+, asyncio, aiohttp
SQLAlchemy + asyncpg (PostgreSQL async ORM)
PostGIS (via psycopg2)
RapidFuzz (fuzzy deduplication)
pydantic (schema validation)
Apache Airflow OR Prefect (pipeline orchestration)
```

**Realistic Record Targets:**
- Wikidata extraction: 5,000–8,000 raw entities
- After dedup: ~4,000–5,000 unique sites
- With full Wikipedia description (non-stub): ~2,500–3,500
- With coordinates: ~3,000–4,000
- With at least 1 image: ~2,000–3,000

**Risk**: Wikipedia API rate limits slow bulk fetching. Mitigation: cache responses locally, use async with max 3 concurrent requests, run over 48–72 hours.

**Time Estimate**: 3–4 weeks for 2 engineers (most of the work is debugging edge cases).

---

### Phase 3: RAG Pipeline Setup (Week 7–9)

**Goal**: Build and test the RAG system: chunking → embedding → vector storage → retrieval.

**Tasks:**
- [ ] Implement hierarchical chunker (section-aware, 400–600 token chunks)
- [ ] Implement embedding pipeline (sentence-transformers, batch processing)
- [ ] Set up Chroma (Phase 3) → populate with all chunks
- [ ] Build retriever: semantic search + metadata filtering (state, category, era)
- [ ] Implement cross-encoder reranker for result quality
- [ ] Build citation assembler (chunk → source URL → formatted citation)
- [ ] Evaluate RAG quality: write 50 "golden questions" → measure recall@5

**Tools:**
```
LangChain OR LlamaIndex (RAG orchestration)
sentence-transformers (embedding)
chromadb (vector store for Phase 3)
cross-encoders/ms-marco (reranker)
Gemini 1.5 Flash or Llama 3.1 (LLM)
RAGAS (RAG evaluation framework)
```

**Golden Questions to Test:**
1. "What is the architectural style of the Brihadeeswarar Temple?"
2. "When was the Qutb Minar built and by whom?"
3. "How many UNESCO World Heritage Sites are in Rajasthan?"
4. "What dynasty built the Hampi monuments?"

**Risk**: Embedding quality for transliterated Hindi names (Taj Mahal vs. Tāj Mahal). Mitigation: store alternate names in payload; expand queries at retrieval time.

**Time Estimate**: 2–3 weeks.

---

### Phase 4: API Backend Integration (Week 10–12)

**Goal**: Build a production-grade API backend that serves RAG results to the frontend.

**Tasks:**
- [ ] Build FastAPI application with:
  - `GET /sites` — list sites with filters (state, category, era, is_unesco)
  - `GET /sites/{site_id}` — full site detail
  - `POST /query` — RAG question answering with citations
  - `GET /sites/nearby` — geospatial query (lat, lon, radius_km)
  - `GET /sites/search` — full-text + semantic search
- [ ] Connect FastAPI to PostgreSQL (SQLAlchemy async)
- [ ] Connect FastAPI to Chroma/Qdrant
- [ ] Add response caching (Redis) for frequent queries
- [ ] Add rate limiting (slowapi)
- [ ] Write API tests (pytest + httpx)

**Tools:**
```
FastAPI + Uvicorn
SQLAlchemy 2.0 (async)
asyncpg
Redis (caching)
slowapi (rate limiting)
pytest + httpx (testing)
docker-compose (local orchestration)
```

**Endpoints (MVP):**
```
POST /api/v1/query
  Body: { "question": "...", "filters": { "state": "Rajasthan" } }
  Response: { "answer": "...", "sources": [...], "sites": [...] }

GET /api/v1/sites?state=Rajasthan&category=fort&limit=20&offset=0

GET /api/v1/sites/{site_id}

GET /api/v1/sites/nearby?lat=27.17&lon=78.04&radius_km=50
```

**Risk**: RAG latency (embedding + vector search + LLM) may exceed 3 seconds. Mitigation: cache frequent queries in Redis with 1-hour TTL.

**Time Estimate**: 2–3 weeks.

---

### Phase 5: Frontend + Map Integration (Week 13–15)

**Goal**: Connect the backend to the frontend (Echolore UI).

**Tasks:**
- [ ] Integrate `GET /query` endpoint into chat interface
- [ ] Build site detail pages (metadata + images + RAG-powered Q&A)
- [ ] Integrate map view using Leaflet.js + OSM tiles (free)
- [ ] Add state-based filtering UI
- [ ] Add citation display in answers
- [ ] Performance testing: ensure API responds in < 3s for 95th percentile

**Tools:**
```
Leaflet.js (maps — free, OSM tiles)
Axios/Fetch (API calls)
```

> [!NOTE]
> No AR/VR, no 3D visualization, no paid map APIs (Google Maps). Leaflet + OSM tiles is entirely free and sufficient for a heritage map.

**Time Estimate**: 2–3 weeks.

---

## Summary Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Wikipedia rate limiting stalls ingestion | High | Medium | Proper User-Agent, async 3-concurrent, 72hr window |
| Wikidata SPARQL timeout on large queries | Medium | Medium | Paginate by state, use OFFSET, cache results |
| High stub rate for minor ASI monuments | High | Medium | Accept lower coverage; focus on quality over quantity |
| Government data (data.gov.in) is stale | High | Low | Treat as secondary; Wikidata is primary |
| Deduplication misses near-duplicate records | Medium | Medium | Use QID as primary key; fuzzy match as secondary |
| LLM hallucination in RAG answers | Medium | High | Strict citation-grounded prompting; RAGAS evaluation |
| Embedding quality for regional names | Low | Medium | Store alternate names; test transliteration edge cases |

---

## Technology Stack Summary

| Layer | Technology | Justification |
|---|---|---|
| Language | Python 3.11+ | Best ecosystem for data + ML |
| Async HTTP | `aiohttp` / `httpx` | Concurrent API extraction |
| Data Processing | `pandas` / `polars` | ETL transformations |
| Schema Validation | `pydantic` v2 | Type-safe data models |
| Relational DB | PostgreSQL + PostGIS | Metadata + geospatial queries |
| Vector DB (MVP) | Chroma | Zero-config, fast iteration |
| Vector DB (Prod) | Qdrant | Scalable, advanced filtering |
| Orchestration | Prefect (simpler) or Airflow | Pipeline scheduling + monitoring |
| Embedding | sentence-transformers | Free, self-hosted, multilingual |
| RAG Framework | LangChain or LlamaIndex | Proven RAG tooling |
| LLM | Gemini 1.5 Flash | Cost-effective, fast |
| API Backend | FastAPI + Uvicorn | Modern async Python API |
| Caching | Redis | Query result caching |
| Frontend Map | Leaflet.js + OSM tiles | Free, no API key needed |
| Containerization | Docker + docker-compose | Reproducible deployment |

---

*Document version: 1.0 | Prepared for: Echolore Student Project | Phase: Data Validation + Pipeline Design*
