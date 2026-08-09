# Module 6 — Entity Extractor (NER)

## Purpose
The Entity Extractor module scans the final generated text returned by the LLM and extracts specific entities—such as tribe names, locations (GPE), and historical time periods (DATE)—to emit map synchronization events (`MAP_HIGHLIGHT`, `MAP_PAN`, `TIMELINE_SEEK`) via Server-Sent Events (SSE).

## Files
- `ai/ai/ner/entity_extractor.py`

## Entry Points
- `EntityExtractor.extract_map_events(text)` (async)
- `extract_map_events(text)` (global async helper)

## Inputs
- `text`: `str` (The raw generated response from the LLM)

## Outputs
Returns a `List[Dict[str, Any]]` of map events. Schema:
```python
[
    {
        "type": "MAP_HIGHLIGHT", # or MAP_PAN / TIMELINE_SEEK
        "tribe_id": "tribe_warli_001",
        "tribe_name": "Warli"
    }
]
```

## Current Architecture
The NER system relies on a hybrid approach. It uses precompiled word-boundary regular expressions for hyper-fast, accurate tribe identification. For unscripted geographical and temporal entities, it offloads text inference to a lightweight `spaCy` NLP model (`en_core_web_sm`). To maintain the non-blocking architecture of the Arkana API, the heavy CPU-bound NLP processing is pushed to background worker threads using `asyncio.to_thread`.

## Final Implementation
1. `pipeline.py` yields the final generated LLM tokens, then awaits `extract_map_events(full_response)`.
2. `entity_extractor.py` matches pre-compiled exact word-boundary regexes against the text to locate tribes, bypassing generic substring false positives.
3. The remaining string is evaluated by `spaCy`'s NER pipeline running on a background worker thread.
4. SpaCy extracts `GPE` tags (cross-referenced against `REGION_MAP`) and `DATE` tags containing numbers.
5. Events are deduplicated based on type and string identifier, then returned to the pipeline for emission to the client.

## Implemented Improvements
### 1. Replaced Substring Matching with Regex Word Boundaries
- **Problem:** The system used standard Python `in` operators to locate tribes. This caused massive false positives (e.g., the tribe `mali` would match inside the word `malicious`, forcing the map to highlight Mali artifacts).
- **Root Cause:** Naive string matching without boundary awareness.
- **Implementation:** During class instantiation, the module compiles `re.compile(rf"\b{re.escape(tribe_name)}\b", re.IGNORECASE)` for every registered tribe.
- **Impact:** Guarantees 100% exact-word precision. The map will never hallucinate a pan/highlight based on partial string matches.

### 2. Converted NLP Parsing to Non-Blocking Async Threads
- **Problem:** `doc = self.nlp(text)` executed synchronously on the main thread, freezing the ASGI event loop for 50–150ms per query.
- **Root Cause:** Blocking CPU-bound dependency placed inside an async orchestration pipeline.
- **Implementation:** Upgraded the method to `async def` and executed the model via `await asyncio.to_thread(self.nlp, text)`. All upstream callers (`pipeline.py`) were successfully refactored to `await` it.
- **Impact:** Arkana maintains full vertical async concurrency from the initial HTTP request down to the final map event emission.

## Important Design Decisions
- **Deduplication:** The module guarantees that if the LLM repeats "Warli... Warli... Warli", only a single `MAP_HIGHLIGHT` event will be dispatched over the wire, optimizing network bandwidth.
- **Immutable Schemas:** The JSON schemas of the extracted events (`MAP_HIGHLIGHT`, `MAP_PAN`, `TIMELINE_SEEK`) were strictly preserved so as not to break existing frontend Mapbox/D3 animation listeners.

## Breaking Changes
- **API Migration:** Any downstream caller interacting with `extract_map_events()` MUST now use `await`.

## Future Improvements
- **Move spaCy Model Download to Build Pipeline**
  - **Future owner:** DevOps / System Architect
  - **Target module:** Final Deployment (Dockerfile / CI)
  - **Reason:** Currently, if `en_core_web_sm` is missing, the module executes a `subprocess.run` to pip-install the weights dynamically at runtime. This is a severe anti-pattern that violates immutable containerization rules and will likely crash production environments lacking outbound network access.

## AI Notes
- **Safe refactors:** Expanding the `TRIBE_MAP` or `REGION_MAP` dictionaries.
- **Things that must never change:** The output array dictionary schema.
- **Public interfaces:** `extract_map_events` is the primary and singular gateway into the module.
