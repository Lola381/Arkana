"""
Arkana — OpenStreetMap Overpass API Extractor
Extracts heritage site nodes/ways/relations from OpenStreetMap for India.

⚠️ WARNING: OSM is used ONLY for coordinate enrichment.
  - Do NOT use as primary source for site discovery.
  - Coverage for rural/minor sites is incomplete.
  - Use only when Wikidata P625 coordinate is missing.

Rate limit: max 2 concurrent requests.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from ingestion.config import RAW_DIR, USER_AGENT
from ingestion.models.heritage_schema import Coordinates, DataSource
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = RAW_DIR / "osm"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OVERPASS_ENDPOINT = "https://overpass-api.de/api/interpreter"
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",       # Primary (public)
    "https://overpass.kumi.systems/api/interpreter", # Mirror 1
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",  # Mirror 2
]
OVERPASS_SEMAPHORE = asyncio.Semaphore(2)  # Max 2 concurrent OSM requests

# ── Overpass QL Queries ───────────────────────────────────────────────────────

INDIA_HERITAGE_QUERY = """
[out:json][timeout:90];
area["name"="India"]["admin_level"="2"]->.india;
(
  nwr["historic"~"monument|archaeological_site|fort|temple|palace|mosque|church|monastery|ruins|castle|shrine|tomb|mausoleum|memorial"](area.india);
  nwr["tourism"="attraction"]["heritage"](area.india);
  nwr["heritage"~"yes|1|national|state|world"](area.india);
  nwr["building"~"temple|mosque|church|monastery|fort|castle|palace"](area.india);
  nwr["amenity"~"place_of_worship"]["heritage"](area.india);
);
out center tags;
"""

# Lighter query for a single state (use for testing)
STATE_HERITAGE_QUERY = """
[out:json][timeout:90];
area["name"="{state_name}"]["admin_level"="4"]->.state;
(
  nwr["historic"~"monument|archaeological_site|fort|temple|palace|mosque|church|monastery|ruins|castle|shrine|tomb|mausoleum|memorial"](area.state);
  nwr["tourism"="attraction"]["heritage"](area.state);
  nwr["heritage"~"yes|1|national|state|world"](area.state);
  nwr["building"~"temple|mosque|church|monastery|fort|castle|palace"](area.state);
);
out center tags;
"""


# ── OSM Record Parser ─────────────────────────────────────────────────────────

def parse_osm_element(element: dict[str, Any]) -> dict[str, Any] | None:
    """
    Parse a single OSM element (node/way/relation) to a coordinate record.
    Returns a dict with: osm_id, osm_type, name, lat, lon, tags
    """
    tags = element.get("tags", {})
    name = (
        tags.get("name:en")
        or tags.get("name")
        or tags.get("name:hi")
    )
    if not name:
        return None

    # Get coordinates — nodes have direct lat/lon; ways/relations have center
    center = element.get("center", {})
    lat = element.get("lat") or center.get("lat")
    lon = element.get("lon") or center.get("lon")
    if not lat or not lon:
        return None

    # Validate India bounding box
    lat, lon = float(lat), float(lon)
    if not (6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0):
        return None

    return {
        "osm_id": f"{element['type']}/{element['id']}",
        "osm_type": element["type"],
        "name": name,
        "name_hi": tags.get("name:hi"),
        "lat": lat,
        "lon": lon,
        "historic_tag": tags.get("historic"),
        "tourism_tag": tags.get("tourism"),
        "heritage_tag": tags.get("heritage"),
        "wikidata": tags.get("wikidata"),   # QID if tagged — use for cross-reference!
        "wikipedia": tags.get("wikipedia"),
        "addr_state": tags.get("addr:state"),
        "tags": tags,
    }


class OSMExtractor:

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=120,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _overpass_query(self, query: str) -> list[dict[str, Any]]:
        """Execute Overpass QL query and return list of elements.
        Tries primary endpoint first, then mirrors if primary is overloaded.
        """
        async with OVERPASS_SEMAPHORE:
            for endpoint in OVERPASS_ENDPOINTS:
                for attempt in range(2):  # 2 tries per endpoint
                    try:
                        resp = await self.client.post(
                            endpoint,
                            data={"data": query},
                            timeout=120,
                        )
                        # 504/503 = server overload (transient). Back off and retry.
                        if resp.status_code in (504, 503, 429):
                            wait = 20 * (attempt + 1)
                            logger.warning(
                                f"Overpass attempt {attempt+1} failed: "
                                f"HTTP {resp.status_code} (transient). Retry in {wait}s"
                            )
                            await asyncio.sleep(wait)
                            continue
                        resp.raise_for_status()
                        elements = resp.json().get("elements", [])
                        if elements:
                            if endpoint != OVERPASS_ENDPOINTS[0]:
                                logger.info(f"Got {len(elements)} elements from mirror: {endpoint}")
                            return elements
                        # Empty response — server-side timeout or no data
                        logger.warning(
                            f"Overpass {endpoint} attempt {attempt+1}: empty elements. "
                            f"Trying next..."
                        )
                        break  # Move to next endpoint
                    except Exception as e:
                        wait = 10 * (attempt + 1)
                        logger.warning(
                            f"Overpass {endpoint} attempt {attempt+1} failed: {e}. "
                            f"Retry in {wait}s"
                        )
                        await asyncio.sleep(wait)
                await asyncio.sleep(5)  # Brief pause between endpoints
        logger.error("All Overpass endpoints returned empty or failed.")
        return []

    async def query_state(self, state_name: str) -> list[dict[str, Any]]:
        """Query OSM heritage nodes for a single state."""
        logger.info(f"OSM query: {state_name}")
        query = STATE_HERITAGE_QUERY.format(state_name=state_name)
        elements = await self._overpass_query(query)
        records = [parse_osm_element(e) for e in elements]
        return [r for r in records if r is not None]

    async def query_all_india(self) -> list[dict[str, Any]]:
        """
        Query all heritage nodes across India.
        Warning: This can return 10,000+ elements and take 30–60 seconds.
        """
        logger.info("Running full India OSM heritage query...")
        elements = await self._overpass_query(INDIA_HERITAGE_QUERY)
        records = [parse_osm_element(e) for e in elements]
        valid = [r for r in records if r is not None]
        logger.info(f"OSM total India: {len(elements)} elements → {len(valid)} valid records")
        return valid

    def get_coordinate_for_qid(
        self,
        records: list[dict[str, Any]],
        qid: str,
    ) -> Coordinates | None:
        """
        Look up a Wikidata QID in OSM records to find coordinates.
        Only use when Wikidata P625 is missing.
        """
        for r in records:
            if r.get("wikidata") == qid:
                try:
                    return Coordinates(
                        lat=r["lat"],
                        lon=r["lon"],
                        source=DataSource.OSM,
                    )
                except Exception:
                    continue
        return None

    def save(self, records: list[dict[str, Any]], filename: str) -> Path:
        output_file = OUTPUT_DIR / filename
        # IMPORTANT: Never overwrite an existing non-empty file with 0 records.
        # A 0-record result after a server error (504, etc.) must not destroy
        # a previously-good checkpoint. Preserve and report the existing data.
        if not records and output_file.exists() and output_file.stat().st_size > 0:
            existing_count = sum(1 for line in output_file.read_text(encoding="utf-8").splitlines() if line.strip())
            if existing_count > 0:
                logger.warning(
                    f"Overpass returned 0 records but {output_file.name} already has "
                    f"{existing_count} records. Preserving existing data (transient server error)."
                )
                return output_file
        with open(output_file, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        logger.info(f"Saved {len(records)} OSM records -> {output_file}")
        return output_file

    def load_checkpoint(self, filename: str) -> list[dict[str, Any]]:
        """Load existing OSM checkpoint if available."""
        output_file = OUTPUT_DIR / filename
        if not output_file.exists():
            return []
        records = []
        with open(output_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records


# ── Phase 1 Validation ────────────────────────────────────────────────────────

async def validate_osm() -> None:
    print("\n" + "=" * 60)
    print("ARKANA — OSM Overpass Extractor Validation")
    print("=" * 60)

    extractor = OSMExtractor()
    try:
        # Test with 2 sample states
        results: dict[str, int] = {}
        for state in ["Rajasthan", "Tamil Nadu"]:
            records = await extractor.query_state(state)
            extractor.save(records, f"osm_{state.lower().replace(' ', '_')}.jsonl")
            results[state] = len(records)
            await asyncio.sleep(5)  # Wait between Overpass requests

    finally:
        await extractor.close()

    # Stats
    with_wikidata = 0
    for state_records in []:
        with_wikidata += sum(1 for r in state_records if r.get("wikidata"))

    print(f"\n{'State':<25} {'OSM Records':>15}")
    print("-" * 42)
    for state, count in results.items():
        print(f"{state:<25} {count:>15}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("\n⚠️  Reminder: OSM used ONLY for coordinate enrichment when Wikidata P625 is missing")
    print("\n✅ OSM validation complete")


if __name__ == "__main__":
    asyncio.run(validate_osm())
