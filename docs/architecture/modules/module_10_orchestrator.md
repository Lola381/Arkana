# Module 10 — Pipeline Orchestrator

## Purpose
The Pipeline Orchestrator serves as the central AI nervous system for the Arkana backend. It acts as the definitive bridge between the HTTP API (Module 9) and all underlying machine learning, retrieval, and generation logic (Modules 1–8). It manages the memory lifecycle of heavy ML models, coordinates the strict sequential execution order for RAG, handles multimodal input routing, and safely delegates heavy evaluation workloads to background tasks.

## Files
- `ai/ai/pipeline.py`
  - *The core orchestrator singleton class and logic.*

## Entry Points
- `ArkanaPipeline.initialize()`
- `ArkanaPipeline.query(query, ...)`
- `ArkanaPipeline.identify_image(image_path)`
- `ArkanaPipeline.chunk_and_index_documents(...)`

## Inputs
- **Text RAG (`query`):** A string `query`, optional `conversation_history`, and optional `map_context`.
- **Visual RAG (`identify_image`):** A string `image_path` pointing to a local temporary file representing the uploaded image.
- **Indexing:** A file path and dictionary of metadata.

## Outputs
- **Text RAG:** An asynchronous generator yielding dictionaries in a strict Server-Sent Event (SSE) payload sequence (e.g., `token`, `citation`, `map_event`, `insight_card`, `done`).
- **Visual RAG:** A dictionary containing style classification predictions, similar visual artifacts retrieved from Qdrant, and synthesized RAG context.

## Current Architecture
The orchestrator leverages a decoupled, lazy-initialization pattern.
- **Initialization:** Upon the FastAPI server lifecycle startup, the pipeline lazily instantiates all chunkers, embedders, retrievers, language models, and evaluation engines exactly once, passing down the shared PostgreSQL connection pool.
- **Execution Order (RAG):** The orchestrator controls the exact sequence of ML events: Hybrid Search Retrieval $\rightarrow$ Cross-Encoder Reranking $\rightarrow$ Prompt Context Building $\rightarrow$ LLM Streaming.
- **Concurrency & Backgrounding:** Long-running evaluation tasks (Faithfulness and Relevance metrics) are intentionally detached from the main request execution thread using `asyncio.create_task` and tracked in `self._background_tasks`, preventing the Python garbage collector from destroying them mid-flight. Error propagation inside the pipeline yields `[Error: ...]` as a stream token, ensuring the client connection isn't abruptly terminated without explanation.

## Final Implementation
1. The FastAPI router requests the initialized `ArkanaPipeline` from the application state.
2. For text chats, the pipeline executes retrieval and reranking, then yields the `llm_client.generate_streaming()` tokens back to the router.
3. After the text stream completes, the pipeline synchronously yields `citation` events, awaits the NER engine's `extract_map_events(full_response)`, and yields `map_event` and `insight_card` events.
4. An `asyncio` task is created to execute `_run_evaluation` in the background.
5. The pipeline yields a final `done` event.
6. For visual chats, the pipeline parses the uploaded image via `PIL` and delegates execution directly to the Visual Intelligence Module.

## Implemented Improvements
Module 10 required no code modifications. During the architecture review phase:
- The architecture audit found no blocking issues or race conditions.
- A proposed SSE payload reordering (to yield citations and insight cards before the LLM stream) was explicitly withdrawn after frontend code verification confirmed that the React UI deliberately hides citations and defers card animations until the streaming animation completes. 
- The end-to-end integration verification script passed successfully, confirming robust startup, complete RAG routing, and correct multimodal execution.
- Therefore, the orchestrator remained completely unchanged.

## Deferred Improvements
- **NER-Based Insight Cards**
  - **Reason:** Currently, the orchestrator utilizes a hardcoded substring match (`"artifact" in chunk.get("source_title", "").lower()`) to trigger insight cards. Delegating this extraction to the SpaCy NER module or database metadata flags was deferred to avoid disrupting the UI prototype.
- **True Async Streaming NER**
  - **Reason:** Upgrading the NER module to process sliding windows of text *during* the LLM stream (to pan the map synchronously while the AI types) requires significant NLP engineering and is deferred to a future phase.

## AI Notes
- **Execution strictness:** Module 10 is an orchestrator. It must *never* implement its own AI logic; it only delegates to Modules 1-8.
- **Background tasks:** The `_background_tasks.discard` callback logic is critical for preventing GC failures in production and should not be modified.
- **SSE Schema Contract:** The execution yield sequence in `query()` perfectly mirrors the frontend's intentional slide-in UX design and state logic (`!msg.isStreaming`).
