# Changelog

All notable changes to ARKANA are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Planned
- MongoDB `artifacts` collection with full CRUD REST API
- Dynamic artifact routing: `GET /api/artifacts/:id` → `/artifact/:id`
- Dynamic culture pages: `GET /api/cultures/:id` → `/culture/:id`
- Real AI vision model integration for the Identify page
- Image upload to cloud storage (Cloudinary or AWS S3)
- Admin panel for curators to manage artifact content
- TypeScript migration for frontend and backend
- Unit tests with Vitest (frontend) and Jest (backend)
- End-to-end tests with Playwright
- Docker + `docker-compose.yml` for local development
- GitHub Actions CI/CD pipeline (lint → build → deploy)
- Helmet.js for HTTP security headers
- express-rate-limit for brute-force protection on auth routes
- React error boundaries to prevent full-app crashes
- Route-level code splitting with `React.lazy` + `Suspense`
- Replace Tailwind CDN with npm-installed + PostCSS (tree-shaking)
- Automatic JWT refresh interceptor in the frontend
- Protected route wrapper component for auth-gated pages

---

## [0.3.0] — 2026-08-09

### Added

#### AI / Backend Integration (Echolore)
- Consolidated Python AI infrastructure into the `ai/` workspace.
- RAG Pipeline finalized with Qdrant (Vector DB) and PostGIS.
- FastAPI server established as the primary backend data engine.
- Complete cleanup of legacy documentation into consolidated `PRESENT_WORK.md` and `FUTURE_WORK.md`.
- Consolidated React UI and Express Auth docs into `FRONTEND_MASTER.md`.

---

## [0.2.0] — 2026-07-08

*Commit: `ea61b7a` — Author: Abhishek Singh*

### Added

#### Backend — Node.js / Express / MongoDB
- Complete authentication REST API at `/api/auth/*`:
  - `POST /api/auth/register` — create account, bcrypt password hash, dual JWT tokens
  - `POST /api/auth/login` — verify credentials, issue httpOnly cookie session
  - `POST /api/auth/logout` — revoke refresh token in DB, clear cookies
  - `POST /api/auth/refresh-token` — rotate access + refresh token pair
  - `GET /api/auth/profile` — return authenticated user's profile
  - `GET /api/health` — server health check endpoint
- `verifyJWT` middleware — validates `httpOnly` cookie or `Authorization: Bearer` header
- `User` Mongoose model — schema with pre-save bcrypt hook (12 rounds) + JWT instance methods
- `generateAccessAndRefreshTokens` helper — creates both tokens and persists refresh token to DB
- Token rotation security — stored refresh token validated against incoming token on refresh
- Backend environment configuration via `dotenv` (`.env` file, gitignored)
- `constants.js` — centralized `DB_NAME` and `COOKIE_OPTIONS`

#### Frontend
- `Login.jsx` — split-screen login form with clip-reveal entry animations + JWT auth
- `Register.jsx` — split-screen registration form with field validation + JWT auth
- `LiquidImage.jsx` — WebGL liquid distortion effect using Three.js + custom GLSL shaders + GSAP
- `CardModal.jsx` — full-screen artifact detail modal via `createPortal` with 3D image tilt
- `CardModalContext.jsx` — React context + `useCardModal()` hook for modal state management
- `GlobalCursor.jsx` — custom "READ" cursor that activates over `.article-card` elements
- Vite dev proxy — `/api/*` requests proxied to `http://localhost:5000` in development

---

## [0.1.0] — 2026-06-27

*Commit: `2d25aea` — Author: Abhishek Singh*

### Added

#### Project Scaffold
- React 19 + Vite 8 project initialized
- React Router DOM v7 with `BrowserRouter`
- oxlint configured as linter (`react/rules-of-hooks`, `react/only-export-components`)

#### Pages (6 initial routes)
- `Home.jsx` (`/`) — Hero section with parallax floating images + featured collection grid + LiquidImage
- `Explore.jsx` (`/explore`) — AI-style chat interface (mocked) + interactive India map + timeline slider
- `Browse.jsx` (`/browse`) — Filterable artifact grid with search bar + chip filters + accordion sidebar
- `Culture.jsx` (`/culture`) — Warli culture deep-dive profile with artifact grid and related cultures
- `ArtifactDetail.jsx` (`/artifact`) — Dancing Nataraja detail view with metadata and related works
- `Identify.jsx` (`/identify`) — Artifact upload UI with animated confidence bar + similarity results

#### Shared Components
- `Navbar.jsx` — Fixed navigation bar with scroll detection, mobile hamburger menu, auth-aware
- `ArtifactCard.jsx` — Hover-reveal card component for featured collections
- `ArticleCard.jsx` — Hover-reveal card component for Browse grid
- `ProfileCard.jsx` — Expanding poster-to-profile card (implemented, not yet used)
- `ScrollReveal.jsx` — `IntersectionObserver` wrapper for scroll-based fade-in animations
- `TransitionContext.jsx` — Custom page transition system (geometric wipe + card-expand)
- `TransitionOverlay.jsx` — Renders transition overlays (wipe panels + card cover element)

#### Data Layer
- `src/data/artifacts.js` — Centralized static data file with 9 exports:
  - `COLLECTION_ARTIFACTS` (6 items), `BROWSE_ARTIFACTS` (8 items), `RELATED_ARTIFACTS` (4 items)
  - `HERO_IMAGES` (4 items), `FILTER_COUNTS` (7 categories), `CHAT_RESPONSES` (4 items)
  - `WARLI_ARTIFACTS` (4 items), `RELATED_CULTURES` (3 items), `SIMILAR_ARTIFACTS` (4 items)

#### Design System
- `src/index.css` (758 lines) — Complete design system:
  - CSS custom properties (design tokens): colors, fonts, easing curves, spacing
  - Geometric wipe transition animation classes (`.wipe-overlay`, `.wipe-piece`)
  - Card animation classes (lift-glow, tilt-reveal, article-card hover-reveal)
  - CardModal overlay styles
  - Profile card styles
  - LiquidImage WebGL canvas positioning styles
  - ScrollReveal animation (`.reveal` → `.reveal.active`)
  - Global cursor styles
- `index.html` — Tailwind CDN loaded with extended custom config (colors, spacing, fonts)
- Google Fonts: Inter (400, 500, 600) + Playfair Display (500, 600, italic)
- Material Symbols Outlined icon font

---

## [Documentation] — 2026-07-11

### Added
- `README.md` — Professional project readme (replaces default Vite template)
- `ARCHITECTURE.md` — System architecture with Mermaid diagrams
- `PROJECT_STRUCTURE.md` — File-by-file project breakdown
- `API.md` — Complete API endpoint documentation with examples
- `CONTRIBUTING.md` — Developer onboarding and contribution guide
- `.env.example` — Safe environment variable template
- `CHANGELOG.md` — This file
