from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's input query")
    conversation_history: Optional[List[Dict[str, str]]] = Field(default_factory=list, description="Previous messages")
    map_context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Current map state")

class ChatResponseEvent(BaseModel):
    type: str = Field(..., description="Event type: token, citation, map_event, insight_card, done")
    data: Any = Field(..., description="Event payload")

class StyleClassification(BaseModel):
    top_style: str
    confidence: float
    all_scores: Dict[str, float]

class VisualIdentifyResponse(BaseModel):
    style_classification: StyleClassification
    similar_artifacts: List[Dict[str, Any]]
    rag_query: str
    rag_context: Dict[str, Any]

class SiteResponse(BaseModel):
    site_id: str
    name: str
    state: str
    category: str
    coordinates: Optional[Dict[str, float]]
    short_summary: Optional[str]
    # Future fields from canonical schema can be added here

class ErrorResponse(BaseModel):
    error: str
    details: Optional[Any] = None
