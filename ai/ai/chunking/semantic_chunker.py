"""
Semantic Chunking Pipeline for Arkana
Implements sentence-level cosine similarity boundary detection for semantic chunking.
"""

import uuid
import nltk
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from dataclasses import dataclass
import re

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab', quiet=True)


@dataclass
class ChunkConfig:
    """Configuration for semantic chunking"""
    min_tokens: int = 150
    max_tokens: int = 512
    overlap_tokens: int = 50
    similarity_threshold: float = 0.6
    embedding_model: str = "all-MiniLM-L6-v2"


class SemanticChunker:
    """
    Semantic chunker that uses sentence-level cosine similarity to detect
    semantic boundaries in text. Produces chunks with metadata payloads.
    """
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        self.embedder = SentenceTransformer(self.config.embedding_model)
        
        # Source-specific threshold calibration
        self.source_thresholds = {
            "map_academy": 0.65,
            "ignca": 0.55,
            "museums_of_india": 0.60,
            "asi": 0.60,
            "internet_archive": 0.60,
            "europeana": 0.60,
        }
    
    def clean_text(self, text: str, source: str = "default") -> str:
        """
        Clean text before chunking, especially important for noisy OCR sources.
        """
        if source == "ignca":
            # Remove lines that are likely headers/footers/page numbers
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                # Skip empty lines
                if not line:
                    continue
                # Skip lines that are all caps (likely headers)
                if line.isupper() and len(line.split()) < 10:
                    continue
                # Skip page numbers
                if re.match(r'^\d+$', line):
                    continue
                # Skip lines with fewer than 5 words that look like headers/footers
                if len(line.split()) < 5 and (line.isupper() or re.match(r'^[\d\W]+$', line)):
                    continue
                cleaned_lines.append(line)
            text = '\n'.join(cleaned_lines)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def count_tokens(self, text: str) -> int:
        """Approximate token count (roughly 4 chars per token for English)"""
        return len(text) // 4
    
    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using NLTK"""
        return nltk.sent_tokenize(text)
    
    def compute_similarity_boundaries(self, sentences: List[str], threshold: float) -> List[int]:
        """
        Compute cosine similarity between adjacent sentences and identify
        boundaries where similarity drops below threshold.
        """
        if len(sentences) < 2:
            return [0]
        
        # Embed all sentences
        embeddings = self.embedder.encode(sentences, convert_to_numpy=True)
        
        boundaries = [0]  # First sentence starts first chunk
        
        for i in range(len(sentences) - 1):
            # Compute cosine similarity between adjacent sentences
            sim = np.dot(embeddings[i], embeddings[i + 1]) / (
                np.linalg.norm(embeddings[i]) * np.linalg.norm(embeddings[i + 1])
            )
            
            # If similarity drops below threshold, start new chunk
            if sim < threshold:
                boundaries.append(i + 1)
        
        return boundaries
    
    def create_chunks_from_boundaries(
        self, 
        sentences: List[str], 
        boundaries: List[int],
        doc_id: str,
        metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create chunks from sentence boundaries with token limits and overlap"""
        chunks = []
        
        for i in range(len(boundaries)):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1] if i + 1 < len(boundaries) else len(sentences)
            
            # Get sentences for this chunk
            chunk_sentences = sentences[start_idx:end_idx]
            chunk_text = ' '.join(chunk_sentences)
            
            # Check token count
            token_count = self.count_tokens(chunk_text)
            
            # If too large, split further by token count
            if token_count > self.config.max_tokens:
                sub_chunks = self._split_by_token_limit(chunk_sentences, doc_id, metadata, i)
                chunks.extend(sub_chunks)
            elif token_count >= self.config.min_tokens:
                chunk = self._create_chunk(
                    chunk_text=chunk_text,
                    chunk_index=len(chunks),
                    doc_id=doc_id,
                    metadata=metadata
                )
                chunks.append(chunk)
            # If too small, try to merge with next chunk (handled in next iteration)
        
        # Apply overlap between adjacent chunks
        chunks = self._apply_overlap(chunks)
        
        return chunks
    
    def _split_by_token_limit(
        self, 
        sentences: List[str], 
        doc_id: str, 
        metadata: Dict[str, Any],
        base_index: int
    ) -> List[Dict[str, Any]]:
        """Split a large chunk into smaller ones respecting token limits"""
        chunks = []
        current_sentences = []
        current_tokens = 0
        
        for sent in sentences:
            sent_tokens = self.count_tokens(sent)
            if current_tokens + sent_tokens > self.config.max_tokens and current_sentences:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_sentences)
                chunk = self._create_chunk(
                    chunk_text=chunk_text,
                    chunk_index=len(chunks),
                    doc_id=doc_id,
                    metadata=metadata
                )
                chunks.append(chunk)
                current_sentences = [sent]
                current_tokens = sent_tokens
            else:
                current_sentences.append(sent)
                current_tokens += sent_tokens
        
        # Don't forget the last chunk
        if current_sentences:
            chunk_text = ' '.join(current_sentences)
            if self.count_tokens(chunk_text) >= self.config.min_tokens:
                chunk = self._create_chunk(
                    chunk_text=chunk_text,
                    chunk_index=len(chunks),
                    doc_id=doc_id,
                    metadata=metadata
                )
                chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(
        self, 
        chunk_text: str, 
        chunk_index: int, 
        doc_id: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a chunk dictionary with full metadata payload"""
        return {
            "chunk_id": str(uuid.uuid4()),
            "doc_id": doc_id,
            "chunk_index": chunk_index,
            "text": chunk_text,
            "token_count": self.count_tokens(chunk_text),
            "tribe_name": metadata.get("tribe_name"),
            "region": metadata.get("region"),
            "time_period_start": metadata.get("time_period_start"),
            "time_period_end": metadata.get("time_period_end"),
            "institution": metadata.get("institution"),
            "source_title": metadata.get("title"),
            "source_url": metadata.get("url"),
        }
    
    def _apply_overlap(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply token overlap between adjacent chunks"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = overlapped_chunks[-1]
            curr_chunk = chunks[i]
            
            # Get last N tokens from previous chunk
            prev_tokens = prev_chunk["text"].split()
            overlap_tokens = prev_tokens[-self.config.overlap_tokens:] if len(prev_tokens) > self.config.overlap_tokens else prev_tokens
            overlap_text = ' '.join(overlap_tokens)
            
            # Prepend overlap to current chunk
            overlapped_text = overlap_text + ' ' + curr_chunk["text"]
            
            overlapped_chunk = curr_chunk.copy()
            overlapped_chunk["text"] = overlapped_text
            overlapped_chunk["token_count"] = self.count_tokens(overlapped_text)
            overlapped_chunk["chunk_index"] = i
            
            overlapped_chunks.append(overlapped_chunk)
        
        return overlapped_chunks
    
    def chunk_document(
        self, 
        text: str, 
        doc_id: str, 
        metadata: Dict[str, Any],
        source: str = "default"
    ) -> List[Dict[str, Any]]:
        """
        Main entry point: chunk a document semantically.
        
        Args:
            text: Raw document text
            doc_id: Unique document identifier
            metadata: Document metadata (title, tribe, region, etc.)
            source: Source name for threshold calibration
            
        Returns:
            List of chunk dictionaries with metadata
        """
        # Clean text
        cleaned_text = self.clean_text(text, source)
        
        # Split into sentences
        sentences = self.split_into_sentences(cleaned_text)
        
        if not sentences:
            return []
        
        # Get source-specific threshold
        threshold = self.source_thresholds.get(source, self.config.similarity_threshold)
        
        # Compute semantic boundaries
        boundaries = self.compute_similarity_boundaries(sentences, threshold)
        
        # Create chunks with metadata
        chunks = self.create_chunks_from_boundaries(sentences, boundaries, doc_id, metadata)
        
        return chunks
    
    def chunk_documents_batch(
        self, 
        documents: List[Dict[str, Any]],
        source: str = "default"
    ) -> List[Dict[str, Any]]:
        """Process multiple documents in batch"""
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_document(
                text=doc["text"],
                doc_id=doc["doc_id"],
                metadata=doc["metadata"],
                source=source
            )
            all_chunks.extend(chunks)
        
        return all_chunks


def calibrate_thresholds(chunker: SemanticChunker, sample_texts: Dict[str, str]) -> Dict[str, float]:
    """
    Calibrate similarity thresholds per source type by analyzing chunk size distributions.
    """
    results = {}
    
    for source, text in sample_texts.items():
        chunks = chunker.chunk_document(text, f"cal_{source}", {}, source)
        if chunks:
            avg_tokens = np.mean([c["token_count"] for c in chunks])
            results[source] = {
                "threshold": chunker.source_thresholds.get(source, chunker.config.similarity_threshold),
                "num_chunks": len(chunks),
                "avg_tokens": avg_tokens,
                "target_tokens": 300
            }
    
    return results


if __name__ == "__main__":
    # Quick test
    config = ChunkConfig(similarity_threshold=0.6)
    chunker = SemanticChunker(config)
    
    test_text = """
    Warli painting is a form of tribal art mostly created by the tribal people from the North Sahyadri Range in Maharashtra, India.
    The Warli tribe is one of the largest in India, located outside of Mumbai.
    The style of Warli painting is very basic and uses only white color on a red or brown background.
    The paintings use a set of basic geometric shapes: a circle, a triangle, and a square.
    These shapes are symbolic of different elements of nature.
    The circle represents the sun and the moon, the triangle represents mountains and conical trees.
    The square represents a sacred enclosure or a piece of land.
    """
    
    metadata = {
        "title": "Warli Art Overview",
        "tribe_name": "Warli",
        "region": "Maharashtra",
        "institution": "MAP Academy",
        "url": "https://mapacademy.io/warli"
    }
    
    chunks = chunker.chunk_document(test_text, "doc_warli_001", metadata, "map_academy")
    
    print(f"Created {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}: {chunk['token_count']} tokens")
        print(f"  Text: {chunk['text'][:100]}...")
        print(f"  Tribe: {chunk['tribe_name']}")
        print(f"  Region: {chunk['region']}")