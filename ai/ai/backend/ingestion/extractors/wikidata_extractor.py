"""
Arkana -- Wikidata SPARQL Extractor (v2)

Query strategy (per Wikimedia SPARQL guidelines):
  - Avoid P131* transitive closure + P31/P279* on same query (causes timeout)
  - Use explicit 4-hop P131 UNION + flat P31 VALUES list
  - Paginate via OFFSET (PAGE_SIZE=500)
  - For large states (Rajasthan, etc.) that timeout even on page 1:
    automatically fall back to district-level queries

Output: JSONL per state -> data/raw/wikidata/
Primary dedup key: wikidata_qid (never changes)
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import httpx
from pydantic import ValidationError

from ingestion.config import (
    INDIA_STATES_WIKIDATA,
    RAW_DIR,
    USER_AGENT,
)
from ingestion.models.heritage_schema import (
    Coordinates,
    DataSource,
    HeritageSite,
    HeritageStatus,
    HistoricalCertainty,
    HistoricalPeriod,
    Location,
    RelatedEntities,
    SiteCategory,
    SiteImage,
    SourceUrls,
)
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
OUTPUT_DIR = RAW_DIR / "wikidata"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── District-level fallback QIDs ──────────────────────────────────────────────
# Used when a state-level query times out (empty body on first page).
# These are the major districts in each problematic large state.
DISTRICT_FALLBACK: dict[str, dict[str, str]] = {
    "Rajasthan": {
        "Jaipur": "Q213812",
        "Jodhpur": "Q244022",
        "Udaipur": "Q207800",
        "Ajmer": "Q230508",
        "Bikaner": "Q231084",
        "Jaisalmer": "Q26773",
        "Chittorgarh": "Q392459",
        "Kota": "Q1755",
        "Alwar": "Q232469",
        "Bharatpur": "Q39753",
        "Sawai Madhopur": "Q1321395",
        "Sikar": "Q1963513",
        "Pali": "Q2085476",
        "Bundi": "Q371060",
        "Barmer": "Q231236",
        "Nagaur": "Q1545978",
        "Jhalawar": "Q1340440",
        "Dungarpur": "Q1337014",
        "Sirohi": "Q2241832",
        "Jhunjhunu": "Q1340508",
        "Banswara": "Q1099085",
    },
    "Madhya Pradesh": {
        "Bhopal": "Q170063",
        "Indore": "Q231440",
        "Gwalior": "Q232422",
        "Jabalpur": "Q48387",
        "Ujjain": "Q200893",
        "Satna": "Q2267498",
        "Rewa": "Q2121016",
        "Sagar": "Q2256143",
        "Vidisha": "Q2591218",
        "Raisen": "Q2119219",
        "Chhatarpur": "Q1292576",
        "Tikamgarh": "Q2608217",
        "Panna": "Q2071012",
        "Damoh": "Q1306268",
        "Dewas": "Q1318792",
    },
}

# ── SPARQL Query ──────────────────────────────────────────────────────────────
# Key changes from v1:
#   1. Removed P31/P279* chain — too expensive, causes empty response (soft timeout)
#   2. Use direct P31 VALUES with expanded QID list (no subclass traversal)
#   3. Use P131|P131/P131|P131/P131/P131 — explicit 3-level location path
#      instead of P131* which attempts full transitive closure (very slow)
#   4. Reduced optional fields per query to lower memory usage at endpoint

# Expanded set of P31 QIDs — direct instance types only (no P279* chain)
HERITAGE_INSTANCE_TYPES = " ".join([
    "wd:Q4989906",   # monument
    "wd:Q839954",    # archaeological site
    "wd:Q12034",     # fort
    "wd:Q1081138",   # palace
    "wd:Q44613",     # monastery
    "wd:Q16748868",  # historic building
    "wd:Q45393",     # Hindu temple
    "wd:Q32815",     # mosque
    "wd:Q16970",     # church
    "wd:Q2977",      # cathedral
    "wd:Q33506",     # museum
    "wd:Q2469128",   # stepwell (vav)
    "wd:Q811938",    # nature reserve
    "wd:Q23413",     # castle (mapped to fort)
    "wd:Q35112127",  # mausoleum
    "wd:Q460422",    # Jain temple
    "wd:Q163687",    # stupa
    "wd:Q42948",     # wall (defensive)
    "wd:Q79007",     # street / road (low value, filtered later)
    "wd:Q486972",    # human settlement (may catch historic towns)
    "wd:Q3947",      # house (historic)
    "wd:Q24398318",  # religious building
    "wd:Q17350442",  # place of worship
    "wd:Q2221906",   # geographic location (catch-all, filtered on quality)
    "wd:Q210272",    # cultural heritage
    "wd:Q570116",    # tourist attraction
    "wd:Q4022",      # river (for historic ghats)
    "wd:Q10990",     # dam
    "wd:Q23397",     # lake
    "wd:Q8502",      # mountain
])

# Query fetches items at state level, district level, and sub-district level.
# Uses explicit 3-hop path instead of P131* to avoid full transitive closure.
HERITAGE_QUERY_TEMPLATE = """\
SELECT DISTINCT
  ?item ?itemLabel ?itemDescription
  ?coords ?inception ?image ?officialWebsite
  ?heritageDesig ?heritageDesigLabel
  ?instanceOf ?instanceOfLabel
WHERE {{
  {{
    ?item wdt:P131 wd:{state_qid} .
  }} UNION {{
    ?item wdt:P131/wdt:P131 wd:{state_qid} .
  }} UNION {{
    ?item wdt:P131/wdt:P131/wdt:P131 wd:{state_qid} .
  }} UNION {{
    ?item wdt:P131/wdt:P131/wdt:P131/wdt:P131 wd:{state_qid} .
  }}
  ?item wdt:P31 ?instanceOf .
  VALUES ?instanceOf {{
    {instance_types}
  }}
  OPTIONAL {{ ?item wdt:P625 ?coords }}
  OPTIONAL {{ ?item wdt:P571 ?inception }}
  OPTIONAL {{ ?item wdt:P18 ?image }}
  OPTIONAL {{ ?item wdt:P856 ?officialWebsite }}
  OPTIONAL {{ ?item wdt:P1435 ?heritageDesig }}
  SERVICE wikibase:label {{
    bd:serviceParam wikibase:language "en,hi" .
  }}
}}
LIMIT {limit}
OFFSET {offset}
"""

PAGE_SIZE = 500  # Safe page size for Wikidata


# ── Category Normalization ────────────────────────────────────────────────────

WIKIDATA_QID_TO_CATEGORY: dict[str, SiteCategory] = {
    "Q4989906": SiteCategory.MONUMENT,
    "Q839954": SiteCategory.ARCHAEOLOGICAL_SITE,
    "Q12034": SiteCategory.FORT,
    "Q1081138": SiteCategory.PALACE,
    "Q44613": SiteCategory.MONASTERY,
    "Q16748868": SiteCategory.HERITAGE_BUILDING,
    "Q45393": SiteCategory.TEMPLE,
    "Q32815": SiteCategory.MOSQUE,
    "Q16970": SiteCategory.CHURCH,
    "Q2977": SiteCategory.TEMPLE,
    "Q33506": SiteCategory.MUSEUM,
    "Q2469128": SiteCategory.OTHER,  # stepwell
    "Q811938": SiteCategory.NATURAL_SITE,
    "Q23413": SiteCategory.FORT,
    "Q35112127": SiteCategory.MAUSOLEUM,
    "Q460422": SiteCategory.TEMPLE,   # Jain temple
    "Q163687": SiteCategory.STUPA,
    "Q24398318": SiteCategory.MONUMENT,  # religious building
    "Q17350442": SiteCategory.MONUMENT,  # place of worship
    "Q570116": SiteCategory.MONUMENT,   # tourist attraction
    "Q210272": SiteCategory.MONUMENT,   # cultural heritage
}


def normalize_category(instance_of_qid: str | None) -> SiteCategory:
    if not instance_of_qid:
        return SiteCategory.UNKNOWN
    qid = instance_of_qid.split("/")[-1]
    return WIKIDATA_QID_TO_CATEGORY.get(qid, SiteCategory.UNKNOWN)


def parse_coords(coords_str: str | None) -> tuple[float, float] | None:
    """Parse 'Point(lon lat)' format from Wikidata SPARQL."""
    if not coords_str:
        return None
    try:
        inner = coords_str.replace("Point(", "").replace(")", "").strip()
        lon_str, lat_str = inner.split()
        lat, lon = float(lat_str), float(lon_str)
        # Validate India bounding box
        if 6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0:
            return lat, lon
        return None
    except Exception:
        return None


def parse_year(inception_str: str | None) -> int | None:
    """Parse Wikidata inception date -> year integer."""
    if not inception_str:
        return None
    try:
        year = int(inception_str[:4])
        if inception_str.startswith("-"):
            year = -int(inception_str[1:5])
        return year if -3000 <= year <= 2026 else None
    except Exception:
        return None


# ── Main Extractor ────────────────────────────────────────────────────────────

class WikidataExtractor:

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/sparql-results+json",
            },
            timeout=120,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _sparql_query(self, query: str, retries: int = 4) -> list[dict[str, Any]]:
        """
        Execute SPARQL query against Wikidata endpoint.
        Returns list of result bindings, or [] on failure.
        Uses exponential backoff with jitter on errors or empty responses.
        """
        for attempt in range(retries):
            try:
                resp = await self.client.get(
                    SPARQL_ENDPOINT,
                    params={"query": query, "format": "json"},
                )

                # Wikidata sometimes returns 429, 503, or an empty body on overload
                if resp.status_code == 429:
                    wait = 30 + attempt * 15
                    logger.warning(f"SPARQL rate limited (429). Waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                if resp.status_code == 503:
                    wait = 20 + attempt * 10
                    logger.warning(f"SPARQL service unavailable (503). Waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                resp.raise_for_status()

                # Guard against empty body (soft timeout response from WQDS)
                text = resp.text.strip()
                if not text:
                    wait = 15 + attempt * 10
                    logger.warning(f"SPARQL returned empty body (attempt {attempt+1}). Waiting {wait}s...")
                    await asyncio.sleep(wait)
                    continue

                data = resp.json()
                return data.get("results", {}).get("bindings", [])

            except httpx.ReadTimeout:
                wait = 20 + attempt * 15
                logger.warning(f"SPARQL ReadTimeout (attempt {attempt+1}). Waiting {wait}s...")
                await asyncio.sleep(wait)
            except json.JSONDecodeError as e:
                wait = 10 + attempt * 5
                logger.warning(f"SPARQL JSON decode error (attempt {attempt+1}): {e}. Waiting {wait}s...")
                await asyncio.sleep(wait)
            except Exception as e:
                wait = 5 * (attempt + 1)
                logger.warning(f"SPARQL error (attempt {attempt+1}): {e}. Waiting {wait}s...")
                await asyncio.sleep(wait)

        logger.error("SPARQL query failed after all retries.")
        return []

    def _binding_value(self, binding: dict, key: str) -> str | None:
        """Safely extract a value from a SPARQL result binding."""
        entry = binding.get(key)
        if entry is None:
            return None
        return entry.get("value")

    def _build_site(self, row: dict[str, Any], state_name: str) -> HeritageSite | None:
        """Convert a SPARQL result row to a HeritageSite record."""
        qid_url = self._binding_value(row, "item")
        if not qid_url:
            return None

        qid = qid_url.split("/")[-1]
        name = self._binding_value(row, "itemLabel") or ""

        # Skip unlabelled entities (label == QID means no English label)
        if not name or name == qid or name.startswith("Q") and name[1:].isdigit():
            return None

        description = self._binding_value(row, "itemDescription")
        coords_raw = self._binding_value(row, "coords")
        inception_raw = self._binding_value(row, "inception")
        image_url = self._binding_value(row, "image")
        official_website = self._binding_value(row, "officialWebsite")
        instance_of_url = self._binding_value(row, "instanceOf")
        heritage_desig_label = self._binding_value(row, "heritageDesigLabel") or ""

        # Coordinates
        coordinates = None
        coord_pair = parse_coords(coords_raw)
        if coord_pair:
            lat, lon = coord_pair
            try:
                coordinates = Coordinates(lat=lat, lon=lon, source=DataSource.WIKIDATA)
            except ValidationError:
                logger.debug(f"Invalid coords for {qid}: lat={lat}, lon={lon}")

        # Category
        category = normalize_category(instance_of_url)

        # Heritage status
        is_unesco = "UNESCO" in heritage_desig_label or "World Heritage" in heritage_desig_label
        is_asi = "Archaeological Survey" in heritage_desig_label or "ASI" in heritage_desig_label

        # Year
        start_year = parse_year(inception_raw)

        # Images
        images = []
        if image_url:
            images = [SiteImage(url=image_url, source=DataSource.WIKIMEDIA_COMMONS)]

        try:
            site = HeritageSite(
                wikidata_qid=qid,
                name=name,
                short_summary=description,
                description=description,
                location=Location(state=state_name),
                coordinates=coordinates,
                category=category,
                heritage_status=HeritageStatus(
                    is_unesco_whs=is_unesco,
                    is_asi_protected=is_asi,
                    heritage_designations=[heritage_desig_label] if heritage_desig_label else [],
                ),
                historical_period=HistoricalPeriod(
                    start_year=start_year,
                    certainty=HistoricalCertainty.APPROXIMATE if start_year else HistoricalCertainty.UNKNOWN,
                ),
                images=images,
                source_urls=SourceUrls(
                    wikidata=f"https://www.wikidata.org/entity/{qid}",
                    official_website=official_website,
                ),
                data_sources=[DataSource.WIKIDATA],
                related_entities=RelatedEntities(),
            )
            site.compute_quality_score()
            return site
        except ValidationError as e:
            logger.warning(f"Schema validation failed for {qid} ({name}): {e}")
            return None

    async def extract_state(
        self, state_name: str, state_qid: str
    ) -> list[HeritageSite]:
        """
        Extract heritage sites for a single state.
        If state-level query times out (returns 0 on first page), automatically
        falls back to district-level queries for better coverage.
        """
        logger.info(f"Extracting Wikidata: {state_name} ({state_qid})")

        # Try state-level first
        sites = await self._extract_by_location(state_qid, state_name)

        if not sites and state_name in DISTRICT_FALLBACK:
            logger.warning(
                f"  {state_name}: state-level query returned 0. "
                f"Falling back to district-level queries..."
            )
            sites = await self._extract_by_districts(state_name)

        logger.info(f"  {state_name} complete: {len(sites)} unique sites")
        return sites

    async def _extract_by_location(
        self, location_qid: str, location_name: str
    ) -> list[HeritageSite]:
        """
        Core paginated extraction for any location QID (state or district).
        Returns deduplicated list of HeritageSite records.
        """
        sites_by_qid: dict[str, HeritageSite] = {}
        offset = 0
        page_num = 0

        while True:
            query = HERITAGE_QUERY_TEMPLATE.format(
                state_qid=location_qid,
                instance_types=HERITAGE_INSTANCE_TYPES,
                limit=PAGE_SIZE,
                offset=offset,
            )

            rows = await self._sparql_query(query)
            page_num += 1

            if not rows:
                logger.info(
                    f"  {location_name} page {page_num}: 0 results (offset={offset})"
                )
                if offset == 0:
                    # First page empty — retry once after delay
                    await asyncio.sleep(12)
                    rows = await self._sparql_query(query)
                    if not rows:
                        break
                else:
                    break

            page_new = 0
            for row in rows:
                # Use location_name as the state label only at state level
                # (district-level calls pass district name, we'll override with state)
                site = self._build_site(row, location_name)
                if site and site.wikidata_qid not in sites_by_qid:
                    sites_by_qid[site.wikidata_qid] = site
                    page_new += 1

            logger.info(
                f"  {location_name} page {page_num}: {page_new} new "
                f"(offset={offset}, total={len(sites_by_qid)})"
            )

            if len(rows) < PAGE_SIZE:
                break

            offset += PAGE_SIZE
            await asyncio.sleep(3)

        return list(sites_by_qid.values())

    async def _extract_by_districts(
        self, state_name: str
    ) -> list[HeritageSite]:
        """
        District-level fallback extraction.
        Queries each major district individually (smaller scope = no timeout).
        All resulting sites get state_name as their location label.
        """
        districts = DISTRICT_FALLBACK.get(state_name, {})
        if not districts:
            logger.warning(f"No district fallback configured for {state_name}")
            return []

        sites_by_qid: dict[str, HeritageSite] = {}

        for district_name, district_qid in districts.items():
            logger.info(f"  Querying district: {district_name} ({district_qid})")
            district_sites = await self._extract_by_location(
                district_qid, district_name
            )
            # Override location state to the parent state name
            for site in district_sites:
                if not site.location.state:
                    site.location.state = state_name
                if site.wikidata_qid not in sites_by_qid:
                    sites_by_qid[site.wikidata_qid] = site

            logger.info(
                f"  District {district_name}: {len(district_sites)} sites "
                f"(state total so far: {len(sites_by_qid)})"
            )
            await asyncio.sleep(4)  # Extra polite between district queries

        return list(sites_by_qid.values())

    async def save_state_output(self, state_name: str, sites: list[HeritageSite]) -> Path:
        """Save sites to JSONL checkpoint file."""
        safe_name = state_name.lower().replace(" ", "_")
        output_file = OUTPUT_DIR / f"{safe_name}.jsonl"
        with open(output_file, "w", encoding="utf-8") as f:
            for site in sites:
                f.write(site.model_dump_json() + "\n")
        logger.info(f"Saved {len(sites)} sites -> {output_file}")
        return output_file

    def load_checkpoint(self, state_name: str) -> list[HeritageSite] | None:
        """Load existing checkpoint if it exists and is non-empty."""
        safe_name = state_name.lower().replace(" ", "_")
        checkpoint = OUTPUT_DIR / f"{safe_name}.jsonl"
        if not checkpoint.exists():
            return None
        sites = []
        try:
            with open(checkpoint, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        sites.append(HeritageSite.model_validate_json(line))
        except Exception as e:
            logger.warning(f"Checkpoint corrupt for {state_name}: {e}. Will re-extract.")
            return None
        return sites if sites else None

    async def run_full_extraction(
        self,
        states: dict[str, str] | None = None,
        delay_between_states: float = 5.0,
        force_refresh: bool = False,
    ) -> dict[str, int]:
        """
        Run extraction for all (or given) Indian states.
        Returns dict of {state_name: record_count}.
        Uses JSONL checkpoints — skips states already extracted unless force_refresh=True.
        """
        target_states = states or INDIA_STATES_WIKIDATA
        results: dict[str, int] = {}

        for state_name, state_qid in target_states.items():
            # Check for valid checkpoint
            if not force_refresh:
                cached = self.load_checkpoint(state_name)
                if cached is not None:
                    logger.info(f"Checkpoint loaded: {state_name} ({len(cached)} records)")
                    results[state_name] = len(cached)
                    continue

            sites = await self.extract_state(state_name, state_qid)

            if sites:
                await self.save_state_output(state_name, sites)
            else:
                logger.warning(f"No sites extracted for {state_name} — NOT saving checkpoint so it will retry next run.")

            results[state_name] = len(sites)
            await asyncio.sleep(delay_between_states)

        return results


# ── CLI Validation Entry Point ────────────────────────────────────────────────

async def validate_wikidata() -> None:
    print("\n" + "=" * 60)
    print("ARKANA -- Wikidata Extractor Validation (v2)")
    print("=" * 60)

    sample_states = {
        "Rajasthan": INDIA_STATES_WIKIDATA["Rajasthan"],
        "Uttar Pradesh": INDIA_STATES_WIKIDATA["Uttar Pradesh"],
        "Tamil Nadu": INDIA_STATES_WIKIDATA["Tamil Nadu"],
    }

    extractor = WikidataExtractor()
    try:
        results = await extractor.run_full_extraction(
            states=sample_states,
            force_refresh=True,  # Re-test all states for validation
        )
    finally:
        await extractor.close()

    total = sum(results.values())
    print(f"\n{'State':<25} {'Records':>10}")
    print("-" * 37)
    for state, count in results.items():
        status = "OK" if count > 0 else "ZERO - CHECK SPARQL"
        print(f"{state:<25} {count:>10}  [{status}]")
    print("-" * 37)
    print(f"{'TOTAL':<25} {total:>10}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\nWikidata validation complete")


if __name__ == "__main__":
    asyncio.run(validate_wikidata())
