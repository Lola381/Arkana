"""
Arkana — Centralized Configuration
All API keys, rate limits, DB URLs, and tunable parameters live here.
Load secrets from .env via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── Project Identity ─────────────────────────────────────────────────────────
PROJECT_NAME = "Arkana"
PROJECT_VERSION = "1.0.0"
USER_AGENT = "Arkana/1.0 (arkana-heritage-project@example.com)"

# ── Data Directories ─────────────────────────────────────────────────────────
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"

for _dir in [RAW_DIR, PROCESSED_DIR, REPORTS_DIR]:
    _dir.mkdir(parents=True, exist_ok=True)

# ── Database ─────────────────────────────────────────────────────────────────
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "arkana")
POSTGRES_USER = os.getenv("POSTGRES_USER", "arkana")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "arkana_secret")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)
SYNC_DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# ── Vector Database ───────────────────────────────────────────────────────────
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8001"))
CHROMA_COLLECTION_NAME = "arkana_heritage_chunks"

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ── API Keys ──────────────────────────────────────────────────────────────────
DATAGOV_API_KEY = os.getenv("DATAGOV_API_KEY", "")       # data.gov.in — free registration
EUROPEANA_API_KEY = os.getenv("EUROPEANA_API_KEY", "")   # Phase 3+
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")         # For AI layer

# ── Rate Limits (requests per second per source) ──────────────────────────────
RATE_LIMITS = {
    "wikipedia": 3.0,         # 3 req/sec ≈ 180/min (well under 200/min limit)
    "wikidata": 5.0,          # 5 req/sec (generous limit)
    "wikimedia_commons": 3.0, # Same as Wikipedia
    "wikivoyage": 3.0,        # Same as Wikipedia
    "unesco": 2.0,            # Not documented; be conservative
    "osm": 0.5,               # 2 concurrent requests; 1 req/2sec to be safe
    "datagov": 1.0,           # Not documented; conservative
    "internet_archive": 1.0,  # 1 req/sec recommended
}

# Max concurrent connections per source
MAX_CONCURRENT = {
    "wikipedia": 3,
    "wikidata": 3,
    "wikimedia_commons": 3,
    "osm": 2,
    "unesco": 2,
    "datagov": 2,
    "internet_archive": 2,
}

# ── Retry Configuration ───────────────────────────────────────────────────────
MAX_RETRIES = 5
RETRY_BASE_DELAY = 1.0      # seconds
RETRY_MAX_DELAY = 60.0      # seconds
RETRY_JITTER = True

# ── Data Quality Thresholds ───────────────────────────────────────────────────
# Wikipedia article minimum chars to be considered "non-stub"
STUB_THRESHOLD_CHARS = 500

# Quality score weights (must sum to 1.0)
QUALITY_WEIGHTS = {
    "has_description": 0.25,
    "has_coordinates": 0.20,
    "has_state": 0.10,
    "has_category": 0.10,
    "has_historical_period": 0.10,
    "has_images": 0.10,
    "has_source_urls": 0.10,
    "has_related_entities": 0.05,
}

# ── India Geographic Bounding Box ─────────────────────────────────────────────
INDIA_BOUNDS = {
    "lat_min": 6.0,
    "lat_max": 38.0,
    "lon_min": 68.0,
    "lon_max": 98.0,
}

# ── Wikipedia Categories to Mine ─────────────────────────────────────────────
WIKIPEDIA_CATEGORIES = [
    "Monuments of national importance in India",
    "Archaeological sites in India",
    "UNESCO World Heritage Sites in India",
    "Hindu temples in India",
    "Forts in India",
    "Palaces in India",
    "Stepwells in India",
    "Mosques in India",
    "Churches in India",
    "Buddhist monasteries in India",
    "Jain temples in India",
    "Caves in India",
    "Rock-cut architecture in India",
    "Museums in India",
]

# ── Wikidata Heritage Types (P31 instance-of QIDs) ───────────────────────────
# Used for SPARQL queries and category normalization
WIKIDATA_HERITAGE_TYPES = {
    "Q4989906": "monument",
    "Q23413": "castle",
    "Q79007": "street",
    "Q16748868": "historic building",
    "Q839954": "archaeological site",
    "Q1081138": "palace",
    "Q44613": "monastery",
    "Q12034": "fort",
    "Q2977": "cathedral",
    "Q16970": "church",
    "Q32815": "mosque",
    "Q45393": "temple",
    "Q33506": "museum",
    "Q2469128": "stepwell",
    "Q811938": "nature reserve",
}

# ── India States (for paginated SPARQL queries) ───────────────────────────────
INDIA_STATES_WIKIDATA = {
    "Andhra Pradesh": "Q1159",
    "Arunachal Pradesh": "Q1162",
    "Assam": "Q1164",
    "Bihar": "Q1165",
    "Chhattisgarh": "Q1168",
    "Goa": "Q1171",
    "Gujarat": "Q1061",
    "Haryana": "Q1174",
    "Himachal Pradesh": "Q1177",
    "Jharkhand": "Q1184",
    "Karnataka": "Q1185",
    "Kerala": "Q1186",
    "Madhya Pradesh": "Q1188",
    "Maharashtra": "Q1191",
    "Manipur": "Q1193",
    "Meghalaya": "Q1195",
    "Mizoram": "Q1502",
    "Nagaland": "Q1599",
    "Odisha": "Q22048",
    "Punjab": "Q22424",
    "Rajasthan": "Q1437",
    "Sikkim": "Q1505",
    "Tamil Nadu": "Q1445",
    "Telangana": "Q677037",
    "Tripura": "Q1363",
    "Uttar Pradesh": "Q1498",
    "Uttarakhand": "Q1499",
    "West Bengal": "Q1356",
    "Delhi": "Q1353",
    "Jammu and Kashmir": "Q1180",
    "Ladakh": "Q200667",
}

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
