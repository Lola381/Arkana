# Arkana — Project Context & Development History

This document provides a complete synthesis of all the work done to date on the **Arkana** project—an interactive digital platform for exploring Indian Cultural Heritage.

---

## 1. Project Overview

**Arkana** is an artsy, editorial-style Indian Cultural Heritage platform inspired by Google Arts & Culture, designed to present and explore India's artistic and architectural legacy (e.g., temples, monuments, art forms, dynasties).

### Core Technology Stack
- **Frontend (Legacy / Prototype)**: HTML5, CSS3 (Tailwind CSS and custom style systems), Vanilla JS (Leaflet.js for interactive mapping, client-side integration with Groq LLM).
- **Frontend (Active / React)**: React 18 (Vite), Tailwind CSS (layout structure), Vanilla CSS (animations and transitions), React Router.
- **Node/Express Backend**: Node.js/Express.js application (`arkana-react/backend/`) handling routes, controllers, and models.
- **AI/RAG Pipeline Components**:
  - **Vector DB**: Qdrant (dense vectors) & PostgreSQL (sparse/metadata vectors).
  - **Embeddings**: `sentence-transformers/all-mpnet-base-v2` (768-dim text retrieval), `all-MiniLM-L6-v2` (384-dim semantic chunking boundary check), CLIP `ViT-B/32` (512-dim visual search/classification).
  - **Generation**: Groq API (`llama-3.1-8b-instant`) executing RAG-specific system constraints.

---

## 2. Workspace & Codebase Structure

The workspace (`d:\SPD2`) is divided into several main areas:

```
d:\SPD2\
├── arkana/                      # Vanilla HTML + CSS + JS interactive prototype
│   ├── css/                     # Vanilla styles and Tailwind imports
│   ├── js/                      # Page components, router, and chatbot integrations
│   │   ├── askarkana.js         # Client-side Groq Chat + Leaflet map integration
│   │   ├── exploremap.js        # Timeline, quick-jumps, Leaflet map configuration
│   │   └── router.js / components.js
│   └── pages/                   # HTML page templates
│
├── arkana-react/                # React (Vite) + Tailwind + CSS Project
│   ├── backend/                 # Node.js/Express.js backend app
│   ├── src/                     # React application source code
│   │   ├── components/          # Staggered hover cards, cursors, transitions, modals
│   │   ├── data/                # Hardcoded datasets (artifacts.js, chatResponses.js)
│   │   ├── hooks/               # Custom React hooks (useArkanaChat.js)
│   │   └── pages/               # React Page Views (Home, Browse, Identify, Explore, etc.)
│   └── WORK_LOG.txt             # Chronological React development log
│
├── AUDIT_REPORT.md              # Technical audit of Python AI modules
├── COMPATIBILITY_REPORT.md      # Mapping evaluation between ingestion ETL & Qdrant
├── arkana_implementation_plan.html
└── [Research Documents / PPTX]  # Presentations, project proposal, drafts
```

---

## 3. Work Completed to Date

### Phase 1: Prototype Building & React Migration
*   **Monolithic Prototype**: Built the initial static HTML prototype in `/arkana` featuring styling, interactive routing, and basic Leaflet mapping.
*   **React Scaffold**: Initialized a Vite-powered React container in `/arkana-react`.
*   **Component Migration**: Split the static pages into modular React pages:
    *   `Home.jsx` (landing and parallax layouts)
    *   `Explore.jsx` (interactive map + chatbot interaction)
    *   `Browse.jsx` (artifact catalog)
    *   `Culture.jsx` (specific tribal arts spotlight, e.g., Warli art)
    *   `ArtifactDetail.jsx` (artifact profiles)
    *   `Identify.jsx` (computer-vision asset upload placeholder)
    *   `Login.jsx` (login layout)
*   **Token System**: Created design tokens inside `src/index.css` supporting standard backgrounds (warm beige), primary highlights (gold `#8b6914`/`#c9a227`), and fluid animations.

### Phase 2: Page Transitions & Card Animations
*   **Geometric Wipe Transition**: Navigates routes using a multi-strip horizontal CSS container (`.wipe-overlay` / `.wipe-piece`) that expands and translates out in a staggered, modern sequence.
*   **Card Hover Reveal (Effect #5)**: Integrated an editorial layout featuring staggered grids where:
    *   Hovering zooms images to `1.12x` and reveals titles with dynamic left-to-right underline draws.
    *   A global pointer cursor (`GlobalCursor.jsx`) tracks the mouse position, activating with unique HSL colors (pink/purple vs. teal/blue) depending on card index.
*   **Photography Page Transition (Modal Expand)**:
    *   Clicking an artifact expands a modal portal directly from the clicked card's coordinate origin using `transform: scale()` for optimized rendering.
    *   Left side showcases an image with dynamic 3D perspective tilt reacting to mouse moves.
    *   Right side uses an overflow-hidden copy-wrap technique to slide individual lines of text up sequentially.
    *   Displays a slow, shifting dark warm linear gradient background (`@keyframes arkana-gradient`).

### Phase 3: AI & RAG Backend Audits
*   **AI Code Audit (`AUDIT_REPORT.md`)**: Analysed and catalogued active Python models:
    *   *Semantic Chunker*: Sentence boundary extraction via `all-MiniLM-L6-v2`.
    *   *Hybrid Retrieval*: Dense Qdrant search and sparse PostgreSQL BM25 metadata matching fused using Reciprocal Rank Fusion (RRF).
    *   *Reranker*: Cross-encoder models (`ms-marco-MiniLM-L-6-v2`) checking top results.
    *   *Generation*: Groq LLM API with strict factual grounding instructions.
    *   *NER*: spaCy matching to extract locations and fire events like `MAP_HIGHLIGHT` or `TIMELINE_SEEK`.
*   **Compatibility Audit (`COMPATIBILITY_REPORT.md`)**: Established payload matching tables mapping backend metadata schemas into Qdrant text (`arkana_corpus`) and image (`arkana_images`) vector DB formats.

---

## 4. Current Status & Next Steps

1.  **Frontend**: Fully responsive HTML/JS map dashboard and React components with premium micro-interactions, custom scroll tracking, and card expansions are operational.
2.  **Mock Data**: In-browser chatbot responses run via custom React hooks (`useArkanaChat.js`) simulating typing delays, stream states, map events, and inline insight cards.
3.  **To-Be-Resolved Integration**:
    *   Bridge the gap between the legacy Docker compose configurations (which contain ChromaDB) and the active RAG implementation (configured for Qdrant).
    *   Build standard FastAPI endpoints routing UI queries directly into the verified python pipelines.
