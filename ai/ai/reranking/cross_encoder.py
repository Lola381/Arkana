"""
Cross-Encoder Reranking for Arkana
Reranks retrieved candidates using a cross-encoder model for improved relevance.
"""

from typing import List, Dict, Any, Optional
from sentence_transformers import CrossEncoder
import numpy as np
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RerankConfig:
    """Configuration for cross-encoder reranking"""
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_n: int = 4
    min_relevance_score: float = -5.0
    batch_size: int = 32


class CrossEncoderReranker:
    """
    Cross-encoder reranker that scores query-chunk pairs for relevance.
    More accurate than bi-encoder retrieval but slower, so used on top-k candidates.
    """
    
    def __init__(self, config: Optional[RerankConfig] = None):
        self.config = config or RerankConfig()
        self.reranker = CrossEncoder(self.config.model_name)
        logger.info(f"Loaded cross-encoder: {self.config.model_name}")
    
    def rerank(
        self, 
        query: str, 
        candidates: List[Dict[str, Any]], 
        top_n: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder.
        
        Args:
            query: User query text
            candidates: List of {"chunk": {...}, "score": float, "rank": int} from retrieval
            top_n: Number of top results to return (default from config)
            
        Returns:
            Reranked candidates with rerank_score, filtered by relevance threshold
        """
        if not candidates:
            return []
        
        top_n = top_n or self.config.top_n
        
        # Prepare query-chunk pairs
        pairs = [(query, candidate["chunk"]["text"]) for candidate in candidates]
        
        # Get cross-encoder scores
        scores = self.reranker.predict(pairs, batch_size=self.config.batch_size)
        
        # Attach scores to candidates
        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)
        
        # Sort by rerank score (descending)
        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        
        # Hard filter: reject chunks below minimum relevance threshold
        filtered = [
            c for c in reranked 
            if c["rerank_score"] > self.config.min_relevance_score
        ]
        
        # Return top-n
        return filtered[:top_n]
    
    def rerank_with_details(
        self, 
        query: str, 
        candidates: List[Dict[str, Any]], 
        top_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Rerank with detailed scoring information.
        
        Returns:
            Dict with reranked results and score statistics
        """
        if not candidates:
            return {"results": [], "stats": {}}
        
        top_n = top_n or self.config.top_n
        
        pairs = [(query, candidate["chunk"]["text"]) for candidate in candidates]
        scores = self.reranker.predict(pairs, batch_size=self.config.batch_size)
        
        # Attach scores
        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)
        
        # Sort and filter
        reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
        filtered = [
            c for c in reranked 
            if c["rerank_score"] > self.config.min_relevance_score
        ]
        top_results = filtered[:top_n]
        
        # Compute stats
        all_scores = [c["rerank_score"] for c in candidates]
        stats = {
            "num_candidates": len(candidates),
            "num_after_filter": len(filtered),
            "num_returned": len(top_results),
            "max_score": max(all_scores) if all_scores else 0,
            "min_score": min(all_scores) if all_scores else 0,
            "mean_score": np.mean(all_scores) if all_scores else 0,
            "threshold": self.config.min_relevance_score
        }
        
        return {
            "results": top_results,
            "stats": stats
        }


def create_reranker(model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> CrossEncoderReranker:
    """Factory function to create a reranker with default config"""
    config = RerankConfig(model_name=model_name)
    return CrossEncoderReranker(config)


if __name__ == "__main__":
    # Quick test
    config = RerankConfig()
    reranker = CrossEncoderReranker(config)
    
    query = "What is the significance of Warli painting?"
    
    candidates = [
        {
            "chunk": {
                "chunk_id": "c1",
                "text": "Warli painting is a form of tribal art from Maharashtra using geometric shapes."
            },
            "score": 0.85,
            "rank": 0
        },
        {
            "chunk": {
                "chunk_id": "c2",
                "text": "The Warli tribe lives in the Thane district of Maharashtra near Mumbai."
            },
            "score": 0.72,
            "rank": 1
        },
        {
            "chunk": {
                "chunk_id": "c3",
                "text": "Mughal miniature painting flourished under Akbar, Jahangir, and Shah Jahan."
            },
            "score": 0.65,
            "rank": 2
        }
    ]
    
    result = reranker.rerank_with_details(query, candidates, top_n=2)
    
    print("Reranked results:")
    for i, r in enumerate(result["results"]):
        print(f"  {i+1}. [{r['rerank_score']:.3f}] {r['chunk']['text'][:60]}...")
    
    print(f"\nStats: {result['stats']}")