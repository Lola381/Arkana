"""
Embedding Pipeline for Arkana
Batch embeddings using sentence-transformers/all-mpnet-base-v2 and Qdrant indexing.
"""

import uuid
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import asyncpg
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding pipeline"""
    model_name: str = "sentence-transformers/all-mpnet-base-v2"
    vector_size: int = 768
    batch_size: int = 32
    qdrant_collection: str = "arkana_corpus"
    qdrant_url: str = "http://localhost:6333"


class Embedder:
    """
    Handles embedding generation and Qdrant indexing for semantic chunks.
    Also manages PostgreSQL full-text search index (BM25).
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None, db_pool: Optional[asyncpg.Pool] = None):
        self.config = config or EmbeddingConfig()
        self.model = SentenceTransformer(self.config.model_name)
        self.qdrant = QdrantClient(url=self.config.qdrant_url)
        self.db_pool = db_pool
        
        # Ensure Qdrant collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create Qdrant collection if it doesn't exist"""
        collections = self.qdrant.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.config.qdrant_collection not in collection_names:
            self.qdrant.create_collection(
                collection_name=self.config.qdrant_collection,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {self.config.qdrant_collection}")
    
    def embed_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for a list of chunks.
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
            
        Returns:
            Chunks with added 'vector' field
        """
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings in batches
        vectors = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        # Attach vectors to chunks
        for chunk, vector in zip(chunks, vectors):
            chunk["vector"] = vector.tolist()
        
        return chunks
    
    def upsert_to_qdrant(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Upsert chunks with embeddings to Qdrant.
        
        Args:
            chunks: List of chunks with 'vector' field
            
        Returns:
            Number of points upserted
        """
        points = []
        
        for chunk in chunks:
            if "vector" not in chunk:
                logger.warning(f"Chunk {chunk.get('chunk_id')} missing vector, skipping")
                continue
            
            # Prepare payload (all metadata except vector)
            payload = {k: v for k, v in chunk.items() if k != "vector"}
            
            point = PointStruct(
                id=chunk["chunk_id"],
                vector=chunk["vector"],
                payload=payload
            )
            points.append(point)
        
        # Upsert in batches
        batch_size = 100
        total_upserted = 0
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.qdrant.upsert(
                collection_name=self.config.qdrant_collection,
                points=batch
            )
            total_upserted += len(batch)
            logger.info(f"Upserted batch {i//batch_size + 1}: {len(batch)} points")
        
        return total_upserted
    
    async def upsert_to_postgres(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Upsert chunk metadata to PostgreSQL for BM25 full-text search.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Number of rows upserted
        """
        if not self.db_pool:
            logger.warning("No database pool provided, skipping PostgreSQL upsert")
            return 0
        
        async with self.db_pool.acquire() as conn:
            # Prepare insert statement
            query = """
                INSERT INTO chunks (
                    chunk_id, doc_id, chunk_index, chunk_text, token_count,
                    tribe_name, region, time_period_start, time_period_end,
                    institution, source_title, source_url
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    chunk_text = EXCLUDED.chunk_text,
                    token_count = EXCLUDED.token_count,
                    tribe_name = EXCLUDED.tribe_name,
                    region = EXCLUDED.region,
                    time_period_start = EXCLUDED.time_period_start,
                    time_period_end = EXCLUDED.time_period_end,
                    institution = EXCLUDED.institution,
                    source_title = EXCLUDED.source_title,
                    source_url = EXCLUDED.source_url
            """
            
            values = [
                (
                    chunk["chunk_id"],
                    chunk["doc_id"],
                    chunk["chunk_index"],
                    chunk["text"],
                    chunk["token_count"],
                    chunk.get("tribe_name"),
                    chunk.get("region"),
                    chunk.get("time_period_start"),
                    chunk.get("time_period_end"),
                    chunk.get("institution"),
                    chunk.get("source_title"),
                    chunk.get("source_url"),
                )
                for chunk in chunks
            ]
            
            await conn.executemany(query, values)
            return len(values)
    
    def process_and_index(self, chunks: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Full pipeline: embed chunks and index to both Qdrant and PostgreSQL.
        
        Returns:
            Dict with counts of processed items
        """
        logger.info(f"Embedding {len(chunks)} chunks...")
        chunks_with_vectors = self.embed_chunks(chunks)
        
        logger.info(f"Upserting to Qdrant...")
        qdrant_count = self.upsert_to_qdrant(chunks_with_vectors)
        
        pg_count = 0
        if self.db_pool:
            import asyncio
            pg_count = asyncio.run(self.upsert_to_postgres(chunks_with_vectors))
        
        return {
            "embedded": len(chunks_with_vectors),
            "qdrant_upserted": qdrant_count,
            "postgres_upserted": pg_count
        }
    
    def search_dense(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Dense vector search in Qdrant.
        
        Args:
            query: Search query text
            filters: Optional metadata filters (e.g., {"tribe_name": "Warli"})
            top_k: Number of results to return
            
        Returns:
            List of search results with scores
        """
        query_vector = self.model.encode(query).tolist()
        
        # Build Qdrant filter
        qdrant_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                if value is not None:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
            if conditions:
                qdrant_filter = Filter(must=conditions)
        
        results = self.qdrant.search(
            collection_name=self.config.qdrant_collection,
            query_vector=query_vector,
            query_filter=qdrant_filter,
            limit=top_k,
            with_payload=True
        )
        
        return [
            {
                "chunk": r.payload,
                "score": r.score,
                "rank": i
            }
            for i, r in enumerate(results)
        ]
    
    async def search_sparse(
        self, 
        query: str, 
        top_k: int = 20,
        tribe_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Sparse BM25 search using PostgreSQL full-text search.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            tribe_name: Optional tribe filter
            
        Returns:
            List of search results with BM25 scores
        """
        if not self.db_pool:
            logger.warning("No database pool, returning empty results")
            return []
        
        # Build query with optional tribe filter
        where_clause = "WHERE to_tsvector('english', chunk_text) @@ plainto_tsquery('english', $1)"
        params = [query, top_k]
        
        if tribe_name:
            where_clause += " AND tribe_name = $3"
            params.append(tribe_name)
        
        sql = f"""
            SELECT 
                chunk_id, chunk_text, tribe_name, region, source_title, institution,
                ts_rank(to_tsvector('english', chunk_text), plainto_tsquery('english', $1)) AS rank_score
            FROM chunks
            {where_clause}
            ORDER BY rank_score DESC
            LIMIT $2
        """
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
        
        return [
            {
                "chunk": dict(row),
                "score": float(row["rank_score"]),
                "rank": i
            }
            for i, row in enumerate(rows)
        ]


async def create_db_pool(database_url: str) -> asyncpg.Pool:
    """Create asyncpg connection pool"""
    return await asyncpg.create_pool(database_url, min_size=2, max_size=10)


if __name__ == "__main__":
    # Quick test
    config = EmbeddingConfig()
    embedder = Embedder(config)
    
    test_chunks = [
        {
            "chunk_id": str(uuid.uuid4()),
            "doc_id": "test_doc_001",
            "chunk_index": 0,
            "text": "Warli painting is a form of tribal art from Maharashtra, India.",
            "token_count": 20,
            "tribe_name": "Warli",
            "region": "Maharashtra",
            "institution": "MAP Academy",
            "source_title": "Warli Art Overview",
            "source_url": "https://mapacademy.io/warli"
        }
    ]
    
    # Test embedding
    embedded = embedder.embed_chunks(test_chunks)
    print(f"Embedded {len(embedded)} chunks, vector dim: {len(embedded[0]['vector'])}")
    
    # Test dense search
    results = embedder.search_dense("Warli art Maharashtra", top_k=5)
    print(f"Dense search results: {len(results)}")
    for r in results:
        print(f"  Score: {r['score']:.4f} - {r['chunk']['text'][:50]}...")