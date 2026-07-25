"""
Arkana — Wikimedia Commons Image Extractor
Fetches image URLs and attribution metadata for heritage sites.

Strategy:
  - For each site, query Commons API by site name + category
  - Store: URL, thumbnail, license, author, commons filename
  - DO NOT download images — store URLs only

⚠️ Important: Do NOT bulk download images during ingestion.
Store image URLs + attribution metadata only.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from ingestion.config import RAW_DIR, USER_AGENT
from ingestion.models.heritage_schema import DataSource, SiteImage
from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

OUTPUT_DIR = RAW_DIR / "wikimedia_commons"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
THUMB_WIDTH = 400
SEMAPHORE = asyncio.Semaphore(3)

# Wikimedia image URL → thumbnail URL conversion
# Pattern: /wikipedia/commons/X/XY/Filename.jpg
# Thumb: /wikipedia/commons/thumb/X/XY/Filename.jpg/{width}px-Filename.jpg
COMMONS_BASE = "https://upload.wikimedia.org/wikipedia/commons"


def commons_url_to_thumb(url: str, width: int = THUMB_WIDTH) -> str | None:
    """Convert a Wikimedia Commons image URL to a thumbnail URL."""
    try:
        if "/wikipedia/commons/" not in url:
            return None
        parts = url.split("/wikipedia/commons/")
        path = parts[1]          # e.g., "a/ab/Taj_Mahal.jpg"
        filename = path.split("/")[-1]
        return f"{COMMONS_BASE}/thumb/{path}/{width}px-{filename}"
    except Exception:
        return None


class WikimediaCommonsExtractor:

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        )

    async def close(self) -> None:
        await self.client.aclose()

    async def _get(self, params: dict[str, Any]) -> dict[str, Any]:
        async with SEMAPHORE:
            for attempt in range(4):
                try:
                    resp = await self.client.get(COMMONS_API, params=params)
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    wait = 2 ** attempt
                    logger.warning(f"Commons API attempt {attempt+1} failed: {e}. Retry in {wait}s")
                    await asyncio.sleep(wait)
        return {}

    async def get_images_for_page(
        self,
        wikipedia_title: str,
        max_images: int = 5,
    ) -> list[SiteImage]:
        """
        Get images from a Wikipedia page by fetching Commons files linked to it.
        Uses the MediaWiki API to get images associated with a Wikipedia article.
        """
        params = {
            "action": "query",
            "titles": wikipedia_title,
            "prop": "images",
            "imlimit": max_images,
            "format": "json",
            "formatversion": 2,
        }
        data = await self._get(params)
        pages = data.get("query", {}).get("pages", [])
        if not pages:
            return []

        image_titles = []
        for page in pages:
            for img in page.get("images", []):
                title = img.get("title", "")
                if title and not title.endswith((".svg", ".ogg", ".pdf", ".ogv")):
                    image_titles.append(title)

        if not image_titles:
            return []

        return await self._fetch_image_info(image_titles[:max_images])

    async def _fetch_image_info(
        self,
        image_titles: list[str],
    ) -> list[SiteImage]:
        """Fetch image URL, license, and author for a list of Commons image titles."""
        if not image_titles:
            return []

        params = {
            "action": "query",
            "titles": "|".join(image_titles),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": THUMB_WIDTH,
            "format": "json",
            "formatversion": 2,
        }
        data = await self._get(params)
        pages = data.get("query", {}).get("pages", [])

        images: list[SiteImage] = []
        for page in pages:
            info_list = page.get("imageinfo", [])
            if not info_list:
                continue
            info = info_list[0]
            url = info.get("url", "")
            thumb_url = info.get("thumburl") or commons_url_to_thumb(url)

            metadata = info.get("extmetadata", {})
            license_val = (
                metadata.get("LicenseShortName", {}).get("value")
                or metadata.get("License", {}).get("value")
            )
            artist = metadata.get("Artist", {}).get("value", "")
            # Strip HTML tags from artist
            import re
            artist = re.sub(r"<[^>]+>", "", artist).strip() if artist else None

            filename = page.get("title", "").replace("File:", "")

            if url:
                try:
                    images.append(
                        SiteImage(
                            url=url,
                            thumbnail_url=thumb_url,
                            license=license_val,
                            author=artist,
                            source=DataSource.WIKIMEDIA_COMMONS,
                            commons_filename=filename,
                        )
                    )
                except Exception as e:
                    logger.debug(f"Failed to parse image {filename}: {e}")

        return images

    async def search_site_images(
        self,
        site_name: str,
        max_images: int = 5,
    ) -> list[SiteImage]:
        """
        Search Commons for images of a heritage site by name.
        Fallback when Wikipedia page title is unknown.
        """
        params = {
            "action": "query",
            "list": "search",
            "srnamespace": 6,  # File namespace
            "srsearch": f"{site_name} India heritage",
            "srlimit": max_images * 2,
            "format": "json",
        }
        data = await self._get(params)
        results = data.get("query", {}).get("search", [])
        titles = [r["title"] for r in results if not any(
            r["title"].lower().endswith(ext) for ext in [".svg", ".ogg", ".pdf"]
        )]
        if not titles:
            return []
        return await self._fetch_image_info(titles[:max_images])


# ── Phase 1 Validation ────────────────────────────────────────────────────────

async def validate_wikimedia_commons() -> None:
    print("\n" + "=" * 60)
    print("ARKANA — Wikimedia Commons Extractor Validation")
    print("=" * 60)

    test_sites = [
        ("Taj Mahal", "Taj Mahal"),
        ("Qutb Minar", "Qutb Minar"),
        ("Hampi", "Hampi"),
        ("Ajanta Caves", "Ajanta Caves"),
        ("Red Fort", "Red Fort"),
    ]

    extractor = WikimediaCommonsExtractor()
    results = []
    try:
        for name, wiki_title in test_sites:
            images = await extractor.get_images_for_page(wiki_title, max_images=3)
            results.append({
                "site": name,
                "image_count": len(images),
                "first_url": images[0].url if images else None,
                "first_license": images[0].license if images else None,
            })
            print(f"  {name}: {len(images)} images found")
            await asyncio.sleep(0.5)
    finally:
        await extractor.close()

    # Save sample
    output_file = OUTPUT_DIR / "commons_sample.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    total_images = sum(r["image_count"] for r in results)
    print(f"\nTotal images fetched (5 sites): {total_images}")
    print(f"Output: {output_file}")
    print("\n✅ Wikimedia Commons validation complete")


if __name__ == "__main__":
    asyncio.run(validate_wikimedia_commons())
