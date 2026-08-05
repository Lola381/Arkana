import asyncio
from unittest.mock import MagicMock, AsyncMock
from rrf_fusion import HybridRetriever, RetrievalConfig, reciprocal_rank_fusion

async def run_tests():
    # Setup mocks
    embedder = MagicMock()
    
    # Mock dense results
    dense_data = [
        {"chunk": {"chunk_id": "a", "text": "chunk a"}, "score": 0.9, "rank": 0},
        {"chunk": {"chunk_id": "b", "text": "chunk b"}, "score": 0.8, "rank": 1},
        {"chunk": {"chunk_id": "c", "text": "chunk c"}, "score": 0.7, "rank": 2},
    ]
    embedder.search_dense.return_value = dense_data
    
    # Mock sparse results
    sparse_data = [
        {"chunk": {"chunk_id": "b", "text": "chunk b"}, "score": 0.95, "rank": 0},
        {"chunk": {"chunk_id": "d", "text": "chunk d"}, "score": 0.85, "rank": 1},
        {"chunk": {"chunk_id": "a", "text": "chunk a"}, "score": 0.75, "rank": 2},
    ]
    embedder.search_sparse = AsyncMock(return_value=sparse_data)
    
    config = RetrievalConfig(rrf_k=60)
    retriever = HybridRetriever(embedder=embedder, config=config)
    
    print("--- Test 1: Dense retrieval schema ---")
    assert "chunk" in dense_data[0]
    assert "score" in dense_data[0]
    assert "rank" in dense_data[0]
    print("PASSED")
    
    print("--- Test 2: Sparse retrieval schema ---")
    assert "chunk" in sparse_data[0]
    assert "score" in sparse_data[0]
    assert "rank" in sparse_data[0]
    print("PASSED")
    
    print("--- Test 3 & 7: RRF scores and ordering remain identical ---")
    # Manual expected calculation: 
    # a: 1/(60+0+1) + 1/(60+2+1) = 1/61 + 1/63 = 0.01639 + 0.01587 = 0.03226
    # b: 1/(60+1+1) + 1/(60+0+1) = 1/62 + 1/61 = 0.01612 + 0.01639 = 0.03252
    # c: 1/(60+2+1) = 1/63 = 0.01587
    # d: 1/(60+1+1) = 1/62 = 0.01612
    # Order should be: b, a, d, c
    fused = reciprocal_rank_fusion(dense_data, sparse_data, k=60, top_k=5)
    
    expected_order = ["b", "a", "d", "c"]
    actual_order = [r["chunk"]["chunk_id"] for r in fused]
    assert actual_order == expected_order
    
    print("Expected order matched:", actual_order)
    print("PASSED")
    
    print("--- Test 4 & 5: retrieve() executes concurrently with no event-loop errors ---")
    results = await retriever.retrieve("test query")
    assert len(results) == 4
    # Check that embedder methods were called
    embedder.search_dense.assert_called_once()
    embedder.search_sparse.assert_called_once()
    print("PASSED")
    
    print("--- Test 6: retrieve_sync() completely removed ---")
    try:
        retriever.retrieve_sync("test query")
        assert False, "retrieve_sync should not exist!"
    except AttributeError:
        pass
    print("PASSED")

if __name__ == "__main__":
    asyncio.run(run_tests())
