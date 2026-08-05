"""
LLM Client for Arkana - Groq Integration
Handles streaming generation with proper error handling.
"""

import os
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from groq import AsyncGroq
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    model: str = "llama-3.1-8b-instant"
    max_tokens: int = 1024
    temperature: float = 0.1
    api_key: Optional[str] = None


class LLMClient:
    """
    Groq client for streaming text generation.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in config or environment")

        self.client = AsyncGroq(api_key=api_key)

    async def generate_streaming(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from Groq.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Override max tokens
            temperature: Override temperature

        Yields:
            Text chunks as they stream
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                messages=messages,
                stream=True
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            yield "[Error: Failed to generate response]"

    async def generate_complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate complete (non-streaming) response.

        Returns:
            Full response text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
                messages=messages,
                stream=False
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq generation error: {e}")
            return f"[Error: {str(e)}]"

    async def evaluate_faithfulness(
        self,
        query: str,
        response: str,
        excerpts: str,
        max_tokens: int = 200
    ) -> Dict[str, Any]:
        """
        Use LLM-as-judge to evaluate faithfulness and relevance.

        Args:
            query: Original user query
            response: AI response to evaluate
            excerpts: Source excerpts used for generation
            max_tokens: Max tokens for evaluation

        Returns:
            Dict with faithfulness, relevance scores and reasoning
        """
        judge_prompt = f"""You are evaluating whether an AI response is faithful to its source material.

USER QUERY: {query}

SOURCE EXCERPTS:
{excerpts}

AI RESPONSE:
{response}

Score the response on two dimensions:
1. FAITHFULNESS (0-1): Are all factual claims in the response supported by the source excerpts?
   1.0 = every claim directly supported
   0.0 = response contains claims not in excerpts
2. RELEVANCE (0-1): Does the response actually answer the question asked?
   1.0 = fully answers the question
   0.0 = does not address the question

Respond in JSON only:
{{
    "faithfulness": 0.0,
    "relevance": 0.0,
    "reasoning": "brief explanation"
}}"""

        messages = [{"role": "user", "content": judge_prompt}]

        try:
            eval_response = await self.generate_complete(messages, max_tokens=max_tokens, temperature=0.0)

            # Parse JSON response
            import json
            result = json.loads(eval_response)

            # Validate scores
            result["faithfulness"] = max(0.0, min(1.0, float(result.get("faithfulness", 0))))
            result["relevance"] = max(0.0, min(1.0, float(result.get("relevance", 0))))

            return result

        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {
                "faithfulness": 0.0,
                "relevance": 0.0,
                "reasoning": f"Evaluation failed: {str(e)}"
            }


def create_llm_client(config: Optional[LLMConfig] = None) -> LLMClient:
    """Factory function to create LLM client"""
    return LLMClient(config)


# Standalone async function for LLM-as-judge (used by faithfulness_judge.py)
async def complete(prompt: str, max_tokens: int = 200) -> str:
    """
    Standalone completion function for evaluation.
    Creates a temporary client and returns the response string.
    """
    client = create_llm_client()
    messages = [{"role": "user", "content": prompt}]
    return await client.generate_complete(messages, max_tokens=max_tokens, temperature=0.0)


if __name__ == "__main__":
    # Test client (requires GROQ_API_KEY env var)
    import os
    if os.getenv("GROQ_API_KEY"):
        async def test():
            client = create_llm_client()
            messages = [{"role": "user", "content": "Say hello in one sentence."}]
            async for chunk in client.generate_streaming(messages):
                print(chunk, end="", flush=True)
            print()

        asyncio.run(test())
    else:
        print("Set GROQ_API_KEY to test")