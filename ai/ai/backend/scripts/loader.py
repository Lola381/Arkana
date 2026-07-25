"""
Arkana — PostgreSQL Loader (Phase 2.3)
=======================================

Reads canonical_sites.jsonl and loads all records into the PostgreSQL
heritage_sites and site_images tables using idempotent upserts.

Strategy:
  - Primary key for upserts: wikidata_qid (UNIQUE constraint in schema)
  - Records without a wikidata_qid use name+state as conflict key fallback
  - coordinates are serialized as ST_GeogFromText('SRID=4326;POINT(lon lat)')
  - related_entities dict → JSONB
  - list fields → PostgreSQL TEXT[] arrays
  - site_images are inserted/upserted per-site into site_images table
  - ingestion_log entries written for every site (success, error, or duplicate)

Run from the project root:
    python -m scripts.loader [--input PATH] [--dry-run] [--batch-size N] [--log-level LEVEL]

Options:
    --input PATH       Path to canonical_sites.jsonl. Default: data/processed/canonical_sites.jsonl
    --dry-run          Parse and validate all records but do NOT write to PostgreSQL.
    --batch-size N     Records per commit batch. Default: 200.
    --log-level LEVEL  Logging verbosity. Default: INFO.

Prerequisites:
    - Docker postgres container running:  docker compose up -d postgres
    - Tables created via init.sql:        confirmed by docker-entrypoint-initdb.d
    - pip install psycopg2-binary pygeohash
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Ensure project root is importable ─────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import (
    POSTGRES_DB,
    POSTGRES_HOST,
    POSTGRES_PASSWORD,
    POSTGRES_PORT,
    POSTGRES_USER,
    PROCESSED_DIR,
)
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_INPUT = PROCESSED_DIR / "canonical_sites.jsonl"
DEFAULT_BATCH_SIZE = 200

# ── Upsert SQL ────────────────────────────────────────────────────────────────
# Primary conflict key: wikidata_qid (globally unique).
# ON CONFLICT DO UPDATE ensures idempotency — re-running loader is always safe.
UPSERT_SITE_SQL = """
INSERT INTO heritage_sites (
    wikidata_qid,
    wikipedia_title,
    osm_id,
    asi_id,
    unesco_id,
    name,
    alternate_names,
    description,
    short_summary,
    description_quality,
    state,
    district,
    address,
    coordinates,
    coord_source,
    coord_conflict,
    geohash,
    category,
    category_tags,
    is_unesco_whs,
    is_asi_protected,
    heritage_designations,
    historical_era,
    historical_start_year,
    historical_end_year,
    historical_certainty,
    commissioned_by,
    source_wikipedia,
    source_wikidata,
    source_unesco,
    source_osm,
    source_official_website,
    citations,
    related_entities,
    data_sources,
    data_quality_score,
    ingestion_version,
    created_at,
    updated_at
)
VALUES (
    %(wikidata_qid)s,
    %(wikipedia_title)s,
    %(osm_id)s,
    %(asi_id)s,
    %(unesco_id)s,
    %(name)s,
    %(alternate_names)s,
    %(description)s,
    %(short_summary)s,
    %(description_quality)s,
    %(state)s,
    %(district)s,
    %(address)s,
    %(coordinates)s,
    %(coord_source)s,
    %(coord_conflict)s,
    %(geohash)s,
    %(category)s,
    %(category_tags)s,
    %(is_unesco_whs)s,
    %(is_asi_protected)s,
    %(heritage_designations)s,
    %(historical_era)s,
    %(historical_start_year)s,
    %(historical_end_year)s,
    %(historical_certainty)s,
    %(commissioned_by)s,
    %(source_wikipedia)s,
    %(source_wikidata)s,
    %(source_unesco)s,
    %(source_osm)s,
    %(source_official_website)s,
    %(citations)s,
    %(related_entities)s,
    %(data_sources)s,
    %(data_quality_score)s,
    %(ingestion_version)s,
    %(created_at)s,
    %(updated_at)s
)
ON CONFLICT (wikidata_qid) DO UPDATE SET
    wikipedia_title        = EXCLUDED.wikipedia_title,
    osm_id                 = COALESCE(EXCLUDED.osm_id, heritage_sites.osm_id),
    asi_id                 = COALESCE(EXCLUDED.asi_id, heritage_sites.asi_id),
    unesco_id              = COALESCE(EXCLUDED.unesco_id, heritage_sites.unesco_id),
    name                   = EXCLUDED.name,
    alternate_names        = EXCLUDED.alternate_names,
    description            = EXCLUDED.description,
    short_summary          = EXCLUDED.short_summary,
    description_quality    = EXCLUDED.description_quality,
    state                  = EXCLUDED.state,
    district               = COALESCE(EXCLUDED.district, heritage_sites.district),
    address                = COALESCE(EXCLUDED.address, heritage_sites.address),
    coordinates            = COALESCE(EXCLUDED.coordinates, heritage_sites.coordinates),
    coord_source           = EXCLUDED.coord_source,
    coord_conflict         = EXCLUDED.coord_conflict,
    geohash                = EXCLUDED.geohash,
    category               = EXCLUDED.category,
    category_tags          = EXCLUDED.category_tags,
    is_unesco_whs          = EXCLUDED.is_unesco_whs,
    is_asi_protected       = EXCLUDED.is_asi_protected,
    heritage_designations  = EXCLUDED.heritage_designations,
    historical_era         = COALESCE(EXCLUDED.historical_era, heritage_sites.historical_era),
    historical_start_year  = COALESCE(EXCLUDED.historical_start_year, heritage_sites.historical_start_year),
    historical_end_year    = COALESCE(EXCLUDED.historical_end_year, heritage_sites.historical_end_year),
    historical_certainty   = EXCLUDED.historical_certainty,
    commissioned_by        = COALESCE(EXCLUDED.commissioned_by, heritage_sites.commissioned_by),
    source_wikipedia       = COALESCE(EXCLUDED.source_wikipedia, heritage_sites.source_wikipedia),
    source_wikidata        = COALESCE(EXCLUDED.source_wikidata, heritage_sites.source_wikidata),
    source_unesco          = COALESCE(EXCLUDED.source_unesco, heritage_sites.source_unesco),
    source_osm             = COALESCE(EXCLUDED.source_osm, heritage_sites.source_osm),
    source_official_website = COALESCE(EXCLUDED.source_official_website, heritage_sites.source_official_website),
    citations              = EXCLUDED.citations,
    related_entities       = EXCLUDED.related_entities,
    data_sources           = EXCLUDED.data_sources,
    data_quality_score     = EXCLUDED.data_quality_score,
    ingestion_version      = EXCLUDED.ingestion_version,
    updated_at             = NOW()
RETURNING site_id, (xmax = 0) AS is_insert
"""

# Upsert for records with NO wikidata_qid — conflict on name alone is too risky,
# so we do a plain INSERT with ON CONFLICT DO NOTHING (duplicates skipped).
INSERT_NOQID_SITE_SQL = """
INSERT INTO heritage_sites (
    wikidata_qid, wikipedia_title, osm_id, asi_id, unesco_id,
    name, alternate_names, description, short_summary, description_quality,
    state, district, address,
    coordinates, coord_source, coord_conflict, geohash,
    category, category_tags,
    is_unesco_whs, is_asi_protected, heritage_designations,
    historical_era, historical_start_year, historical_end_year, historical_certainty,
    commissioned_by,
    source_wikipedia, source_wikidata, source_unesco, source_osm, source_official_website,
    citations, related_entities, data_sources,
    data_quality_score, ingestion_version, created_at, updated_at
)
VALUES (
    %(wikidata_qid)s, %(wikipedia_title)s, %(osm_id)s, %(asi_id)s, %(unesco_id)s,
    %(name)s, %(alternate_names)s, %(description)s, %(short_summary)s, %(description_quality)s,
    %(state)s, %(district)s, %(address)s,
    %(coordinates)s, %(coord_source)s, %(coord_conflict)s, %(geohash)s,
    %(category)s, %(category_tags)s,
    %(is_unesco_whs)s, %(is_asi_protected)s, %(heritage_designations)s,
    %(historical_era)s, %(historical_start_year)s, %(historical_end_year)s, %(historical_certainty)s,
    %(commissioned_by)s,
    %(source_wikipedia)s, %(source_wikidata)s, %(source_unesco)s, %(source_osm)s, %(source_official_website)s,
    %(citations)s, %(related_entities)s, %(data_sources)s,
    %(data_quality_score)s, %(ingestion_version)s, %(created_at)s, %(updated_at)s
)
ON CONFLICT DO NOTHING
RETURNING site_id
"""

UPDATE_NOQID_SITE_SQL = """
UPDATE heritage_sites SET
    wikipedia_title        = %(wikipedia_title)s,
    osm_id                 = COALESCE(%(osm_id)s, heritage_sites.osm_id),
    asi_id                 = COALESCE(%(asi_id)s, heritage_sites.asi_id),
    unesco_id              = COALESCE(%(unesco_id)s, heritage_sites.unesco_id),
    name                   = %(name)s,
    alternate_names        = %(alternate_names)s,
    description            = %(description)s,
    short_summary          = %(short_summary)s,
    description_quality    = %(description_quality)s,
    state                  = %(state)s,
    district               = COALESCE(%(district)s, heritage_sites.district),
    address                = COALESCE(%(address)s, heritage_sites.address),
    coordinates            = COALESCE(%(coordinates)s, heritage_sites.coordinates),
    coord_source           = %(coord_source)s,
    coord_conflict         = %(coord_conflict)s,
    geohash                = %(geohash)s,
    category               = %(category)s,
    category_tags          = %(category_tags)s,
    is_unesco_whs          = %(is_unesco_whs)s,
    is_asi_protected       = %(is_asi_protected)s,
    heritage_designations  = %(heritage_designations)s,
    historical_era         = COALESCE(%(historical_era)s, heritage_sites.historical_era),
    historical_start_year  = COALESCE(%(historical_start_year)s, heritage_sites.historical_start_year),
    historical_end_year    = COALESCE(%(historical_end_year)s, heritage_sites.historical_end_year),
    historical_certainty   = %(historical_certainty)s,
    commissioned_by        = COALESCE(%(commissioned_by)s, heritage_sites.commissioned_by),
    source_wikipedia       = COALESCE(%(source_wikipedia)s, heritage_sites.source_wikipedia),
    source_wikidata        = COALESCE(%(source_wikidata)s, heritage_sites.source_wikidata),
    source_unesco          = COALESCE(%(source_unesco)s, heritage_sites.source_unesco),
    source_osm             = COALESCE(%(source_osm)s, heritage_sites.source_osm),
    source_official_website = COALESCE(%(source_official_website)s, heritage_sites.source_official_website),
    citations              = %(citations)s,
    related_entities       = %(related_entities)s,
    data_sources           = %(data_sources)s,
    data_quality_score     = %(data_quality_score)s,
    ingestion_version      = %(ingestion_version)s,
    updated_at             = NOW()
WHERE site_id = %(target_site_id)s
RETURNING site_id
"""

UPSERT_IMAGE_SQL = """
INSERT INTO site_images (site_id, url, thumbnail_url, license, author, source, commons_filename)
VALUES (%(site_id)s, %(url)s, %(thumbnail_url)s, %(license)s, %(author)s, %(source)s, %(commons_filename)s)
ON CONFLICT DO NOTHING
"""

INSERT_LOG_SQL = """
INSERT INTO ingestion_log (site_id, wikidata_qid, source_name, status, error_message, raw_record_id)
VALUES (%(site_id)s, %(wikidata_qid)s, %(source_name)s, %(status)s, %(error_message)s, %(raw_record_id)s)
"""


# ══════════════════════════════════════════════════════════════════════════════
# Type Conversion Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _to_pg_array(value: Any) -> list | None:
    """Convert a list (or empty string) to a PostgreSQL-compatible Python list."""
    if value is None:
        return None
    if isinstance(value, list):
        # Filter out None/empty and stringify everything
        return [str(v) for v in value if v is not None and str(v).strip()]
    if isinstance(value, str):
        # Guard against accidental string serialisation
        if not value.strip():
            return []
        return [value]
    return []


def _to_pg_jsonb(value: Any) -> str | None:
    """Serialize a dict to a JSON string for JSONB insertion via psycopg2."""
    if value is None:
        return None
    if isinstance(value, dict):
        # Normalize nested lists (handle empty-string serialization artefacts)
        cleaned: dict[str, Any] = {}
        for k, v in value.items():
            if isinstance(v, list):
                cleaned[k] = [str(item) for item in v if item is not None and str(item).strip()]
            elif isinstance(v, str):
                cleaned[k] = v if v.strip() else None
            else:
                cleaned[k] = v
        return json.dumps(cleaned, ensure_ascii=False)
    return json.dumps(value, ensure_ascii=False)


def _to_pg_geography(coords: dict | None) -> str | None:
    """
    Convert a Coordinates dict to a PostGIS WKT geography string.
    Format: 'SRID=4326;POINT(lon lat)'   <-- lon THEN lat (OGC standard)
    psycopg2 passes this as a literal string; PostGIS recognises it via ST_GeogFromText.
    """
    if not coords:
        return None
    lat = coords.get("lat")
    lon = coords.get("lon")
    if lat is None or lon is None:
        return None
    try:
        lat = float(lat)
        lon = float(lon)
        # Basic India bounds sanity check
        if not (6.0 <= lat <= 38.0 and 68.0 <= lon <= 98.0):
            logger.debug(f"Skipping out-of-bounds coords: lat={lat}, lon={lon}")
            return None
        return f"SRID=4326;POINT({lon} {lat})"
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str | None:
    """Return a stripped string or None."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _to_pg_datetime(value: Any) -> datetime | None:
    """Parse an ISO datetime string to a Python datetime (timezone-aware)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    try:
        # Handle both naive and aware ISO strings
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return datetime.now(timezone.utc)


def build_site_params(record: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a canonical_sites.jsonl record dict into the parameter dict
    expected by the UPSERT SQL.

    This is the critical type-mapping layer between Pydantic JSON output
    and PostgreSQL column types.
    """
    coords = record.get("coordinates")
    location = record.get("location") or {}
    heritage = record.get("heritage_status") or {}
    hist = record.get("historical_period") or {}
    urls = record.get("source_urls") or {}
    related = record.get("related_entities") or {}

    return {
        # Identity
        "wikidata_qid": _safe_str(record.get("wikidata_qid")),
        "wikipedia_title": _safe_str(record.get("wikipedia_title")),
        "osm_id": _safe_str(record.get("osm_id")),
        "asi_id": _safe_str(record.get("asi_id")),
        "unesco_id": _safe_str(record.get("unesco_id")),

        # Core
        "name": _safe_str(record.get("name")) or "UNKNOWN",
        "alternate_names": _to_pg_array(record.get("alternate_names")),
        "description": _safe_str(record.get("description")),
        "short_summary": _safe_str(record.get("short_summary")),
        "description_quality": _safe_str(record.get("description_quality")) or "missing",

        # Location
        "state": _safe_str(location.get("state")),
        "district": _safe_str(location.get("district")),
        "address": _safe_str(location.get("address")),

        # Coordinates — passed as WKT string; psycopg2 uses %s literal
        "coordinates": _to_pg_geography(coords),
        "coord_source": _safe_str(coords.get("source")) if coords else None,
        "coord_conflict": bool(coords.get("coordinate_conflict", False)) if coords else False,
        "geohash": _safe_str(coords.get("geohash")) if coords else None,

        # Classification
        "category": _safe_str(record.get("category")) or "unknown",
        "category_tags": _to_pg_array(record.get("category_tags")),

        # Heritage status
        "is_unesco_whs": bool(heritage.get("is_unesco_whs", False)),
        "is_asi_protected": bool(heritage.get("is_asi_protected", False)),
        "heritage_designations": _to_pg_array(heritage.get("heritage_designations")),

        # Historical period
        "historical_era": _safe_str(hist.get("era")),
        "historical_start_year": hist.get("start_year"),
        "historical_end_year": hist.get("end_year"),
        "historical_certainty": _safe_str(hist.get("certainty")) or "unknown",
        "commissioned_by": _safe_str(record.get("commissioned_by")),

        # Source URLs (flattened into individual columns)
        "source_wikipedia": _safe_str(urls.get("wikipedia")),
        "source_wikidata": _safe_str(urls.get("wikidata")),
        "source_unesco": _safe_str(urls.get("unesco")),
        "source_osm": _safe_str(urls.get("osm")),
        "source_official_website": _safe_str(urls.get("official_website")),
        "citations": _to_pg_array(record.get("citations")),

        # Related entities → JSONB
        "related_entities": _to_pg_jsonb(related),

        # Ingestion metadata
        "data_sources": _to_pg_array(record.get("data_sources")),
        "data_quality_score": float(record.get("data_quality_score") or 0.0),
        "ingestion_version": _safe_str(record.get("ingestion_version")) or "1.0",
        "created_at": _to_pg_datetime(record.get("created_at")),
        "updated_at": _to_pg_datetime(record.get("updated_at")),
    }


def build_image_params(site_uuid: str, image: dict | str) -> dict[str, Any] | None:
    """Build parameter dict for site_images INSERT from an image record."""
    if isinstance(image, str):
        # Malformed — plain string stored as image entry
        url = image.strip()
        if not url or not url.startswith("http"):
            return None
        return {
            "site_id": site_uuid,
            "url": url,
            "thumbnail_url": None,
            "license": None,
            "author": None,
            "source": "unknown",
            "commons_filename": None,
        }
    if not isinstance(image, dict):
        return None
    url = _safe_str(image.get("url"))
    if not url:
        return None
    return {
        "site_id": site_uuid,
        "url": url,
        "thumbnail_url": _safe_str(image.get("thumbnail_url")),
        "license": _safe_str(image.get("license")),
        "author": _safe_str(image.get("author")),
        "source": _safe_str(image.get("source")) or "wikimedia_commons",
        "commons_filename": _safe_str(image.get("commons_filename")),
    }


# ══════════════════════════════════════════════════════════════════════════════
# JSONL Reader
# ══════════════════════════════════════════════════════════════════════════════

def load_canonical_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load and parse canonical_sites.jsonl. Returns list of raw dicts."""
    if not path.exists():
        logger.error(f"Input file not found: {path}")
        logger.error("Run 'python -m scripts.pipeline --force' first to generate canonical output.")
        sys.exit(1)

    records: list[dict[str, Any]] = []
    corrupt = 0
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                corrupt += 1
                logger.warning(f"Line {lineno}: corrupt JSON — {e}")

    logger.info(f"Loaded {len(records)} records from {path.name} ({corrupt} corrupt lines skipped)")
    if corrupt > 0 and corrupt / max(len(records), 1) > 0.01:
        logger.error(
            f"Corruption rate {corrupt/(len(records)+corrupt)*100:.1f}% exceeds 1% threshold. "
            f"Re-run pipeline with --force before loading."
        )
        sys.exit(1)

    return records


# ══════════════════════════════════════════════════════════════════════════════
# Database Connection
# ══════════════════════════════════════════════════════════════════════════════

def get_connection():
    """Return a psycopg2 connection to the Arkana PostgreSQL database."""
    try:
        import psycopg2
        from psycopg2.extras import Json
    except ImportError:
        logger.error("psycopg2-binary not installed. Run: pip install psycopg2-binary")
        sys.exit(1)

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=10,
        )
        conn.autocommit = False
        logger.info(
            f"Connected to PostgreSQL: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
        )
        return conn
    except Exception as e:
        logger.error(
            f"Cannot connect to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB} — {e}"
        )
        logger.error(
            "Ensure Docker is running: docker compose up -d postgres"
        )
        sys.exit(1)


def verify_schema(conn) -> None:
    """
    Verify that the required tables exist.
    Raises RuntimeError if schema is not initialized.
    """
    required_tables = ["heritage_sites", "site_images", "ingestion_log"]
    with conn.cursor() as cur:
        for table in required_tables:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = %s",
                (table,),
            )
            if not cur.fetchone():
                raise RuntimeError(
                    f"Table '{table}' not found. "
                    f"Run 'docker compose up -d postgres' to initialize the schema."
                )
    logger.info(f"Schema verified: {required_tables}")


# ══════════════════════════════════════════════════════════════════════════════
# Core Load Function
# ══════════════════════════════════════════════════════════════════════════════

def load_records(
    records: list[dict[str, Any]],
    conn,
    batch_size: int = DEFAULT_BATCH_SIZE,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Load all records into PostgreSQL in batches.

    Returns:
        stats dict with inserted, updated, skipped, failed, image counts.
    """
    from psycopg2.extras import Json

    stats = {
        "total": len(records),
        "inserted": 0,
        "updated": 0,
        "skipped_no_qid": 0,
        "failed": 0,
        "images_inserted": 0,
        "images_failed": 0,
        "log_entries": 0,
    }

    log_buffer: list[dict[str, Any]] = []

    with conn.cursor() as cur:
        for i, record in enumerate(records):
            site_uuid: str | None = None
            is_insert: bool = False

            try:
                params = build_site_params(record)
                wikidata_qid = params.get("wikidata_qid")

                if dry_run:
                    # Validate params but don't execute
                    _ = params  # force evaluation
                    stats["inserted"] += 1
                    continue

                # ── Site upsert ─────────────────────────────────────────────
                if wikidata_qid:
                    # Use geography literal directly via mogrify-safe approach
                    # psycopg2 can't handle geography WKT as a plain %s with named params.
                    # We pass geography as a string and cast in SQL using ST_GeogFromText.
                    geo_wkt = params.pop("coordinates")
                    if geo_wkt:
                        params["coordinates"] = geo_wkt  # will be injected below
                        # Rebuild SQL to use ST_GeogFromText for this column
                        sql = UPSERT_SITE_SQL.replace(
                            "%(coordinates)s",
                            "ST_GeogFromText(%(coordinates)s)"
                        )
                    else:
                        params["coordinates"] = None
                        sql = UPSERT_SITE_SQL

                    # Serialize JSONB via psycopg2 Json adapter
                    params["related_entities"] = Json(
                        json.loads(params["related_entities"] or "{}")
                    )

                    cur.execute(sql, params)
                    row = cur.fetchone()
                    if row:
                        site_uuid = str(row[0])
                        is_insert = bool(row[1])
                        if is_insert:
                            stats["inserted"] += 1
                        else:
                            stats["updated"] += 1
                    else:
                        stats["skipped_no_qid"] += 1

                else:
                    # No QID — check if record already exists by unesco_id or name+state
                    existing_uuid = None
                    if params.get("unesco_id"):
                        cur.execute("SELECT site_id FROM heritage_sites WHERE unesco_id = %s LIMIT 1", (params["unesco_id"],))
                        ex_row = cur.fetchone()
                        if ex_row:
                            existing_uuid = str(ex_row[0])
                    if not existing_uuid and params.get("name"):
                        cur.execute("SELECT site_id FROM heritage_sites WHERE wikidata_qid IS NULL AND name = %s AND COALESCE(state, '') = COALESCE(%s, '') LIMIT 1", (params["name"], params.get("state")))
                        ex_row = cur.fetchone()
                        if ex_row:
                            existing_uuid = str(ex_row[0])

                    geo_wkt = params.pop("coordinates")
                    if existing_uuid:
                        params["target_site_id"] = existing_uuid
                        if geo_wkt:
                            params["coordinates"] = geo_wkt
                            sql = UPDATE_NOQID_SITE_SQL.replace(
                                "%(coordinates)s",
                                "ST_GeogFromText(%(coordinates)s)"
                            )
                        else:
                            params["coordinates"] = None
                            sql = UPDATE_NOQID_SITE_SQL
                    else:
                        if geo_wkt:
                            params["coordinates"] = geo_wkt
                            sql = INSERT_NOQID_SITE_SQL.replace(
                                "%(coordinates)s",
                                "ST_GeogFromText(%(coordinates)s)"
                            )
                        else:
                            params["coordinates"] = None
                            sql = INSERT_NOQID_SITE_SQL

                    params["related_entities"] = Json(
                        json.loads(params["related_entities"] or "{}")
                    )

                    cur.execute(sql, params)
                    row = cur.fetchone()
                    if row:
                        site_uuid = str(row[0])
                        if existing_uuid:
                            stats["updated"] += 1
                        else:
                            stats["inserted"] += 1
                    else:
                        stats["skipped_no_qid"] += 1

                # ── Images ──────────────────────────────────────────────────
                if site_uuid:
                    images = record.get("images") or []
                    for image in images:
                        img_params = build_image_params(site_uuid, image)
                        if img_params:
                            try:
                                cur.execute("SAVEPOINT img_insert")
                                cur.execute(UPSERT_IMAGE_SQL, img_params)
                                cur.execute("RELEASE SAVEPOINT img_insert")
                                stats["images_inserted"] += 1
                            except Exception as img_err:
                                cur.execute("ROLLBACK TO SAVEPOINT img_insert")
                                logger.debug(f"Image insert failed for site {site_uuid}: {img_err}")
                                stats["images_failed"] += 1

                # ── Ingestion log entry ──────────────────────────────────────
                data_sources = record.get("data_sources") or []
                primary_source = data_sources[0] if data_sources else "unknown"
                log_buffer.append({
                    "site_id": site_uuid,
                    "wikidata_qid": record.get("wikidata_qid"),
                    "source_name": primary_source,
                    "status": "success",
                    "error_message": None,
                    "raw_record_id": record.get("wikidata_qid") or record.get("site_id"),
                })

            except Exception as e:
                stats["failed"] += 1
                name = record.get("name", "?")
                qid = record.get("wikidata_qid", "no-qid")
                logger.warning(f"Load failed for '{name}' ({qid}): {e}")
                try:
                    conn.rollback()
                except Exception:
                    pass

                log_buffer.append({
                    "site_id": None,
                    "wikidata_qid": record.get("wikidata_qid"),
                    "source_name": (record.get("data_sources") or ["unknown"])[0],
                    "status": "error",
                    "error_message": str(e)[:500],
                    "raw_record_id": record.get("wikidata_qid") or record.get("site_id"),
                })

            # ── Batch commit ─────────────────────────────────────────────────
            if (i + 1) % batch_size == 0:
                if not dry_run:
                    # Flush log buffer before commit
                    _flush_log_buffer(cur, log_buffer)
                    log_buffer.clear()
                    conn.commit()
                processed = stats["inserted"] + stats["updated"] + stats["skipped_no_qid"] + stats["failed"]
                logger.info(
                    f"Batch committed: {i+1}/{len(records)} records processed "
                    f"(ins={stats['inserted']}, upd={stats['updated']}, "
                    f"skip={stats['skipped_no_qid']}, fail={stats['failed']})"
                )

        # ── Final commit ──────────────────────────────────────────────────────
        if not dry_run:
            _flush_log_buffer(cur, log_buffer)
            stats["log_entries"] = stats["inserted"] + stats["updated"] + stats["skipped_no_qid"] + stats["failed"]
            log_buffer.clear()
            conn.commit()
            logger.info("Final batch committed.")

    return stats


def _flush_log_buffer(cur, log_buffer: list[dict[str, Any]]) -> None:
    """Write buffered ingestion log entries."""
    for entry in log_buffer:
        try:
            cur.execute(INSERT_LOG_SQL, entry)
        except Exception as e:
            logger.debug(f"Log entry write failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# Validation
# ══════════════════════════════════════════════════════════════════════════════

def validate_row_counts(
    conn,
    expected_sites: int,
    expected_images: int,
) -> dict[str, Any]:
    """
    Query the database to verify row counts match expectations.
    Returns a validation result dict.
    """
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM heritage_sites")
        db_sites = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM site_images")
        db_images = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ingestion_log WHERE status = 'success'")
        db_log_success = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ingestion_log WHERE status = 'error'")
        db_log_errors = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM heritage_sites WHERE coordinates IS NOT NULL"
        )
        db_with_coords = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM heritage_sites WHERE description_quality = 'full'"
        )
        db_rag_eligible = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM heritage_sites WHERE is_unesco_whs = TRUE"
        )
        db_unesco = cur.fetchone()[0]

        cur.execute(
            "SELECT AVG(data_quality_score) FROM heritage_sites"
        )
        db_avg_score = cur.fetchone()[0] or 0.0

        # Category breakdown
        cur.execute(
            "SELECT category, COUNT(*) as n FROM heritage_sites "
            "GROUP BY category ORDER BY n DESC LIMIT 10"
        )
        db_categories = cur.fetchall()

    # Sites count should be >= expected (can be higher if prior runs inserted records
    # without QIDs that couldn't be upserted-over)
    sites_ok = db_sites >= (expected_sites * 0.95)  # allow 5% tolerance for no-QID skips

    return {
        "db_sites": db_sites,
        "expected_sites": expected_sites,
        "sites_ok": sites_ok,
        "db_images": db_images,
        "expected_images": expected_images,
        "db_log_success": db_log_success,
        "db_log_errors": db_log_errors,
        "db_with_coords": db_with_coords,
        "db_rag_eligible": db_rag_eligible,
        "db_unesco": db_unesco,
        "db_avg_score": round(float(db_avg_score), 4),
        "db_categories": db_categories,
    }


def print_load_report(
    stats: dict[str, Any],
    validation: dict[str, Any] | None,
    elapsed: float,
    dry_run: bool,
) -> None:
    """Print a structured load report."""
    sep = "-" * 62
    mode = "[DRY-RUN — no data written]" if dry_run else ""
    print(f"\n{sep}")
    print(f"  ARKANA LOADER -- LOAD REPORT  {mode}")
    print(sep)

    print("\n[RECORDS PROCESSED]")
    print(f"   Total input:         {stats['total']:>6}")
    print(f"   Inserted (new):      {stats['inserted']:>6}")
    print(f"   Updated (existing):  {stats['updated']:>6}")
    print(f"   Skipped (no QID):    {stats['skipped_no_qid']:>6}")
    print(f"   Failed:              {stats['failed']:>6}")

    print("\n[IMAGES]")
    print(f"   Images inserted:     {stats['images_inserted']:>6}")
    print(f"   Images failed:       {stats['images_failed']:>6}")

    if validation:
        print("\n[DATABASE VERIFICATION]")
        sites_status = "OK" if validation["sites_ok"] else "WARN"
        print(f"   heritage_sites:      {validation['db_sites']:>6}  [{sites_status}] (expected ~{validation['expected_sites']})")
        print(f"   site_images:         {validation['db_images']:>6}")
        print(f"   With coordinates:    {validation['db_with_coords']:>6}  ({validation['db_with_coords']/max(validation['db_sites'],1)*100:.1f}%)")
        print(f"   RAG-eligible:        {validation['db_rag_eligible']:>6}  ({validation['db_rag_eligible']/max(validation['db_sites'],1)*100:.1f}%)")
        print(f"   UNESCO WHS:          {validation['db_unesco']:>6}")
        print(f"   Avg quality score:   {validation['db_avg_score']:>8.4f}")
        print(f"   Log entries (ok):    {validation['db_log_success']:>6}")
        print(f"   Log entries (err):   {validation['db_log_errors']:>6}")

        print("\n[DATABASE CATEGORY DISTRIBUTION]")
        for cat, count in validation["db_categories"]:
            print(f"   {(cat or 'null'):<25} {count:>6}")

        if not validation["sites_ok"]:
            print("\n  [!] WARNING: DB site count is significantly below expected.")
            print("      Check logs for failed inserts.")

    throughput = stats["total"] / max(elapsed, 0.001)
    print(f"\n[TIMING]")
    print(f"   Elapsed:             {elapsed:>6.1f}s")
    print(f"   Throughput:          {throughput:>6.0f} records/sec")
    print(f"\n{sep}\n")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def run_loader(
    input_path: Path = DEFAULT_INPUT,
    dry_run: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> dict[str, Any]:
    """
    Execute the full load pipeline.

    Returns:
        stats dict from load_records.
    """
    start = time.monotonic()

    logger.info("=" * 62)
    logger.info("  ARKANA POSTGRESQL LOADER -- STARTING")
    logger.info("=" * 62)
    logger.info(f"Input: {input_path}  |  dry_run={dry_run}  |  batch_size={batch_size}")

    # ── Step 1: Load JSONL ────────────────────────────────────────────────────
    logger.info("\n[Step 1/4] Loading canonical_sites.jsonl...")
    records = load_canonical_jsonl(input_path)
    total_images = sum(len(r.get("images") or []) for r in records)
    logger.info(f"  {len(records)} sites, {total_images} images to load")

    if dry_run:
        logger.info("\n[Step 2/4] DRY-RUN: Validating all record mappings...")
        errors = 0
        for i, record in enumerate(records):
            try:
                build_site_params(record)
            except Exception as e:
                errors += 1
                logger.warning(f"Record {i} ('{record.get('name')}'): mapping error — {e}")
        logger.info(f"  Mapping validation complete: {errors} errors out of {len(records)} records")
        elapsed = time.monotonic() - start
        stats = {
            "total": len(records),
            "inserted": len(records) - errors,
            "updated": 0,
            "skipped_no_qid": 0,
            "failed": errors,
            "images_inserted": 0,
            "images_failed": 0,
            "log_entries": 0,
        }
        print_load_report(stats, None, elapsed, dry_run=True)
        return stats

    # ── Step 2: Connect + verify schema ──────────────────────────────────────
    logger.info("\n[Step 2/4] Connecting to PostgreSQL and verifying schema...")
    conn = get_connection()
    try:
        verify_schema(conn)
    except RuntimeError as e:
        logger.error(str(e))
        conn.close()
        sys.exit(1)

    # ── Step 3: Load records ──────────────────────────────────────────────────
    logger.info(f"\n[Step 3/4] Loading {len(records)} records in batches of {batch_size}...")
    try:
        stats = load_records(records, conn, batch_size=batch_size, dry_run=False)
    except Exception as e:
        logger.error(f"Load failed with unhandled exception: {e}")
        conn.rollback()
        conn.close()
        raise

    # ── Step 4: Validate row counts ───────────────────────────────────────────
    logger.info("\n[Step 4/4] Validating database row counts...")
    try:
        validation = validate_row_counts(conn, len(records), total_images)
    except Exception as e:
        logger.error(f"Validation query failed: {e}")
        validation = None
    finally:
        conn.close()

    elapsed = time.monotonic() - start
    print_load_report(stats, validation, elapsed, dry_run=False)

    # Exit with error code if load had significant failures
    if stats["failed"] > 0:
        fail_rate = stats["failed"] / max(stats["total"], 1)
        if fail_rate > 0.05:
            logger.error(
                f"Failure rate {fail_rate*100:.1f}% exceeds 5% threshold. "
                f"Review logs and re-run."
            )
            sys.exit(3)
        else:
            logger.warning(
                f"{stats['failed']} records failed ({fail_rate*100:.1f}%). "
                f"Within tolerance — check logs for details."
            )

    return stats


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Arkana PostgreSQL Loader -- Phase 2.3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to canonical_sites.jsonl. Default: {DEFAULT_INPUT}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Parse and validate all records but do NOT write to PostgreSQL.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"Records per commit batch. Default: {DEFAULT_BATCH_SIZE}.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity. Default: INFO.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    import logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    run_loader(
        input_path=args.input,
        dry_run=args.dry_run,
        batch_size=args.batch_size,
    )
