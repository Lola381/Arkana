import asyncio
from unittest.mock import patch, MagicMock
from cross_encoder import CrossEncoderReranker, RerankConfig

async def run_tests():
    config = RerankConfig(min_relevance_score=-5.0, top_n=2)
    
    # Mock the sentence_transformers CrossEncoder
    with patch('cross_encoder.CrossEncoder') as MockEncoder:
        mock_instance = MagicMock()
        # Mock predict to return known scores for our test pairs
        # Let's say pairs are [ (query, "good chunk"), (query, "bad chunk"), (query, "best chunk") ]
        # We will return [0.5, -6.0, 0.9]
        mock_instance.predict.return_value = [0.5, -6.0, 0.9]
        MockEncoder.return_value = mock_instance
        
        reranker = CrossEncoderReranker(config)
        
        query = "test query"
        candidates = [
            {"chunk": {"text": "good chunk"}, "rank": 0, "score": 0.8},
            {"chunk": {"text": "bad chunk"}, "rank": 1, "score": 0.7},
            {"chunk": {"text": "best chunk"}, "rank": 2, "score": 0.6},
        ]
        
        # Deepcopy to check immutability manually
        import copy
        original_candidates = copy.deepcopy(candidates)
        
        print("--- Test 1 & 3: rerank executes without blocking and schema is unchanged ---")
        results = await reranker.rerank(query, candidates)
        
        # Schema unchanged: should have 'chunk', 'rank', 'score', and 'rerank_score'
        assert "chunk" in results[0]
        assert "rerank_score" in results[0]
        assert "score" in results[0]
        print("PASSED")
        
        print("--- Test 2: Immutability (Input candidates are untouched) ---")
        assert "rerank_score" not in candidates[0]
        assert candidates == original_candidates
        print("PASSED")
        
        print("--- Test 4 & 5: Ordering and threshold identical ---")
        # -6.0 is below min_relevance_score (-5.0), so "bad chunk" should be filtered out.
        # "best chunk" has 0.9, "good chunk" has 0.5.
        # So results should be ["best chunk", "good chunk"]
        assert len(results) == 2
        assert results[0]["chunk"]["text"] == "best chunk"
        assert results[0]["rerank_score"] == 0.9
        
        assert results[1]["chunk"]["text"] == "good chunk"
        assert results[1]["rerank_score"] == 0.5
        print("PASSED")
        
        print("--- Test 6: rerank_with_details is completely removed ---")
        try:
            getattr(reranker, "rerank_with_details")
            assert False, "rerank_with_details should not exist"
        except AttributeError:
            pass
        print("PASSED")

if __name__ == "__main__":
    asyncio.run(run_tests())
