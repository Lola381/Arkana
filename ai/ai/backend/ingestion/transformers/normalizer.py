"""
Arkana — Normalization Layer
Handles: Unicode normalization, coordinate validation, date parsing,
         category normalization, text cleaning.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any

from ingestion.models.heritage_schema import SiteCategory
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)


# ── Text Normalization ────────────────────────────────────────────────────────

def normalize_text(text: str | None) -> str | None:
    """Apply Unicode NFKC normalization and strip excess whitespace."""
    if not text:
        return None
    normalized = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized if normalized else None


def normalize_name(name: str) -> str:
    """Normalize a site name for deduplication comparison."""
    if not name:
        return ""
    text = unicodedata.normalize("NFKC", name.lower())
    # Remove common suffixes/prefixes that create false non-matches
    text = re.sub(r"\b(the|a|an|of|in|at|temple|fort|palace|mosque|church)\b", "", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ── Coordinate Validation ─────────────────────────────────────────────────────

INDIA_BOUNDS = {"lat": (6.0, 38.0), "lon": (68.0, 98.0)}


def validate_india_coordinates(lat: Any, lon: Any) -> tuple[float, float] | None:
    """
    Validate that coordinates fall within India's bounding box.
    Returns (lat, lon) tuple or None if invalid.
    """
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return None

    if not (INDIA_BOUNDS["lat"][0] <= lat <= INDIA_BOUNDS["lat"][1]):
        return None
    if not (INDIA_BOUNDS["lon"][0] <= lon <= INDIA_BOUNDS["lon"][1]):
        return None

    return round(lat, 6), round(lon, 6)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two lat/lon points (Haversine formula)."""
    import math
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ── Date Parsing ──────────────────────────────────────────────────────────────

DATE_PATTERNS = [
    (r"^(-?\d{1,4})-\d{2}-\d{2}T", 1),    # ISO 8601: "1632-01-01T00:00:00Z"
    (r"^(-?\d{1,4})-\d{2}-\d{2}$", 1),    # "1632-01-01"
    (r"^(-?\d{1,4})$", 1),                  # Just a year: "1632"
    (r"(\d{4})\s*(?:CE|AD|CE\.)?$", 1),    # "1632 CE"
    (r"(\d{4})\s*(?:BCE|BC)$", 1),         # "300 BCE" → negative year
]

BCE_RE = re.compile(r"(\d+)\s*(?:BCE|BC)", re.IGNORECASE)


def parse_year(raw: Any) -> int | None:
    """
    Parse various date/year formats to an integer year.
    Returns negative integers for BCE years.
    """
    if raw is None:
        return None
    text = str(raw).strip()

    # Check for BCE
    bce_match = BCE_RE.search(text)
    if bce_match:
        try:
            return -int(bce_match.group(1))
        except ValueError:
            return None

    # Try each pattern
    for pattern, group in DATE_PATTERNS:
        m = re.search(pattern, text)
        if m:
            try:
                year = int(m.group(group))
                if -3000 <= year <= 2026:
                    return year
            except ValueError:
                continue

    return None


# ── Category Normalization ────────────────────────────────────────────────────

CATEGORY_KEYWORD_MAP: list[tuple[list[str], SiteCategory]] = [
    (["fort", "fortress", "citadel", "castle", "qila", "kila"], SiteCategory.FORT),
    (["temple", "mandir", "shrine", "kovil", "devalaya"], SiteCategory.TEMPLE),
    (["mosque", "masjid", "dargah", "jama"], SiteCategory.MOSQUE),
    (["church", "cathedral", "basilica", "chapel"], SiteCategory.CHURCH),
    (["monastery", "vihara", "matha", "math", "abbey"], SiteCategory.MONASTERY),
    (["mausoleum", "tomb", "makbara", "dargah", "rauza"], SiteCategory.MAUSOLEUM),
    (["stupa", "dagoba", "chedi"], SiteCategory.STUPA),
    (["museum", "gallery", "sangrahalaya"], SiteCategory.MUSEUM),
    (["palace", "mahal", "haveli", "darbar"], SiteCategory.PALACE),
    (["stepwell", "vav", "baoli", "kund", "pushkarni"], SiteCategory.STEPWELL),
    (["cave", "cavern", "grotto", "gupha"], SiteCategory.CAVE),
    (["archaeological", "excavation", "ruins", "site"], SiteCategory.ARCHAEOLOGICAL_SITE),
    (["national park", "wildlife", "sanctuary", "forest", "reserve", "biosphere"], SiteCategory.NATURAL_SITE),
    (["monument", "memorial", "pillar", "stambha"], SiteCategory.MONUMENT),
    (["heritage building", "historic building", "bungalow", "mansion"], SiteCategory.HERITAGE_BUILDING),
]


def normalize_category_from_text(name: str, description: str | None = None) -> SiteCategory:
    """
    Infer site category from name and description keywords.
    Used when Wikidata P31 is unavailable or maps to UNKNOWN.
    """
    combined = (name + " " + (description or "")).lower()

    for keywords, category in CATEGORY_KEYWORD_MAP:
        for kw in keywords:
            if kw in combined:
                return category

    return SiteCategory.UNKNOWN


# ── Wikipedia Text Cleaning ───────────────────────────────────────────────────

def clean_wikipedia_text(text: str | None) -> str | None:
    """
    Clean raw Wikipedia plain text:
    - Remove citation markers like [1], [2], [citation needed]
    - Remove markup artifacts
    - Normalize whitespace
    """
    if not text:
        return None
    # Remove citation numbers: [1], [23], [citation needed], [note 1]
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[citation needed\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[note \d+\]", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[edit\]", "", text, flags=re.IGNORECASE)
    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Normalize whitespace within lines
    lines = [re.sub(r" {2,}", " ", line) for line in text.splitlines()]
    text = "\n".join(lines).strip()
    return text if text else None


def extract_intro_paragraph(full_text: str | None) -> str | None:
    """Extract the first substantive paragraph from Wikipedia text."""
    if not full_text:
        return None
    paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
    for para in paragraphs:
        if len(para) > 100 and not para.startswith("=="):
            return para[:500]  # Cap at 500 chars for short_summary
    return None
