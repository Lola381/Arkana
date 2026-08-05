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
from transformers import AutoTokenizer

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
    target_tokenizer_model: str = "sentence-transformers/all-mpnet-base-v2"


class SemanticChunker:
    """
    Semantic chunker that uses sentence-level cosine similarity to detect
    semantic boundaries in text. Produces chunks with metadata payloads.
    """
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        self.config = config or ChunkConfig()
        self.embedder = SentenceTransformer(self.config.embedding_model)
        
        # Load the exact tokenizer used by the downstream Embedder pipeline
        self.target_tokenizer = AutoTokenizer.from_pretrained(self.config.target_tokenizer_model)
        
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
        """Exact token count using the embedding model's tokenizer"""
        if not text.strip(): return 0
        return len(self.target_tokenizer.encode(text, add_special_tokens=False))
    
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
        orphan_sentences = []
        
        for i in range(len(boundaries)):
            start_idx = boundaries[i]
            end_idx = boundaries[i + 1] if i + 1 < len(boundaries) else len(sentences)
            
            # Get sentences for this chunk, including any orphans
            chunk_sentences = orphan_sentences + sentences[start_idx:end_idx]
            orphan_sentences = []
            
            if not chunk_sentences:
                continue
                
            chunk_text = ' '.join(chunk_sentences)
            
            # Check token count
            token_count = self.count_tokens(chunk_text)
            
            # The effective max tokens depends on whether this chunk will receive an overlap
            effective_max_tokens = self.config.max_tokens
            if len(chunks) > 0:
                effective_max_tokens -= self.config.overlap_tokens
                
            # If too large, split further by token count
            if token_count > effective_max_tokens:
                sub_chunks, leftover = self._split_by_token_limit(chunk_sentences, doc_id, metadata, len(chunks), effective_max_tokens)
                chunks.extend(sub_chunks)
                orphan_sentences = leftover
            elif token_count >= self.config.min_tokens:
                chunk = self._create_chunk(
                    chunk_text=chunk_text,
                    chunk_index=len(chunks),
                    doc_id=doc_id,
                    metadata=metadata
                )
                chunks.append(chunk)
            else:
                # If too small, keep as orphan to merge with next chunk
                orphan_sentences = chunk_sentences
        
        # Handle trailing orphans
        if orphan_sentences:
            chunk_text = ' '.join(orphan_sentences)
            if self.count_tokens(chunk_text) > 0:
                if chunks and chunks[-1]["token_count"] + self.count_tokens(chunk_text) <= self.config.max_tokens:
                    # Merge backward
                    merged_text = chunks[-1]["text"] + ' ' + chunk_text
                    chunks[-1]["text"] = merged_text
                    chunks[-1]["token_count"] = self.count_tokens(merged_text)
                else:
                    # Create standalone chunk
                    chunk = self._create_chunk(
                        chunk_text=chunk_text,
                        chunk_index=len(chunks),
                        doc_id=doc_id,
                        metadata=metadata
                    )
                    chunks.append(chunk)
                    
        # Apply overlap between adjacent chunks
        chunks = self._apply_overlap(chunks)
        
        return chunks
    
    def _split_by_token_limit(
        self, 
        sentences: List[str], 
        doc_id: str, 
        metadata: Dict[str, Any],
        base_index: int,
        effective_max_tokens: int
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """Split a large chunk into smaller ones respecting token limits. Returns (chunks, leftover_sentences)."""
        chunks = []
        current_sentences = []
        current_tokens = 0
        
        for sent in sentences:
            sent_tokens = self.count_tokens(sent)
            if current_tokens + sent_tokens > effective_max_tokens and current_sentences:
                # Create chunk from current sentences
                chunk_text = ' '.join(current_sentences)
                chunk = self._create_chunk(
                    chunk_text=chunk_text,
                    chunk_index=base_index + len(chunks),
                    doc_id=doc_id,
                    metadata=metadata
                )
                chunks.append(chunk)
                current_sentences = [sent]
                current_tokens = sent_tokens
                # All subsequent sub-chunks will receive an overlap from the previous one
                effective_max_tokens = self.config.max_tokens - self.config.overlap_tokens
            else:
                current_sentences.append(sent)
                current_tokens += sent_tokens
        
        # Handle the last chunk
        leftover_sentences = []
        if current_sentences:
            chunk_text = ' '.join(current_sentences)
            if self.count_tokens(chunk_text) >= self.config.min_tokens:
                chunk = self._create_chunk(
                    chunk_text=chunk_text,
                    chunk_index=base_index + len(chunks),
                    doc_id=doc_id,
                    metadata=metadata
                )
                chunks.append(chunk)
            else:
                leftover_sentences = current_sentences
        
        return chunks, leftover_sentences
    
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
            
            # Get last N tokens from previous chunk using tokenizer
            prev_token_ids = self.target_tokenizer.encode(prev_chunk["text"], add_special_tokens=False)
            overlap_token_ids = prev_token_ids[-self.config.overlap_tokens:] if len(prev_token_ids) > self.config.overlap_tokens else prev_token_ids
            overlap_text = self.target_tokenizer.decode(overlap_token_ids).strip()
            
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