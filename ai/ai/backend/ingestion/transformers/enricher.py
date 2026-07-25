"""
Arkana — Enrichment Layer
Cross-source field filling after normalization and deduplication.

Responsibilities:
  - Fill missing coordinates from OSM when Wikidata P625 is absent
  - Fill missing description from Wikipedia when Wikidata description is short
  - Resolve coordinate conflicts (Wikidata vs OSM > 500m apart → flag)
  - Build related entities from Wikipedia linked articles
  - Generate geohash for coordinates
  - Final quality score computation
"""

from __future__ import annotations

from typing import Any

from ingestion.models.heritage_schema import (
    Coordinates,
    DataSource,
    DescriptionQuality,
    HeritageSite,
)
from ingestion.transformers.normalizer import (
    clean_wikipedia_text,
    extract_intro_paragraph,
    haversine_distance_km,
    normalize_category_from_text,
)
from ingestion.models.heritage_schema import SiteCategory
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

# If Wikidata and OSM coordinates disagree by more than this → flag conflict
COORDINATE_CONFLICT_THRESHOLD_KM = 0.5  # 500 meters


def _compute_geohash(lat: float, lon: float, precision: int = 6) -> str | None:
    """Compute geohash string for a lat/lon pair."""
    try:
        import pygeohash as pgh
        return pgh.encode(lat, lon, precision=precision)
    except ImportError:
        return None
    except Exception:
        return None


class Enricher:
    """
    Enriches HeritageSite records by merging data from multiple sources.
    Call enrich() after deduplication is complete.
    """

    def __init__(
        self,
        osm_records: list[dict[str, Any]] | None = None,
        wikipedia_articles: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        """
        Args:
            osm_records: List of OSM records (from OSMExtractor)
            wikipedia_articles: Dict of {title: article_dict} (from WikipediaExtractor)
        """
        # Build OSM lookup by Wikidata QID (most important) and by normalized name
        self.osm_by_qid: dict[str, dict[str, Any]] = {}
        self.osm_by_name: dict[str, dict[str, Any]] = {}

        for r in (osm_records or []):
            if r.get("wikidata"):
                self.osm_by_qid[r["wikidata"]] = r
            if r.get("name"):
                self.osm_by_name[r["name"].lower()] = r

        self.wikipedia_articles = wikipedia_articles or {}

    def enrich(self, site: HeritageSite) -> HeritageSite:
        """Apply all enrichment steps to a single site. Returns modified site."""
        site = self._fill_coordinates(site)
        site = self._fill_description(site)
        site = self._fill_short_summary(site)
        site = self._fill_category(site)
        site = self._add_geohash(site)
        site = self._fill_related_entities(site)
        site.compute_quality_score()
        return site

    def enrich_batch(self, sites: list[HeritageSite]) -> list[HeritageSite]:
        """Enrich all sites in a batch."""
        enriched = []
        for i, site in enumerate(sites):
            try:
                enriched.append(self.enrich(site))
            except Exception as e:
                logger.error(f"Enrichment failed for {site.name} ({site.site_id}): {e}")
                enriched.append(site)
            if (i + 1) % 100 == 0:
                logger.info(f"Enriched {i + 1}/{len(sites)} sites...")
        return enriched

    def _fill_coordinates(self, site: HeritageSite) -> HeritageSite:
        """Fill missing coordinates from OSM if Wikidata P625 is absent."""
        # Already has Wikidata coords
        if site.coordinates and site.coordinates.source == DataSource.WIKIDATA:
            # Cross-check with OSM to detect conflicts
            osm_record = self._get_osm(site)
            if osm_record:
                osm_lat = osm_record.get("lat")
                osm_lon = osm_record.get("lon")
                if osm_lat and osm_lon:
                    dist_km = haversine_distance_km(
                        site.coordinates.lat, site.coordinates.lon,
                        float(osm_lat), float(osm_lon),
                    )
                    if dist_km > COORDINATE_CONFLICT_THRESHOLD_KM:
                        site.coordinates.coordinate_conflict = True
                        logger.debug(
                            f"Coordinate conflict for '{site.name}': "
                            f"Wikidata vs OSM = {dist_km:.2f}km apart → flagged"
                        )
            return site

        # No Wikidata coords — try OSM
        osm_record = self._get_osm(site)
        if osm_record and osm_record.get("lat") and osm_record.get("lon"):
            try:
                site.coordinates = Coordinates(
                    lat=float(osm_record["lat"]),
                    lon=float(osm_record["lon"]),
                    source=DataSource.OSM,
                )
                logger.debug(f"Filled coordinates from OSM for '{site.name}'")
            except Exception as e:
                logger.debug(f"OSM coord fill failed for '{site.name}': {e}")

        return site

    def _get_osm(self, site: HeritageSite) -> dict[str, Any] | None:
        """Look up an OSM record by QID first, then by name."""
        if site.wikidata_qid and site.wikidata_qid in self.osm_by_qid:
            return self.osm_by_qid[site.wikidata_qid]
        return self.osm_by_name.get(site.name.lower())

    def _fill_description(self, site: HeritageSite) -> HeritageSite:
        """
        Fill or upgrade the description from Wikipedia.
        Wikidata descriptions are short (~50 chars) — Wikipedia provides the full text.
        """
        wiki_article = self._get_wikipedia_article(site)
        if not wiki_article:
            return site

        wiki_text = clean_wikipedia_text(wiki_article.get("full_text", ""))
        if not wiki_text:
            return site

        # Upgrade description if Wikipedia provides a better one
        current_desc_len = len(site.description or "")
        if len(wiki_text) > current_desc_len:
            site.description = wiki_text
            if not site.source_urls.wikipedia:
                site.source_urls.wikipedia = wiki_article.get("url")
            if DataSource.WIKIPEDIA not in site.data_sources:
                site.data_sources.append(DataSource.WIKIPEDIA)
            if not site.wikipedia_title:
                site.wikipedia_title = wiki_article.get("title")
            logger.debug(
                f"Enriched description for '{site.name}': "
                f"{current_desc_len} → {len(wiki_text)} chars"
            )

        return site

    def _fill_short_summary(self, site: HeritageSite) -> HeritageSite:
        """Generate short_summary from intro paragraph if not already set."""
        if site.short_summary:
            return site

        wiki_article = self._get_wikipedia_article(site)
        if wiki_article:
            intro = wiki_article.get("intro") or extract_intro_paragraph(
                wiki_article.get("full_text")
            )
            if intro:
                site.short_summary = intro[:300]
        elif site.description:
            site.short_summary = site.description[:300]

        return site

    def _fill_category(self, site: HeritageSite) -> HeritageSite:
        """Infer category from name/description if still UNKNOWN."""
        if site.category != SiteCategory.UNKNOWN:
            return site
        inferred = normalize_category_from_text(site.name, site.description)
        if inferred != SiteCategory.UNKNOWN:
            site.category = inferred
        return site

    def _add_geohash(self, site: HeritageSite) -> HeritageSite:
        """Compute geohash for coordinates."""
        if site.coordinates and not site.coordinates.geohash:
            geohash = _compute_geohash(site.coordinates.lat, site.coordinates.lon)
            if geohash:
                site.coordinates.geohash = geohash
        return site

    def _fill_related_entities(self, site: HeritageSite) -> HeritageSite:
        """
        Extract related entities (people, locations, topics) from Wikipedia article links.
        Links mentioning dynasties, rulers, or regions are categorized accordingly.
        """
        wiki_article = self._get_wikipedia_article(site)
        if not wiki_article:
            return site

        links = wiki_article.get("links", [])
        categories = wiki_article.get("categories", [])

        # Extract topics from categories
        topic_keywords = [
            "architecture", "dynasty", "empire", "period", "art",
            "style", "culture", "temple", "fort", "mosque", "palace"
        ]
        for cat in categories:
            cat_lower = cat.lower()
            if any(kw in cat_lower for kw in topic_keywords):
                clean_cat = cat.replace("Indian", "").replace("in India", "").strip()
                if clean_cat and clean_cat not in site.related_entities.topics:
                    site.related_entities.topics.append(clean_cat)

        # Cap lists
        site.related_entities.topics = site.related_entities.topics[:20]
        return site

    def _get_wikipedia_article(self, site: HeritageSite) -> dict[str, Any] | None:
        """Look up Wikipedia article by title."""
        if site.wikipedia_title and site.wikipedia_title in self.wikipedia_articles:
            return self.wikipedia_articles[site.wikipedia_title]
        if site.name in self.wikipedia_articles:
            return self.wikipedia_articles[site.name]
        return None
