"""
Evaluation & Observability for Arkana
Implements LLM-as-judge faithfulness evaluation and retrieval precision testing.
"""

import json
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class GoldenTestItem:
    """Single item in the golden test set"""
    id: str
    query: str
    expected_source_doc_ids: List[str]
    expected_answer_contains: List[str]
    tribe: Optional[str] = None
    region: Optional[str] = None
    difficulty: str = "medium"  # easy, medium, hard


@dataclass
class EvaluationResult:
    """Result of a single evaluation"""
    query: str
    response: str
    chunks_used: List[Dict[str, Any]]
    faithfulness_score: float
    relevance_score: float
    reasoning: str
    timestamp: str


@dataclass
class RetrievalEvalResult:
    """Result of retrieval precision evaluation"""
    precision_at_3: float
    passed: bool
    test_set_size: int
    timestamp: str
    details: List[Dict[str, Any]]


# LLM-as-Judge prompt for faithfulness evaluation
JUDGE_PROMPT = """You are evaluating whether an AI response is faithful to its source material.

SOURCE EXCERPTS:
{excerpts}

USER QUERY: {query}

AI RESPONSE:
{response}

Score the response on two dimensions:

1. FAITHFULNESS (0-1): Are ALL factual claims in the response supported by the source excerpts?
   - 1.0 = Every claim is directly supported by the excerpts
   - 0.5 = Some claims supported, some not verifiable
   - 0.0 = Response contains claims not in the excerpts (hallucination)

2. RELEVANCE (0-1): Does the response actually answer the question asked?
   - 1.0 = Fully answers the question
   - 0.5 = Partially answers
   - 0.0 = Does not address the question

IMPORTANT: The AI must refuse to answer if information is not in the excerpts.
A refusal response like "This information is not currently in the Arkana archive." 
should score 1.0 faithfulness if the info is truly absent, and 1.0 relevance.

Respond in JSON ONLY:
{{
    "faithfulness": 0.0,
    "relevance": 0.0,
    "reasoning": "brief explanation of scores"
}}"""


class FaithfulnessJudge:
    """
    LLM-as-judge evaluator for response faithfulness and relevance.
    Runs asynchronously after each production response.
    """
    
    def __init__(self, llm_client, config: Optional[Dict] = None):
        self.llm_client = llm_client
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
    
    async def evaluate(
        self, 
        query: str, 
        response: str, 
        chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate a single response for faithfulness and relevance.
        
        Args:
            query: User's original query
            response: AI-generated response
            chunks: Retrieved chunks used for generation
            
        Returns:
            Dict with faithfulness, relevance scores and reasoning
        """
        if not self.enabled:
            return {"faithfulness": 1.0, "relevance": 1.0, "reasoning": "Evaluation disabled"}
        
        # Build excerpts text
        excerpts = "\n\n".join([
            f"EXCERPT {i+1} [Source: {c['chunk'].get('institution', 'Unknown')} — {c['chunk'].get('source_title', 'Unknown')}]:\n{c['chunk']['text']}"
            for i, c in enumerate(chunks)
        ])
        
        prompt = JUDGE_PROMPT.format(
            excerpts=excerpts,
            query=query,
            response=response
        )
        
        try:
            result = await self.llm_client.evaluate_faithfulness(
                query=query,
                response=response,
                excerpts=excerpts
            )
            
            # Validate scores
            result["faithfulness"] = max(0.0, min(1.0, float(result.get("faithfulness", 0))))
            result["relevance"] = max(0.0, min(1.0, float(result.get("relevance", 0))))
            
            return result
            
        except Exception as e:
            logger.error(f"Faithfulness evaluation failed: {e}")
            return {
                "faithfulness": 0.0,
                "relevance": 0.0,
                "reasoning": f"Evaluation error: {str(e)}"
            }
    
    async def evaluate_batch(
        self, 
        items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluate multiple responses in parallel with concurrency limits"""
        semaphore = asyncio.Semaphore(10)
        
        async def _bounded_evaluate(item):
            async with semaphore:
                return await self.evaluate(item["query"], item["response"], item["chunks"])
                
        tasks = [_bounded_evaluate(item) for item in items]
        return await asyncio.gather(*tasks)


class RetrievalEvaluator:
    """
    Evaluates retrieval precision against golden test set.
    Used as CI gate for corpus ingestion.
    """
    
    def __init__(
        self, 
        hybrid_retriever,  # HybridRetriever instance
        cross_encoder_reranker,  # CrossEncoderReranker instance
        test_set_path: str = "ai/evaluation/golden_test_set.json"
    ):
        self.retriever = hybrid_retriever
        self.reranker = cross_encoder_reranker
        self.test_set_path = test_set_path
        self.test_set: List[GoldenTestItem] = []
        self._load_test_set()
    
    def _load_test_set(self):
        """Load golden test set from JSON file"""
        try:
            with open(self.test_set_path, 'r') as f:
                data = json.load(f)
                self.test_set = [GoldenTestItem(**item) for item in data]
            logger.info(f"Loaded {len(self.test_set)} golden test items")
        except FileNotFoundError:
            logger.warning(f"Test set not found at {self.test_set_path}, creating empty")
            self.test_set = []
        except Exception as e:
            logger.error(f"Failed to load test set: {e}")
            self.test_set = []
    
    def save_test_set(self, test_set: Optional[List[GoldenTestItem]] = None):
        """Save test set to JSON"""
        data = [asdict(item) for item in (test_set or self.test_set)]
        Path(self.test_set_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.test_set_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(data)} test items to {self.test_set_path}")
    
    def add_test_item(self, item: GoldenTestItem):
        """Add a new test item"""
        self.test_set.append(item)
        self.save_test_set()
    
    async def run_retrieval_evaluation(self) -> RetrievalEvalResult:
        """
        Run precision@3 evaluation on the golden test set.
        
        Returns:
            RetrievalEvalResult with precision score and pass/fail
        """
        if not self.test_set:
            logger.warning("Empty test set, returning default result")
            return RetrievalEvalResult(
                precision_at_3=0.0,
                passed=False,
                test_set_size=0,
                timestamp=datetime.utcnow().isoformat(),
                details=[]
            )
        
        precision_scores = []
        details = []
        
        for item in self.test_set:
            # Retrieve
            dense_results = self.retriever.embedder.search_dense(
                item.query, 
                filters={"tribe_name": item.tribe} if item.tribe else None,
                top_k=20
            )
            
            sparse_results = await self.retriever.embedder.search_sparse(
                item.query,
                top_k=20,
                tribe_name=item.tribe
            )
            
            # Fuse
            from ai.retrieval.rrf_fusion import reciprocal_rank_fusion
            fused = reciprocal_rank_fusion(dense_results, sparse_results, top_k=20)
            
            # Rerank
            reranked = await self.reranker.rerank(item.query, fused, top_n=3)
            
            # Check precision@3
            retrieved_doc_ids = [c["chunk"]["doc_id"] for c in reranked]
            expected_doc_ids = set(item.expected_source_doc_ids)
            
            hits = len(set(retrieved_doc_ids) & expected_doc_ids)
            precision = hits / 3.0 if retrieved_doc_ids else 0.0
            precision_scores.append(precision)
            
            details.append({
                "query_id": item.id,
                "query": item.query,
                "retrieved": retrieved_doc_ids,
                "expected": item.expected_source_doc_ids,
                "hits": hits,
                "precision_at_3": precision
            })
        
        mean_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
        passed = mean_precision >= 0.85  # CI gate threshold
        
        result = RetrievalEvalResult(
            precision_at_3=mean_precision,
            passed=passed,
            test_set_size=len(self.test_set),
            timestamp=datetime.utcnow().isoformat(),
            details=details
        )
        
        logger.info(f"Retrieval evaluation: P@3 = {mean_precision:.3f} {'PASSED' if passed else 'FAILED'}")
        
        return result
    
    def run_retrieval_evaluation_sync(self) -> RetrievalEvalResult:
        """Synchronous version for CI/CD"""
        import asyncio
        return asyncio.run(self.run_retrieval_evaluation())

def create_golden_test_set_template() -> List[GoldenTestItem]:
    """Create a template golden test set for Indian cultural heritage"""
    return [
        GoldenTestItem(
            id="gts_001",
            query="What is the significance of the dot pattern in Warli art?",
            expected_source_doc_ids=["doc_mapacademy_warli_001", "doc_ignca_tribal_art_vol3"],
            expected_answer_contains=["community", "ritual", "nature", "circle"],
            tribe="Warli",
            region="Maharashtra",
            difficulty="easy"
        ),
        GoldenTestItem(
            id="gts_002",
            query="Which tribe creates Gond art and where are they located?",
            expected_source_doc_ids=["doc_mapacademy_gond_001", "doc_museums_india_gond_002"],
            expected_answer_contains=["Gond", "Madhya Pradesh", "central India"],
            tribe="Gond",
            region="Madhya Pradesh",
            difficulty="easy"
        ),
        GoldenTestItem(
            id="gts_003",
            query="What are the characteristic colors used in Madhubani painting?",
            expected_source_doc_ids=["doc_ignca_madhubani_001", "doc_mapacademy_madhubani_002"],
            expected_answer_contains=["natural", "pigments", "red", "yellow", "blue", "green"],
            tribe="Madhubani",
            region="Bihar",
            difficulty="medium"
        ),
        GoldenTestItem(
            id="gts_004",
            query="Describe the Pithora ritual painting tradition.",
            expected_source_doc_ids=["doc_asi_pithora_001", "doc_europeana_pithora_002"],
            expected_answer_contains=["Rathwa", "Gujarat", "ritual", "horse", "deity"],
            tribe="Rathwa",
            region="Gujarat",
            difficulty="medium"
        ),
        GoldenTestItem(
            id="gts_005",
            query="What is the historical significance of Bhil painting?",
            expected_source_doc_ids=["doc_museums_india_bhil_001", "doc_internet_archive_elwin_bhil"],
            expected_answer_contains=["Bhil", "Rajasthan", "Gujarat", "tribal", "forest"],
            tribe="Bhil",
            region="Rajasthan/Gujarat",
            difficulty="medium"
        ),
        GoldenTestItem(
            id="gts_006",
            query="How does Mughal miniature painting differ from Rajput painting?",
            expected_source_doc_ids=["doc_mapacademy_mughal_001", "doc_mapacademy_rajput_002"],
            expected_answer_contains=["Mughal", "Rajput", "court", "persian", "indigenous"],
            tribe="Mughal/Rajput",
            region="North India",
            difficulty="hard"
        ),
        GoldenTestItem(
            id="gts_007",
            query="What materials are used in Chola bronze sculpture creation?",
            expected_source_doc_ids=["doc_asi_chola_bronze_001", "doc_unesco_chola_002"],
            expected_answer_contains=["lost wax", "bronze", "copper", "tin", "cire perdue"],
            tribe="Chola",
            region="Tamil Nadu",
            difficulty="hard"
        ),
        GoldenTestItem(
            id="gts_008",
            query="Explain the symbolism in Kalamkari textile art.",
            expected_source_doc_ids=["doc_mapacademy_kalamkari_001", "doc_museums_india_kalamkari_002"],
            expected_answer_contains=["pen", "kalam", "natural dyes", "mythology", "epic"],
            tribe="Kalamkari",
            region="Andhra Pradesh",
            difficulty="medium"
        ),
        GoldenTestItem(
            id="gts_009",
            query="What is the UNESCO World Heritage status of the Chola temples?",
            expected_source_doc_ids=["doc_unesco_chola_temples_001"],
            expected_answer_contains=["UNESCO", "World Heritage", "1987", "Great Living Chola Temples"],
            tribe="Chola",
            region="Tamil Nadu",
            difficulty="easy"
        ),
        GoldenTestItem(
            id="gts_010",
            query="Describe the Warli tribe's marriage ceremony traditions.",
            expected_source_doc_ids=["doc_ignca_warli_marriage_001", "doc_internet_archive_elwin_warli"],
            expected_answer_contains=["marriage", "ceremony", "tarpa", "dance", "community"],
            tribe="Warli",
            region="Maharashtra",
            difficulty="medium"
        )
    ]


if __name__ == "__main__":
    # Create template test set
    template = create_golden_test_set_template()
    
    # Save to file
    Path("ai/evaluation").mkdir(parents=True, exist_ok=True)
    with open("ai/evaluation/golden_test_set.json", 'w') as f:
        json.dump([asdict(item) for item in template], f, indent=2)
    
    print(f"Created template with {len(template)} test items")
    for item in template:
        print(f"  {item.id}: {item.query[:60]}...")