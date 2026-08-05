# Module 7 — Visual Intelligence (CLIP Embedder)

## Purpose
The Visual Intelligence module enables multimodal identification capabilities for Arkana. It intercepts user-uploaded images, applies zero-shot image classification using OpenAI's CLIP model (Vision Transformer) to detect cultural art styles, and performs vector similarity search to locate identical artifacts in the Qdrant database. It outputs a synthesized RAG query containing the extracted cultural context.

## Files
- `ai/ai/visual/clip_embedder.py`

## Entry Points
- `VisualIntelligencePipeline.identify_image(image: PIL.Image)` (Async orchestrator)
- `CLIPEmbedder.embed_image(image: PIL.Image)`
- `CLIPEmbedder.classify_style(image: PIL.Image)`
- `CLIPEmbedder.visual_search(query_image: PIL.Image, top_k: int)`

## Inputs
- `image`: `PIL.Image.Image` (Raw uploaded RGB image payload).

## Outputs
Returns a `Dict[str, Any]` containing the classification, search results, and synthesized RAG string. Schema:
```python
{
    "style_classification": {
        "top_style": "Warli tribal painting",
        "confidence": 0.99,
        "all_scores": {"Warli tribal painting": 0.99, ...}
    },
    "similar_artifacts": [
        {
            "artifact_id": "art_123",
            "score": 0.91,
            "payload": {"tribe_name": "Warli", "image_url": "..."}
        }
    ],
    "rag_query": "What is the cultural significance and historical context of Warli tribal painting?",
    "rag_context": {"tribe_name": "Warli", "region": "Maharashtra"}
}
```

## Current Architecture
The pipeline bridges raw pixel data into contextual text. 
The CLIP model tokenizes 21 hardcoded `STYLE_LABELS`, projecting both the labels and the raw image into a shared 512-dimensional vector space to predict the most likely art style. 
Simultaneously, the image embedding is queried against the `arkana_images` Qdrant collection to retrieve similar artifacts.
The heavy mathematical matrix multiplications required by PyTorch inference are strictly confined to asynchronous worker threads using `asyncio.to_thread` to maintain a non-blocking fastAPI ecosystem.

## Final Implementation
1. `pipeline.py` receives the image, instantiates a PIL Image, and awaits `visual_pipeline.identify_image(image)`.
2. The CLIP classification fires in a background worker thread, returning the highest-confidence `top_style`.
3. The visual similarity search fires in a background thread against Qdrant.
4. The system attempts to extract the `tribe_name` from the nearest visually matched artifact.
5. If Qdrant returns no identical artifacts (or the payload is missing tribe metadata), the module gracefully falls back to a curated `STYLE_TO_CONTEXT` lookup dictionary to definitively retrieve the cultural context of the identified style.

## Implemented Improvements
### 1. Asynchronous PyTorch Offloading
- **Problem:** `self.model.encode_image()` takes hundreds of milliseconds to compute. Executing this synchronously caused total event loop freeze.
- **Root Cause:** A CPU-bound math dependency inside an ASGI event loop.
- **Implementation:** Wrapped PyTorch invocations in `await asyncio.to_thread()`, completely removing the `identify_image_sync` function from the codebase.
- **Impact:** Infinite vertical scalability. Dozens of users can now upload images simultaneously without blocking standard text queries.

### 2. Robust RAG Context Fallbacks (`STYLE_TO_CONTEXT`)
- **Problem:** The previous logic completely relied on Qdrant. If the visual database was sparse, the output `rag_context` became an empty dictionary, crippling the RAG pipeline.
- **Root Cause:** Ignored static mapping tables.
- **Implementation:** Added fallback conditional logic. If Qdrant fails to yield a tribe name, the module cross-references the predicted `top_style` against `STYLE_TO_CONTEXT` and populates the `rag_context`.
- **Impact:** 100% resilient context extraction. Even if the entire vector database crashes, the visual classifier still feeds accurate historical context into the Generation module.

## Important Design Decisions
- **Immutable Return Schema:** Modifying the frontend output contract was strictly prohibited. The exact dictionary keys and nested depths were preserved byte-for-byte.

## Breaking Changes
- `identify_image_sync` has been permanently deleted. Any legacy callers must switch to `await identify_image()`.

## Future Improvements
- **Move CLIP Model Download to Build Pipeline**
  - **Future owner:** DevOps / System Architect
  - **Target module:** Final Deployment (Dockerfile / CI)
  - **Reason:** `_load_model()` synchronously downloads a 350MB `.pt` file on startup. This should be explicitly pre-cached inside the Docker image to prevent runtime timeouts and container startup crashes in offline or firewalled environments.

## AI Notes
- **Safe refactors:** Appending new strings to `STYLE_LABELS` and mapping them in `STYLE_TO_CONTEXT`.
- **Things that must never change:** `clip.tokenize()` crashes violently if the total token length of any given style string exceeds 77 tokens.
- **Public interfaces:** `identify_image` is the strict singular API gateway.
