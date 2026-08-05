import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from embedder import Embedder, EmbeddingConfig

async def run_tests():
    # Setup Config and mock the external services
    config = EmbeddingConfig()
    
    # Mock Qdrant before init
    with patch('embedder.QdrantClient') as MockQdrant:
        mock_qdrant_instance = MockQdrant.return_value
        embedder = Embedder(config)
        embedder.qdrant = mock_qdrant_instance
    
    # Mock Postgres Pool
    mock_pool = MagicMock()
    mock_conn = AsyncMock()
    # fetch returns rows, executemany returns None
    mock_conn.fetch.return_value = [{"chunk_id": "test", "chunk_text": "mock row", "tribe_name": "Warli", "region": "Maharashtra", "source_title": "Title", "institution": "MAP", "rank_score": 1.0}]
    
    # acquire context manager
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    embedder.db_pool = mock_pool
    
    test_chunks = [
        {
            "chunk_id": str(uuid.uuid4()),
            "doc_id": "test_doc",
            "chunk_index": 0,
            "text": "This is a test document.",
            "token_count": 5
        }
    ]
    
    print("--- Test 1: Embedding still works ---")
    chunks_with_vec = embedder.embed_chunks(test_chunks)
    assert "vector" in chunks_with_vec[0]
    print("PASSED")

    print("--- Test 2: Qdrant upsert succeeds ---")
    embedder.upsert_to_qdrant(chunks_with_vec)
    embedder.qdrant.upsert.assert_called_once()
    print("PASSED")

    print("--- Test 3: PostgreSQL upsert succeeds into rag_chunks ---")
    await embedder.upsert_to_postgres(chunks_with_vec)
    # Check that executemany was called with rag_chunks
    call_args = mock_conn.executemany.call_args[0]
    query = call_args[0]
    assert "INSERT INTO rag_chunks" in query
    print("PASSED")
    
    print("--- Test 4: Dense search returns expected schema ---")
    # Mock search
    mock_point = MagicMock()
    mock_point.payload = {"text": "mock"}
    mock_point.score = 0.99
    embedder.qdrant.search.return_value = [mock_point]
    dense_results = embedder.search_dense("test", top_k=1)
    assert "chunk" in dense_results[0]
    assert "score" in dense_results[0]
    assert "rank" in dense_results[0]
    print("PASSED")
    
    print("--- Test 5: Sparse search returns expected schema ---")
    sparse_results = await embedder.search_sparse("test", top_k=1)
    assert "chunk" in sparse_results[0]
    assert "score" in sparse_results[0]
    assert "rank" in sparse_results[0]
    
    # Verify the query has rag_chunks
    call_args = mock_conn.fetch.call_args[0]
    query = call_args[0]
    assert "FROM rag_chunks" in query
    print("PASSED")
    
    print("--- Test 6: process_and_index() can be awaited natively ---")
    res = await embedder.process_and_index(test_chunks)
    assert res["embedded"] == 1
    print("PASSED")
    
    print("--- Test 7: Public API signatures unaffected ---")
    import inspect
    assert inspect.iscoroutinefunction(embedder.process_and_index)
    print("PASSED")

if __name__ == "__main__":
    asyncio.run(run_tests())
