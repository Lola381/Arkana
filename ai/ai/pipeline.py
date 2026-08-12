"""
Arkana AI/ML Pipeline - Unified Entry Point
Main interface for TM3 (Full Stack) to call from FastAPI routes.
"""
# at the top of ai/pipeline.py or ai/core/config.py
from dotenv import load_dotenv
load_dotenv()  # looks for .env in cwd, which is project root when you run from there
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
import uuid

# Import all AI modules
from ai.chunking.semantic_chunker import SemanticChunker, ChunkConfig
from ai.embedding.embedder import Embedder, EmbeddingConfig
from ai.retrieval.rrf_fusion import HybridRetriever, RetrievalConfig, reciprocal_rank_fusion
from ai.reranking.cross_encoder import CrossEncoderReranker, RerankConfig
from ai.generation.prompt_builder import build_prompt, format_citations, PromptConfig
from ai.generation.llm_client import LLMClient, LLMConfig, create_llm_client
from ai.ner.entity_extractor import EntityExtractor, NERConfig, extract_map_events
from ai.visual.clip_embedder import CLIPEmbedder, CLIPConfig, VisualIntelligencePipeline
from ai.evaluation.faithfulness_judge import FaithfulnessJudge, RetrievalEvaluator, GoldenTestItem

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    """Global pipeline configuration"""
    # Chunking
    chunk_min_tokens: int = 150
    chunk_max_tokens: int = 512
    chunk_overlap_tokens: int = 50
    chunk_similarity_threshold: float = 0.6
    
    # Embedding
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "arkana_corpus"
    vector_size: int = 768
    
    # Retrieval
    dense_top_k: int = 20
    sparse_top_k: int = 20
    fused_top_k: int = 20
    rrf_k: int = 60
    
    # Reranking
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_n: int = 4
    min_relevance_score: float = -5.0
    
    # Generation
    llm_model: str = "gemini-3.5-flash"
    llm_max_tokens: int = 1024
    llm_temperature: float = 0.1
    max_history_turns: int = 3
    
    # NER
    spacy_model: str = "en_core_web_sm"
    
    # Visual
    enable_clip: bool = False
    clip_model: str = "ViT-B/32"
    clip_device: str = "cpu"
    image_collection: str = "arkana_images"
    
    # Evaluation
    eval_enabled: bool = True
    golden_test_set_path: str = "ai/evaluation/golden_test_set.json"


class ArkanaPipeline:
    """
    Main AI/ML pipeline for Arkana.
    Provides query() and identify_image() entry points for the backend.
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None, db_pool=None):
        self.config = config or PipelineConfig()
        self.db_pool = db_pool
        self._initialized = False
        self._background_tasks = set()
        
        # Components (lazy initialized)
        self.chunker = None
        self.embedder = None
        self.retriever = None
        self.reranker = None
        self.llm_client = None
        self.entity_extractor = None
        self.clip_embedder = None
        self.visual_pipeline = None
        self.faithfulness_judge = None
        self.retrieval_evaluator = None

    
    async def initialize(self):
        """Initialize all pipeline components"""
        if self._initialized:
            return
        
        logger.info("Initializing Arkana AI/ML pipeline...")
        
        # 1. Chunker
        chunk_config = ChunkConfig(
            min_tokens=self.config.chunk_min_tokens,
            max_tokens=self.config.chunk_max_tokens,
            overlap_tokens=self.config.chunk_overlap_tokens,
            similarity_threshold=self.config.chunk_similarity_threshold
        )
        self.chunker = SemanticChunker(chunk_config)
        
        # 2. Embedder (with DB pool for PostgreSQL BM25)
        embed_config = EmbeddingConfig(
            model_name=self.config.embedding_model,
            vector_size=self.config.vector_size,
            qdrant_url=self.config.qdrant_url,
            qdrant_collection=self.config.qdrant_collection
        )
        self.embedder = Embedder(embed_config, db_pool=self.db_pool)
        
        # 3. Hybrid Retriever
        retrieval_config = RetrievalConfig(
            dense_top_k=self.config.dense_top_k,
            sparse_top_k=self.config.sparse_top_k,
            fused_top_k=self.config.fused_top_k,
            rrf_k=self.config.rrf_k
        )
        self.retriever = HybridRetriever(self.embedder, retrieval_config)
        
        # 4. Reranker
        rerank_config = RerankConfig(
            model_name=self.config.reranker_model,
            top_n=self.config.rerank_top_n,
            min_relevance_score=self.config.min_relevance_score
        )
        self.reranker = CrossEncoderReranker(rerank_config)
        
        # 5. LLM Client
        llm_config = LLMConfig(
            model=self.config.llm_model,
            max_tokens=self.config.llm_max_tokens,
            temperature=self.config.llm_temperature
        )
        self.llm_client = create_llm_client(llm_config)
        
        # 6. Entity Extractor (NER)
        ner_config = NERConfig(spacy_model=self.config.spacy_model)
        self.entity_extractor = EntityExtractor(ner_config)
        
        # 7. CLIP Visual Intelligence
        if self.config.enable_clip:
            clip_config = CLIPConfig(
                model_name=self.config.clip_model,
                device=self.config.clip_device,
                image_collection=self.config.image_collection
            )
            self.clip_embedder = CLIPEmbedder(clip_config, qdrant_client=self.embedder.qdrant)
            self.visual_pipeline = VisualIntelligencePipeline(
                self.clip_embedder, 
                text_retriever=self.retriever
            )
        else:
            self.clip_embedder = None
            self.visual_pipeline = None
        
        # 8. Evaluation
        if self.config.eval_enabled:
            self.faithfulness_judge = FaithfulnessJudge(
                self.llm_client, 
                {"enabled": True}
            )
            self.retrieval_evaluator = RetrievalEvaluator(
                self.retriever,
                self.reranker,
                self.config.golden_test_set_path
            )
        
        # 9. Metrics Logger (Disabled)
        # self.metrics_logger = MetricsLogger(db_pool=self.db_pool)
        
        self._initialized = True
        logger.info("Arkana AI/ML pipeline initialized successfully!")
    
    async def query(
        self,
        user_query: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        map_context: Optional[Dict[str, Any]] = None,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main RAG query pipeline.
        
        Args:
            user_query: User's question
            conversation_history: Previous messages [{"role": "user|assistant", "content": "..."}]
            map_context: Current map state {"tribe_name": "...", "region": "..."}
            stream: Whether to stream tokens
            
        Yields:
            SSE-compatible event dicts: {"type": "token|citation|map_event|insight_card|done", "data": ...}
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = asyncio.get_event_loop().time()
        conversation_history = conversation_history or []
        map_context = map_context or {}
        
        try:
            # 1. Hybrid Retrieval
            logger.info(f"Retrieving for query: {user_query[:100]}...")
            fused_results = await self.retriever.retrieve(
                user_query, 
                filters=map_context if map_context else None
            )
            
            # 2. Rerank
            logger.info(f"Reranking {len(fused_results)} candidates...")
            reranked = await self.reranker.rerank(
                user_query, 
                fused_results, 
                top_n=self.config.rerank_top_n
            )
            
            # 3. Build Prompt
            map_ctx_str = None
            if map_context.get("state") or map_context.get("category"):
                parts = []
                if map_context.get("state"):
                    parts.append(map_context["state"])
                if map_context.get("category"):
                    parts.append(map_context["category"])
                map_ctx_str = " — ".join(parts)
            
            prompt_messages = build_prompt(
                query=user_query,
                chunks=reranked,
                conversation_history=conversation_history,
                map_context=map_ctx_str
            )
            
            # 4. Stream Generation
            full_response = ""
            if stream:
                async for token in self.llm_client.generate_streaming(prompt_messages):
                    full_response += token
                    yield {"type": "token", "data": token}
            else:
                full_response = await self.llm_client.generate_complete(prompt_messages)
                yield {"type": "token", "data": full_response}
            
            # 5. Emit Citations
            citations = format_citations(reranked)
            for citation in citations:
                yield {"type": "citation", "data": citation}
            
            # 6. Extract Map Events (NER)
            map_events = await extract_map_events(full_response)
            for event in map_events:
                yield {"type": "map_event", "data": event}
            
            # 7. Check for Insight Card triggers (artifact mentions)
            # This would be enhanced with actual artifact detection
            for chunk_data in reranked:
                chunk = chunk_data["chunk"]
                if chunk.get("source_url") and "artifact" in chunk.get("source_url", "").lower():
                    yield {
                        "type": "insight_card",
                        "data": {
                            "artifact_id": chunk.get("chunk_id", str(uuid.uuid4())),
                            "title": chunk.get("chunk_source", "Artifact"),
                            "image_url": chunk.get("image_url", ""),
                            "url": chunk.get("source_url", "")
                        }
                    }
            
            # 8. Async evaluation and unified metrics logging (non-blocking)
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            task = asyncio.create_task(self._run_evaluation(
                query=user_query, 
                response=full_response, 
                chunks=reranked,
                latency_ms=latency_ms,
                user_region=map_context.get("region")
            ))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            
            yield {"type": "done", "data": None}
            
        except Exception as e:
            logger.error(f"Query pipeline error: {e}")
            yield {"type": "token", "data": f"[Error: {str(e)}]"}
            yield {"type": "done", "data": None}
    
    async def _run_evaluation(
        self, 
        query: str, 
        response: str, 
        chunks: List[Dict[str, Any]], 
        latency_ms: float, 
        user_region: Optional[str] = None
    ):
        """Run faithfulness evaluation and log unified metrics asynchronously"""
        faithfulness = 0.0
        relevance = 0.0
        
        try:
            if self.faithfulness_judge:
                result = await self.faithfulness_judge.evaluate(query, response, chunks)
                faithfulness = result.get("faithfulness", 0.0)
                relevance = result.get("relevance", 0.0)
                logger.info(f"Evaluation: faithfulness={faithfulness:.2f}, relevance={relevance:.2f}")
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            
        # Metrics logging is currently disabled
    
    async def identify_image(self, image_path: str) -> Dict[str, Any]:
        """
        Visual identification pipeline.
        
        Args:
            image_path: Path to uploaded image
            
        Returns:
            Dict with style classification, similar artifacts, RAG query and context
        """
        if not self._initialized:
            await self.initialize()
        
        try:
            from PIL import Image
            image = Image.open(image_path).convert("RGB")
            
            # Run visual pipeline
            if not self.visual_pipeline:
                return {"error": "Image processing is currently disabled to save RAM."}
            result = await self.visual_pipeline.identify_image(image)
            
            logger.info(f"Visual identification: {result['style_classification']['top_style']} ({result['style_classification']['confidence']:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Visual identification error: {e}")
            return {
                "style_classification": {"top_style": "unknown", "confidence": 0.0, "all_scores": {}},
                "similar_artifacts": [],
                "rag_query": "",
                "rag_context": {}
            }
    
    async def run_retrieval_evaluation(self) -> Dict[str, Any]:
        """
        Run retrieval precision evaluation (for CI gate).
        """
        if not self._initialized:
            await self.initialize()
        
        if not self.retrieval_evaluator:
            return {"error": "Evaluation not enabled"}
        
        result = await self.retrieval_evaluator.run_retrieval_evaluation()
        return {
            "precision_at_3": result.precision_at_3,
            "passed": result.passed,
            "test_set_size": result.test_set_size,
            "timestamp": result.timestamp,
            "details": result.details
        }
    
    async def chunk_and_index_documents(self, documents: List[Dict[str, Any]], source: str = "default") -> Dict[str, int]:
        """
        Process documents: chunk, embed, and index.
        Used by TM3's ingestion pipeline.
        """
        if not self._initialized:
            await self.initialize()
        
        # Chunk documents
        all_chunks = []
        for doc in documents:
            chunks = self.chunker.chunk_document(
                text=doc["text"],
                doc_id=doc["doc_id"],
                metadata=doc["metadata"],
                source=source
            )
            all_chunks.extend(chunks)
        
        # Embed and index
        result = await self.embedder.process_and_index(all_chunks)
        
        logger.info(f"Processed {len(documents)} documents into {result['embedded']} chunks")
        
        return result



if __name__ == "__main__":
    # Test pipeline initialization
    async def test():
        pipeline = ArkanaPipeline()
        await pipeline.initialize()
        print("Pipeline initialized successfully!")
        
        # Test query (requires GROQ_API_KEY and running Qdrant/PostgreSQL)
        # async for event in pipeline.query("What is Warli art?"):
        #     print(event)
    
    asyncio.run(test())