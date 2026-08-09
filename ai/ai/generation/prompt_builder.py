"""
Prompt Engineering for Arkana RAG Pipeline
Builds constrained prompts that enforce citation requirements and refusal behavior.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PromptConfig:
    """Configuration for prompt building"""
    max_history_turns: int = 3  # Last 3 user-assistant pairs
    max_tokens_context: int = 3000  # Approximate token budget for context


# System prompt with strict rules
SYSTEM_PROMPT = """You are Arkana, a specialist knowledge system for Indian historical and cultural heritage.

STRICT RULES — you must follow these without exception:

1. Answer ONLY using the SOURCE EXCERPTS provided below. Do not use any other knowledge.
2. If the answer is not present in the excerpts, respond with exactly: "This information is not currently in the Arkana archive."
3. Every factual claim must end with a citation in this format: [Source: {{institution}} — {{source_title}}]
4. Never speculate, extrapolate, or infer beyond what the excerpts explicitly state.
5. Never mention that you are an AI, a language model, or that you are "looking up" information.
6. Be concise but complete. Use neutral, informative tone.

Current map context: {map_context}

SOURCE EXCERPTS:
{excerpts}"""


def build_excerpt_block(chunks: List[Dict[str, Any]]) -> str:
    """
    Build formatted excerpt block from retrieved chunks.
    
    Args:
        chunks: List of reranked chunk dictionaries with metadata
        
    Returns:
        Formatted string with numbered excerpts and source citations
    """
    excerpts = []
    
    for i, chunk_data in enumerate(chunks):
        chunk = chunk_data["chunk"]
        excerpt = f"EXCERPT {i+1} [Source: {chunk.get('institution', 'Unknown')} — {chunk.get('source_title', 'Unknown')}]:"
        excerpt += f"\n{chunk['text']}"
        excerpts.append(excerpt)
    
    return "\n\n".join(excerpts)


def build_conversation_history(
    history: List[Dict[str, str]], 
    max_turns: int = 3
) -> List[Dict[str, str]]:
    """
    Build conversation history for context.
    
    Args:
        history: List of {"role": "user|assistant", "content": "..."} messages
        max_turns: Maximum number of user-assistant pairs to include
        
    Returns:
        List of message dicts for the prompt
    """
    # Take last N turns (each turn = user + assistant)
    max_messages = max_turns * 2
    recent_history = history[-max_messages:] if history else []
    
    return recent_history


def build_prompt(
    query: str,
    chunks: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None,
    map_context: Optional[str] = None,
    config: Optional[PromptConfig] = None
) -> List[Dict[str, str]]:
    """
    Build the complete prompt for LLM generation.
    
    Args:
        query: User's question
        chunks: Reranked chunks from retrieval
        conversation_history: Previous messages (optional)
        map_context: Current map context (tribe, region, etc.)
        config: Prompt configuration
        
    Returns:
        List of message dicts ready for LLM API
    """
    config = config or PromptConfig()
    map_ctx = map_context or "No specific region selected"
    
    # Build excerpt block
    excerpts = build_excerpt_block(chunks)
    
    # Format system prompt
    system_content = SYSTEM_PROMPT.format(
        map_context=map_ctx,
        excerpts=excerpts
    )
    
    messages = [{"role": "system", "content": system_content}]
    
    # Add conversation history
    if conversation_history:
        history = build_conversation_history(conversation_history, config.max_history_turns)
        messages.extend(history)
    
    # Add current query
    messages.append({"role": "user", "content": query})
    
    return messages


def build_refusal_check_prompt(response: str, excerpts: str) -> str:
    """
    Build a prompt to verify if a response is grounded in the excerpts.
    Used for evaluation/quality control.
    """
    return f"""You are evaluating whether an AI response is fully grounded in provided source excerpts.

SOURCE EXCERPTS:
{excerpts}

AI RESPONSE:
{response}

EVALUATION CRITERIA:
1. Does every factual claim in the response appear in the source excerpts?
2. Are all citations in the response valid (matching the provided sources)?
3. Does the response contain any information not in the excerpts?

Respond with ONLY a JSON object:
{{
    "grounded": true/false,
    "unsupported_claims": ["claim 1", "claim 2"],
    "invalid_citations": ["citation 1"],
    "reasoning": "brief explanation"
}}"""


def format_citations(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format citations for the response.
    
    Returns:
        List of citation objects with index, source_title, institution, chunk_id
    """
    citations = []
    for i, chunk_data in enumerate(chunks):
        chunk = chunk_data["chunk"]
        citations.append({
            "index": i + 1,
            "source_url": chunk.get("source_url", ""),
            "chunk_source": chunk.get("chunk_source", "ArkanaSemanticChunker"),
            "chunk_id": chunk.get("chunk_id", ""),
            "score": chunk_data.get("rerank_score", chunk_data.get("score", 0.0))
        })
    return citations


if __name__ == "__main__":
    # Test prompt building
    test_chunks = [
        {
            "chunk": {
                "chunk_id": "c1",
                "text": "Warli painting is a form of tribal art from Maharashtra using geometric shapes.",
                "chunk_source": "MAP Academy",
                "source_url": "https://mapacademy.io/warli"
            },
            "rerank_score": 0.92
        },
        {
            "chunk": {
                "chunk_id": "c2",
                "text": "The Warli tribe uses circles for sun/moon, triangles for mountains, squares for sacred enclosures.",
                "chunk_source": "IGNCA",
                "source_url": "https://ignca.gov.in"
            },
            "rerank_score": 0.87
        }
    ]
    
    messages = build_prompt(
        query="What do Warli painting symbols mean?",
        chunks=test_chunks,
        conversation_history=[
            {"role": "user", "content": "Tell me about Warli art"},
            {"role": "assistant", "content": "Warli painting is a tribal art form from Maharashtra..."}
        ],
        map_context="Warli tribe, Maharashtra region"
    )
    
    print("=== PROMPT MESSAGES ===")
    for msg in messages:
        print(f"\n[{msg['role'].upper()}]")
        print(msg['content'][:500] + "..." if len(msg['content']) > 500 else msg['content'])
    
    print("\n=== CITATIONS ===")
    citations = format_citations(test_chunks)
    for c in citations:
        print(f"  [{c['index']}] {c['chunk_source']} — {c['source_url']}")