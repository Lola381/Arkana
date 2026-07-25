"""
Arkana -- data.gov.in ASI Monument List Extractor (v2)

ARCHITECTURAL DECISION (June 2026): data.gov.in is DEPRIORITIZED.
─────────────────────────────────────────────────────────────────
A bounded investigation of ~17 datasets confirmed that all monument-related
datasets on data.gov.in contain only: S.No., Monument Name, Location, District.
No coordinates, descriptions, categories, or Wikidata QIDs are present.
The data originates from 2015-2021 parliamentary annexures and all API
resource IDs tested returned HTTP 403/400.

This extractor is RETAINED for two reasons:
  1. It handles the case where a DATAGOV_API_KEY is eventually configured and
     the API becomes usable in future (resource IDs may change over time).
  2. It provides a CSV fallback: place a manually-downloaded CSV at
     data/raw/datagov/asi_monuments.csv and the extractor will auto-load it.

DO NOT integrate data.gov.in into Phase 2 ETL without explicit re-evaluation.
See handoff_summary.md → "data.gov.in — Final Investigation Findings" for the
full assessment and decision rationale.

API troubleshooting (for reference):
  - The API returns HTTP 302 redirect to https://www.data.gov.in (www prefix).
  - data.gov.in API v1 (datastore/resource.json) was deprecated.
  - Current API v2 requires the resource endpoint and header-based auth.
  - Known resource IDs (as of June 2026) return HTTP 403 even with valid keys.
  - No public catalogue API exists; resource IDs must be extracted from SPA HTML.
"""

from __future__ import annotations

import asyncio
import csv
import io
import json
from pathlib import Path
from typing import Any

import httpx

from ingestion.config import DATAGOV_API_KEY, RAW_DIR, USER_AGENT
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = RAW_DIR / "datagov"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# API v2 endpoint (new format as of 2023)
DATAGOV_API_V2 = "https://data.gov.in/api/1/datastore/resource"

# ASI Centrally Protected Monuments - resource IDs (try both known versions)
ASI_RESOURCE_IDS = [
    "3c28ddee-a3e9-410a-9e31-52cbc0f8a57d",  # Original ID
    "7a8a0b31-8e3c-4b30-98db-b5cc9fd58862",  # Alternative/updated ID
]

# Direct CSV download URL (fallback - publicly accessible)
ASI_CSV_URL = (
    "https://data.gov.in/resource/district-wise-list-centrally-protected-monuments"
    "?format=csv"
)


class DataGovExtractor:

    def __init__(self) -> None:
        self.api_key = (DATAGOV_API_KEY or "").strip()
        if not self.api_key:
            logger.warning(
                "DATAGOV_API_KEY not set. data.gov.in API will be skipped.\n"
                "Register at https://data.gov.in/user/register (free)"
            )
        self.client = httpx.AsyncClient(
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            },
            timeout=60,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _try_api_v2(self, resource_id: str) -> list[dict[str, Any]]:
        """
        Try data.gov.in API v2 format.
        Authentication is via api-key header (not query param).
        """
        all_records: list[dict[str, Any]] = []
        offset = 0
        page_size = 100

        while True:
            url = f"{DATAGOV_API_V2}/{resource_id}"
            params = {
                "limit": page_size,
                "offset": offset,
                "format": "json",
            }
            headers = {
                "api-key": self.api_key,
                "User-Agent": USER_AGENT,
            }

            try:
                resp = await self.client.get(url, params=params, headers=headers)

                if resp.status_code == 403:
                    logger.warning(f"data.gov.in 403 for resource {resource_id}. May need re-registration.")
                    return []
                if resp.status_code == 404:
                    logger.warning(f"data.gov.in 404 for resource {resource_id}. Resource ID may have changed.")
                    return []
                if resp.status_code not in (200, 201):
                    logger.warning(f"data.gov.in unexpected status {resp.status_code}")
                    return []

                resp.raise_for_status()
                data = resp.json()
                records = data.get("records", data.get("data", []))

                if not records:
                    break

                all_records.extend(records)
                total = data.get("total", data.get("count", 0))
                logger.info(f"data.gov.in: {len(all_records)}/{total} records fetched")

                if len(all_records) >= total or len(records) < page_size:
                    break

                offset += page_size
                await asyncio.sleep(1.0)

            except json.JSONDecodeError:
                logger.warning(f"data.gov.in returned non-JSON for resource {resource_id}")
                return []
            except Exception as e:
                logger.error(f"data.gov.in API error at offset {offset}: {e}")
                break

        return all_records

    async def _try_api_v1(self, resource_id: str) -> list[dict[str, Any]]:
        """
        Try data.gov.in API v1 format (legacy, api-key as query param).
        """
        all_records: list[dict[str, Any]] = []
        offset = 0
        page_size = 100

        while True:
            try:
                resp = await self.client.get(
                    "https://data.gov.in/api/datastore/resource.json",
                    params={
                        "resource_id": resource_id,
                        "api-key": self.api_key,
                        "limit": page_size,
                        "offset": offset,
                        "format": "json",
                    },
                )

                if resp.status_code in (301, 302, 307, 308):
                    location = resp.headers.get("location", "")
                    logger.info(f"Redirect to: {location}")

                if resp.status_code not in (200, 201):
                    logger.warning(f"data.gov.in v1 status {resp.status_code}")
                    return []

                data = resp.json()
                records = data.get("records", [])
                if not records:
                    break

                all_records.extend(records)
                total = int(data.get("total", 0))
                logger.info(f"data.gov.in v1: {len(all_records)}/{total}")

                if len(all_records) >= total or len(records) < page_size:
                    break

                offset += page_size
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"data.gov.in v1 error at offset {offset}: {e}")
                break

        return all_records

    def normalize_record(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        """
        Normalize a raw data.gov.in record.
        The dataset has inconsistent column names across vintages.
        """
        def get(*keys: str) -> str | None:
            for k in keys:
                for variant in [k, k.lower(), k.upper(), k.title()]:
                    val = raw.get(variant)
                    if val and str(val).strip() not in ("-", "N/A", "NA", "", "NULL"):
                        return str(val).strip()
            return None

        name = get(
            "Monument_Name", "monument_name", "Monument Name",
            "MONUMENT_NAME", "name", "Name", "monument"
        )
        state = get("State", "STATE", "state")
        district = get("District", "DISTRICT", "district")
        circle = get("Circle", "ASI_Circle", "ASI Circle", "asi_circle", "circle")
        serial = get("Serialno", "S.No", "serial_no", "SERIAL_NO", "sl_no")

        if not name:
            return None

        return {
            "name": name,
            "state": state,
            "district": district,
            "asi_circle": circle,
            "asi_id": serial,
        }

    async def fetch_asi_monuments(self) -> list[dict[str, Any]]:
        """
        Try all available methods to fetch ASI monuments.
        Returns list of raw records (not normalized).
        """
        if not self.api_key:
            return []

        # Try API v2 with each resource ID
        for resource_id in ASI_RESOURCE_IDS:
            logger.info(f"Trying data.gov.in API v2 with resource: {resource_id}")
            records = await self._try_api_v2(resource_id)
            if records:
                logger.info(f"API v2 success: {len(records)} records")
                return records
            await asyncio.sleep(2)

        # Try API v1 with each resource ID
        for resource_id in ASI_RESOURCE_IDS:
            logger.info(f"Trying data.gov.in API v1 with resource: {resource_id}")
            records = await self._try_api_v1(resource_id)
            if records:
                logger.info(f"API v1 success: {len(records)} records")
                return records
            await asyncio.sleep(2)

        logger.warning(
            "All data.gov.in API attempts failed.\n"
            "This is a known data.gov.in API instability issue.\n"
            "The dataset can be manually downloaded from:\n"
            "https://data.gov.in/resource/district-wise-list-centrally-protected-monuments\n"
            "Save the CSV as: data/raw/datagov/asi_monuments.csv"
        )
        return []

    def load_from_csv(self, csv_path: Path | None = None) -> list[dict[str, Any]]:
        """Load ASI monuments from a manually-downloaded CSV file."""
        path = csv_path or (OUTPUT_DIR / "asi_monuments.csv")
        if not path.exists():
            return []
        records = []
        with open(path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(dict(row))
        logger.info(f"Loaded {len(records)} records from CSV: {path}")
        return records

    def save(self, raw_records: list[dict], normalized: list[dict]) -> None:
        """Save raw and normalized records to disk."""
        raw_file = OUTPUT_DIR / "asi_monuments_raw.jsonl"
        with open(raw_file, "w", encoding="utf-8") as f:
            for r in raw_records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        norm_file = OUTPUT_DIR / "asi_monuments_normalized.jsonl"
        with open(norm_file, "w", encoding="utf-8") as f:
            for r in normalized:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

        logger.info(f"Saved {len(raw_records)} ASI records")

    async def run(self) -> list[dict[str, Any]]:
        """Full extraction run. Returns normalized records."""
        # Try API first
        raw_records = await self.fetch_asi_monuments()

        # If API fails, try manual CSV
        if not raw_records:
            raw_records = self.load_from_csv()

        if not raw_records:
            return []

        normalized = [
            n for r in raw_records
            if (n := self.normalize_record(r)) is not None
        ]
        self.save(raw_records, normalized)
        return normalized


# ── Phase 1 Validation ────────────────────────────────────────────────────────

async def validate_datagov() -> None:
    print("\n" + "=" * 60)
    print("ARKANA -- data.gov.in ASI Extractor Validation (v2)")
    print("=" * 60)

    if not DATAGOV_API_KEY:
        print("\n  SKIPPED -- DATAGOV_API_KEY not set.")
        print("  Register at https://data.gov.in/user/register (free)")
        return

    extractor = DataGovExtractor()
    try:
        normalized = await extractor.run()
    finally:
        await extractor.close()

    if not normalized:
        print("\n  FAILED -- No records fetched.")
        print("  If API fails persistently:")
        print("  1. Download CSV manually from data.gov.in")
        print("  2. Save to: data/raw/datagov/asi_monuments.csv")
        print("  3. The extractor will auto-detect and load it.")
        return

    states = {}
    for r in normalized:
        state = r.get("state") or "Unknown"
        states[state] = states.get(state, 0) + 1

    print(f"\nTotal ASI monument records: {len(normalized)}")
    print(f"\nTop 10 states by monument count:")
    for state, count in sorted(states.items(), key=lambda x: -x[1])[:10]:
        print(f"  {state:<30} {count:>6}")

    print(f"\nOutput: {OUTPUT_DIR}")
    print("\ndata.gov.in validation complete")


if __name__ == "__main__":
    asyncio.run(validate_datagov())
