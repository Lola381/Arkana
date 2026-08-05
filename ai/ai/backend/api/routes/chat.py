import json
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from ai.pipeline import ArkanaPipeline
from ai.backend.api.schemas import ChatRequest, ChatResponseEvent
from ai.backend.api.dependencies import get_pipeline

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, pipeline: ArkanaPipeline = Depends(get_pipeline)):
    """
    RAG chat endpoint using Server-Sent Events (SSE) to stream tokens, citations, and map events.
    """
    async def sse_generator():
        try:
            async for event_dict in pipeline.query(
                user_query=request.query,
                conversation_history=request.conversation_history,
                map_context=request.map_context
            ):
                # Validate and serialize using the Pydantic schema
                event = ChatResponseEvent(type=event_dict["type"], data=event_dict["data"])
                yield f"data: {event.model_dump_json()}\n\n"
        except Exception as e:
            # Fallback for unexpected generator crashes to maintain SSE protocol
            error_event = ChatResponseEvent(type="token", data=f"[Error: {str(e)}]")
            yield f"data: {error_event.model_dump_json()}\n\n"
            done_event = ChatResponseEvent(type="done", data=None)
            yield f"data: {done_event.model_dump_json()}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")
