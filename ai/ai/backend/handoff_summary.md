# Arkana — Engineering Handoff Summary

> **Phase 1 Status: COMPLETE (June 2026).**
> All four active data sources (Wikidata, Wikipedia, UNESCO, OSM) are validated and production-ready.
> **Phase 2 Status: ~80% COMPLETE (July 2026).**
> `pipeline.py` implemented and executed (3,826 canonical records). `loader.py` implemented and dry-run validated (0 mapping errors). Real PostgreSQL load blocked by Docker Desktop failure during previous session.
> data.gov.in has been investigated and **formally deprioritised**. Do not re-open this decision.

This document provides a comprehensive engineering overview of the current state of the Arkana project.
It enables the next developer or AI agent to resume development immediately with complete context,
without re-investigating completed decisions or re-validating completed work.

---

## 1. Overall Architecture

Arkana is an AI-powered RAG platform for exploring India's history, monuments, and heritage. The ingestion pipeline works in two distinct phases:

**Phase 1: Data Extraction & Validation**
1. **Extractors** query external APIs (Wikidata, Wikipedia, UNESCO, OSM, data.gov.in).
2. Data is dumped as raw `JSONL` files into `data/raw/` to serve as resilient checkpoints.
3. `validate.py` runs health checks on the raw checkpoints to ensure data quality before ETL begins.

**Phase 2: ETL & RAG Prep — Infrastructure Implemented, Pipeline Not Yet Run**

All Phase 2 transformer modules are **fully implemented** with production-quality logic:
1. **Normalizer** (`normalizer.py`): Cleans text (Unicode NFKC), validates coordinates, parses dates (ISO 8601 + BCE), infers categories from name/description keywords, cleans Wikipedia citation markers.
2. **Deduplicator** (`deduplicator.py`): Two-tier deduplication. Tier 1 uses Wikidata QID (exact match). Tier 2 uses `rapidfuzz` (fuzzy name + state match, threshold 90). Winner is based on a computed `data_quality_score`. Merge log written to `data/raw/dedup_log.jsonl`.
3. **Enricher** (`enricher.py`): Cross-pollinates records. Fills missing coordinates from OSM (QID lookup first, name fallback). Upgrades short descriptions with Wikipedia full text. Computes geohashes. Infers categories. Extracts related entities from Wikipedia article links/categories.
4. **Chunker** (`chunker.py`): Section-aware parent-child chunking. Lead + named sections split into overlapping 500-token windows. Boilerplate sections (References, See Also, etc.) removed.
5. **PostgreSQL Schema** (`docker/postgres/init.sql`): Full schema with PostGIS geography columns, FTS index, GiST spatial index, and update timestamp triggers.

**What is not yet done for Phase 2:** No `pipeline.py` orchestrator to wire these modules together. No full 31-state Wikidata extraction run. No ChromaDB embedding run.

---

## 2. Current Pipeline Status

The validated state of Phase 1 extraction (June 2026):

| Source | Final Status | Validated Output |
|---|---|---|
| **Wikidata** | ✅ **COMPLETE** | ~3,785 records / 3 sample states. Estimated ~37k nationwide. QID root cause fixed (Q1437 Rajasthan, Q1180 J&K, Q200667 Ladakh). |
| **Wikipedia** | ✅ **COMPLETE** | ~55 articles, 0% stub rate, ~2,200 avg words, 100% Wikidata QID linkage. |
| **UNESCO** | ✅ **COMPLETE** | Official UNESCO Open Data API. 44 records (37 cultural, 7 natural). All have coordinates + inscription year. Three-tier fallback implemented. Raw cache: `india_whs_api_raw.json`. |
| **OSM** | ✅ **COMPLETE (with caveat)** | Checkpoint fallback for transient Overpass 504s. ~200–500 nodes (Rajasthan sample). |
| **data.gov.in** | 🚫 **DEPRIORITISED (June 2026)** | Bounded investigation of ~17 datasets confirmed: name+district only, no coordinates/descriptions. API broken (HTTP 403). Wikidata already covers ASI status. ~4 days cost for negligible benefit. **Do not integrate.** See §data.gov.in Final Investigation Findings. |

*(Note: Run `python -m ingestion.validate` to regenerate fresh numbers. Checkpoint fallback ensures reproducibility.)*

---

## 3. Correct Root Cause Analysis (Wikidata)

Previous debugging incorrectly assumed Wikidata query complexity was the issue causing zero records for certain states. The actual root cause was incorrect Wikidata entity IDs inside `config.py`.

**Old QIDs:**
* Rajasthan -> `Q1145` (Jean-Philippe Rameau)
* Jammu & Kashmir -> `Q43100` (Incorrect generic entity)
* Ladakh -> `Q51529` (Soviet satellite)

**The Fix:** Correct state entities were substituted (Rajasthan to `Q1437`, J&K to `Q1180`, Ladakh to `Q200667`). Once the correct QIDs were used, Rajasthan immediately returned ~529 records. This confirms the SPARQL query itself was functioning perfectly.

### Wikidata Lessons Learned
* **Never assume a QID is correct.**
* **Always verify a QID manually through SPARQL before debugging queries.**
* **Administrative hierarchy (`P131`) is reliable.**
* **QIDs are the primary deduplication key throughout the pipeline.**
* **Query optimisation should happen only after validating the data itself.**

---

## 4. Architectural Decisions on External APIs

### UNESCO Decision (Updated: v3 Extractor — Official API as Primary)
The production extractor now targets the official UNESCO Open Data API as the **primary** data source.

**Base endpoint:**
`https://data.unesco.org/api/explore/v2.1/catalog/datasets/whc001/records`

**India filter (ODSQL):**
`where=states_names="India"`

**Verified live results (June 2026):**
* API reachable: ✓
* HTTP 200 returned: ✓
* Total India records (`total_count`): **44** (includes transboundary sites where India is a states party)
* Cultural sites: 37 | Natural sites: 7
* All 44 records have inscription year
* Coordinates: **44/44** (all records have coordinates)
* Descriptions (>50 chars): **44/44**
* Wikidata QIDs: **0** — expected at this stage; QIDs will be cross-referenced and added during Phase 2 enrichment via `enricher.py`
* Transboundary sites: **1** (Le Corbusier — India + 6 other countries)

**Verified field names (from live API):**

| API Field | Description | Example |
|---|---|---|
| `name_en` | Site name in English | `"Taj Mahal"` |
| `states_names` | Array of country names | `["India"]` or `["India", "Japan", ...]` |
| `id_no` | UNESCO site ID | `"252"` |
| `date_inscribed` | Inscription year (string) | `"1983"` |
| `criteria_txt` | Heritage criteria | `"(i)(ii)(iii)(vi)"` |
| `category` | Site category | `"Cultural"` or `"Natural"` |
| `coordinates` | `{"lat": float, "lon": float}` | `{"lat": 27.17, "lon": 78.04}` |
| `short_description_en` | English description | Long text |
| `transboundary` | Transboundary flag | `"True"` or `"False"` |

**Important correction:**
The correct field name is `states_names` (an **array**), NOT `states_name_en`. The previous v2 extractor never actually queried this field because it used Wikidata SPARQL as its primary source.

**Three-tier fallback strategy (v3):**
1. **Primary:** Official UNESCO Open Data API — downloads all India records in one paginated call.
2. **Secondary:** Wikidata SPARQL — queries for items with heritage designation P1435 = Q9259.
3. **Emergency:** Hardcoded `INDIA_UNESCO_SITES` list (42 sites, all with QIDs and coordinates).

**Local cache:**
Raw API response is saved to `data/raw/unesco/india_whs_api_raw.json` on every successful download. This serves as the permanent checkpoint.

**Why the legacy `whc.unesco.org` endpoint is no longer used:**
The legacy endpoint (`https://whc.unesco.org/en/list/?output=json`) returned HTTP 403 (Cloudflare-blocked) and was never a documented public REST API. The official Open Data portal is the correct, stable, and supported alternative.

**Future strategy:**
Refresh the local cache every 6 months. ETL and RAG query only the local JSONL checkpoint — never the live API during user queries.

Hardcoded UNESCO fallback should remain only as an emergency backup.

### OSM Decision
OSM is **enrichment only**. It is NOT authoritative. It is used only for:
* Additional coordinates
* Missing geometry
* Map visualization
Public Overpass servers frequently timeout. Checkpoints should always be preserved, and mirror fallback exists. No further optimisation needed unless extraction quality drops.

### data.gov.in Decision — FINAL (June 2026)

After completing a bounded manual investigation (see §Data.gov.in — Final Investigation Findings
below), data.gov.in is **permanently deprioritised**.

**Summary:** All monument datasets contain only name + district. No coordinates, descriptions,
or structured metadata. All known API resource IDs return HTTP 403/400. The ASI protection status
(the only unique data point) is already covered by Wikidata P1435.

**Do not re-open this investigation** without a strong justification grounded in new evidence.
The architectural decision is frozen. The extractor is retained as a graceful-skip fallback.

### Data.gov.in — Final Investigation Findings (June 2026)

A bounded manual investigation was completed (June 24, 2026) covering ~17 datasets across 6 keyword searches and direct API probing.

**Datasets inspected included:**
* Centrally protected monuments and sites under ASI, by state (Punjab, West Bengal, MP, Rajasthan, UP, TN, etc.) — sourced from Rajya Sabha parliamentary answers
* Number of CPM sites per state (aggregate counts only)
* Visitor statistics for ticketed ASI monuments
* Conservation expenditure on monuments
* Parliamentary Q&A on ASI monument status

**Key findings:**
* All state-wise CPM lists contain only: `S.No.`, `Name of Monument/Sites`, `Location` (free text), `District`. **No coordinates, no descriptions, no categories, no years, no Wikidata QIDs.**
* All datasets are from parliamentary annexures (2015–2021). No live database.
* All 10 seed resource IDs confirmed stale (HTTP 403/400).
* data.gov.in search engine is unreliable — "List of Centrally Protected Monuments" returns Pincode Directory as top result.
* The only unique data point (ASI protection status) is already captured in Wikidata via P1435.
* No coordinates, descriptions, or rich monument metadata exist on data.gov.in that would improve RAG quality.

**Decision:** data.gov.in is **deprioritized**. Do not integrate into Phase 1. Revisit only after MVP if Wikidata ASI coverage proves insufficient for minor sites.

**Estimated integration cost vs. benefit:** ~4 days engineering effort for negligible RAG quality improvement. Not justified.

### data.gov.in Discovery Tool (Built — June 2026)

**File:** `ingestion/extractors/datagov_discovery.py`

**Two-phase approach:**
1. **Phase A (Seed probe):** Probes a curated list of known resource IDs via `api.data.gov.in/resource/{id}`. Returns JSON with `total`, `field`, `records`.
2. **Phase B (HTML search):** Fetches `data.gov.in/search?keyword=...` per keyword. **Constraint:** data.gov.in is a Nuxt.js SPA — static HTML contains no dataset links. Phase B returns nothing unless a headless browser is used.

**Critical engineering finding:** The `api.data.gov.in` datastore endpoint is the correct API. All 10 curated seed resource IDs returned `"Meta not found"` — they are stale. data.gov.in reassigns resource IDs when datasets are updated or re-uploaded. The only reliable way to obtain current IDs is to manually browse the site, navigate to a dataset's resource page, and copy the UUID from the URL.

**How to run:**
```
# Dry-run (no network calls)
python -m ingestion.extractors.datagov_discovery --dry-run

# Full run (50 datasets max, 80 requests max)
python -m ingestion.extractors.datagov_discovery --max-datasets 50 --max-requests 80

# Resume a previous run
python -m ingestion.extractors.datagov_discovery --resume
```

**Output files** (`data/raw/datagov/discovery/`):
- `discovery_raw.json` — full raw probe results for every resource ID
- `discovery_catalogue.json` — scored, ranked catalogue (machine-readable)
- `discovery_report.md` — human-readable ranked report

**Scoring rubric (0-100):**
- Title relevance to heritage / monuments: 0-25
- API accessible (HTTP 200 + data): 0-20
- Record count: 0-15
- Field quality (coords, names, descriptions): 0-20
- Provider credibility (ASI/MoC/NMA): 0-10
- Data recency: 0-10

**Tiers:** HIGH >= 60, MEDIUM 35-59, LOW 15-34, IRRELEVANT < 15

**First run results (June 2026):**
- Datasets probed: 10 (all from seed list)
- HIGH: 0 | MEDIUM: 0 | LOW: 9 | IRRELEVANT: 1
- Root cause: all resource IDs stale ("Meta not found")
- HTML search: 0 results (SPA rendering — expected)
- **Action required:** Browse data.gov.in manually for current resource IDs and add to `SEED_RESOURCE_IDS` in `datagov_discovery.py`, then rerun with `--resume`.

---

## 5. Data Persistence Strategy

During Phase 2, all successfully extracted API data will be downloaded once and stored permanently inside PostgreSQL.

Future RAG retrieval will operate entirely on the local database. External APIs are only required for:
* Initial population
* Scheduled refreshes
* Optional incremental updates

**The production system should never depend on live external APIs during user queries.**

---

## 6. Data Refresh Policy

Recommended policy for external API refreshes:
* **Wikipedia:** Refresh monthly
* **Wikidata:** Refresh monthly
* **UNESCO:** Refresh every 6 months
* **OSM:** Refresh when map enrichment is required
* **data.gov.in:** N/A — permanently deprioritised (see §4)

---

## 7. Current Bottlenecks

Phase 1 remaining tasks before proceeding to Phase 2:
1. ✅ **Final OSM validation complete.** Mirror fallback implemented. Checkpoints preserved.
2. ✅ **data.gov.in investigation complete.** Conclusion: **Deprioritized.** See "Final Investigation Findings" above. No integration needed before Phase 2.
3. ✅ **UNESCO extraction completed and validated.** (`india_whs_api_raw.json` created, all 44 records confirmed.)
4. ✅ **UNESCO validation completed.** (v3 extractor is production-ready, committed as root commit `da16edd`.)
5. ✅ **Extraction layer frozen.** Phase 1 is COMPLETE. Phase 2 may begin.

---

## 8. Phase 2 Roadmap

After Phase 1 freeze, the next work is to orchestrate and execute the transformation pipeline:
1. `normalizer.py`
2. `deduplicator.py`
3. `enricher.py`
4. PostgreSQL loading
5. Parquet generation
6. ChromaDB embeddings
7. FastAPI backend

---

## 9. Phase 1 — Completion Record (June 2026)

### UNESCO Extraction Layer — Production Ready

The UNESCO extraction layer is **production-ready** and Phase 1 is complete.

**What was completed across all Phase 1 sessions:**
- Official UNESCO Open Data API adopted as primary source (replaces deprecated legacy endpoint).
- Live API field names verified: `states_names`, `name_en`, `id_no`, `date_inscribed`, `criteria_txt`, `category`, `coordinates`.
- 44 India World Heritage records downloaded and validated end-to-end.
- Raw API response cached permanently at `data/raw/unesco/india_whs_api_raw.json`.
- Three-tier fallback strategy implemented and tested (API → Wikidata SPARQL → hardcoded list).
- Windows CP1252 Unicode arrow encoding bug fixed in logger calls.
- `validate.py` updated: expected count now dynamically set to 44 (API) or 42 (fallback).
- `.gitignore` created and `.env` removed from tracking (contains real API keys).
- data.gov.in formally investigated (~17 datasets, 6 keyword searches) and deprioritised.
- All Phase 1 documentation updated to reflect final state.

---

## 10. Important Rule For Future Agents

> **🚨 ENGINEERING NOTE: Verify Before Assuming Blockage**
> 
> Do not assume public APIs are broken until endpoints, schemas, authentication methods, and field names have been independently verified.
> 
> Once a source has been validated, prefer local snapshots and PostgreSQL caching over repeated network requests.

---

## 11. Files That Should Be Read First By The Next Developer or AI Agent

When starting Phase 2, read these files in order:
1. `handoff_summary.md` (This document).
2. `ingestion/config.py` — State QID mappings, rate limits, directory paths.
3. `ingestion/models/heritage_schema.py` — The `HeritageSite` Pydantic schema: the single source of truth for all record structure.
4. `ingestion/validate.py` — The health-check runner and data quality classification logic.
5. `ingestion/transformers/normalizer.py` — Full implementation of text/coord/date/category normalization.
6. `ingestion/transformers/deduplicator.py` — QID-exact + RapidFuzz two-tier deduplication with merge logic.
7. `ingestion/transformers/enricher.py` — OSM coord fill, Wikipedia description upgrade, geohash, related entities.
8. `ingestion/utils/chunker.py` — Section-aware parent-child text chunking for RAG embedding.
9. `ingestion/extractors/unesco_extractor.py` — v3 three-tier API strategy, field mapping, and cache logic.
10. `docker/postgres/init.sql` — Full PostgreSQL/PostGIS schema with indexes and triggers.

**Do NOT read:**
- `app/load.py` — An unrelated early experiment (PDF + FAISS). Not part of the Arkana pipeline.
- `data/raw/datagov/` — Excluded from git (gitignored). data.gov.in is deprioritised.
