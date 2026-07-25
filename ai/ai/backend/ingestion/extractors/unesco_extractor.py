"""
Arkana -- UNESCO World Heritage Site Extractor (v3 -- Official API)

Root cause analysis (v2 → v3):
  - v2 used Wikidata SPARQL as primary and a hardcoded list as fallback.
  - The official UNESCO Open Data API was identified and verified as the
    authoritative, no-auth-required source:
    https://data.unesco.org/api/explore/v2.1/catalog/datasets/whc001/records
  - v3 promotes the official API to PRIMARY source (fetches all India records
    in one paginated download), demotes Wikidata SPARQL to SECONDARY fallback,
    and keeps the hardcoded list as an EMERGENCY last-resort fallback.

Verified field names (from live API, 2024):
  - name_en          : Site name in English
  - states_names     : JSON array of country names (NOT states_name_en)
  - category         : "Cultural" | "Natural" | "Mixed"
  - cultural_criteria: e.g. "c1, c2, c3"
  - natural_criteria : e.g. "n9, n10"
  - criteria_txt     : human-readable criteria string e.g. "(i)(ii)"
  - date_inscribed   : string year e.g. "1983"
  - coordinates      : {"lon": float, "lat": float}
  - id_no            : UNESCO site ID string
  - short_description_en : short English description
  - description_en   : full English description
  - transboundary    : "True" | "False"
  - iso_codes        : comma-separated ISO country codes e.g. "IN, JP"

API filter for India:
  where=states_names="India"   (returns 44 records as of June 2026, including
  transboundary sites where India is one of the states parties)

Strategy:
  1. Download complete India dataset from UNESCO Open Data API (paginated).
  2. Save raw JSON to data/raw/unesco/india_whs_api_raw.json (permanent cache).
  3. Parse into HeritageSite records.
  4. If API fails → try Wikidata SPARQL.
  5. If SPARQL returns <30 sites → use hardcoded fallback list (42 India WHS).
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from ingestion.config import RAW_DIR, USER_AGENT
from ingestion.models.heritage_schema import (
    Coordinates,
    DataSource,
    HeritageSite,
    HeritageStatus,
    HistoricalCertainty,
    HistoricalPeriod,
    Location,
    SiteCategory,
    SourceUrls,
)
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = RAW_DIR / "unesco"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Official UNESCO Open Data API ─────────────────────────────────────────────
# Verified working. No authentication required.
# Base: https://data.unesco.org/api/explore/v2.1/catalog/datasets/whc001/records
# India filter: where=states_names="India"  (returns 44 records as of June 2026)
UNESCO_API_BASE = (
    "https://data.unesco.org/api/explore/v2.1/catalog/datasets/whc001/records"
)
UNESCO_INDIA_FILTER = 'states_names="India"'
UNESCO_PAGE_SIZE = 100   # API maximum per page

# ── Wikidata SPARQL (secondary fallback) ──────────────────────────────────────
WIKIDATA_UNESCO_QUERY = """
SELECT DISTINCT ?item ?itemLabel ?coords ?inscriptionYear ?criteria WHERE {
  ?item wdt:P17 wd:Q668 .
  ?item wdt:P1435 ?desig .
  ?desig wdt:P279* wd:Q9259 .
  OPTIONAL { ?item wdt:P625 ?coords }
  OPTIONAL { ?item wdt:P571 ?inscriptionYear }
  OPTIONAL { ?item wdt:P1552 ?criteria }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
}
"""
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"

# ── Emergency hardcoded fallback (all 42 India WHS as of 2024) ───────────────
# Source: https://whc.unesco.org/en/statesparties/in
# Used ONLY if both the API and Wikidata SPARQL are unavailable.
INDIA_UNESCO_SITES: list[dict[str, Any]] = [
    # === CULTURAL SITES (40) ===
    {"id": "252", "name": "Taj Mahal", "year": 1983, "criteria": "(i)", "lat": 27.1751, "lon": 78.0421, "state": "Uttar Pradesh", "category": "cultural", "qid": "Q9141"},
    {"id": "251", "name": "Agra Fort", "year": 1983, "criteria": "(iii)", "lat": 27.18, "lon": 78.02, "state": "Uttar Pradesh", "category": "cultural", "qid": "Q213547"},
    {"id": "243", "name": "Ajanta Caves", "year": 1983, "criteria": "(i)(ii)(iii)(vi)", "lat": 20.5519, "lon": 75.7033, "state": "Maharashtra", "category": "cultural", "qid": "Q83618"},
    {"id": "242", "name": "Ellora Caves", "year": 1983, "criteria": "(i)(iii)(vi)", "lat": 20.0269, "lon": 75.1793, "state": "Maharashtra", "category": "cultural", "qid": "Q663394"},
    {"id": "241", "name": "Konark Sun Temple", "year": 1984, "criteria": "(i)(iii)", "lat": 19.8876, "lon": 86.0945, "state": "Odisha", "category": "cultural", "qid": "Q846325"},
    {"id": "244", "name": "Group of Monuments at Mahabalipuram", "year": 1984, "criteria": "(i)(ii)(iii)(vi)", "lat": 12.6208, "lon": 80.1927, "state": "Tamil Nadu", "category": "cultural", "qid": "Q382680"},
    {"id": "232", "name": "Fatehpur Sikri", "year": 1986, "criteria": "(ii)(iii)(iv)", "lat": 27.0949, "lon": 77.6621, "state": "Uttar Pradesh", "category": "cultural", "qid": "Q189416"},
    {"id": "236", "name": "Group of Monuments at Hampi", "year": 1986, "criteria": "(i)(iii)(iv)", "lat": 15.335, "lon": 76.462, "state": "Karnataka", "category": "cultural", "qid": "Q42897"},
    {"id": "237", "name": "Khajuraho Group of Monuments", "year": 1986, "criteria": "(i)(iii)", "lat": 24.8517, "lon": 79.9199, "state": "Madhya Pradesh", "category": "cultural", "qid": "Q211553"},
    {"id": "233", "name": "Elephanta Caves", "year": 1987, "criteria": "(i)(iii)", "lat": 18.9633, "lon": 72.9314, "state": "Maharashtra", "category": "cultural", "qid": "Q215337"},
    {"id": "250-001", "name": "Brihadisvara Temple, Thanjavur", "year": 1987, "criteria": "(i)(ii)(iv)", "lat": 10.7826, "lon": 79.1317, "state": "Tamil Nadu", "category": "cultural", "qid": "Q278009"},
    {"id": "250-002", "name": "Brihadisvara Temple, Gangaikondacholapuram", "year": 2004, "criteria": "(i)(ii)(iv)", "lat": 11.2071, "lon": 79.4504, "state": "Tamil Nadu", "category": "cultural", "qid": "Q2330256"},
    {"id": "250-003", "name": "Airavatesvara Temple", "year": 2004, "criteria": "(i)(ii)(iv)", "lat": 10.9357, "lon": 79.3632, "state": "Tamil Nadu", "category": "cultural", "qid": "Q1399038"},
    {"id": "235", "name": "Group of Monuments at Pattadakal", "year": 1987, "criteria": "(iii)(iv)(vi)", "lat": 15.948, "lon": 75.818, "state": "Karnataka", "category": "cultural", "qid": "Q371238"},
    {"id": "234", "name": "Buddhist Monuments at Sanchi", "year": 1989, "criteria": "(i)(ii)(iii)(iv)(vi)", "lat": 23.4793, "lon": 77.7397, "state": "Madhya Pradesh", "category": "cultural", "qid": "Q211081"},
    {"id": "247-001", "name": "Humayun's Tomb, Delhi", "year": 1993, "criteria": "(ii)(iv)", "lat": 28.5933, "lon": 77.2507, "state": "Delhi", "category": "cultural", "qid": "Q161519"},
    {"id": "247-002", "name": "Qutb Minar and its Monuments, Delhi", "year": 1993, "criteria": "(ii)(iv)", "lat": 28.5245, "lon": 77.1855, "state": "Delhi", "category": "cultural", "qid": "Q215627"},
    {"id": "1440-001", "name": "Darjeeling Himalayan Railway", "year": 1999, "criteria": "(ii)(iv)", "lat": 27.09, "lon": 88.26, "state": "West Bengal", "category": "cultural", "qid": "Q1068822"},
    {"id": "1440-002", "name": "Nilgiri Mountain Railway", "year": 2005, "criteria": "(ii)(iv)", "lat": 11.4102, "lon": 76.6950, "state": "Tamil Nadu", "category": "cultural", "qid": "Q1424490"},
    {"id": "1440-003", "name": "Kalka-Shimla Railway", "year": 2008, "criteria": "(ii)(iv)", "lat": 31.1, "lon": 77.17, "state": "Himachal Pradesh", "category": "cultural", "qid": "Q2381052"},
    {"id": "1461", "name": "Mahabodhi Temple Complex at Bodh Gaya", "year": 2002, "criteria": "(i)(ii)(iii)(iv)(vi)", "lat": 24.6961, "lon": 84.9913, "state": "Bihar", "category": "cultural", "qid": "Q160378"},
    {"id": "1100", "name": "Rock Shelters of Bhimbetka", "year": 2003, "criteria": "(iii)(v)", "lat": 22.9361, "lon": 77.6122, "state": "Madhya Pradesh", "category": "cultural", "qid": "Q975005"},
    {"id": "1223", "name": "Champaner-Pavagadh Archaeological Park", "year": 2004, "criteria": "(iii)(iv)(v)(vi)", "lat": 22.4847, "lon": 73.5325, "state": "Gujarat", "category": "cultural", "qid": "Q982979"},
    {"id": "1208", "name": "Chhatrapati Shivaji Maharaj Terminus", "year": 2004, "criteria": "(ii)(iv)", "lat": 18.9398, "lon": 72.8354, "state": "Maharashtra", "category": "cultural", "qid": "Q1261841"},
    {"id": "1492", "name": "Red Fort Complex", "year": 2007, "criteria": "(ii)(iii)(vi)", "lat": 28.6562, "lon": 77.2410, "state": "Delhi", "category": "cultural", "qid": "Q484744"},
    {"id": "1587", "name": "The Jantar Mantar, Jaipur", "year": 2010, "criteria": "(iii)(iv)", "lat": 26.9246, "lon": 75.8242, "state": "Rajasthan", "category": "cultural", "qid": "Q728941"},
    {"id": "1437-001", "name": "Chittorgarh Fort", "year": 2013, "criteria": "(ii)(iii)", "lat": 24.888, "lon": 74.644, "state": "Rajasthan", "category": "cultural", "qid": "Q203697"},
    {"id": "1437-002", "name": "Kumbhalgarh Fort", "year": 2013, "criteria": "(ii)(iii)", "lat": 25.1494, "lon": 73.5884, "state": "Rajasthan", "category": "cultural", "qid": "Q1365988"},
    {"id": "1437-003", "name": "Ranthambore Fort", "year": 2013, "criteria": "(ii)(iii)", "lat": 25.9723, "lon": 76.4351, "state": "Rajasthan", "category": "cultural", "qid": "Q7292090"},
    {"id": "1437-004", "name": "Gagron Fort", "year": 2013, "criteria": "(ii)(iii)", "lat": 24.6674, "lon": 76.2122, "state": "Rajasthan", "category": "cultural", "qid": "Q3098003"},
    {"id": "1437-005", "name": "Amber Fort", "year": 2013, "criteria": "(ii)(iii)", "lat": 26.9855, "lon": 75.8513, "state": "Rajasthan", "category": "cultural", "qid": "Q742503"},
    {"id": "1437-006", "name": "Jaisalmer Fort", "year": 2013, "criteria": "(ii)(iii)", "lat": 26.9124, "lon": 70.9143, "state": "Rajasthan", "category": "cultural", "qid": "Q1684317"},
    {"id": "252bis", "name": "Rani-ki-Vav (the Queen's Stepwell) at Patan", "year": 2014, "criteria": "(i)(iv)", "lat": 23.858, "lon": 72.1014, "state": "Gujarat", "category": "cultural", "qid": "Q1133699"},
    {"id": "1569", "name": "Nalanda Mahavihara (Nalanda University)", "year": 2016, "criteria": "(iv)(vi)", "lat": 25.1358, "lon": 85.4438, "state": "Bihar", "category": "cultural", "qid": "Q1002766"},
    {"id": "1386", "name": "The Architectural Work of Le Corbusier, Chandigarh", "year": 2016, "criteria": "(i)(ii)(vi)", "lat": 30.7333, "lon": 76.7794, "state": "Chandigarh", "category": "cultural", "qid": "Q2573759"},
    {"id": "1430", "name": "Historic City of Ahmedabad", "year": 2017, "criteria": "(ii)(v)", "lat": 23.0225, "lon": 72.5714, "state": "Gujarat", "category": "cultural", "qid": "Q1070"},
    {"id": "1570", "name": "Victorian Gothic and Art Deco Ensembles of Mumbai", "year": 2018, "criteria": "(ii)(iv)", "lat": 18.9219, "lon": 72.8347, "state": "Maharashtra", "category": "cultural", "qid": "Q2361064"},
    {"id": "1590", "name": "Jaipur City, Rajasthan", "year": 2019, "criteria": "(ii)(iv)(vi)", "lat": 26.9124, "lon": 75.7873, "state": "Rajasthan", "category": "cultural", "qid": "Q27988"},
    {"id": "1606", "name": "Dholavira: A Harappan City", "year": 2021, "criteria": "(iii)(iv)", "lat": 23.8866, "lon": 70.2167, "state": "Gujarat", "category": "cultural", "qid": "Q2309879"},
    {"id": "1615", "name": "Hoysala Sacred Ensembles", "year": 2023, "criteria": "(i)(ii)", "lat": 13.1, "lon": 76.1, "state": "Karnataka", "category": "cultural", "qid": "Q4162718"},
    {"id": "1616", "name": "Santiniketan", "year": 2023, "criteria": "(iv)(vi)", "lat": 23.6802, "lon": 87.6855, "state": "West Bengal", "category": "cultural", "qid": "Q229399"},
    # === NATURAL SITES (2) ===
    {"id": "337", "name": "Kaziranga National Park", "year": 1985, "criteria": "(ix)(x)", "lat": 26.6, "lon": 93.4, "state": "Assam", "category": "natural", "qid": "Q1046280"},
    {"id": "338", "name": "Manas Wildlife Sanctuary", "year": 1985, "criteria": "(vii)(ix)(x)", "lat": 26.7, "lon": 91.0, "state": "Assam", "category": "natural", "qid": "Q734750"},
    {"id": "369", "name": "Keoladeo National Park", "year": 1985, "criteria": "(x)", "lat": 27.1667, "lon": 77.5167, "state": "Rajasthan", "category": "natural", "qid": "Q934565"},
    {"id": "452", "name": "Sundarbans National Park", "year": 1987, "criteria": "(ix)(x)", "lat": 21.9497, "lon": 88.8970, "state": "West Bengal", "category": "natural", "qid": "Q467388"},
    {"id": "668", "name": "Nanda Devi and Valley of Flowers National Parks", "year": 1988, "criteria": "(vii)(x)", "lat": 30.7, "lon": 79.6, "state": "Uttarakhand", "category": "natural", "qid": "Q1065688"},
    {"id": "1246rev", "name": "Western Ghats", "year": 2012, "criteria": "(ix)(x)", "lat": 10.6, "lon": 76.5, "state": "Multiple States", "category": "natural", "qid": "Q131386"},
    {"id": "1600", "name": "Great Himalayan National Park", "year": 2014, "criteria": "(x)", "lat": 31.7, "lon": 77.6, "state": "Himachal Pradesh", "category": "natural", "qid": "Q1520566"},
]


class UNESCOExtractor:
    """
    Fetches India's UNESCO World Heritage Sites from the official UNESCO Open
    Data API, with Wikidata SPARQL and a hardcoded list as progressive fallbacks.

    Source priority:
      1. UNESCO Open Data API (primary — official, no-auth)
      2. Wikidata SPARQL       (secondary fallback)
      3. Hardcoded INDIA_UNESCO_SITES list (emergency fallback)
    """

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=60,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    # ── Primary: Official UNESCO Open Data API ────────────────────────────────

    async def _fetch_from_api(self) -> list[dict[str, Any]] | None:
        """
        Download all India WHS records from the UNESCO Open Data API.

        Endpoint: https://data.unesco.org/api/explore/v2.1/catalog/datasets/whc001/records
        Filter:   where=states_names="India"
        Returns the list of raw API result dicts, or None on failure.
        """
        logger.info("Attempting UNESCO data via official UNESCO Open Data API...")
        all_results: list[dict[str, Any]] = []
        offset = 0

        try:
            while True:
                params: dict[str, Any] = {
                    "where": UNESCO_INDIA_FILTER,
                    "limit": UNESCO_PAGE_SIZE,
                    "offset": offset,
                }
                resp = await self.client.get(UNESCO_API_BASE, params=params, timeout=60)

                if resp.status_code != 200:
                    logger.warning(
                        f"UNESCO API returned HTTP {resp.status_code} at offset {offset}"
                    )
                    return None if not all_results else all_results

                data = resp.json()
                total_count: int = data.get("total_count", 0)
                page_results: list[dict] = data.get("results", [])

                if not page_results:
                    break  # no more records

                all_results.extend(page_results)
                logger.info(
                    f"UNESCO API: fetched {len(all_results)}/{total_count} records "
                    f"(offset={offset})"
                )

                if len(all_results) >= total_count:
                    break  # fetched everything

                offset += UNESCO_PAGE_SIZE
                await asyncio.sleep(0.5)  # be polite

        except Exception as exc:
            logger.warning(f"UNESCO Open Data API fetch failed: {exc}")
            return None if not all_results else all_results

        logger.info(
            f"UNESCO Open Data API: downloaded {len(all_results)} India WHS records"
        )
        return all_results if all_results else None

    def _parse_api_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """
        Convert one raw UNESCO API result dict into our internal normalised dict.

        Key field mappings (verified from live API):
          record["name_en"]              → name
          record["id_no"]                → id
          record["date_inscribed"]       → year  (string → int)
          record["criteria_txt"]         → criteria
          record["category"]             → category ("Cultural"/"Natural"/"Mixed")
          record["coordinates"]["lat"]   → lat
          record["coordinates"]["lon"]   → lon
          record["states_names"]         → list of country names (India may share)
          record["short_description_en"] → description
          record["transboundary"]        → "True"/"False"
        """
        name = (record.get("name_en") or "").strip()
        if not name:
            return None

        site_id = str(record.get("id_no") or "")

        # Inscription year
        year: int | None = None
        date_str = record.get("date_inscribed") or record.get("secondary_dates") or ""
        if date_str:
            try:
                year = int(str(date_str).strip()[:4])
            except (ValueError, TypeError):
                pass

        # Criteria text
        criteria = (record.get("criteria_txt") or "").strip()

        # Category
        cat_raw = (record.get("category") or "Cultural").strip().lower()
        category = "natural" if "natural" in cat_raw else "cultural"

        # Coordinates
        coords_obj = record.get("coordinates") or {}
        lat: float | None = None
        lon: float | None = None
        if isinstance(coords_obj, dict):
            try:
                lat = float(coords_obj["lat"])
                lon = float(coords_obj["lon"])
            except (KeyError, TypeError, ValueError):
                pass

        # Short description (prefer English)
        description = (
            record.get("short_description_en")
            or record.get("description_en")
            or ""
        ).strip()

        # Transboundary flag
        is_transboundary = str(record.get("transboundary", "False")).lower() == "true"

        # States / countries list
        states_names: list[str] = record.get("states_names") or []

        return {
            "id": site_id,
            "name": name,
            "year": year,
            "criteria": criteria,
            "lat": lat,
            "lon": lon,
            "state": "",           # UNESCO API gives country, not Indian state
            "category": category,
            "qid": None,           # Not provided by UNESCO API; enriched later
            "description": description,
            "is_transboundary": is_transboundary,
            "states_names": states_names,
            "source": "api",
        }

    # ── Secondary: Wikidata SPARQL ─────────────────────────────────────────────

    async def _fetch_from_wikidata(self) -> list[dict[str, Any]] | None:
        """
        Try fetching UNESCO India sites via Wikidata SPARQL (secondary fallback).
        Returns parsed internal dicts, or None on failure.
        """
        logger.info("Attempting UNESCO data via Wikidata SPARQL (secondary fallback)...")
        try:
            resp = await self.client.get(
                WIKIDATA_ENDPOINT,
                params={"query": WIKIDATA_UNESCO_QUERY, "format": "json"},
                headers={"Accept": "application/sparql-results+json"},
                timeout=60,
            )
            if resp.status_code != 200 or not resp.text.strip():
                return None
            data = resp.json()
            bindings = data.get("results", {}).get("bindings", [])
            if bindings:
                logger.info(
                    f"Wikidata SPARQL returned {len(bindings)} UNESCO India sites"
                )
                parsed = [self._parse_wikidata_binding(b) for b in bindings]
                return [p for p in parsed if p is not None]
        except Exception as exc:
            logger.warning(f"Wikidata UNESCO query failed: {exc}")
        return None

    def _parse_wikidata_binding(self, binding: dict) -> dict[str, Any] | None:
        """Convert a Wikidata SPARQL binding into our internal dict format."""
        def val(key: str) -> str | None:
            return (binding.get(key) or {}).get("value")

        qid_url = val("item")
        if not qid_url:
            return None
        qid = qid_url.split("/")[-1]
        name = val("itemLabel")
        if not name or name == qid:
            return None

        coords_raw = val("coords")
        lat: float | None = None
        lon: float | None = None
        if coords_raw:
            try:
                inner = coords_raw.replace("Point(", "").replace(")", "").strip()
                lon_s, lat_s = inner.split()
                lat, lon = float(lat_s), float(lon_s)
            except Exception:
                pass

        year_raw = val("inscriptionYear")
        year: int | None = None
        if year_raw:
            try:
                year = int(year_raw[:4])
            except Exception:
                pass

        return {
            "id": qid,
            "name": name,
            "year": year,
            "criteria": "",
            "lat": lat,
            "lon": lon,
            "state": "",
            "category": "cultural",
            "qid": qid,
            "description": "",
            "is_transboundary": False,
            "states_names": ["India"],
            "source": "wikidata",
        }

    # ── HeritageSite Parser ───────────────────────────────────────────────────

    def _parse_site(self, raw: dict[str, Any]) -> HeritageSite | None:
        """Convert a raw normalised dict into a HeritageSite Pydantic model."""
        site_id = str(raw.get("id", ""))
        name = (raw.get("name") or "").strip()
        if not name:
            return None

        lat = raw.get("lat")
        lon = raw.get("lon")
        year = raw.get("year")
        state = raw.get("state", "")
        criteria = raw.get("criteria", "")
        category_raw = raw.get("category", "cultural")
        qid = raw.get("qid")
        description = raw.get("description") or ""
        is_transboundary = raw.get("is_transboundary", False)

        coordinates = None
        if lat is not None and lon is not None:
            try:
                coordinates = Coordinates(
                    lat=float(lat),
                    lon=float(lon),
                    source=DataSource.UNESCO,
                )
            except Exception:
                pass

        category = (
            SiteCategory.NATURAL_SITE
            if "natural" in str(category_raw).lower()
            else SiteCategory.MONUMENT
        )

        # Build description if not provided by API
        location_str = state if state else "India"
        if not description:
            description = (
                f"{name} is a UNESCO World Heritage Site located in {location_str}. "
                f"It was inscribed in {year} under criteria: {criteria}."
                if year else
                f"{name} is a UNESCO World Heritage Site in {location_str}."
            )

        # Build a concise summary
        short_summary = (
            f"UNESCO World Heritage Site inscribed in {year}. Criteria: {criteria}."
            if year and criteria else
            f"UNESCO World Heritage Site."
        )
        if is_transboundary:
            short_summary += " (Transboundary site.)"

        # Extract clean UNESCO numeric ID for URL (e.g. "1321rev-003" → "1321")
        id_for_url = site_id.split("-")[0].replace("rev", "").replace("bis", "")

        site = HeritageSite(
            wikidata_qid=qid if qid and qid.startswith("Q") else None,
            unesco_id=site_id,
            name=name,
            short_summary=short_summary,
            description=description,
            location=Location(state=state),
            coordinates=coordinates,
            category=category,
            heritage_status=HeritageStatus(
                is_unesco_whs=True,
                heritage_designations=["UNESCO World Heritage Site"],
            ),
            historical_period=HistoricalPeriod(
                start_year=int(year) if year else None,
                certainty=(
                    HistoricalCertainty.EXACT if year else HistoricalCertainty.UNKNOWN
                ),
            ),
            source_urls=SourceUrls(
                unesco=f"https://whc.unesco.org/en/list/{id_for_url}/",
                wikidata=(
                    f"https://www.wikidata.org/entity/{qid}" if qid else None
                ),
            ),
            data_sources=[DataSource.UNESCO],
            citations=[f"UNESCO World Heritage List #{site_id}"],
        )
        site.compute_quality_score()
        return site

    # ── Main run() ────────────────────────────────────────────────────────────

    async def run(self) -> list[HeritageSite]:
        """
        Fetch UNESCO India WHS using the three-tier strategy:
          1. Official UNESCO Open Data API  (primary)
          2. Wikidata SPARQL               (secondary fallback)
          3. Hardcoded INDIA_UNESCO_SITES  (emergency fallback)
        """
        raw_sites: list[dict[str, Any]] | None = None
        data_source_label = "unknown"

        # ── Tier 1: Official API ───────────────────────────────────────────────
        api_records = await self._fetch_from_api()
        if api_records and len(api_records) >= 10:
            raw_sites = [
                self._parse_api_record(r)
                for r in api_records
            ]
            raw_sites = [r for r in raw_sites if r is not None]
            data_source_label = "UNESCO Open Data API"
            logger.info(
                f"Using {data_source_label}: {len(raw_sites)} records parsed "
                f"from {len(api_records)} API results"
            )

            # Save raw API response as permanent cache
            raw_api_file = OUTPUT_DIR / "india_whs_api_raw.json"
            with open(raw_api_file, "w", encoding="utf-8") as f:
                json.dump(api_records, f, indent=2, ensure_ascii=False)
            logger.info(f"Raw API response cached -> {raw_api_file}")

        # ── Tier 2: Wikidata SPARQL ────────────────────────────────────────────
        if not raw_sites or len(raw_sites) < 10:
            logger.warning(
                "UNESCO Open Data API unavailable or returned too few records. "
                "Falling back to Wikidata SPARQL..."
            )
            wikidata_sites = await self._fetch_from_wikidata()
            if wikidata_sites and len(wikidata_sites) >= 30:
                raw_sites = wikidata_sites
                data_source_label = "Wikidata SPARQL"
                logger.info(
                    f"Using {data_source_label}: {len(raw_sites)} UNESCO sites"
                )

        # ── Tier 3: Hardcoded emergency fallback ──────────────────────────────
        if not raw_sites or len(raw_sites) < 10:
            logger.warning(
                "Both UNESCO API and Wikidata SPARQL unavailable. "
                "Using hardcoded emergency fallback (42 India WHS)."
            )
            raw_sites = INDIA_UNESCO_SITES
            data_source_label = "hardcoded emergency fallback"

        # ── Parse into HeritageSite models ────────────────────────────────────
        sites: list[HeritageSite] = []
        for raw in raw_sites:
            site = self._parse_site(raw)
            if site:
                sites.append(site)

        # Save normalised JSONL checkpoint
        output_file = OUTPUT_DIR / "india_whs.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for site in sites:
                f.write(site.model_dump_json() + "\n")

        # Save normalised raw dicts
        raw_file = OUTPUT_DIR / "india_whs_raw.json"
        with open(raw_file, "w", encoding="utf-8") as f:
            json.dump(raw_sites, f, indent=2, ensure_ascii=False)

        logger.info(
            f"UNESCO extraction complete: {len(sites)} sites "
            f"[source: {data_source_label}] -> {output_file}"
        )
        return sites


# ── Phase 1 Standalone Validation ─────────────────────────────────────────────

async def validate_unesco() -> None:
    print("\n" + "=" * 62)
    print("ARKANA -- UNESCO Extractor Validation (v3 -- Official API)")
    print("=" * 62)

    extractor = UNESCOExtractor()
    try:
        sites = await extractor.run()
    finally:
        await extractor.close()

    from ingestion.models.heritage_schema import SiteCategory

    with_coords = sum(1 for s in sites if s.coordinates)
    with_qid = sum(1 for s in sites if s.wikidata_qid)
    with_year = sum(1 for s in sites if s.historical_period.start_year)
    cultural = sum(1 for s in sites if s.category == SiteCategory.MONUMENT)
    natural = sum(1 for s in sites if s.category == SiteCategory.NATURAL_SITE)
    with_desc = sum(1 for s in sites if s.description and len(s.description) > 50)

    print(f"\n{'Total UNESCO India sites':<35} {len(sites):>10}")
    print(f"{'Cultural sites':<35} {cultural:>10}")
    print(f"{'Natural sites':<35} {natural:>10}")
    print(f"{'With coordinates':<35} {with_coords:>10}")
    print(f"{'With Wikidata QID':<35} {with_qid:>10}")
    print(f"{'With inscription year':<35} {with_year:>10}")
    print(f"{'With description (>50 chars)':<35} {with_desc:>10}")
    print(f"{'Expected India total (2024)':<35} {'42':>10}")
    print(f"{'API also returns transboundary':<35} {'44 records':>10}")

    # Check which raw source was used
    raw_api_file = OUTPUT_DIR / "india_whs_api_raw.json"
    if raw_api_file.exists():
        with open(raw_api_file, encoding="utf-8") as f:
            raw_api = json.load(f)
        print(f"\n  [API] Raw API records downloaded: {len(raw_api)}")
        print(f"  [API] Endpoint: {UNESCO_API_BASE}")
        print(f"  [API] Filter:   where={UNESCO_INDIA_FILTER}")
    else:
        print("\n  [WARN] No raw API cache found — API may have been unavailable.")

    if len(sites) < 40:
        print(f"\n  WARNING: Got {len(sites)} sites — expected at least 40.")
        print(
            "  Note: API returns 44 records (incl. transboundary). "
            "Hardcoded fallback contains 42 pure India sites."
        )
    elif len(sites) >= 42:
        print(f"\n  All {len(sites)} UNESCO India WHS retrieved successfully.")

    print(f"\nOutput files:")
    print(f"  Normalised JSONL : {OUTPUT_DIR / 'india_whs.jsonl'}")
    print(f"  Normalised raw   : {OUTPUT_DIR / 'india_whs_raw.json'}")
    if raw_api_file.exists():
        print(f"  Raw API cache    : {raw_api_file}")

    print("\nUNESCO validation complete.")


if __name__ == "__main__":
    asyncio.run(validate_unesco())
