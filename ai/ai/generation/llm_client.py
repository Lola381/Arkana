"""
LLM Client for Arkana - Gemini Integration
Handles streaming generation with proper error handling.
"""

import os
import asyncio
from typing import AsyncGenerator, List, Dict, Any, Optional
from google import genai
from google.genai import types
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Configuration for LLM client"""
    model: str = "gemini-3.5-flash"
    max_tokens: int = 1024
    temperature: float = 0.1
    api_key: Optional[str] = None


class LLMClient:
    """
    Gemini client for streaming text generation.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()

        # Get API key from config or environment
        api_key = self.config.api_key or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in config or environment")

        # Initialize the synchronous client (google-genai provides async methods via .aio)
        self.client = genai.Client(api_key=api_key)

    def _convert_messages(self, messages: List[Dict[str, str]]) -> List[types.Content]:
        """Convert OpenAI style messages to Gemini Content types."""
        gemini_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Map roles
            gemini_role = "user"
            if role == "assistant":
                gemini_role = "model"
            elif role == "system":
                # System instructions are handled separately in generate methods
                continue

            gemini_messages.append(
                types.Content(role=gemini_role, parts=[types.Part.from_text(text=content)])
            )
        return gemini_messages

    async def generate_streaming(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response from Gemini.
        """
        try:
            # Handle system prompt separation
            system_instruction = None
            if messages and messages[0].get("role") == "system":
                system_instruction = messages[0].get("content")

            contents = self._convert_messages(messages)
            
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
            )
            
            if system_instruction:
                config.system_instruction = system_instruction

            # Use the async generator method
            stream = await self.client.aio.models.generate_content_stream(
                model=self.config.model,
                contents=contents,
                config=config
            )

            async for chunk in stream:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield f"[Error: Failed to generate response - {str(e)}]"

    async def generate_complete(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Generate complete (non-streaming) response.
        """
        try:
            system_instruction = None
            if messages and messages[0].get("role") == "system":
                system_instruction = messages[0].get("content")

            contents = self._convert_messages(messages)
            
            config = types.GenerateContentConfig(
                max_output_tokens=max_tokens or self.config.max_tokens,
                temperature=temperature or self.config.temperature,
            )
            
            if system_instruction:
                config.system_instruction = system_instruction

            response = await self.client.aio.models.generate_content(
                model=self.config.model,
                contents=contents,
                config=config
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
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

            # Clean markdown JSON blocks if present
            eval_response = eval_response.strip()
            if eval_response.startswith("```json"):
                eval_response = eval_response[7:]
            if eval_response.startswith("```"):
                eval_response = eval_response[3:]
            if eval_response.endswith("```"):
                eval_response = eval_response[:-3]

            result = json.loads(eval_response.strip())

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
    """
    client = create_llm_client()
    messages = [{"role": "user", "content": prompt}]
    return await client.generate_complete(messages, max_tokens=max_tokens, temperature=0.0)


if __name__ == "__main__":
    # Test client
    import os
    if os.getenv("GEMINI_API_KEY"):
        async def test():
            client = create_llm_client()
            messages = [{"role": "user", "content": "Say hello in one sentence."}]
            async for chunk in client.generate_streaming(messages):
                print(chunk, end="", flush=True)
            print()

        asyncio.run(test())
    else:
        print("Set GEMINI_API_KEY to test")