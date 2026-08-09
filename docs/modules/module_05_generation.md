# Module 5 — Generation (Prompt Builder & LLM Client)

## Purpose
The Generation module handles the final phase of the RAG pipeline. It constructs strictly constrained conversational prompts and streams them to a Large Language Model (`llama-3.1-8b-instant`). It is entirely responsible for maintaining system instructions, citation injection, map context, conversation history, and enforcing hallucination prevention rules.

## Files
- `ai/ai/generation/llm_client.py`
- `ai/ai/generation/prompt_builder.py`

## Entry Points
- `prompt_builder.build_prompt(query, chunks, conversation_history, map_context)`
- `llm_client.generate_streaming(messages)`
- `llm_client.generate_complete(messages)`

## Inputs
- `query`: `str` (Raw text query)
- `chunks`: `List[Dict[str, Any]]` (Array of candidate dictionaries produced by Module 4 Reranker)
- `conversation_history`: `List[Dict[str, str]]` (Previous turn history)
- `map_context`: `Dict[str, Any]` (Current active map filters, eg. region/tribe)

## Outputs
- Raw string generator yielding streaming text tokens, followed by JSON citation metadata output by `pipeline.py`.

## Current Architecture
The module relies on the `AsyncGroq` client to orchestrate non-blocking network requests against the API. The prompt builder formats a massive system instruction block that injects the retrieved chunks, explicit refusal rules, and strict citation formats (`[Source: {institution} — {source_title}]`). 

## Final Implementation
1. `build_prompt()` compiles the chunks into an `EXCERPT` block and injects them into the `SYSTEM_PROMPT`.
2. It correctly orders the payload chronological logic: `[System Instructions] -> [Previous Chat History] -> [Current User Query]`.
3. The array is passed to `generate_streaming()` in `LLMClient`.
4. `LLMClient` fires an `await self.client.chat.completions.create(stream=True)`.
5. The `async for` loop yields string tokens immediately as they arrive over the network, ensuring zero ASGI event loop blocking.

## Implemented Improvements
### 1. Replaced Synchronous Network Blocking
- **Problem:** The original `LLMClient` instantiated a synchronous `Groq` object and used synchronous `for` loops inside an `async def` streaming generator.
- **Root Cause:** Improper SDK usage within a FastAPI/async ecosystem.
- **Implementation:** Imported `AsyncGroq` and migrated `create()` and iteration loops to `await` and `async for`.
- **Impact:** The LLM generation phase no longer freezes the web server. Arkana can securely handle multiple concurrent RAG queries simultaneously.

### 2. Fixed Conversational Amnesia
- **Problem:** `build_prompt` originally injected the active user query into the `System` prompt at index 0, and appended the historical conversational history *afterwards* at the end of the array.
- **Root Cause:** Misunderstanding of chronological LLM attention mechanics. 
- **Implementation:** Stripped the `query` variable from the system instruction template. Instead, a new `{"role": "user", "content": query}` message is appended to the absolute end of the message array.
- **Impact:** The LLM perfectly understands the difference between previous chat history and the current active user question.

## Important Design Decisions
- **Strict Formatting Persistence:** Even through refactoring, the literal string formatting for `[Source: {institution} — {source_title}]` was maintained byte-for-byte. `pipeline.py` depends heavily on this for citation regex extraction.

## Breaking Changes
- None. API signatures were maintained strictly.

## Future Improvements
- **Fragile JSON Parsing in Evaluator**
  - **Future owner:** Evaluation / ML Metrics
  - **Target module:** Module 8 (Evaluation)
  - **Reason:** `llm_client.py` contains an `evaluate_faithfulness` method that blindly runs `json.loads(response)`. If the LLM wraps the response in markdown blocks (` ```json `), it will crash. This should be fixed when the evaluation suite is focused.

- **Conversation Memory Manager**
  - **Future owner:** API Layer / Conversation Orchestrator
  - **Target module:** Module 9 (API) or Module 10 (ETL/Orchestration)
  - **Reason:** As conversations grow, sending the full history on every request increases token usage and latency. A future memory manager should periodically summarize older conversation while preserving recent turns.
  - **Future prompt structure:**
    - System Prompt
    - Conversation Summary
    - Recent Conversation (last N turns)
    - Current User Query
  - **Status:** Deferred (not part of Module 5).

## AI Notes
- **Safe refactors:** Altering model configurations or temperature.
- **Things that must never change:** The `[Source: ...]` citation string structure.
- **Public interfaces:** `generate_streaming` must always yield raw string tokens, not wrapped objects.
