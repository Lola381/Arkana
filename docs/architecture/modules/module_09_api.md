# Module 9 — API / FastApi Layer

## Purpose
The API module serves as the primary HTTP REST boundary for the Echolore AI backend. It is responsible for bridging the external Node.js API Gateway with the internal machine learning orchestrator (Module 10). It handles dependency injection, strict Pydantic payload validation, centralized exception handling, Server-Sent Events (SSE) streaming for AI generation, and the full application lifecycle (startup warmup and graceful shutdown).

## Files
- `ai/ai/backend/main.py`
  - *FastAPI application initialization, CORS configuration, and lifespan management.*
- `ai/ai/backend/api/schemas.py`
  - *Strict Pydantic models for incoming requests and outgoing responses.*
- `ai/ai/backend/api/exceptions.py`
  - *Centralized HTTP error mapping.*
- `ai/ai/backend/api/dependencies.py`
  - *Dependency injection for the pipeline singleton.*
- `ai/ai/backend/api/routes/chat.py`, `visual.py`, `sites.py`
  - *HTTP route handlers.*

## Entry Points
- `uvicorn ai.backend.main:app` (Application Server)
- `POST /api/chat` (Streaming RAG endpoint)
- `POST /api/identify` (Visual identification endpoint)
- `GET /api/sites`, `GET /api/sites/{id}` (Database query endpoints)

## Inputs
- **Chat Endpoint:** `ChatRequest` containing a `query` (str), `conversation_history` (list), and `map_context` (dict).
- **Identify Endpoint:** Multipart form-data containing an `UploadFile` (image).
- **Sites Endpoint:** URL query parameters (e.g., `limit`, `offset`) or path parameters (`site_id`).

## Outputs
- **Chat Endpoint:** W3C compliant Server-Sent Events (SSE) structured via `ChatResponseEvent` (e.g., `data: {"type": "token", "data": "..."}\n\n`).
- **Identify Endpoint:** JSON payload matching the `VisualIdentifyResponse` schema (style classification and similar artifacts).
- **Sites Endpoint:** JSON array or object matching the `SiteResponse` schema.
- **Errors:** Standardized `ErrorResponse` JSON with `error` string and `details`.

## Current Architecture
The FastAPI layer leverages a strict separation of concerns from the core ML logic. 
- **Application Lifespan:** On server startup, the `lifespan` context instantiates the `ArkanaPipeline` and calls its async `.initialize()` method to synchronously load heavy ML models (spaCy, CLIP, CrossEncoder) into memory before the server binds to port 8000.
- **Dependency Injection:** The warmed-up pipeline is safely stored in `app.state.pipeline`. Route handlers access it via `Depends(get_pipeline)`, completely decoupling request logic from global singletons.
- **Routing:** Dedicated routers cleanly map business capabilities to HTTP verbs. For chat, `StreamingResponse` wraps the asynchronous generator yielded by the core pipeline, emitting real-time telemetry (tokens, citations, map events) to the frontend.
- **Exception Handling:** A global middleware layer catches `RequestValidationError`, `HTTPException`, and unhandled standard exceptions, ensuring the Node gateway never receives an HTML traceback or malformed response.

## Final Implementation
1. The web user sends a POST request to the Node proxy, which forwards it to `/api/chat`.
2. FastAPI validates the JSON payload against `ChatRequest`.
3. The dependency injector resolves the active `ArkanaPipeline` from the application state.
4. The router invokes the async generator on the pipeline and initiates an HTTP streaming response.
5. As the pipeline yields internal event dictionaries, the router strictly validates them against `ChatResponseEvent` and serializes them into SSE format.
6. Upon a graceful server shutdown signal (SIGTERM/Ctrl+C), FastAPI halts incoming requests. The `lifespan` teardown iterates over `pipeline._background_tasks`, awaiting any pending metric evaluations to prevent telemetry loss, and cleanly closes the PostgreSQL connection pool.

## Implemented Improvements
### 1. Removal of Unmanaged Singletons
- **Problem:** Previously, the ML pipeline utilized an unmanaged global variable (`_pipeline_instance`) and lazy initialization, leading to race conditions, poor testability, and a massive 10+ second "cold start" latency for the first HTTP request.
- **Implementation:** Shifted model warmup entirely to the FastAPI `lifespan` event. Removed dead global getter logic from the core pipeline, enforcing DI via `app.state`.
- **Impact:** The first incoming user request is now instantly serviced. The pipeline is strictly managed and scoped.

### 2. Standardized API Contracts
- **Problem:** Data was passed around as arbitrary dictionaries, risking silent failures if the frontend schema expectations drifted.
- **Implementation:** Created `schemas.py` with Pydantic models acting as the absolute source of truth for the HTTP boundary.
- **Impact:** Validation errors are automatically caught and standardized. Developer experience is greatly improved with deterministic schemas.

### 3. Graceful Background Task Termination
- **Problem:** Background tasks spawned by the core pipeline (e.g., metric logging) would abruptly die mid-flight if the web server shut down.
- **Implementation:** The FastAPI `lifespan` exit handler explicitly gathers and awaits the pipeline's tracked `_background_tasks`.
- **Impact:** Guaranteed metric durability during server re-deployments.

## Deferred Improvements
- **Redis Query Caching**
  - **Reason:** Caching for FTS and proximity queries (Phase 3 deliverables) requires setting up `aioredis` and invalidation logic, which is deferred to a dedicated caching PR to minimize initial MVP scope.
- **Docker Compose Wiring**
  - **Reason:** Connecting the `uvicorn` startup command and exposing port 8000 alongside PostgreSQL and ChromaDB in the `docker-compose.yml` belongs to deployment operations.

## AI Notes
- **Safe refactors:** Modifying the Pydantic schemas to add new optional metadata fields.
- **Hidden coupling:** The Node.js API Gateway explicitly routes `/api/chat/ask` to this module's `/api/chat`. Renaming this route prefix will break frontend AI integration.
- **Things that must never change:** The `media_type="text/event-stream"` declaration on the chat endpoint and the exact serialization format `data: {json}\n\n`. React's EventSource parser will fail silently if the SSE standard is violated.
