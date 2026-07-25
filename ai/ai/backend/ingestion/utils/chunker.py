"""
Arkana — Text Chunker (shared with AI layer)
Implements hierarchical parent-child chunking strategy.
Parent chunks stored in PostgreSQL; child chunks embedded in vector DB.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ingestion.utils.logger import get_logger

logger = get_logger(__name__)

# Approximate token count: ~1.3 chars per token for English
CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


@dataclass
class TextChunk:
    chunk_index: int
    chunk_text: str
    parent_section: str | None
    token_count: int
    source_url: str | None = None
    site_id: str | None = None
    site_name: str | None = None
    state: str | None = None
    category: str | None = None
    era: str | None = None
    metadata: dict = field(default_factory=dict)


# ── Section-Aware Splitter ────────────────────────────────────────────────────

SECTION_HEADER_RE = re.compile(r"^(==+)\s*(.+?)\s*\1\s*$", re.MULTILINE)

BOILERPLATE_SECTIONS = {
    "see also", "references", "external links", "further reading",
    "notes", "bibliography", "citations", "sources", "footnotes",
    "gallery", "awards", "gallery", "categories",
}


def split_by_sections(text: str) -> list[tuple[str, str]]:
    """
    Split Wikipedia article text into (section_name, section_text) pairs.
    The lead paragraph is named '__lead__'.
    Boilerplate sections (References, See Also, etc.) are dropped.
    """
    matches = list(SECTION_HEADER_RE.finditer(text))
    sections: list[tuple[str, str]] = []

    # Lead paragraph (before first header)
    lead_end = matches[0].start() if matches else len(text)
    lead_text = text[:lead_end].strip()
    if lead_text:
        sections.append(("__lead__", lead_text))

    for i, match in enumerate(matches):
        section_name = match.group(2).strip().lower()
        if section_name in BOILERPLATE_SECTIONS:
            continue
        section_start = match.end()
        section_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[section_start:section_end].strip()
        if section_text:
            sections.append((match.group(2).strip(), section_text))

    return sections


def _split_text_into_windows(
    text: str,
    max_tokens: int = 500,
    overlap_pct: float = 0.15,
) -> list[str]:
    """
    Split a single block of text into overlapping windows.
    Tries to split at sentence boundaries first.
    """
    max_chars = max_tokens * CHARS_PER_TOKEN
    overlap_chars = int(max_chars * overlap_pct)

    if estimate_tokens(text) <= max_tokens:
        return [text]

    # Try splitting by sentences
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for sent in sentences:
        sent_len = len(sent)
        if current_len + sent_len > max_chars and current:
            chunk = " ".join(current).strip()
            if chunk:
                chunks.append(chunk)
            # Keep overlap: walk back from end
            overlap_text = " ".join(current).strip()[-overlap_chars:]
            current = [overlap_text] if overlap_text else []
            current_len = len(overlap_text)
        current.append(sent)
        current_len += sent_len + 1

    if current:
        chunk = " ".join(current).strip()
        if chunk:
            chunks.append(chunk)

    return chunks if chunks else [text]


# ── Main Chunker ──────────────────────────────────────────────────────────────

def chunk_article(
    full_text: str,
    site_id: str,
    site_name: str,
    source_url: str | None = None,
    state: str | None = None,
    category: str | None = None,
    era: str | None = None,
    max_tokens_per_chunk: int = 500,
    overlap_pct: float = 0.15,
) -> list[TextChunk]:
    """
    Main entry point: chunk a Wikipedia article text into child chunks.
    Each chunk carries full metadata for RAG retrieval.

    Strategy: section-aware → split oversized sections into windows.
    Skips chunks with fewer than 50 tokens.

    Returns: list of TextChunk objects ready for embedding.
    """
    sections = split_by_sections(full_text)
    chunks: list[TextChunk] = []
    chunk_index = 0

    for section_name, section_text in sections:
        windows = _split_text_into_windows(
            section_text, max_tokens=max_tokens_per_chunk, overlap_pct=overlap_pct
        )
        for window in windows:
            token_count = estimate_tokens(window)
            if token_count < 50:
                continue  # Skip tiny fragments

            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    chunk_text=window,
                    parent_section=section_name if section_name != "__lead__" else None,
                    token_count=token_count,
                    source_url=source_url,
                    site_id=site_id,
                    site_name=site_name,
                    state=state,
                    category=category,
                    era=era,
                    metadata={
                        "site_id": site_id,
                        "site_name": site_name,
                        "section": section_name,
                        "state": state,
                        "category": category,
                        "era": era,
                        "source_url": source_url,
                        "chunk_index": chunk_index,
                    },
                )
            )
            chunk_index += 1

    logger.debug(
        f"Chunked '{site_name}' → {len(chunks)} chunks "
        f"from {len(sections)} sections"
    )
    return chunks
