"""
Hybrid Retrieval with Reciprocal Rank Fusion (RRF) for Arkana
Combines dense vector search (Qdrant) and sparse BM25 search (PostgreSQL).
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RetrievalConfig:
    """Configuration for hybrid retrieval"""
    dense_top_k: int = 20
    sparse_top_k: int = 20
    fused_top_k: int = 20
    rrf_k: int = 60  # RRF parameter


def reciprocal_rank_fusion(
    dense_results: List[Dict[str, Any]],
    sparse_results: List[Dict[str, Any]],
    k: int = 60,
    top_k: int = 20
) -> List[Dict[str, Any]]:
    """
    Apply Reciprocal Rank Fusion to merge dense and sparse retrieval results.
    
    RRF formula: score = sum(1 / (k + rank)) for each result list
    
    Args:
        dense_results: List of {"chunk": {...}, "score": float, "rank": int}
        sparse_results: List of {"chunk": {...}, "score": float, "rank": int}
        k: RRF parameter (default 60)
        top_k: Number of fused results to return
        
    Returns:
        Fused results sorted by RRF score
    """
    scores = {}
    all_chunks = {}
    
    # Process dense results
    for result in dense_results:
        chunk_id = result["chunk"]["chunk_id"]
        rank = result["rank"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        all_chunks[chunk_id] = result["chunk"]
    
    # Process sparse results
    for result in sparse_results:
        chunk_id = result["chunk"]["chunk_id"]
        rank = result["rank"]
        scores[chunk_id] = scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        all_chunks[chunk_id] = result["chunk"]
    
    # Sort by combined RRF score
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return top-k fused results
    fused_results = []
    for chunk_id, rrf_score in ranked[:top_k]:
        fused_results.append({
            "chunk": all_chunks[chunk_id],
            "rrf_score": rrf_score,
            "chunk_id": chunk_id
        })
    
    return fused_results


class HybridRetriever:
    """
    Hybrid retriever that combines dense (Qdrant) and sparse (PostgreSQL BM25) search
    using Reciprocal Rank Fusion.
    """
    
    def __init__(
        self, 
        embedder,  # Embedder instance with search_dense and search_sparse methods
        config: Optional[RetrievalConfig] = None
    ):
        self.embedder = embedder
        self.config = config or RetrievalConfig()
    
    async def retrieve(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid retrieval: dense + sparse + RRF fusion.
        
        Args:
            query: Search query text
            filters: Optional metadata filters (e.g., {"tribe_name": "Warli"})
            top_k: Number of final results to return
            
        Returns:
            Fused results sorted by RRF score
        """
        import asyncio
        top_k = top_k or self.config.fused_top_k
        
        # Run both retrievers concurrently
        
        dense_task = asyncio.to_thread(
            self.embedder.search_dense,
            query, 
            filters, 
            self.config.dense_top_k
        )
        
        sparse_task = self.embedder.search_sparse(
            query, 
            top_k=self.config.sparse_top_k
        )
        
        dense_results, sparse_results = await asyncio.gather(dense_task, sparse_task)
        
        # Apply RRF fusion
        fused = reciprocal_rank_fusion(
            dense_results,
            sparse_results,
            k=self.config.rrf_k,
            top_k=top_k
        )
        
        return fused
    



if __name__ == "__main__":
    # Test RRF fusion
    dense = [
        {"chunk": {"chunk_id": "a", "text": "chunk a"}, "score": 0.9, "rank": 0},
        {"chunk": {"chunk_id": "b", "text": "chunk b"}, "score": 0.8, "rank": 1},
        {"chunk": {"chunk_id": "c", "text": "chunk c"}, "score": 0.7, "rank": 2},
    ]
    
    sparse = [
        {"chunk": {"chunk_id": "b", "text": "chunk b"}, "score": 0.95, "rank": 0},
        {"chunk": {"chunk_id": "d", "text": "chunk d"}, "score": 0.85, "rank": 1},
        {"chunk": {"chunk_id": "a", "text": "chunk a"}, "score": 0.75, "rank": 2},
    ]
    
    fused = reciprocal_rank_fusion(dense, sparse, k=60, top_k=5)
    
    print("Fused results:")
    for i, r in enumerate(fused):
        print(f"  {i+1}. {r['chunk']['chunk_id']} - RRF score: {r['rrf_score']:.4f}")