# ARKANA Repository Deep Audit & Architecture Review

## 1. Repository Overview
The **ARKANA** repository is a monorepo that houses a React 19 Single Page Application (frontend) and a Node.js/Express REST API (backend), along with extensive legacy code, AI backend code (Echolore), and project documentation. 
The platform is designed to be an interactive digital museum and AI-guided spatial exploration tool for India's cultural heritage. Currently, the frontend UI is highly polished with cinematic animations and WebGL effects, but it is heavily reliant on static dummy data. The authentication backend is fully functional using MongoDB, while the core domain data (heritage sites and AI chat) awaits integration with a Python/FastAPI data layer (Echolore). A recent merge has brought the Echolore AI workspace (`ai/`) and legacy HTML prototypes (`arkana/`) directly into this repository, leading to a complex and somewhat cluttered structure.

## 2. Documentation Summary
The repository contains comprehensive documentation detailing the system architecture, API contracts, project structure, and integration plans.
- **README.md**: Outlines the project vision, tech stack (React 19, Node.js, MongoDB), system architecture, and setup instructions. Highlights key features like the multi-filter browse, interactive maps, and card animations.
- **ARCHITECTURE.md**: Explains the frontend routing (React Router v7), state management (`TransitionContext`, `CardModalContext`, `localStorage`), backend middleware stack, authentication flow (JWT refresh rotation), and the design system tokens.
- **API.md**: Documents the existing Node.js authentication endpoints (`/auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh-token`, `/auth/profile`) and their expected payloads/responses.
- **PROJECT_STRUCTURE.md**: Provides a file-by-file breakdown of the active application, exposing legacy dead code (`server.py`, `mongodb.py`, `arkana/`) and identifying hardcoded components (e.g., `Culture.jsx` hardcoded to Warli).
- **INTEGRATION_PLAN.md**: The most critical document for backend developers. It defines the relationship between the ARKANA application layer and the Echolore data/AI layer. It outlines a 5-step plan to proxy heritage and chat requests from the Node.js backend to a Python FastAPI service, replace static frontend data with live fetches, and eventually migrate authentication from MongoDB to PostgreSQL.

*Inconsistencies identified*: The frontend `.env` file is flagged as being in the wrong location and containing backend secrets. There is also planned database churn (MongoDB currently active, but a migration to PostgreSQL is planned).

## 3. Architecture Overview
The system follows a standard modern web architecture but is currently in a transitional state:
- **Frontend (Client)**: A React 19 SPA built with Vite. It uses vanilla CSS for design tokens and animations, GSAP and Three.js for liquid image transitions, and Leaflet for mapping. Routing is handled by React Router DOM. 
- **State Management**: Context API is used for UI state (`TransitionContext`, `CardModalContext`), while `localStorage` is used for basic auth state. Real data fetching state (e.g., React Query or Redux) is conspicuously absent because data is currently imported synchronously from static files.
- **API Gateway (Node.js/Express)**: Runs on port 5000. It currently handles JWT authentication natively and stores users in MongoDB. According to the `INTEGRATION_PLAN.md`, this server will eventually act as a proxy gateway to route `/api/heritage/*` and `/api/chat/*` requests to the Echolore FastAPI backend.
- **Data/AI Backend (Python/FastAPI)**: Handled by Echolore (located in the `ai/` folder). It uses PostgreSQL + PostGIS for 3,826 heritage sites, and Qdrant + Gemini for RAG (Retrieval-Augmented Generation). 

The frontend architecture is scalable in terms of UI components, but the data layer requires significant refactoring to support asynchronous API calls instead of static arrays.

## 4. Folder Structure Review
- `backend/`: Node.js Express server containing auth controllers, MongoDB connection logic, Mongoose models, and JWT middleware. This is the canonical API gateway.
- `src/`: The active React 19 application.
  - `src/assets/`: Static images and SVGs.
  - `src/components/`: Reusable UI elements (`Navbar`, `CardModal`, `LiquidImage`). `ProfileCard.jsx` is dead/unused code.
  - `src/data/`: `artifacts.js` and `chatResponses.js`. These contain all the mocked data currently powering the UI.
  - `src/pages/`: Page-level components. Many are hardcoded (e.g., `ArtifactDetail`, `Culture`, `Identify`).
- `docs/`: Extensive project documentation and legacy archive.
- `ai/`: The Echolore RAG pipeline and FastAPI backend. Note: It contains a nested `ai/backend/src/` which appears to be a duplicated React frontend that needs to be removed.
- `arkana/`: Legacy vanilla HTML/JS/CSS prototype. Dead code.
- Root scripts (`server.py`, `mongodb.py`): Legacy Python scripts for a deprecated Flask server. Dead code.

## 5. Feature-by-Feature Analysis
| Feature | Purpose | Status | Backend Requirements |
|---------|---------|--------|----------------------|
| **Authentication** | User registration, login, and secure sessions. | **Complete** | Handled by Node.js and MongoDB. (Migration to PostgreSQL planned later). |
| **Browse Page** | Multi-filter grid (Region, Period, Art Form) with live search. | **UI Only (Mocked)** | Requires `GET /api/heritage/sites` with query parameters (`region`, `period`, `category`, `q`, `limit`, `offset`). |
| **Ask Arkana / Map** | AI chat interface with interactive Leaflet mapping. | **UI Only (Mocked)** | Requires `POST /api/chat/ask` (returning text, citations, and GeoJSON) and `GET /api/map/bounds`. |
| **Culture Deep-Dives** | Rich profiles for specific cultures (Warli, Gond, etc.). | **Partial (Hardcoded)** | Currently hardcoded to "Warli". Requires an endpoint to fetch culture-specific details and related artifacts. |
| **ArtifactDetail** | Deep metadata view, 360 viewer, related works. | **Partial (Hardcoded)** | Currently hardcoded to "Dancing Nataraja". Requires `GET /api/heritage/sites/:id`. |
| **Identify** | Upload an image for visual similarity matching. | **UI Only (Mocked)** | UI simulates an 87% confidence match. Requires a new ML endpoint (e.g., `POST /api/identify`) taking an image payload. |
| **Heritage Cards / Modal** | Cinematic 3D tilt modal expanding from cards. | **Complete** | UI feature only; no backend required. |
| **Transitions / Animations**| Page wipes, scroll reveals, custom cursors. | **Complete** | UI feature only; no backend required. |

## 6. Data Model Expectations
Based on `src/data/artifacts.js` and `src/data/chatResponses.js`, the frontend expects the following data structures:

**Heritage Site (Artifact) Object:**
- `id` (string): Unique identifier.
- `title` (string): Name of the artifact/site.
- `type` / `artForm` (string): Category (e.g., 'Sculpture', 'Painting').
- `period` / `timePeriod` (string): Time period description (e.g., '11th Century CE · Tamil Nadu').
- `description` (string): Detailed text.
- `image` (string): URL to the image.
- `filter` / `region` (string): For UI filtering.
- `location` (string): (Optional) Used in Identify matches.
- `match` (string): (Optional) Used in Identify matches (e.g., '92% Match').

**AI Chat Response (RAG Payload):**
- `text` (string): The LLM generated response.
- `citation` (string): Citation identifier.
- `source` (string): Source name.
- `insightCard` (object, optional): Data to render a related artifact card (`title`, `period`, `image`, `link`).
- `mapEvent` (object, optional): `pinId` and `label` to trigger map actions.
- `geoData` (object, optional): 
  - `type` (string): 'marker', 'markers', or 'region'.
  - `lat`, `lng` (number): Coordinates for a single marker.
  - `points` / `markers` (array): Array of `{lat, lng, label, color}`.
  - `polygon` (array): Array of `[lat, lng]` arrays for drawing boundaries.
  - `center` (array): `[lat, lng]` to center the map.
  - `zoom` (number): Map zoom level.
  - `label`, `color` (string): Metadata for polygons/markers.

## 7. API Expectations
The frontend currently makes `fetch` calls to `/api/auth/*`. To fully integrate the UI, the frontend will need to make asynchronous calls to the following endpoints (which the Node.js backend must proxy to the Echolore FastAPI server):

- **GET `/api/heritage/sites`**: Must support query parameters for `region`, `period`, `category`, `q` (search), `limit`, and `offset`. Must return an array of Heritage Site objects and total counts for pagination/filters.
- **GET `/api/heritage/sites/:id`**: Must return the full detail object for a specific artifact/site.
- **POST `/api/chat/ask`**: Accepts `{ query: string, session_id?: string }`. Must return the AI Chat Response payload described above.
- **GET `/api/map/bounds`**: Accepts `?qid=...`. Must return GeoJSON FeatureCollections for the map.
- **POST `/api/identify`**: (Future) Accepts FormData (image file), returns an array of visually similar artifacts with match percentages.

## 8. Backend Requirements
To achieve full integration, the following backend work is required:
1. **Echolore FastAPI Service**: Must be finalized and deployed locally (port 8000) to serve the PostgreSQL site data and execute the Gemini RAG pipeline.
2. **Node.js Proxy Configuration**: The existing Node.js server (`backend/app.js`) must be updated to securely proxy requests to `ECHOLORE_API_URL`.
3. **Authentication Middleware**: The proxy routes for `/api/chat/ask` may need the JWT `authMiddleware` applied if chat is restricted to logged-in users.
4. **Data Normalization**: The data models exposed by Echolore's PostgreSQL must be mapped to match the frontend's expected properties (e.g., mapping `image_url` to `image`, ensuring `geoData` strictly follows the mock shapes).
5. **Database Migration**: Eventually execute the planned migration of user auth data from MongoDB to PostgreSQL to achieve a single source of truth.

## 9. Technical Debt
- **Static Data Coupling**: The frontend is heavily coupled to synchronous, static data in `src/data/artifacts.js` and `src/data/chatResponses.js`. Removing this requires implementing API service layers, loading states, error boundaries, and replacing synchronous imports with `useEffect` or a data-fetching library.
- **Dead Code & Duplication**: `server.py`, `mongodb.py`, the `arkana/` folder, and the duplicate frontend inside `ai/ai/backend/src/` should be deleted to prevent confusion.
- **Hardcoded Pages**: `Culture.jsx` and `ArtifactDetail.jsx` are rigidly hardcoded to single examples (Warli and Dancing Nataraja). These pages need to be rewritten to accept dynamic route parameters (`/:id`).
- **Fake UI Elements**: The Identify page's drag-and-drop upload and confidence bar are entirely fake UI animations. The Newsletter signup has no backend.
- **Configuration Leaks**: The frontend `.env` contains MongoDB URIs which is a security risk if bundled by Vite.

## 10. Integration Readiness
- **Frontend**: **Not Ready**. While visually complete, the React application lacks an API service layer for non-auth data. The transition from static synchronous arrays to asynchronous API calls will require significant refactoring of components to handle loading spinners, empty states, and pagination.
- **Backend (Node.js)**: **Ready**. The Node.js server is well-structured and ready to have proxy routes attached.
- **Backend (Echolore/AI)**: **Not Ready**. The FastAPI endpoints do not yet exist, and the vector embeddings have not been run.

## 11. Risks
- **Data Shape Mismatch**: The complex nested objects required by the frontend map (`geoData` with distinct `type`, `polygon`, `markers`) might be difficult to generate accurately on-the-fly using the LLM in the RAG pipeline. If the LLM hallucinates the JSON structure, the Leaflet map will crash.
- **Performance**: Fetching from 3,826 sites with multiple active filters (Region, Period, Art Form) requires robust indexing in PostgreSQL and proper pagination in the UI, neither of which are currently wired up on the frontend.
- **State Management**: As the application moves to live data, relying solely on local `useState` for complex filtering and caching will become brittle.

## 12. Suggested Improvements
1. **Implement React Query**: Introduce `@tanstack/react-query` to handle data fetching, caching, loading states, and error handling gracefully. This will drastically simplify the transition from static data to live APIs.
2. **Clean the Repository**: Execute a strict pruning of dead code (`server.py`, `arkana/` prototype, duplicated `ai` frontends) to clarify the repository structure for new developers.
3. **Dynamic Routing**: Refactor `App.jsx` to support dynamic routes like `/culture/:id` and `/artifact/:id`, and update the respective page components to fetch data based on `useParams()`.
4. **Strict Schema Validation**: Implement Zod or JSON Schema validation on the frontend specifically for the AI Chat `geoData` payloads to prevent malformed LLM responses from crashing the Leaflet map.
5. **Fix Git Submodules**: Resolve the broken gitlink for `arkana-react` mentioned in the project structure docs to ensure the repo clones cleanly for all developers.
