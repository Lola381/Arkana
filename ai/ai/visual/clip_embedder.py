"""
CLIP Visual Intelligence for Arkana
Handles image embedding, artifact classification, and visual search.
"""

import torch
import clip
import asyncio
from PIL import Image
from typing import List, Dict, Any, Optional
import numpy as np
from dataclasses import dataclass
import requests
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


@dataclass
class CLIPConfig:
    """Configuration for CLIP model"""
    model_name: str = "ViT-B/32"
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    image_collection: str = "arkana_images"
    vector_size: int = 512


# Art style labels for zero-shot classification
STYLE_LABELS = [
    # Paintings & Art
    "Warli tribal painting",
    "Gond art",
    "Madhubani painting",
    "Pithora art",
    "Bhil painting",
    "Mughal miniature painting",
    "Buddhist art",
    "Chola bronze sculpture",
    "Kalamkari textile",
    "Tanjore painting",
    "Pattachitra painting",
    "Phad painting",
    "Cheriyal scroll painting",
    "Mysore painting",
    "Rajput painting",
    "Deccan painting",
    "Company style painting",
    # Architecture & Monuments
    "Mughal architecture monument",
    "Dravidian temple architecture",
    "Nagara style temple architecture",
    "Indo-Saracenic architecture",
    "Ancient Indian rock-cut cave architecture",
    "Indian stepwell architecture",
    "Rajput fort architecture",
    "Maratha military architecture",
    "other Indian art or monument"
]

# Tribe/style to region mapping for RAG context
STYLE_TO_CONTEXT = {
    "Warli tribal painting": {"tribe": "Warli", "region": "Maharashtra"},
    "Gond art": {"tribe": "Gond", "region": "Madhya Pradesh"},
    "Madhubani painting": {"tribe": "Madhubani", "region": "Bihar"},
    "Pithora art": {"tribe": "Rathwa", "region": "Gujarat"},
    "Bhil painting": {"tribe": "Bhil", "region": "Rajasthan/Gujarat"},
    "Mughal miniature painting": {"tribe": "Mughal", "region": "North India"},
    "Buddhist art": {"tribe": "Buddhist", "region": "Pan-India"},
    "Chola bronze sculpture": {"tribe": "Chola", "region": "Tamil Nadu"},
    "Kalamkari textile": {"tribe": "Kalamkari", "region": "Andhra Pradesh"},
    "Tanjore painting": {"tribe": "Tanjore", "region": "Tamil Nadu"},
    "Pattachitra painting": {"tribe": "Pattachitra", "region": "Odisha/West Bengal"},
    "Phad painting": {"tribe": "Phad", "region": "Rajasthan"},
    "Cheriyal scroll painting": {"tribe": "Cheriyal", "region": "Telangana"},
}


class CLIPEmbedder:
    """
    CLIP image embedder for visual search and classification.
    """
    
    def __init__(self, config: Optional[CLIPConfig] = None, qdrant_client=None):
        self.config = config or CLIPConfig()
        self.qdrant = qdrant_client
        self.model = None
        self.preprocess = None
        self._load_model()
    
    def _load_model(self):
        """Load CLIP model"""
        try:
            self.model, self.preprocess = clip.load(
                self.config.model_name, 
                device=self.config.device
            )
            logger.info(f"Loaded CLIP model: {self.config.model_name} on {self.config.device}")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def embed_image(self, image: Image.Image) -> List[float]:
        """
        Generate CLIP embedding for an image.
        
        Args:
            image: PIL Image object
            
        Returns:
            512-dimensional normalized embedding vector
        """
        # Preprocess and embed
        image_input = self.preprocess(image).unsqueeze(0).to(self.config.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy()[0].tolist()
    
    def embed_image_from_path(self, image_path: str) -> List[float]:
        """Embed image from file path"""
        image = Image.open(image_path).convert("RGB")
        return self.embed_image(image)
    
    def embed_image_from_url(self, url: str) -> List[float]:
        """Download and embed image from URL"""
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert("RGB")
        return self.embed_image(image)
    
    def classify_style(self, image: Image.Image) -> Dict[str, Any]:
        """
        Zero-shot style classification using CLIP.
        
        Returns:
            Dict with top_style, confidence, and all_scores
        """
        image_input = self.preprocess(image).unsqueeze(0).to(self.config.device)
        text_tokens = clip.tokenize(STYLE_LABELS).to(self.config.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text_tokens)
            
            # Normalize
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            
            # Compute similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
        
        scores = similarity[0].cpu().numpy()
        
        # Get sorted results
        results = sorted(zip(STYLE_LABELS, scores), key=lambda x: x[1], reverse=True)
        
        return {
            "top_style": results[0][0],
            "confidence": float(results[0][1]),
            "all_scores": {label: float(score) for label, score in results}
        }
    
    def index_artifact_images(
        self, 
        artifacts: List[Dict[str, Any]],
        collection_name: Optional[str] = None
    ) -> int:
        """
        Index artifact images into Qdrant for visual search.
        
        Args:
            artifacts: List of artifact dicts with image_url, artifact_id, tribe_name, style, institution
            collection_name: Qdrant collection name
            
        Returns:
            Number of artifacts indexed
        """
        if not self.qdrant:
            logger.warning("No Qdrant client provided, skipping indexing")
            return 0
        
        collection = collection_name or self.config.image_collection
        
        # Ensure collection exists
        self._ensure_collection(collection)
        
        points = []
        for artifact in artifacts:
            if not artifact.get("image_url"):
                continue
            
            try:
                vector = self.embed_image_from_url(artifact["image_url"])
                
                point = {
                    "id": artifact["artifact_id"],
                    "vector": vector,
                    "payload": {
                        "artifact_id": artifact["artifact_id"],
                        "tribe_name": artifact.get("tribe_name"),
                        "style": artifact.get("style"),
                        "institution": artifact.get("institution"),
                        "title": artifact.get("title"),
                        "image_url": artifact.get("image_url"),
                        "period": artifact.get("period"),
                        "region": artifact.get("region")
                    }
                }
                points.append(point)
                
            except Exception as e:
                logger.warning(f"Failed to embed artifact {artifact.get('artifact_id')}: {e}")
        
        # Batch upsert
        if points:
            from qdrant_client.models import PointStruct
            qdrant_points = [
                PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
                for p in points
            ]
            self.qdrant.upsert(collection_name=collection, points=qdrant_points)
            logger.info(f"Indexed {len(points)} artifact images to {collection}")
        
        return len(points)
    
    def _ensure_collection(self, collection_name: str):
        """Create Qdrant collection if it doesn't exist"""
        collections = self.qdrant.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            from qdrant_client.models import Distance, VectorParams
            self.qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {collection_name}")
    
    def visual_search(
        self, 
        query_image: Image.Image, 
        top_k: int = 5,
        collection_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for visually similar artifacts.
        
        Args:
            query_image: PIL Image to search with
            top_k: Number of results
            collection_name: Qdrant collection
            
        Returns:
            List of similar artifacts with scores
        """
        if not self.qdrant:
            logger.warning("No Qdrant client, returning empty results")
            return []
        
        collection = collection_name or self.config.image_collection
        
        # Embed query image
        query_vector = self.embed_image(query_image)
        
        # Search
        from qdrant_client.models import Filter
        results = self.qdrant.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=top_k,
            with_payload=True
        )
        
        return [
            {
                "artifact_id": r.payload.get("artifact_id"),
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]


class VisualIntelligencePipeline:
    """
    Complete visual identification pipeline:
    1. Classify image style
    2. Find similar artifacts
    3. Generate RAG query for cultural context
    """
    
    def __init__(self, clip_embedder: CLIPEmbedder, text_retriever=None):
        self.clip = clip_embedder
        self.text_retriever = text_retriever  # HybridRetriever instance
    
    async def identify_image(self, image: Image.Image) -> Dict[str, Any]:
        """
        Full visual identification pipeline.
        
        Returns:
            Dict with style classification, similar artifacts, and RAG context
        """
        # 1. Classify style
        style_result = await asyncio.to_thread(self.clip.classify_style, image)
        
        # 2. Find visually similar artifacts
        similar = await asyncio.to_thread(self.clip.visual_search, image, 5)
        
        # 3. Get top artifact for RAG context
        top_artifact = similar[0] if similar else None
        rag_context = {}
        rag_query = ""
        
        style = style_result["top_style"]
        
        if top_artifact:
            tribe = top_artifact["payload"].get("tribe_name")
            if tribe:
                rag_context = {"tribe_name": tribe}
        
        # Fallback to STYLE_TO_CONTEXT if Qdrant yields no tribe context
        if not rag_context and style in STYLE_TO_CONTEXT:
            rag_context = STYLE_TO_CONTEXT[style].copy()
            
        rag_query = f"What is the cultural significance and historical context of {style}?"
        
        return {
            "style_classification": style_result,
            "similar_artifacts": similar,
            "rag_query": rag_query,
            "rag_context": rag_context
        }


if __name__ == "__main__":
    # Test CLIP embedder
    config = CLIPConfig()
    clip_embedder = CLIPEmbedder(config)
    
    # Create a test image (white square)
    test_image = Image.new("RGB", (224, 224), color="white")
    
    async def run_test():
        pipeline = VisualIntelligencePipeline(clip_embedder)
        print("Running async image identification...")
        result = await pipeline.identify_image(test_image)
        
        print(f"Top style: {result['style_classification']['top_style']} (confidence: {result['style_classification']['confidence']:.3f})")
        print(f"RAG Context Fallback: {result['rag_context']}")
        print(f"RAG Query: {result['rag_query']}")
        
    asyncio.run(run_test())