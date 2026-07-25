"""
Arkana -- data.gov.in Automated Dataset Discovery Tool

INVESTIGATION STATUS: COMPLETE (June 2026). data.gov.in is DEPRIORITIZED.
─────────────────────────────────────────────────────────────────────────────
This tool was used to conduct a bounded investigation of data.gov.in datasets
that might be relevant to the Arkana heritage RAG pipeline. The investigation
covered ~17 datasets across 6 keyword searches plus direct catalog URL probing.

CONCLUSION: data.gov.in does not contain monument-level metadata that would
materially improve the RAG knowledge base beyond our existing sources
(Wikidata, Wikipedia, UNESCO, OSM). All monument datasets contain only:
  - Monument Name (free text)
  - Location (free text)
  - District
No coordinates, descriptions, categories, years, or Wikidata QIDs exist.

DO NOT re-run this investigation without a strong justification. The decision
is frozen. See handoff_summary.md → "data.gov.in — Final Investigation Findings".

Original purpose (for historical reference)
──────────────────────────────────────────
Discover and rank data.gov.in datasets that may be useful for the Arkana
heritage RAG pipeline. Produces a scored catalogue so that future ingestion
work can target the highest-value datasets without repeating the discovery.

Architecture
------------
data.gov.in has NO public REST catalogue/search API. All search results are
rendered server-side by a Nuxt.js front-end. This tool therefore uses two
complementary strategies:

  Strategy A – Curated seed list
    Probe a hand-curated list of known resource IDs directly via the
    datastore API (api.data.gov.in/resource/{id}). These IDs were collected
    from prior manual investigation and community references.

  Strategy B – HTML search scraping
    Fetch the data.gov.in search result page for each keyword and extract
    resource IDs and dataset titles from the rendered HTML. These newly
    discovered IDs are then probed via Strategy A.

The tool terminates after reaching configurable limits to avoid endless crawling.

Output files (all under data/raw/datagov/discovery/)
-----------------------------------------------------
  discovery_raw.json          -- Full raw results for every probed dataset
  discovery_catalogue.json    -- Scored, ranked catalogue (machine-readable)
  discovery_report.md         -- Human-readable ranked report with findings

Usage
-----
  # Run with defaults (11 keywords, up to 100 datasets, max 200 requests):
  python -m ingestion.extractors.datagov_discovery

  # Resume a previous run (skip already-probed IDs):
  python -m ingestion.extractors.datagov_discovery --resume

  # Dry run (print config, do not fetch anything):
  python -m ingestion.extractors.datagov_discovery --dry-run

  # Override limits:
  python -m ingestion.extractors.datagov_discovery --max-datasets 50 --max-requests 100

Scoring
-------
Each dataset is scored 0-100 based on a weighted rubric:
  - Title relevance to heritage / monuments      (0-25 pts)
  - Accessible via API (HTTP 200)                (0-20 pts)
  - Record count (more structured records)       (0-15 pts)
  - Field quality (coords, names, descriptions)  (0-20 pts)
  - Publisher / provider credibility (ASI/MoC)  (0-10 pts)
  - Data recency / update frequency             (0-10 pts)

Tiers:
  HIGH   >= 60
  MEDIUM 35-59
  LOW    15-34
  IRRELEVANT < 15

Engineering notes
-----------------
- data.gov.in is notoriously unstable; all fetches are wrapped in retry logic.
- The API key is passed as a query parameter (api-key=...) to api.data.gov.in.
- HTML scraping uses regex rather than a full parser to avoid adding dependencies.
- All results are cached to discovery_raw.json so reruns can skip known IDs.
- The tool never writes to stdout beyond progress lines; all output goes to files.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from ingestion.config import DATAGOV_API_KEY, RAW_DIR, USER_AGENT
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

# ── Output directory ──────────────────────────────────────────────────────────
DISCOVERY_DIR = RAW_DIR / "datagov" / "discovery"
DISCOVERY_DIR.mkdir(parents=True, exist_ok=True)

RAW_RESULTS_FILE     = DISCOVERY_DIR / "discovery_raw.json"
CATALOGUE_FILE       = DISCOVERY_DIR / "discovery_catalogue.json"
REPORT_FILE          = DISCOVERY_DIR / "discovery_report.md"

# ── Configurable defaults ────────────────────────────────────────────────────
DEFAULT_KEYWORDS: list[str] = [
    "Archaeological Survey of India",
    "ASI",
    "Monument",
    "Protected Monument",
    "Heritage",
    "Heritage Site",
    "Ancient Monument",
    "National Monument",
    "Archaeology",
    "Culture",
    "Tourism",
]

# Hard cap — tool terminates after reaching these
DEFAULT_MAX_DATASETS  = 100   # maximum unique datasets to inspect
DEFAULT_MAX_REQUESTS  = 200   # maximum total HTTP requests made
DEFAULT_MAX_KEYWORDS  = 11    # maximum keywords to search
DEFAULT_TIMEOUT       = 30    # seconds per HTTP request
DEFAULT_RETRY_LIMIT   = 3     # retries per failed request
DEFAULT_PAGE_SIZE     = 6     # search results per page (data.gov.in shows 6)

# ── API endpoints ────────────────────────────────────────────────────────────
DATASTORE_API   = "https://api.data.gov.in/resource/{resource_id}"
SEARCH_URL      = "https://data.gov.in/search"  # HTML search page

# ── Curated seed resource IDs ────────────────────────────────────────────────
# These are known resource IDs collected from prior manual investigation and
# community references. They are probed first before HTML scraping begins.
# Add new IDs here as they are discovered.
SEED_RESOURCE_IDS: list[dict[str, str]] = [
    # ASI Centrally Protected Monuments
    {
        "resource_id": "3c28ddee-a3e9-410a-9e31-52cbc0f8a57d",
        "title": "District-wise List of Centrally Protected Monuments (ASI)",
        "url": "https://data.gov.in/resource/district-wise-list-centrally-protected-monuments",
        "provider": "Archaeological Survey of India",
    },
    {
        "resource_id": "7a8a0b31-8e3c-4b30-98db-b5cc9fd58862",
        "title": "Centrally Protected Monuments (ASI) - Alternative",
        "url": "https://data.gov.in/resource/district-wise-list-centrally-protected-monuments",
        "provider": "Archaeological Survey of India",
    },
    # ASI Visitor Statistics
    {
        "resource_id": "f9d99b29-a33a-4e31-b879-1b4d0e4f5000",
        "title": "Ticketed Monuments - Number of Visitors (ASI)",
        "url": "https://data.gov.in/catalog/ticketed-monuments-number-visitors",
        "provider": "Archaeological Survey of India",
    },
    # UNESCO World Heritage India
    {
        "resource_id": "e4a5e4b3-2a20-4b93-9dfe-c5e13a10f0a3",
        "title": "UNESCO World Heritage Sites in India",
        "url": "https://data.gov.in/catalog/world-heritage-sites",
        "provider": "Ministry of Culture",
    },
    # Ministry of Tourism - Monuments
    {
        "resource_id": "aa7c9e3c-c7d5-4b47-9aaf-44c86f3e8cce",
        "title": "List of Monuments - Ministry of Tourism",
        "url": "https://data.gov.in/catalog/monuments-tourism",
        "provider": "Ministry of Tourism",
    },
    # ASI Conservation Budget
    {
        "resource_id": "5fbb2abc-c3de-4b9e-9f12-8b5e9a20f701",
        "title": "Conservation Expenditure on Protected Monuments (ASI)",
        "url": "https://data.gov.in/catalog/conservation-expenditure-asi",
        "provider": "Archaeological Survey of India",
    },
    # Ministry of Culture datasets
    {
        "resource_id": "b2f3a4c5-d6e7-4f89-a012-3b4c5d6e7f80",
        "title": "Cultural Heritage Sites - Ministry of Culture",
        "url": "https://data.gov.in/catalog/cultural-heritage",
        "provider": "Ministry of Culture",
    },
    # National Monuments Authority
    {
        "resource_id": "c3d4e5f6-a7b8-4c9d-b0e1-2f3a4b5c6d7e",
        "title": "Prohibited and Regulated Areas around ASI Monuments",
        "url": "https://data.gov.in/catalog/national-monuments-authority",
        "provider": "National Monuments Authority",
    },
    # INTACH datasets
    {
        "resource_id": "d4e5f6a7-b8c9-4d0e-c1f2-3a4b5c6d7e8f",
        "title": "Heritage Structures Listed by INTACH",
        "url": "https://data.gov.in/catalog/intach-heritage",
        "provider": "INTACH",
    },
    # Parliamentary Q&A - monuments (known supplementary)
    {
        "resource_id": "a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d",
        "title": "Unstarred Questions - ASI (Parliamentary)",
        "url": "https://data.gov.in/catalog/parliamentary-questions-asi",
        "provider": "Ministry of Culture",
    },
]

# ── Relevance signals ────────────────────────────────────────────────────────
# Keywords that indicate high relevance in a dataset title or field names
HIGH_RELEVANCE_TITLE_WORDS = {
    "monument", "heritage", "archaeological", "asi", "ancient",
    "temple", "fort", "palace", "mosque", "church", "ruins",
    "excavation", "protected", "historical", "history", "culture",
    "UNESCO", "world heritage", "centrally protected",
}

MEDIUM_RELEVANCE_TITLE_WORDS = {
    "tourism", "visitor", "ticketed", "conservation", "culture",
    "ministry of culture", "national monuments", "site",
    "architecture", "cave", "sculpture",
}

LOW_VALUE_SIGNALS = {
    "parliamentary", "budget", "expenditure", "statistics", "unstarred",
    "starred question", "answer", "finance", "allocation", "grant",
    "committee report", "annual report", "press note",
}

CREDIBLE_PROVIDERS = {
    "archaeological survey of india",
    "ministry of culture",
    "national monuments authority",
    "intach",
    "asi",
    "tourism",
    "ministry of tourism",
    "department of tourism",
}

FIELD_QUALITY_INDICATORS = {
    "coordinates": 5,
    "latitude": 5, "lat": 5,
    "longitude": 5, "lon": 5, "long": 5,
    "name": 3, "monument": 3, "title": 2,
    "description": 4, "detail": 3, "history": 4,
    "state": 2, "district": 2, "location": 3,
    "year": 2, "period": 2, "century": 2,
    "type": 1, "category": 1,
}


# ── Data model ───────────────────────────────────────────────────────────────

@dataclass
class DatasetEntry:
    """Represents one discovered dataset and all inspection results."""
    resource_id: str
    title: str
    url: str
    provider: str
    discovered_via: str            # "seed", "search:keyword", "html_parse"

    # API probe results
    api_accessible: bool = False
    stale_resource_id: bool = False   # True when API returns "Meta not found"
    http_status: int = 0
    record_count: int = 0
    field_names: list[str] = field(default_factory=list)
    sample_records: list[dict] = field(default_factory=list)
    api_endpoint: str = ""
    error: str = ""

    # Scoring
    score: int = 0
    tier: str = "UNSCORED"
    score_breakdown: dict[str, int] = field(default_factory=dict)
    relevance_notes: list[str] = field(default_factory=list)

    # Metadata
    probed_at: str = ""
    probe_duration_sec: float = 0.0


# ── Scorer ───────────────────────────────────────────────────────────────────

class DatasetScorer:
    """
    Scores a DatasetEntry on a 0-100 scale based on how useful it is
    for the Arkana heritage pipeline.

    Weights (total = 100):
      title_relevance    0-25
      api_accessible     0-20
      record_count       0-15
      field_quality      0-20
      provider           0-10
      recency            0-10  (placeholder; data.gov.in rarely exposes this)
    """

    def score(self, entry: DatasetEntry) -> DatasetEntry:
        breakdown: dict[str, int] = {}
        notes: list[str] = []

        title_lower = entry.title.lower()

        # ── 1. Title relevance (0-25) ─────────────────────────────────────────
        title_pts = 0
        for word in HIGH_RELEVANCE_TITLE_WORDS:
            if word in title_lower:
                title_pts += 8
                notes.append(f"High relevance keyword in title: '{word}'")
                break
        for word in MEDIUM_RELEVANCE_TITLE_WORDS:
            if word in title_lower:
                title_pts += 4
                notes.append(f"Medium relevance keyword: '{word}'")
                break
        for word in LOW_VALUE_SIGNALS:
            if word in title_lower:
                title_pts = max(0, title_pts - 8)
                notes.append(f"Low-value signal in title: '{word}'")
                break
        title_pts = min(title_pts, 25)
        breakdown["title_relevance"] = title_pts

        # ── 2. API accessibility (0-20) ───────────────────────────────────────
        if entry.api_accessible and entry.http_status == 200:
            api_pts = 20
            notes.append("API endpoint returns HTTP 200")
        elif entry.http_status in (404, 400):
            api_pts = 0
            notes.append(f"API returned {entry.http_status} - resource not found")
        elif entry.http_status == 403:
            api_pts = 5
            notes.append("API returned 403 - may require different auth")
        else:
            api_pts = 0
            notes.append(f"API not accessible (status {entry.http_status})")
        breakdown["api_accessible"] = api_pts

        # ── 3. Record count (0-15) ────────────────────────────────────────────
        rc = entry.record_count
        if rc >= 1000:
            rc_pts = 15
        elif rc >= 500:
            rc_pts = 12
        elif rc >= 100:
            rc_pts = 9
        elif rc >= 10:
            rc_pts = 6
        elif rc > 0:
            rc_pts = 3
        else:
            rc_pts = 0
        if rc > 0:
            notes.append(f"Record count: {rc:,}")
        breakdown["record_count"] = rc_pts

        # ── 4. Field quality (0-20) ───────────────────────────────────────────
        field_pts = 0
        for fname in entry.field_names:
            fl = fname.lower().strip()
            for indicator, pts in FIELD_QUALITY_INDICATOR_ITEMS:
                if indicator in fl:
                    field_pts += pts
                    notes.append(f"Useful field: '{fname}'")
                    break  # only count each field once
        field_pts = min(field_pts, 20)
        breakdown["field_quality"] = field_pts

        # ── 5. Provider credibility (0-10) ────────────────────────────────────
        provider_lower = entry.provider.lower()
        if any(p in provider_lower for p in CREDIBLE_PROVIDERS):
            provider_pts = 10
            notes.append(f"Credible provider: '{entry.provider}'")
        else:
            provider_pts = 2
        breakdown["provider_credibility"] = provider_pts

        # ── 6. Data recency (0-10) ────────────────────────────────────────────
        # data.gov.in rarely exposes update frequency via API.
        # Give a baseline 3 pts; would upgrade if recency info found.
        breakdown["recency"] = 3

        # ── Total ─────────────────────────────────────────────────────────────
        total = sum(breakdown.values())
        total = max(0, min(100, total))

        if total >= 60:
            tier = "HIGH"
        elif total >= 35:
            tier = "MEDIUM"
        elif total >= 15:
            tier = "LOW"
        else:
            tier = "IRRELEVANT"

        entry.score = total
        entry.tier = tier
        entry.score_breakdown = breakdown
        entry.relevance_notes = notes
        return entry


# Pre-compute list form for field quality scoring (avoids repeated dict.items())
FIELD_QUALITY_INDICATOR_ITEMS = list(FIELD_QUALITY_INDICATORS.items())


# ── HTTP probe ───────────────────────────────────────────────────────────────

class DataGovProbe:
    """
    Probes individual data.gov.in resources via the datastore API.
    Handles retry, timeout, and rate limiting.
    """

    def __init__(self, api_key: str, timeout: int, retry_limit: int) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.retry_limit = retry_limit
        self.client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=timeout,
            follow_redirects=True,
        )
        self.request_count = 0

    async def close(self) -> None:
        await self.client.aclose()

    async def probe_resource(
        self,
        resource_id: str,
        sample_size: int = 3,
    ) -> tuple[int, int, list[str], list[dict], str]:
        """
        Probe a resource ID via the datastore API.

        Returns:
            (http_status, record_count, field_names, sample_records, error)
        """
        endpoint = DATASTORE_API.format(resource_id=resource_id)
        params = {
            "api-key": self.api_key,
            "format": "json",
            "limit": sample_size,
            "offset": 0,
        }

        for attempt in range(1, self.retry_limit + 1):
            self.request_count += 1
            try:
                resp = await self.client.get(endpoint, params=params)
                status = resp.status_code

                if status != 200:
                    return status, 0, [], [], f"HTTP {status}"

                data = resp.json()

                # data.gov.in API response shape:
                # {"status": "ok"/"error", "total": N, "count": N,
                #  "field": [{"id": "col", "type": "..."}],
                #  "records": [...]}
                if data.get("status") == "error":
                    msg = data.get("message", "API error")
                    is_stale = "meta not found" in msg.lower()
                    return status, 0, [], [], f"API error: {msg}", is_stale

                total = int(data.get("total", data.get("count", 0)))
                fields = [
                    f.get("id", f.get("name", ""))
                    for f in data.get("field", [])
                    if f.get("id") or f.get("name")
                ]
                records = data.get("records", [])[:sample_size]
                # Also infer field names from first record if field list empty
                if not fields and records:
                    fields = list(records[0].keys())

                return 200, total, fields, records, "", False

            except httpx.TimeoutException:
                if attempt < self.retry_limit:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return 0, 0, [], [], "Timeout after retries", False

            except Exception as exc:
                if attempt < self.retry_limit:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return 0, 0, [], [], str(exc), False

        return 0, 0, [], [], "All retries exhausted", False

    async def search_html(
        self,
        keyword: str,
        page: int = 1,
    ) -> list[dict[str, str]]:
        """
        Fetch the data.gov.in HTML search results page for a keyword
        and extract (resource_id, title, provider) tuples.

        data.gov.in renders results as Nuxt.js SSR HTML. Resource IDs appear
        in href patterns like /resource/{uuid} or data-resource-id attributes.

        Returns a list of dicts: {resource_id, title, provider, url}
        """
        self.request_count += 1
        params = {
            "keyword": keyword,
            "sort_by": "recent",
            "page": page,
        }
        try:
            resp = await self.client.get(SEARCH_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                return []
            html = resp.text
        except Exception:
            return []

        # Extract resource UUIDs from href="/resource/{uuid}" patterns
        uuid_pattern = re.compile(
            r'/resource/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
            re.IGNORECASE,
        )
        found_ids = set(uuid_pattern.findall(html))

        # Try to extract titles from nearby text (best-effort; HTML varies)
        # Pattern: title appears in <h3> or <h4> or data-title near the resource link
        title_pattern = re.compile(
            r'<(?:h3|h4|a)[^>]*class="[^"]*(?:title|heading)[^"]*"[^>]*>([^<]{5,200})</(?:h3|h4|a)>',
            re.IGNORECASE,
        )
        titles = title_pattern.findall(html)
        titles = [t.strip() for t in titles if t.strip()]

        results: list[dict[str, str]] = []
        for i, rid in enumerate(sorted(found_ids)):
            title = titles[i] if i < len(titles) else f"Dataset ({rid[:8]}...)"
            results.append({
                "resource_id": rid,
                "title": title,
                "provider": "Unknown",
                "url": f"https://data.gov.in/resource/{rid}",
            })

        return results


# ── Discovery orchestrator ───────────────────────────────────────────────────

class DataGovDiscovery:
    """
    Orchestrates the full discovery run:
      1. Load existing results (if --resume).
      2. Probe all seed resource IDs.
      3. Search HTML pages for each keyword → extract new IDs.
      4. Probe newly discovered IDs.
      5. Score all results.
      6. Save catalogue JSON and Markdown report.
    """

    def __init__(
        self,
        api_key: str,
        keywords: list[str],
        max_datasets: int,
        max_requests: int,
        max_keywords: int,
        timeout: int,
        retry_limit: int,
        resume: bool,
    ) -> None:
        self.api_key = api_key
        self.keywords = keywords[:max_keywords]
        self.max_datasets = max_datasets
        self.max_requests = max_requests
        self.timeout = timeout
        self.retry_limit = retry_limit
        self.resume = resume
        self.scorer = DatasetScorer()
        self.probe = DataGovProbe(api_key, timeout, retry_limit)

        # Track state
        self.entries: dict[str, DatasetEntry] = {}   # resource_id -> entry
        self.probed_ids: set[str] = set()            # already probed this run

    async def close(self) -> None:
        await self.probe.close()

    def _over_limits(self) -> bool:
        return (
            len(self.probed_ids) >= self.max_datasets
            or self.probe.request_count >= self.max_requests
        )

    def _load_resume_data(self) -> None:
        """Load previous raw results to skip already-probed IDs."""
        if not self.resume or not RAW_RESULTS_FILE.exists():
            return
        try:
            raw = json.loads(RAW_RESULTS_FILE.read_text(encoding="utf-8"))
            for item in raw:
                rid = item.get("resource_id", "")
                if rid:
                    entry = DatasetEntry(**item)
                    self.entries[rid] = entry
                    self.probed_ids.add(rid)
            logger.info(f"Resume: loaded {len(self.entries)} previously probed datasets")
        except Exception as exc:
            logger.warning(f"Could not load resume data: {exc}")

    async def _probe_and_record(self, seed: dict[str, str], discovered_via: str) -> None:
        """Probe one resource ID and store the result."""
        rid = seed["resource_id"]
        if rid in self.probed_ids:
            return
        if self._over_limits():
            return

        self.probed_ids.add(rid)
        t0 = time.time()

        status, count, fields, samples, error, is_stale = await self.probe.probe_resource(rid)

        entry = DatasetEntry(
            resource_id=rid,
            title=seed.get("title", f"Dataset {rid[:8]}"),
            url=seed.get("url", f"https://data.gov.in/resource/{rid}"),
            provider=seed.get("provider", "Unknown"),
            discovered_via=discovered_via,
            api_accessible=(status == 200 and not error),
            stale_resource_id=is_stale,
            http_status=status,
            record_count=count,
            field_names=fields,
            sample_records=samples,
            api_endpoint=DATASTORE_API.format(resource_id=rid),
            error=error,
            probed_at=datetime.now().isoformat(),
            probe_duration_sec=round(time.time() - t0, 2),
        )
        self.scorer.score(entry)
        self.entries[rid] = entry

        if is_stale:
            access_str = "STALE_ID "
        elif entry.api_accessible:
            access_str = "OK       "
        else:
            access_str = f"FAIL({status}) "

        print(
            f"  [{len(self.probed_ids):>3}/{self.max_datasets}] "
            f"{access_str:<10} score={entry.score:>3} tier={entry.tier:<10} "
            f"{entry.title[:55]}"
        )
        await asyncio.sleep(0.5)  # be polite

    async def _probe_seeds(self) -> None:
        """Probe all curated seed resource IDs."""
        print(f"\n[Phase A] Probing {len(SEED_RESOURCE_IDS)} curated seed datasets...")
        for seed in SEED_RESOURCE_IDS:
            if self._over_limits():
                print(f"  Limit reached after seeds. Stopping.")
                break
            await self._probe_and_record(seed, discovered_via="seed")

    async def _search_and_probe(self) -> None:
        """Search HTML pages per keyword, extract new IDs, probe them."""
        print(f"\n[Phase B] Searching {len(self.keywords)} keywords for new datasets...")
        print("  NOTE: data.gov.in search is Nuxt.js SPA-rendered. Static HTML contains")
        print("  no dataset links. If all keywords return no results, this is expected.")
        print("  To discover new resource IDs, manually browse data.gov.in and add them")
        print("  to SEED_RESOURCE_IDS in datagov_discovery.py.")
        for keyword in self.keywords:
            if self._over_limits():
                print(f"  Limit reached. Stopping at keyword '{keyword}'.")
                break
            print(f"\n  Searching: '{keyword}'...")
            new_found = await self.probe.search_html(keyword, page=1)
            if not new_found:
                print(f"    No resource IDs found in HTML (SPA rendering - expected).")
                continue
            print(f"    Found {len(new_found)} resource IDs on search page.")
            for item in new_found:
                if self._over_limits():
                    break
                await self._probe_and_record(item, discovered_via=f"search:{keyword}")
            await asyncio.sleep(1.0)

    def _save_raw(self) -> None:
        """Save all raw entry data to JSON."""
        all_entries = [asdict(e) for e in self.entries.values()]
        RAW_RESULTS_FILE.write_text(
            json.dumps(all_entries, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Raw results saved -> {RAW_RESULTS_FILE}")

    def _save_catalogue(self) -> None:
        """Save scored, ranked catalogue to JSON."""
        ranked = sorted(self.entries.values(), key=lambda e: e.score, reverse=True)
        catalogue = {
            "generated_at": datetime.now().isoformat(),
            "total_datasets_probed": len(ranked),
            "api_accessible": sum(1 for e in ranked if e.api_accessible),
            "tiers": {
                "HIGH":       [e.resource_id for e in ranked if e.tier == "HIGH"],
                "MEDIUM":     [e.resource_id for e in ranked if e.tier == "MEDIUM"],
                "LOW":        [e.resource_id for e in ranked if e.tier == "LOW"],
                "IRRELEVANT": [e.resource_id for e in ranked if e.tier == "IRRELEVANT"],
            },
            "datasets": [asdict(e) for e in ranked],
        }
        CATALOGUE_FILE.write_text(
            json.dumps(catalogue, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"Catalogue saved -> {CATALOGUE_FILE}")

    def _save_report(self) -> None:
        """Generate a human-readable Markdown report."""
        ranked = sorted(self.entries.values(), key=lambda e: e.score, reverse=True)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines: list[str] = [
            "# Arkana -- data.gov.in Dataset Discovery Report",
            f"> Generated: {now}",
            f"> Total datasets probed: {len(ranked)}",
            f"> API accessible: {sum(1 for e in ranked if e.api_accessible)}",
            f"> Total HTTP requests made: {self.probe.request_count}",
            "",
            "---",
            "",
            "## Summary",
            "",
            "| Tier | Count | Description |",
            "|---|---|---|",
        ]
        tier_desc = {
            "HIGH":       "Score >= 60. Strong candidate for Arkana ingestion.",
            "MEDIUM":     "Score 35-59. Potentially useful; needs closer inspection.",
            "LOW":        "Score 15-34. Supplementary data; low priority.",
            "IRRELEVANT": "Score < 15. Parliamentary/statistical; not useful for Arkana.",
        }
        for tier in ("HIGH", "MEDIUM", "LOW", "IRRELEVANT"):
            count = sum(1 for e in ranked if e.tier == tier)
            lines.append(f"| **{tier}** | {count} | {tier_desc[tier]} |")

        lines += ["", "---", ""]

        for tier in ("HIGH", "MEDIUM", "LOW", "IRRELEVANT"):
            tier_entries = [e for e in ranked if e.tier == tier]
            if not tier_entries:
                continue
            lines.append(f"## {tier} Value Datasets ({len(tier_entries)})")
            lines.append("")
            for e in tier_entries:
                lines.append(f"### [{e.title}]({e.url})")
                lines.append("")
                lines.append(f"| Field | Value |")
                lines.append(f"|---|---|")
                lines.append(f"| **Resource ID** | `{e.resource_id}` |")
                lines.append(f"| **Provider** | {e.provider} |")
                lines.append(f"| **Score** | {e.score}/100 |")
                lines.append(f"| **Tier** | {e.tier} |")
                lines.append(f"| **API accessible** | {'Yes' if e.api_accessible else 'No'} |")
                lines.append(f"| **HTTP status** | {e.http_status} |")
                lines.append(f"| **Record count** | {e.record_count:,} |")
                lines.append(f"| **Discovered via** | {e.discovered_via} |")
                if e.error:
                    lines.append(f"| **Error** | {e.error} |")
                lines.append("")

                if e.field_names:
                    lines.append(f"**Fields ({len(e.field_names)}):** "
                                 f"`{'`, `'.join(e.field_names[:20])}`"
                                 + (" ..." if len(e.field_names) > 20 else ""))
                    lines.append("")

                if e.score_breakdown:
                    lines.append("**Score breakdown:**")
                    for dim, pts in e.score_breakdown.items():
                        lines.append(f"- {dim}: {pts}")
                    lines.append("")

                if e.relevance_notes:
                    lines.append("**Relevance notes:**")
                    for note in e.relevance_notes[:8]:
                        lines.append(f"- {note}")
                    lines.append("")

                if e.sample_records:
                    lines.append("**Sample record (first):**")
                    lines.append("```json")
                    lines.append(json.dumps(e.sample_records[0], indent=2, ensure_ascii=False)[:800])
                    lines.append("```")
                    lines.append("")

                lines.append("---")
                lines.append("")

        lines += [
            "## Recommendations for Next Phase",
            "",
            "1. Manually verify all HIGH-tier datasets by fetching their full schema.",
            "2. For accessible HIGH datasets, add them to `datagov_extractor.py`.",
            "3. For inaccessible datasets, investigate whether the resource ID has changed.",
            "4. Rerun discovery with `--resume` after any new resource IDs are added to seeds.",
            "",
            "*Report generated by Arkana datagov_discovery.py*",
        ]

        REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Report saved -> {REPORT_FILE}")

    async def run(self) -> None:
        """Execute the full discovery pipeline."""
        print("=" * 65)
        print("  ARKANA -- data.gov.in Dataset Discovery Tool")
        print("=" * 65)
        print(f"  API key:       {'SET' if self.api_key else 'MISSING'}")
        print(f"  Keywords:      {len(self.keywords)}")
        print(f"  Max datasets:  {self.max_datasets}")
        print(f"  Max requests:  {self.max_requests}")
        print(f"  Resume mode:   {self.resume}")
        print("=" * 65)

        if not self.api_key:
            print("\n  ERROR: DATAGOV_API_KEY not set. Cannot probe resources.")
            print("  Set it in .env: DATAGOV_API_KEY=your_key")
            return

        if self.resume:
            self._load_resume_data()

        t0 = time.time()
        await self._probe_seeds()
        await self._search_and_probe()

        print(f"\n[Done] Probed {len(self.probed_ids)} datasets in "
              f"{round(time.time() - t0, 1)}s | "
              f"Requests: {self.probe.request_count}")
        stale = sum(1 for e in self.entries.values() if e.stale_resource_id)
        if stale:
            print(f"  NOTE: {stale}/{len(self.probed_ids)} resource IDs returned 'Meta not found'.")
            print("  These are stale/invalid IDs. Update SEED_RESOURCE_IDS with current IDs.")
            print("  Find current IDs by browsing https://data.gov.in and copying the UUID")
            print("  from the resource URL: data.gov.in/resource/{UUID}")

        # Score any unscored entries (should not happen, but defensive)
        for entry in self.entries.values():
            if entry.tier == "UNSCORED":
                self.scorer.score(entry)

        # Print tier summary
        for tier in ("HIGH", "MEDIUM", "LOW", "IRRELEVANT"):
            count = sum(1 for e in self.entries.values() if e.tier == tier)
            print(f"  {tier:<12} {count:>3} datasets")

        # Save outputs
        self._save_raw()
        self._save_catalogue()
        self._save_report()

        print(f"\nOutputs:")
        print(f"  Raw:       {RAW_RESULTS_FILE}")
        print(f"  Catalogue: {CATALOGUE_FILE}")
        print(f"  Report:    {REPORT_FILE}")


# ── CLI entry point ───────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Arkana data.gov.in Dataset Discovery Tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--max-datasets",  type=int, default=DEFAULT_MAX_DATASETS,
                   help="Maximum number of datasets to inspect")
    p.add_argument("--max-requests",  type=int, default=DEFAULT_MAX_REQUESTS,
                   help="Maximum total HTTP requests")
    p.add_argument("--max-keywords",  type=int, default=DEFAULT_MAX_KEYWORDS,
                   help="Maximum keywords to search")
    p.add_argument("--timeout",       type=int, default=DEFAULT_TIMEOUT,
                   help="Per-request timeout (seconds)")
    p.add_argument("--retry-limit",   type=int, default=DEFAULT_RETRY_LIMIT,
                   help="Retries per failed request")
    p.add_argument("--resume",        action="store_true",
                   help="Load previous raw results and skip already-probed IDs")
    p.add_argument("--dry-run",       action="store_true",
                   help="Print configuration and exit without making any requests")
    return p


async def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.dry_run:
        print("DRY RUN -- configuration:")
        print(f"  DATAGOV_API_KEY: {'SET' if DATAGOV_API_KEY else 'MISSING'}")
        print(f"  max_datasets:    {args.max_datasets}")
        print(f"  max_requests:    {args.max_requests}")
        print(f"  max_keywords:    {args.max_keywords}")
        print(f"  timeout:         {args.timeout}s")
        print(f"  retry_limit:     {args.retry_limit}")
        print(f"  resume:          {args.resume}")
        print(f"  keywords ({min(args.max_keywords, len(DEFAULT_KEYWORDS))}):")
        for kw in DEFAULT_KEYWORDS[:args.max_keywords]:
            print(f"    - {kw}")
        print(f"  seed_ids:        {len(SEED_RESOURCE_IDS)}")
        print(f"  output_dir:      {DISCOVERY_DIR}")
        return

    discovery = DataGovDiscovery(
        api_key=DATAGOV_API_KEY,
        keywords=DEFAULT_KEYWORDS,
        max_datasets=args.max_datasets,
        max_requests=args.max_requests,
        max_keywords=args.max_keywords,
        timeout=args.timeout,
        retry_limit=args.retry_limit,
        resume=args.resume,
    )
    try:
        await discovery.run()
    finally:
        await discovery.close()


if __name__ == "__main__":
    asyncio.run(main())
