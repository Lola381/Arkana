"""
Arkana — Canonical Heritage Schema (Pydantic v2)
This is the single source of truth for all heritage site records.
Every extractor maps its raw output to this schema.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ── Enumerations ──────────────────────────────────────────────────────────────

class DescriptionQuality(str, Enum):
    FULL = "full"         # >= 500 chars — eligible for RAG chunking
    STUB = "stub"         # < 500 chars — metadata only, no RAG chunks
    MISSING = "missing"   # No description at all


class CoordinateCertainty(str, Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    MISSING = "missing"


class HistoricalCertainty(str, Enum):
    EXACT = "exact"
    APPROXIMATE = "approximate"
    UNKNOWN = "unknown"


class SiteCategory(str, Enum):
    MONUMENT = "monument"
    FORT = "fort"
    TEMPLE = "temple"
    MOSQUE = "mosque"
    CHURCH = "church"
    MONASTERY = "monastery"
    MUSEUM = "museum"
    PALACE = "palace"
    STEPWELL = "stepwell"
    CAVE = "cave"
    ARCHAEOLOGICAL_SITE = "archaeological_site"
    NATURAL_SITE = "natural_site"
    HERITAGE_BUILDING = "heritage_building"
    MAUSOLEUM = "mausoleum"
    STUPA = "stupa"
    OTHER = "other"
    UNKNOWN = "unknown"


class DataSource(str, Enum):
    WIKIPEDIA = "wikipedia"
    WIKIDATA = "wikidata"
    UNESCO = "unesco"
    OSM = "osm"
    WIKIMEDIA_COMMONS = "wikimedia_commons"
    WIKIVOYAGE = "wikivoyage"
    DATAGOV = "datagov"
    INTERNET_ARCHIVE = "internet_archive"
    MANUAL = "manual"


# ── Sub-models ────────────────────────────────────────────────────────────────

class Coordinates(BaseModel):
    lat: float
    lon: float
    geohash: str | None = None
    source: DataSource = DataSource.WIKIDATA
    certainty: CoordinateCertainty = CoordinateCertainty.EXACT
    coordinate_conflict: bool = False    # True if WD vs OSM disagree >500m

    @field_validator("lat")
    @classmethod
    def validate_lat(cls, v: float) -> float:
        if not (6.0 <= v <= 38.0):
            raise ValueError(f"Latitude {v} is outside India's bounding box [6, 38]")
        return round(v, 6)

    @field_validator("lon")
    @classmethod
    def validate_lon(cls, v: float) -> float:
        if not (68.0 <= v <= 98.0):
            raise ValueError(f"Longitude {v} is outside India's bounding box [68, 98]")
        return round(v, 6)


class Location(BaseModel):
    state: str | None = None
    district: str | None = None
    country: str = "India"
    address: str | None = None


class HeritageStatus(BaseModel):
    is_unesco_whs: bool = False
    is_asi_protected: bool = False
    asi_type: str | None = None             # centrally_protected_monument | state_protected
    heritage_designations: list[str] = Field(default_factory=list)


class HistoricalPeriod(BaseModel):
    era: str | None = None                  # e.g., "Mughal", "Chola", "British Colonial"
    start_year: int | None = None
    end_year: int | None = None
    certainty: HistoricalCertainty = HistoricalCertainty.UNKNOWN

    @field_validator("start_year", "end_year", mode="before")
    @classmethod
    def validate_year(cls, v: Any) -> int | None:
        if v is None:
            return None
        v = int(v)
        # Allow BCE years (negative) and reasonable upper bound
        if not (-3000 <= v <= 2026):
            raise ValueError(f"Year {v} is out of plausible range")
        return v


class SiteImage(BaseModel):
    url: str
    thumbnail_url: str | None = None
    license: str | None = None
    author: str | None = None
    source: DataSource = DataSource.WIKIMEDIA_COMMONS
    commons_filename: str | None = None


class SourceUrls(BaseModel):
    wikipedia: str | None = None
    wikidata: str | None = None
    unesco: str | None = None
    osm: str | None = None
    official_website: str | None = None
    wikivoyage: str | None = None


class RelatedEntities(BaseModel):
    people: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    events: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    dynasties: list[str] = Field(default_factory=list)


class RAGChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chunk_index: int
    parent_section: str | None = None
    chunk_text: str
    token_count: int | None = None
    source_url: str | None = None
    vector_db_id: str | None = None     # ID assigned by ChromaDB/Qdrant


# ── Master Heritage Site Schema ───────────────────────────────────────────────

class HeritageSite(BaseModel):
    """
    Canonical schema for an Arkana heritage site record.
    Every extractor maps its raw output to this model.
    Wikidata QID is the primary deduplication key — never change it after ingestion.
    """

    # ── Identity ──────────────────────────────────────────────────────────────
    site_id: str = Field(default_factory=lambda: f"arkana_{uuid.uuid4().hex[:12]}")
    wikidata_qid: str | None = None         # Primary dedup key (e.g., "Q9141")
    wikipedia_title: str | None = None
    osm_id: str | None = None              # e.g., "relation/5835063"
    asi_id: str | None = None              # ASI monument number (e.g., "N-UP-A5")
    unesco_id: str | None = None           # UNESCO WH site ID (e.g., "252")

    # ── Core Fields ───────────────────────────────────────────────────────────
    name: str
    alternate_names: list[str] = Field(default_factory=list)
    description: str | None = None          # Primary RAG corpus field
    short_summary: str | None = None        # For UI cards (max ~200 chars)
    description_quality: DescriptionQuality = DescriptionQuality.MISSING

    # ── Location ──────────────────────────────────────────────────────────────
    location: Location = Field(default_factory=Location)
    coordinates: Coordinates | None = None

    # ── Classification ────────────────────────────────────────────────────────
    category: SiteCategory = SiteCategory.UNKNOWN
    category_tags: list[str] = Field(default_factory=list)
    heritage_status: HeritageStatus = Field(default_factory=HeritageStatus)

    # ── History ───────────────────────────────────────────────────────────────
    historical_period: HistoricalPeriod = Field(default_factory=HistoricalPeriod)
    commissioned_by: str | None = None

    # ── Assets ────────────────────────────────────────────────────────────────
    images: list[SiteImage] = Field(default_factory=list)

    # ── Sources & Citations ───────────────────────────────────────────────────
    source_urls: SourceUrls = Field(default_factory=SourceUrls)
    citations: list[str] = Field(default_factory=list)

    # ── Related Entities ──────────────────────────────────────────────────────
    related_entities: RelatedEntities = Field(default_factory=RelatedEntities)

    # ── RAG Metadata ─────────────────────────────────────────────────────────
    rag_chunks: list[RAGChunk] = Field(default_factory=list)
    embedding_model: str | None = None

    # ── Ingestion Provenance ──────────────────────────────────────────────────
    data_sources: list[DataSource] = Field(default_factory=list)
    ingestion_version: str = "1.0"
    data_quality_score: float = 0.0         # Computed: 0.0–1.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ── Computed Validators ───────────────────────────────────────────────────
    @model_validator(mode="after")
    def compute_description_quality(self) -> "HeritageSite":
        if not self.description:
            self.description_quality = DescriptionQuality.MISSING
        elif len(self.description) < 500:
            self.description_quality = DescriptionQuality.STUB
        else:
            self.description_quality = DescriptionQuality.FULL
        return self

    @model_validator(mode="after")
    def auto_build_citations(self) -> "HeritageSite":
        """Build citation strings from source_urls if not set."""
        if not self.citations:
            citations = []
            if self.source_urls.wikipedia and self.wikipedia_title:
                citations.append(f"Wikipedia: {self.wikipedia_title}")
            if self.source_urls.wikidata and self.wikidata_qid:
                citations.append(f"Wikidata: {self.wikidata_qid}")
            if self.source_urls.unesco and self.unesco_id:
                citations.append(f"UNESCO World Heritage List #{self.unesco_id}")
            self.citations = citations
        return self

    def compute_quality_score(self) -> float:
        """
        Compute and store data quality score (0.0–1.0).
        Call this after all enrichment steps are done.
        """
        from ingestion.config import QUALITY_WEIGHTS

        score = 0.0
        if self.description_quality == DescriptionQuality.FULL:
            score += QUALITY_WEIGHTS["has_description"]
        if self.coordinates is not None:
            score += QUALITY_WEIGHTS["has_coordinates"]
        if self.location.state:
            score += QUALITY_WEIGHTS["has_state"]
        if self.category != SiteCategory.UNKNOWN:
            score += QUALITY_WEIGHTS["has_category"]
        if (
            self.historical_period.start_year is not None
            or self.historical_period.era is not None
        ):
            score += QUALITY_WEIGHTS["has_historical_period"]
        if self.images:
            score += QUALITY_WEIGHTS["has_images"]
        if any(
            v is not None
            for v in [
                self.source_urls.wikipedia,
                self.source_urls.wikidata,
                self.source_urls.unesco,
            ]
        ):
            score += QUALITY_WEIGHTS["has_source_urls"]
        if any(
            [
                self.related_entities.people,
                self.related_entities.locations,
                self.related_entities.topics,
            ]
        ):
            score += QUALITY_WEIGHTS["has_related_entities"]

        self.data_quality_score = round(score, 4)
        return self.data_quality_score

    def is_rag_eligible(self) -> bool:
        """A site is eligible for RAG chunking only if description is FULL (>=500 chars)."""
        return self.description_quality == DescriptionQuality.FULL

    model_config = ConfigDict(use_enum_values=True)


# ── Ingestion Log Entry ────────────────────────────────────────────────────────

class IngestionLogEntry(BaseModel):
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    site_id: str | None = None
    wikidata_qid: str | None = None
    source_name: DataSource
    status: str                             # success | error | skipped | duplicate
    error_message: str | None = None
    raw_record_id: str | None = None        # e.g., Wikipedia title, QID
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
