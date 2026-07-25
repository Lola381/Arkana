"""
Arkana — Deduplication Engine
Implements two-tier deduplication strategy:
  1. Primary: Wikidata QID (exact match — canonical entity ID)
  2. Secondary: (normalized_name, state) fuzzy match via RapidFuzz

All merges and conflicts are logged to data/raw/dedup_log.jsonl.
The most-complete record (highest data_quality_score) wins merges.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ingestion.config import PROCESSED_DIR, RAW_DIR
from ingestion.models.heritage_schema import DataSource, HeritageSite
from ingestion.transformers.normalizer import normalize_name
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

DEDUP_LOG_FILE = RAW_DIR / "dedup_log.jsonl"
FUZZY_MATCH_THRESHOLD = 90  # RapidFuzz token_set_ratio threshold (0–100)


def _try_import_rapidfuzz():
    try:
        from rapidfuzz import fuzz
        return fuzz
    except ImportError:
        logger.warning("rapidfuzz not installed — secondary fuzzy dedup disabled. Run: pip install rapidfuzz")
        return None


def _log_merge(record_a: HeritageSite, record_b: HeritageSite, reason: str) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "merge",
        "reason": reason,
        "winner_id": record_a.site_id,
        "loser_id": record_b.site_id,
        "winner_qid": record_a.wikidata_qid,
        "loser_qid": record_b.wikidata_qid,
        "winner_name": record_a.name,
        "loser_name": record_b.name,
        "winner_score": record_a.data_quality_score,
        "loser_score": record_b.data_quality_score,
    }
    with open(DEDUP_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def _merge_records(primary: HeritageSite, secondary: HeritageSite) -> HeritageSite:
    """
    Merge two HeritageSite records.
    Primary (higher quality_score) wins on conflicts.
    Non-conflicting fields are filled from secondary if primary is missing.
    """
    # Merge alternate names
    all_names = set(primary.alternate_names) | {secondary.name} | set(secondary.alternate_names)
    all_names.discard(primary.name)
    primary.alternate_names = sorted(all_names)

    # Fill missing fields from secondary
    if not primary.coordinates and secondary.coordinates:
        primary.coordinates = secondary.coordinates

    if not primary.location.state and secondary.location.state:
        primary.location.state = secondary.location.state

    if not primary.location.district and secondary.location.district:
        primary.location.district = secondary.location.district

    if primary.description is None and secondary.description:
        primary.description = secondary.description

    if not primary.images and secondary.images:
        primary.images = secondary.images

    if not primary.historical_period.start_year and secondary.historical_period.start_year:
        primary.historical_period.start_year = secondary.historical_period.start_year
        primary.historical_period.certainty = secondary.historical_period.certainty

    if not primary.historical_period.era and secondary.historical_period.era:
        primary.historical_period.era = secondary.historical_period.era

    # Merge data_sources list
    merged_sources = list(set(primary.data_sources) | set(secondary.data_sources))
    primary.data_sources = merged_sources

    # Merge UNESCO/ASI IDs
    if not primary.unesco_id and secondary.unesco_id:
        primary.unesco_id = secondary.unesco_id
    if not primary.asi_id and secondary.asi_id:
        primary.asi_id = secondary.asi_id
    if not primary.wikidata_qid and secondary.wikidata_qid:
        primary.wikidata_qid = secondary.wikidata_qid
    if not primary.wikipedia_title and secondary.wikipedia_title:
        primary.wikipedia_title = secondary.wikipedia_title

    # Merge source URLs
    for field in ["wikipedia", "wikidata", "unesco", "osm", "official_website"]:
        if not getattr(primary.source_urls, field) and getattr(secondary.source_urls, field):
            setattr(primary.source_urls, field, getattr(secondary.source_urls, field))

    # Merge related entities
    primary.related_entities.people = list(
        set(primary.related_entities.people) | set(secondary.related_entities.people)
    )
    primary.related_entities.locations = list(
        set(primary.related_entities.locations) | set(secondary.related_entities.locations)
    )
    primary.related_entities.topics = list(
        set(primary.related_entities.topics) | set(secondary.related_entities.topics)
    )

    # Merge heritage designations
    primary.heritage_status.heritage_designations = list(
        set(primary.heritage_status.heritage_designations)
        | set(secondary.heritage_status.heritage_designations)
    )
    if secondary.heritage_status.is_unesco_whs:
        primary.heritage_status.is_unesco_whs = True
    if secondary.heritage_status.is_asi_protected:
        primary.heritage_status.is_asi_protected = True

    # Recompute quality score after merge
    primary.compute_quality_score()
    return primary


class Deduplicator:
    """
    Deduplicates a list of HeritageSite records.
    Tier 1: Wikidata QID exact match
    Tier 2: (normalized_name, state) fuzzy match
    """

    def __init__(self) -> None:
        self.fuzz = _try_import_rapidfuzz()

    def deduplicate(self, sites: list[HeritageSite]) -> list[HeritageSite]:
        """
        Main deduplication entry point.
        Returns deduplicated list of HeritageSite records.
        """
        logger.info(f"Starting deduplication: {len(sites)} input records")

        # Tier 1: Exact QID dedup
        sites = self._dedup_by_qid(sites)
        logger.info(f"After QID dedup: {len(sites)} records")

        # Tier 2: Fuzzy name+state dedup (only if rapidfuzz available)
        if self.fuzz:
            sites = self._dedup_by_fuzzy_name(sites)
            logger.info(f"After fuzzy dedup: {len(sites)} records")

        return sites

    def _dedup_by_qid(self, sites: list[HeritageSite]) -> list[HeritageSite]:
        """Remove exact Wikidata QID duplicates, keeping highest quality_score."""
        qid_index: dict[str, HeritageSite] = {}
        no_qid: list[HeritageSite] = []

        for site in sites:
            if not site.wikidata_qid:
                no_qid.append(site)
                continue

            qid = site.wikidata_qid
            if qid in qid_index:
                existing = qid_index[qid]
                # Winner: higher quality score
                if site.data_quality_score > existing.data_quality_score:
                    winner, loser = site, existing
                else:
                    winner, loser = existing, site
                merged = _merge_records(winner, loser)
                _log_merge(winner, loser, "qid_exact_match")
                qid_index[qid] = merged
            else:
                qid_index[qid] = site

        return list(qid_index.values()) + no_qid

    def _dedup_by_fuzzy_name(self, sites: list[HeritageSite]) -> list[HeritageSite]:
        """
        Fuzzy dedup: sites where normalized_name + state match above threshold.
        Only runs on sites WITHOUT a Wikidata QID (already deduped by QID).
        """
        # Separate QID'd and non-QID'd sites
        with_qid = [s for s in sites if s.wikidata_qid]
        without_qid = [s for s in sites if not s.wikidata_qid]

        if not without_qid:
            return sites

        merged_no_qid: list[HeritageSite] = []
        processed_ids = set()

        for i, site_a in enumerate(without_qid):
            if site_a.site_id in processed_ids:
                continue

            norm_a = normalize_name(site_a.name)
            state_a = (site_a.location.state or "").lower()
            current = site_a

            for j, site_b in enumerate(without_qid[i + 1:], start=i + 1):
                if site_b.site_id in processed_ids:
                    continue

                norm_b = normalize_name(site_b.name)
                state_b = (site_b.location.state or "").lower()

                # Only compare if states match (or one is missing)
                if state_a and state_b and state_a != state_b:
                    continue

                score = self.fuzz.token_set_ratio(norm_a, norm_b)
                if score >= FUZZY_MATCH_THRESHOLD:
                    # Merge: winner is higher quality
                    if site_b.data_quality_score > current.data_quality_score:
                        winner, loser = site_b, current
                    else:
                        winner, loser = current, site_b

                    current = _merge_records(winner, loser)
                    processed_ids.add(site_b.site_id)
                    _log_merge(winner, loser, f"fuzzy_name_match_score_{score}")
                    logger.debug(
                        f"Fuzzy merge: '{site_a.name}' ≈ '{site_b.name}' (score={score})"
                    )

            processed_ids.add(site_a.site_id)
            merged_no_qid.append(current)

        return with_qid + merged_no_qid

    def stats(self, original_count: int, final_count: int) -> dict[str, Any]:
        """Return deduplication statistics."""
        removed = original_count - final_count
        return {
            "original_count": original_count,
            "final_count": final_count,
            "removed_duplicates": removed,
            "dedup_rate_pct": round(removed / max(original_count, 1) * 100, 2),
        }
