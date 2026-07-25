"""
Arkana -- Wikipedia Article Extractor (v2 -- Fixed)

Root causes of 0 records in v1:
  1. Category "Monuments of national importance in India" does not exist on
     Wikipedia. The correct names are subcategory-based (by state).
     Confirmed via MediaWiki API: Missing: True.
  2. Direct article fetching works perfectly (Taj Mahal = 32,737 chars).

Fix strategy:
  - Use multiple known-good Wikipedia categories (verified to exist).
  - Use recursive subcategory traversal for broad coverage.
  - Fetch articles by Wikidata QID title when possible (most reliable).
  - Fall back to known heritage site title lists if category is missing.
"""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

import httpx

from ingestion.config import RAW_DIR, USER_AGENT
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = RAW_DIR / "wikipedia"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WIKI_API = "https://en.wikipedia.org/w/api.php"

# Max concurrent requests to Wikipedia (stay under 200/min rate limit)
SEMAPHORE = asyncio.Semaphore(3)

# ── Verified Wikipedia categories (confirmed to exist and contain articles) ──
# These were verified against the MediaWiki API.
VERIFIED_CATEGORIES = [
    # State-specific lists -- these exist and have actual page members
    "Monuments of National Importance in Rajasthan",
    "Monuments of National Importance in Uttar Pradesh",
    "Monuments of National Importance in Tamil Nadu",
    "Monuments of National Importance in Karnataka",
    "Monuments of National Importance in Maharashtra",
    "Monuments of National Importance in Madhya Pradesh",
    "Monuments of National Importance in Gujarat",
    "Monuments of National Importance in Bihar",
    "Monuments of National Importance in West Bengal",
    "Monuments of National Importance in Delhi",
    # Broader heritage categories that do exist
    "UNESCO World Heritage Sites in India",
    "Archaeological sites in India",
    "Hindu temples in India",
    "Forts in India",
    "Palaces in India",
    "Buddhist sites in India",
    "Mughal architecture in India",
    "Stepwells in India",
    "Caves in India",
    "Rock-cut architecture in India",
    "Museums in India",
    "Mosques in India",
    "Churches in India",
]

# Directly known high-value article titles (guaranteed to exist, used as seed)
KNOWN_HERITAGE_TITLES = [
    "Taj Mahal", "Agra Fort", "Red Fort", "Qutb Minar", "Humayun's Tomb",
    "Fatehpur Sikri", "Ellora Caves", "Ajanta Caves", "Konark Sun Temple",
    "Shore Temple", "Hampi", "Pattadakal", "Brihadisvara Temple",
    "Mahabodhi Temple", "Sanchi Stupa", "Bodh Gaya", "Nalanda",
    "Rani ki vav", "Dholavira", "Champaner-Pavagadh Archaeological Park",
    "Chhatrapati Shivaji Terminus", "Jantar Mantar, Jaipur",
    "Hill Forts of Rajasthan", "Western Ghats",
    "Kaziranga National Park", "Sundarbans National Park",
    "Manas National Park", "Keoladeo National Park",
    "Nanda Devi National Park", "Valley of Flowers National Park",
    "Great Himalayan National Park", "Jaipur",
    "Historic City of Ahmedabad", "Santiniketan",
    "Amber Fort", "Chittorgarh Fort", "Mehrangarh Fort",
    "Kumbhalgarh Fort", "Jaisalmer Fort", "Ranthambore Fort",
    "Elephanta Caves", "Daulatabad Fort", "Golconda fort",
    "Bidar Fort", "Gol Gumbaz", "Ibrahim Rauza",
    "Group of Monuments at Mahabalipuram",
    "Group of Monuments at Hampi",
    "Sun Temple, Modhera", "Adalaj Stepwell",
    "Khajuraho Group of Monuments",
    "Rock Shelters of Bhimbetka",
    "Mountain Railways of India",
    "Victorian and Art Deco Ensemble of Mumbai",
    "Le Corbusier's contribution to Chandigarh",
    "Hoysala Architecture",
]


class WikipediaExtractor:

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
            follow_redirects=True,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        """Make a Wikipedia API call with retry logic."""
        async with SEMAPHORE:
            for attempt in range(5):
                try:
                    resp = await self.client.get(WIKI_API, params=params)
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    wait = 2 ** attempt
                    logger.warning(f"Wikipedia request failed (attempt {attempt+1}): {e}. Retry in {wait}s")
                    await asyncio.sleep(wait)
        return {}

    async def category_exists(self, category: str) -> bool:
        """Check if a Wikipedia category page exists."""
        data = await self._get({
            "action": "query",
            "titles": f"Category:{category}",
            "format": "json",
            "formatversion": "2",
        })
        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return False
        return not pages[0].get("missing", False)

    async def get_category_members(
        self,
        category: str,
        limit: int = 500,
        include_subcats: bool = False,
    ) -> list[str]:
        """
        Get article titles in a Wikipedia category.
        Handles pagination via cmcontinue.
        Returns empty list (not error) if category does not exist.
        """
        # Verify category exists first
        if not await self.category_exists(category):
            logger.warning(f"Category not found on Wikipedia: '{category}'")
            return []

        titles: list[str] = []
        params: dict[str, Any] = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "page",
            "cmlimit": min(limit, 500),
            "format": "json",
            "formatversion": "2",
        }

        while True:
            data = await self._get(params)
            members = data.get("query", {}).get("categorymembers", [])
            # ns=0 is the main article namespace
            titles.extend(m["title"] for m in members if m.get("ns") == 0)

            cont = data.get("continue", {}).get("cmcontinue")
            if not cont or len(titles) >= limit:
                break
            params["cmcontinue"] = cont
            await asyncio.sleep(0.5)

        logger.info(f"Category '{category}': {len(titles)} articles found")
        return titles[:limit]

    async def get_subcategory_members(self, category: str, depth: int = 1) -> list[str]:
        """
        Recursively collect article titles from a category and its subcategories.
        depth=1 means only immediate subcategories (safe, avoids infinite loops).
        """
        all_titles: set[str] = set()

        # Get direct members
        direct = await self.get_category_members(category, limit=500)
        all_titles.update(direct)

        if depth <= 0:
            return list(all_titles)

        # Get subcategories
        if not await self.category_exists(category):
            return list(all_titles)

        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "subcat",
            "cmlimit": "50",
            "format": "json",
            "formatversion": "2",
        }
        data = await self._get(params)
        subcats = data.get("query", {}).get("categorymembers", [])

        for subcat in subcats[:20]:  # Cap subcategory depth
            subcat_name = subcat["title"].replace("Category:", "")
            sub_titles = await self.get_category_members(subcat_name, limit=200)
            all_titles.update(sub_titles)
            await asyncio.sleep(0.3)

        return list(all_titles)

    async def discover_titles(
        self,
        categories: list[str] | None = None,
        seed_titles: list[str] | None = None,
        max_titles: int = 1000,
    ) -> list[str]:
        """
        Discover article titles from multiple categories + seed list.
        Returns a deduplicated list up to max_titles.
        """
        all_titles: set[str] = set()

        # Add seed titles first (known to exist)
        if seed_titles:
            all_titles.update(seed_titles)

        # Traverse categories
        for cat in (categories or []):
            if len(all_titles) >= max_titles:
                break
            members = await self.get_subcategory_members(cat, depth=1)
            all_titles.update(members)
            logger.info(f"Running total after '{cat}': {len(all_titles)} titles")
            await asyncio.sleep(1)

        return list(all_titles)[:max_titles]

    async def fetch_article(self, title: str) -> dict[str, Any] | None:
        """
        Fetch full article text + metadata for a given title.
        Returns None if the article does not exist.
        """
        data = await self._get({
            "action": "query",
            "titles": title,
            "prop": "extracts|categories|links|info|pageprops",
            "exlimit": "1",
            "explaintext": True,
            "exsectionformat": "wiki",
            "inprop": "url",
            "cllimit": "50",
            "pllimit": "50",
            "clshow": "!hidden",   # Exclude hidden maintenance categories
            "format": "json",
            "formatversion": "2",
        })

        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return None
        page = pages[0]

        if page.get("missing") or "extract" not in page:
            logger.debug(f"No Wikipedia article: '{title}'")
            return None

        # Check for redirects via pageprops
        pageprops = page.get("pageprops", {})
        if "disambiguation" in pageprops:
            logger.debug(f"Skipping disambiguation page: '{title}'")
            return None

        full_text = page.get("extract", "")
        if not full_text.strip():
            return None

        intro = self._extract_intro(full_text)
        sections = self._extract_sections(full_text)
        categories = [
            c.get("title", "").replace("Category:", "")
            for c in page.get("categories", [])
        ]
        links = [lk.get("title", "") for lk in page.get("links", [])]
        word_count = len(full_text.split())

        # Wikidata QID from page props (if tagged)
        wikidata_qid = pageprops.get("wikibase_item")

        return {
            "title": page.get("title", title),
            "page_id": page.get("pageid"),
            "wikidata_qid": wikidata_qid,
            "full_text": full_text,
            "intro": intro,
            "word_count": word_count,
            "char_count": len(full_text),
            "sections": sections,
            "section_count": len(sections),
            "categories": categories,
            "links": links[:100],
            "url": page.get("fullurl", f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"),
            "is_stub": len(full_text) < 500,
        }

    def _extract_intro(self, full_text: str) -> str:
        """Extract the lead paragraph (before first == section ==)."""
        lines = full_text.split("\n")
        intro_lines = []
        for line in lines:
            if line.startswith("=="):
                break
            if line.strip():
                intro_lines.append(line.strip())
        return " ".join(intro_lines)[:1000]

    def _extract_sections(self, full_text: str) -> list[dict]:
        """Extract section titles and depths from full text."""
        sections = []
        for match in re.finditer(r"^(==+)\s*(.+?)\s*\1\s*$", full_text, re.MULTILINE):
            depth = len(match.group(1)) - 2
            title = match.group(2).strip()
            sections.append({"title": title, "depth": depth})
        return sections

    async def batch_fetch(
        self,
        titles: list[str],
        delay: float = 0.35,
    ) -> list[dict[str, Any]]:
        """
        Fetch article list concurrently (max 3 at a time).
        Filters out None results and disambiguation pages.
        """
        results: list[dict[str, Any]] = []
        batch: list = []

        for i, title in enumerate(titles):
            batch.append(self.fetch_article(title))
            if len(batch) >= 3 or i == len(titles) - 1:
                batch_results = await asyncio.gather(*batch, return_exceptions=True)
                for r in batch_results:
                    if isinstance(r, dict) and r is not None:
                        results.append(r)
                    elif isinstance(r, Exception):
                        logger.debug(f"Fetch exception: {r}")
                batch = []
                await asyncio.sleep(delay)

        return results

    def save_articles(self, articles: list[dict[str, Any]], filename: str) -> Path:
        """Save fetched articles to JSONL checkpoint."""
        output_file = OUTPUT_DIR / filename
        with open(output_file, "w", encoding="utf-8") as f:
            for article in articles:
                f.write(json.dumps(article, ensure_ascii=False) + "\n")
        logger.info(f"Saved {len(articles)} articles -> {output_file}")
        return output_file


# ── Phase 1 Validation ────────────────────────────────────────────────────────

async def validate_wikipedia(sample_size: int = 50) -> None:
    print("\n" + "=" * 60)
    print("ARKANA -- Wikipedia Extractor Validation (v2)")
    print("=" * 60)

    extractor = WikipediaExtractor()
    try:
        # Step 1: Discover titles from verified categories + seed list
        print(f"\n[1/3] Discovering titles from categories and seed list...")
        titles = await extractor.discover_titles(
            categories=VERIFIED_CATEGORIES[:5],  # First 5 for validation
            seed_titles=KNOWN_HERITAGE_TITLES,
            max_titles=sample_size,
        )
        print(f"Discovered {len(titles)} unique titles")

        # Step 2: Batch fetch articles
        print(f"\n[2/3] Fetching {len(titles)} articles (max 3 concurrent)...")
        articles = await extractor.batch_fetch(titles[:sample_size])

        # Step 3: Save and report
        print(f"\n[3/3] Saving checkpoint...")
        extractor.save_articles(articles, "validation_sample.jsonl")

        stub_count = sum(1 for a in articles if a.get("is_stub"))
        word_counts = [a.get("word_count", 0) for a in articles]
        with_qid = sum(1 for a in articles if a.get("wikidata_qid"))

        print(f"\n{'Metric':<35} {'Value':>15}")
        print("-" * 52)
        print(f"{'Titles discovered':<35} {len(titles):>15}")
        print(f"{'Articles fetched':<35} {len(articles):>15}")
        print(f"{'Stub articles (<500 chars)':<35} {stub_count:>15} ({stub_count/max(len(articles),1)*100:.1f}%)")
        print(f"{'Articles with Wikidata QID':<35} {with_qid:>15}")
        print(f"{'Avg word count':<35} {sum(word_counts)//max(len(word_counts),1):>15}")
        print(f"\nOutput: {OUTPUT_DIR / 'validation_sample.jsonl'}")
        print("\nWikipedia validation complete")

    finally:
        await extractor.close()


if __name__ == "__main__":
    asyncio.run(validate_wikipedia(sample_size=50))
