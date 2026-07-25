"""
Arkana — ETL Pipeline Orchestrator (Phase 2)
=============================================

Wires all Phase 2 transformer modules together in dependency order:

  data/raw/  (JSONL checkpoints)
      │
      ▼ Step 1: Load + parse all sources to HeritageSite objects
      │
      ▼ Step 2: Apply normalizer functions to each record
      │
      ▼ Step 3: Merge all sources into one list
      │
      ▼ Step 4: Deduplicator.deduplicate()  (QID exact → fuzzy name)
      │
      ▼ Step 5: Enricher.enrich_batch()     (coords, desc, geohash, categories)
      │
      ▼ Step 6: Validate output integrity
      │
      ▼ Step 7: Save canonical_sites.jsonl  → data/processed/
      │
      ▼ Step 8: Print quality stats report

Run from the project root:
    python -m scripts.pipeline [--dry-run] [--sources wikidata,unesco,osm,wikipedia]

Options:
    --dry-run           Run full pipeline but do NOT write output file.
    --sources SOURCE    Comma-separated list of sources to include.
                        Choices: wikidata, unesco (osm/wikipedia feed the Enricher, not the site list)
                        Default: wikidata,unesco
    --limit N           Process at most N sites (useful for development testing).
    --log-level LEVEL   Logging verbosity. Default: INFO.
    --force             Overwrite existing canonical_sites.jsonl even if it exists.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows (avoids CP1252 UnicodeEncodeError for box-drawing chars)
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Ensure project root is on sys.path so ingestion package is importable ──────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ingestion.config import (
    PROCESSED_DIR,
    RAW_DIR,
)
from ingestion.models.heritage_schema import (
    DataSource,
    DescriptionQuality,
    HeritageSite,
    SiteCategory,
)
from ingestion.transformers.deduplicator import Deduplicator
from ingestion.transformers.enricher import Enricher
from ingestion.transformers.normalizer import (
    clean_wikipedia_text,
    normalize_category_from_text,
    normalize_name,
    normalize_text,
    parse_year,
    validate_india_coordinates,
)
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

# ── Output path ────────────────────────────────────────────────────────────────
CANONICAL_OUTPUT = PROCESSED_DIR / "canonical_sites.jsonl"

# ── Source checkpoint paths ────────────────────────────────────────────────────
WIKIDATA_DIR = RAW_DIR / "wikidata"
UNESCO_FILE = RAW_DIR / "unesco" / "india_whs.jsonl"
OSM_FILE = RAW_DIR / "osm" / "osm_rajasthan_validation.jsonl"
WIKIPEDIA_FILE = RAW_DIR / "wikipedia" / "validation_sample.jsonl"


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Loaders
# ══════════════════════════════════════════════════════════════════════════════

def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load a JSONL file as a list of raw dicts. Returns [] if file missing."""
    if not path.exists():
        logger.warning(f"Checkpoint not found, skipping: {path}")
        return []
    records: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as e:
                logger.warning(f"{path.name}:{i}: JSON parse error — {e}")
    logger.info(f"Loaded {len(records)} records from {path.name}")
    return records


def load_wikidata_sites(limit: int | None = None) -> list[HeritageSite]:
    """
    Load all Wikidata JSONL checkpoints.
    Each record is already a serialized HeritageSite — validate directly.
    """
    all_sites: list[HeritageSite] = []
    jsonl_files = sorted(WIKIDATA_DIR.glob("*.jsonl")) if WIKIDATA_DIR.exists() else []

    if not jsonl_files:
        logger.warning(f"No Wikidata JSONL files found in {WIKIDATA_DIR}")
        return all_sites

    parse_errors = 0
    for path in jsonl_files:
        raw_records = _load_jsonl(path)
        for raw in raw_records:
            try:
                site = HeritageSite.model_validate(raw)
                all_sites.append(site)
            except Exception as e:
                parse_errors += 1
                logger.debug(f"Wikidata record parse failed ({raw.get('name', '?')}): {e}")

            if limit and len(all_sites) >= limit:
                logger.info(f"--limit {limit} reached during Wikidata load")
                return all_sites

    if parse_errors:
        logger.warning(f"Wikidata: {parse_errors} records failed model_validate")
    logger.info(f"Loaded {len(all_sites)} Wikidata HeritageSite records")
    return all_sites


def load_unesco_sites(limit: int | None = None) -> list[HeritageSite]:
    """
    Load UNESCO JSONL checkpoint.
    Each record is already a serialized HeritageSite — validate directly.
    """
    raw_records = _load_jsonl(UNESCO_FILE)
    sites: list[HeritageSite] = []
    parse_errors = 0
    for raw in raw_records:
        try:
            site = HeritageSite.model_validate(raw)
            sites.append(site)
        except Exception as e:
            parse_errors += 1
            logger.debug(f"UNESCO record parse failed ({raw.get('name', '?')}): {e}")
        if limit and len(sites) >= limit:
            break
    if parse_errors:
        logger.warning(f"UNESCO: {parse_errors} records failed model_validate")
    logger.info(f"Loaded {len(sites)} UNESCO HeritageSite records")
    return sites


def load_osm_records() -> list[dict[str, Any]]:
    """
    Load OSM checkpoint as raw dicts (not HeritageSite).
    OSM feeds the Enricher's coordinate lookup — not the primary site list.
    """
    return _load_jsonl(OSM_FILE)


def load_wikipedia_articles() -> dict[str, dict[str, Any]]:
    """
    Load Wikipedia checkpoint as a multi-key lookup.
    Indexed by: exact title, lowercase title, normalized name.
    Wikipedia feeds the Enricher's description and entity enrichment.
    """
    raw_records = _load_jsonl(WIKIPEDIA_FILE)
    by_title: dict[str, dict[str, Any]] = {}
    for record in raw_records:
        title = record.get("title")
        if title:
            # Index by exact title
            by_title[title] = record
            # Index by lowercase for case-insensitive fallback
            by_title[title.lower()] = record
            # Index by normalized name (strips common words) for fuzzy fallback
            norm = normalize_name(title)
            if norm:
                by_title[norm] = record
    logger.info(
        f"Loaded {len(raw_records)} Wikipedia articles → "
        f"{len(by_title)} lookup keys (title + lowercase + normalized)"
    )
    return by_title


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Normalizer pass
# ══════════════════════════════════════════════════════════════════════════════

def normalize_site(site: HeritageSite) -> HeritageSite:
    """
    Apply normalizer functions to a single HeritageSite in-place.
    All normalization is non-destructive: only fills or cleans existing fields.
    """
    # Normalize text fields
    if site.name:
        cleaned = normalize_text(site.name)
        if cleaned:
            site.name = cleaned

    if site.description:
        site.description = normalize_text(site.description)

    if site.short_summary:
        site.short_summary = normalize_text(site.short_summary)

    # Validate coordinates are within India's bounding box
    if site.coordinates:
        result = validate_india_coordinates(site.coordinates.lat, site.coordinates.lon)
        if result is None:
            logger.debug(
                f"Out-of-bounds coordinates dropped for '{site.name}': "
                f"({site.coordinates.lat}, {site.coordinates.lon})"
            )
            site.coordinates = None
        else:
            site.coordinates.lat, site.coordinates.lon = result

    # Parse/validate historical years
    if site.historical_period.start_year is not None:
        parsed = parse_year(site.historical_period.start_year)
        site.historical_period.start_year = parsed

    if site.historical_period.end_year is not None:
        parsed = parse_year(site.historical_period.end_year)
        site.historical_period.end_year = parsed

    # Infer category from name/description if still UNKNOWN
    if site.category == SiteCategory.UNKNOWN or site.category == "unknown":
        inferred = normalize_category_from_text(site.name, site.description)
        if inferred != SiteCategory.UNKNOWN:
            site.category = inferred

    # Recompute quality score after normalization
    site.compute_quality_score()
    return site


def normalize_batch(sites: list[HeritageSite]) -> list[HeritageSite]:
    """Apply normalizer to all sites. Skips on error, logging warnings."""
    normalized: list[HeritageSite] = []
    errors = 0
    for site in sites:
        try:
            normalized.append(normalize_site(site))
        except Exception as e:
            logger.warning(f"Normalization failed for '{site.name}' ({site.site_id}): {e}")
            normalized.append(site)  # Keep unnormalized rather than drop
            errors += 1
    if errors:
        logger.warning(f"Normalization completed with {errors} errors")
    return normalized


# ══════════════════════════════════════════════════════════════════════════════
# STEP 6 — Output integrity validator
# ══════════════════════════════════════════════════════════════════════════════

def validate_output_integrity(
    sites: list[HeritageSite],
    output_path: Path,
) -> dict[str, Any]:
    """
    Post-write integrity check: re-reads canonical_sites.jsonl and verifies:
      - Written record count matches in-memory count
      - All records have required fields (site_id, name, wikidata_qid or name)
      - No duplicate site_ids in output
      - Description quality distribution is sane

    Returns a dict with validation results. Raises RuntimeError on critical failures.
    """
    if not output_path.exists():
        raise RuntimeError(f"Output file not found after write: {output_path}")

    written_count = 0
    seen_site_ids: set[str] = set()
    duplicate_ids: list[str] = []
    missing_name: int = 0
    missing_site_id: int = 0
    corrupt_lines: int = 0

    desc_quality: Counter = Counter()

    with open(output_path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                corrupt_lines += 1
                continue

            written_count += 1

            sid = record.get("site_id")
            if not sid:
                missing_site_id += 1
            elif sid in seen_site_ids:
                duplicate_ids.append(sid)
            else:
                seen_site_ids.add(sid)

            if not record.get("name"):
                missing_name += 1

            dq = record.get("description_quality", "missing")
            desc_quality[dq] += 1

    # Critical checks
    expected = len(sites)
    if written_count != expected:
        raise RuntimeError(
            f"Output integrity FAILED: expected {expected} records, "
            f"found {written_count} in {output_path.name}"
        )
    if corrupt_lines:
        raise RuntimeError(
            f"Output integrity FAILED: {corrupt_lines} corrupt JSON lines in {output_path.name}"
        )

    # Warnings (non-fatal)
    if duplicate_ids:
        logger.warning(f"Duplicate site_ids in output: {len(duplicate_ids)} ({duplicate_ids[:5]}...)")
    if missing_name:
        logger.warning(f"Records with missing name: {missing_name}")
    if missing_site_id:
        logger.warning(f"Records with missing site_id: {missing_site_id}")

    logger.info(
        f"Output integrity OK: {written_count} records written, "
        f"0 corrupt lines, {len(duplicate_ids)} duplicate IDs"
    )

    return {
        "written_count": written_count,
        "expected_count": expected,
        "corrupt_lines": corrupt_lines,
        "duplicate_ids": len(duplicate_ids),
        "missing_name": missing_name,
        "description_quality": dict(desc_quality),
        "integrity_ok": (
            written_count == expected
            and corrupt_lines == 0
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# STEP 8 — Quality stats report
# ══════════════════════════════════════════════════════════════════════════════

def print_quality_report(
    sites: list[HeritageSite],
    input_counts: dict[str, int],
    dedup_stats: dict[str, Any],
    stage_timings: dict[str, float],
    integrity_result: dict[str, Any] | None,
) -> None:
    """Print a structured quality report to stdout."""
    total = len(sites)

    # Description quality distribution
    desc_counts = Counter(
        (s.description_quality if isinstance(s.description_quality, str)
         else s.description_quality.value)
        for s in sites
    )

    # Category distribution (top 10) — handle both str and SiteCategory enum instances
    def _cat_str(c: Any) -> str:
        if isinstance(c, str):
            return c.replace("SiteCategory.", "")
        try:
            return c.value
        except AttributeError:
            return str(c)

    cat_counts = Counter(_cat_str(s.category) for s in sites)

    # Coordinate coverage
    with_coords = sum(1 for s in sites if s.coordinates is not None)
    coord_conflicts = sum(
        1 for s in sites
        if s.coordinates is not None and s.coordinates.coordinate_conflict
    )

    # Quality score distribution
    scores = [s.data_quality_score for s in sites]
    avg_score = sum(scores) / max(len(scores), 1)
    high_quality = sum(1 for sc in scores if sc >= 0.7)
    medium_quality = sum(1 for sc in scores if 0.4 <= sc < 0.7)
    low_quality = sum(1 for sc in scores if sc < 0.4)

    # RAG eligibility
    rag_eligible = sum(1 for s in sites if s.is_rag_eligible())

    # UNESCO / ASI coverage
    unesco_count = sum(1 for s in sites if s.heritage_status.is_unesco_whs)
    asi_count = sum(1 for s in sites if s.heritage_status.is_asi_protected)

    # Wikipedia enrichment
    wiki_enriched = sum(1 for s in sites if s.source_urls.wikipedia is not None)

    sep = "-" * 62
    print(f"\n{sep}")
    print("  ARKANA PIPELINE -- QUALITY REPORT")
    print(sep)

    print("\n[INPUT RECORDS]")
    for source, count in input_counts.items():
        print(f"   {source:<20} {count:>6} records")

    print(f"\n[DEDUPLICATION]")
    print(f"   Input to dedup:      {dedup_stats['original_count']:>6}")
    print(f"   Duplicates removed:  {dedup_stats['removed_duplicates']:>6}")
    print(f"   Dedup rate:          {dedup_stats['dedup_rate_pct']:>5.1f}%")
    print(f"   Final canonical:     {dedup_stats['final_count']:>6}")

    print(f"\n[DESCRIPTION QUALITY] (total {total})")
    print(f"   FULL  (>=500 chars): {desc_counts.get('full', 0):>6}  ({desc_counts.get('full', 0)/max(total,1)*100:.1f}%)")
    print(f"   STUB  (<500 chars):  {desc_counts.get('stub', 0):>6}  ({desc_counts.get('stub', 0)/max(total,1)*100:.1f}%)")
    print(f"   MISSING (no desc):   {desc_counts.get('missing', 0):>6}  ({desc_counts.get('missing', 0)/max(total,1)*100:.1f}%)")

    print(f"\n[CATEGORY DISTRIBUTION] (top 10)")
    for cat, count in cat_counts.most_common(10):
        print(f"   {cat:<25} {count:>6}")

    print(f"\n[GEOGRAPHIC COVERAGE]")
    print(f"   With coordinates:    {with_coords:>6}  ({with_coords/max(total,1)*100:.1f}%)")
    print(f"   Coord conflicts:     {coord_conflicts:>6}")

    print(f"\n[ENRICHMENT]")
    print(f"   Wikipedia-enriched:  {wiki_enriched:>6}  ({wiki_enriched/max(total,1)*100:.1f}%)")

    print(f"\n[QUALITY SCORE DISTRIBUTION] avg={avg_score:.3f}")
    print(f"   High   (>=0.70):     {high_quality:>6}  ({high_quality/max(total,1)*100:.1f}%)")
    print(f"   Medium (0.40-0.69):  {medium_quality:>6}  ({medium_quality/max(total,1)*100:.1f}%)")
    print(f"   Low    (<0.40):      {low_quality:>6}  ({low_quality/max(total,1)*100:.1f}%)")

    print(f"\n[RAG ELIGIBILITY]")
    print(f"   RAG-eligible sites:  {rag_eligible:>6}  ({rag_eligible/max(total,1)*100:.1f}%)")

    print(f"\n[HERITAGE DESIGNATIONS]")
    print(f"   UNESCO WHS:          {unesco_count:>6}")
    print(f"   ASI protected:       {asi_count:>6}")

    print(f"\n[STAGE TIMINGS]")
    total_elapsed = sum(stage_timings.values())
    for stage, elapsed in stage_timings.items():
        print(f"   {stage:<22} {elapsed:>6.1f}s")
    print(f"   {'TOTAL':<22} {total_elapsed:>6.1f}s")
    print(f"   Throughput:          {total/max(total_elapsed, 0.001):.0f} sites/sec")

    if integrity_result:
        status = "OK" if integrity_result["integrity_ok"] else "FAILED"
        print(f"\n[OUTPUT INTEGRITY] {status}")
        print(f"   Written records:     {integrity_result['written_count']:>6}")
        print(f"   Corrupt lines:       {integrity_result['corrupt_lines']:>6}")
        print(f"   Duplicate IDs:       {integrity_result['duplicate_ids']:>6}")

    print(f"\n{sep}\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(
    sources: list[str],
    dry_run: bool = False,
    limit: int | None = None,
    force: bool = False,
) -> list[HeritageSite]:
    """
    Execute the full ETL pipeline.

    Args:
        sources:   List of primary site sources to load. e.g. ["wikidata", "unesco"]
                   Note: "osm" and "wikipedia" always feed the Enricher regardless.
        dry_run:   If True, skip writing output file.
        limit:     Cap total records loaded (for development).
        force:     If True, overwrite existing canonical_sites.jsonl.

    Returns:
        Final canonical list of HeritageSite records.
    """
    stage_timings: dict[str, float] = {}
    logger.info("=" * 62)
    logger.info("  ARKANA ETL PIPELINE -- STARTING")
    logger.info("=" * 62)
    logger.info(f"Sources: {sources}  |  dry_run={dry_run}  |  limit={limit}  |  force={force}")

    # Early exit if output already exists and not forcing
    if not dry_run and not force and CANONICAL_OUTPUT.exists():
        size_kb = CANONICAL_OUTPUT.stat().st_size // 1024
        logger.info(
            f"canonical_sites.jsonl already exists ({size_kb} KB). "
            f"Use --force to overwrite. Exiting."
        )
        # Load and return existing output so callers still get data
        existing: list[HeritageSite] = []
        with open(CANONICAL_OUTPUT, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        existing.append(HeritageSite.model_validate(json.loads(line)))
                    except Exception:
                        pass
        logger.info(f"Returning {len(existing)} existing records.")
        return existing

    # ── Step 1: Load source checkpoints ──────────────────────────────────────
    t0 = time.monotonic()
    logger.info("\n[Step 1/7] Loading source checkpoints...")
    all_sites: list[HeritageSite] = []
    input_counts: dict[str, int] = {}

    if "wikidata" in sources:
        wd_sites = load_wikidata_sites(limit=limit)
        all_sites.extend(wd_sites)
        input_counts["wikidata"] = len(wd_sites)

    if "unesco" in sources:
        un_sites = load_unesco_sites()
        all_sites.extend(un_sites)
        input_counts["unesco"] = len(un_sites)

    # OSM and Wikipedia always load as enrichment inputs (not primary sites)
    osm_records = load_osm_records()
    wikipedia_articles = load_wikipedia_articles()

    if not all_sites:
        logger.error(
            "No sites loaded. Check that data/raw/ checkpoints exist. "
            "Run ingestion extractors first: python -m ingestion.validate"
        )
        sys.exit(1)

    total_loaded = len(all_sites)
    logger.info(f"Total sites loaded across all sources: {total_loaded}")
    stage_timings["1_load"] = time.monotonic() - t0

    # ── Step 2: Normalize ─────────────────────────────────────────────────────
    t0 = time.monotonic()
    logger.info("\n[Step 2/7] Applying normalizer...")
    all_sites = normalize_batch(all_sites)
    logger.info(f"Normalization complete: {len(all_sites)} sites")
    stage_timings["2_normalize"] = time.monotonic() - t0

    # ── Step 3: Merge (sources already loaded into one list) ──────────────────
    logger.info(f"\n[Step 3/7] Source merge complete: {len(all_sites)} sites in unified list")

    # ── Step 4: Deduplicate ───────────────────────────────────────────────────
    t0 = time.monotonic()
    logger.info("\n[Step 4/7] Running deduplicator...")
    pre_dedup_count = len(all_sites)
    deduplicator = Deduplicator()
    all_sites = deduplicator.deduplicate(all_sites)
    post_dedup_count = len(all_sites)
    dedup_stats = deduplicator.stats(pre_dedup_count, post_dedup_count)
    logger.info(
        f"Deduplication complete: {pre_dedup_count} -> {post_dedup_count} sites "
        f"({dedup_stats['removed_duplicates']} duplicates removed, "
        f"{dedup_stats['dedup_rate_pct']}% dedup rate)"
    )
    stage_timings["4_deduplicate"] = time.monotonic() - t0

    # ── Step 5: Enrich ────────────────────────────────────────────────────────
    t0 = time.monotonic()
    logger.info("\n[Step 5/7] Running enricher...")
    enricher = Enricher(
        osm_records=osm_records,
        wikipedia_articles=wikipedia_articles,
    )
    all_sites = enricher.enrich_batch(all_sites)
    logger.info(f"Enrichment complete: {len(all_sites)} sites")
    stage_timings["5_enrich"] = time.monotonic() - t0

    # ── Step 6: Write output ──────────────────────────────────────────────────
    integrity_result: dict[str, Any] | None = None

    if dry_run:
        logger.info("\n[Step 6/7] --dry-run: skipping file write")
    else:
        t0 = time.monotonic()
        logger.info(f"\n[Step 6/7] Writing canonical output -> {CANONICAL_OUTPUT}")
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        written = 0
        failed = 0
        with open(CANONICAL_OUTPUT, "w", encoding="utf-8") as f:
            for site in all_sites:
                try:
                    # Use model_dump for Pydantic v2 serialization
                    record = site.model_dump(mode="json")
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    written += 1
                except Exception as e:
                    logger.warning(f"Serialization failed for '{site.name}': {e}")
                    failed += 1

        logger.info(f"Wrote {written} records to {CANONICAL_OUTPUT}")
        if failed:
            logger.warning(f"Serialization failures: {failed} records skipped")
        stage_timings["6_write"] = time.monotonic() - t0

        # ── Step 6b: Validate output integrity ─────────────────────────────
        logger.info("\n[Step 6b/7] Validating output integrity...")
        try:
            integrity_result = validate_output_integrity(all_sites, CANONICAL_OUTPUT)
            if not integrity_result["integrity_ok"]:
                logger.error(
                    f"Output integrity FAILED — see details above. "
                    f"Do NOT load this file into PostgreSQL."
                )
                sys.exit(2)
        except RuntimeError as e:
            logger.error(f"Output integrity check failed: {e}")
            sys.exit(2)

    # ── Step 7: Quality report ────────────────────────────────────────────────
    print_quality_report(all_sites, input_counts, dedup_stats, stage_timings, integrity_result)

    return all_sites


# ══════════════════════════════════════════════════════════════════════════════
# CLI Entry Point
# ══════════════════════════════════════════════════════════════════════════════

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Arkana ETL Pipeline -- Phase 2 Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Run full pipeline but do NOT write output file.",
    )
    parser.add_argument(
        "--sources",
        type=str,
        default="wikidata,unesco",
        help=(
            "Comma-separated list of primary site sources to include. "
            "Choices: wikidata, unesco. "
            "OSM and Wikipedia always feed the Enricher. "
            "Default: wikidata,unesco"
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process at most N sites (for development/testing). Default: no limit.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity. Default: INFO.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite existing canonical_sites.jsonl even if it exists.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    # Apply log level
    import logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    sources = [s.strip().lower() for s in args.sources.split(",") if s.strip()]
    valid_sources = {"wikidata", "unesco"}
    unknown = set(sources) - valid_sources
    if unknown:
        print(f"ERROR: Unknown sources: {unknown}. Valid choices: {valid_sources}", file=sys.stderr)
        sys.exit(1)

    run_pipeline(
        sources=sources,
        dry_run=args.dry_run,
        limit=args.limit,
        force=args.force,
    )
