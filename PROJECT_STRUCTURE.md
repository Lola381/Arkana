# ARKANA — Project Structure

A complete file-by-file breakdown of every folder and significant file in the project.

---

## Repository Root (`d:\SPD2\`)

This is the parent git repository (`github.com/Lola381/Arkana`).

> ⚠️ **Known Issue:** `arkana-react/` is registered as a broken git gitlink (no `.gitmodules` file exists).
> (Note: The heritage data and AI backend engine is being built separately in the Echolore repository. Once integrated, the static data mocks detailed above will be replaced by dynamic API calls to Echolore's FastAPI service.)
> All React source code is currently invisible on GitHub. This must be fixed before the project can be
> properly cloned by others.

```
d:\SPD2\
├── arkana-react/              ← MAIN APPLICATION (see below)
├── arkana/                    ← Legacy vanilla HTML/JS/CSS prototype (archived)
│   ├── index.html             ← Original monolithic page
│   ├── css/
│   │   └── styles.css         ← Monolithic stylesheet
│   ├── js/
│   │   ├── animations.js      ← Vanilla JS scroll/hover animations
│   │   ├── components.js      ← Vanilla JS card/navbar component factories
│   │   └── router.js          ← Custom hash-based SPA router
│   └── pages/                 ← Individual HTML pages (7 files)
│       ├── artifact.html      ← Artifact detail page
│       ├── browse.html        ← Collection browser
│       ├── culture.html       ← Culture profile
│       ├── explore.html       ← Explore/discover
│       ├── home.html          ← Empty (1 line)
│       ├── identify.html      ← Artifact identification
│       └── login.html         ← Login form
│
├── heritage_editorial/
│   └── DESIGN.md              ← Complete design system specification:
│                                  colors, typography, spacing, components, animations
│
├── [HTML prototype mockups]   ← Early design iterations with screenshots
│   ├── home_arkana/code.html + screen.png
│   ├── browse_collection_arkana/code.html + screen.png
│   ├── identify_artifact_arkana/code.html + screen.png
│   ├── sign_in_arkana/code.html + screen.png
│   ├── warli_culture_arkana/code.html + screen.png
│   ├── artifact_dancing_nataraja_arkana/code.html
│   └── explorer_arkana/code.html + screen.png
│
├── arkana_implementation_plan.html   ← AI-generated implementation plan
├── cardanimations.txt                ← Card animation specifications
├── trans.txt                         ← Page transition specifications
├── kailasa.avif                      ← Source image (not used in active app)
├── kailasa paint.avif                ← Source image (not used in active app)
├── large-thumbnail*.mp4              ← Video file (not used in active app)
├── *.pptx / *.docx / *.pdf          ← Academic research presentations
└── .git/                             ← Root repository git data
```

---

## Active Application — `arkana-react/`

```
arkana-react/
│
├── ─────────────────────────────────────
│   FRONTEND
│   ─────────────────────────────────────
│
├── index.html                     ← Vite HTML shell
│                                     - Sets page title: "ARKANA — Indian Cultural Heritage Platform"
│                                     - Loads: Tailwind CSS CDN (with custom config inline)
│                                     - Loads: Google Fonts (Inter, Playfair Display)
│                                     - Loads: Material Symbols Outlined icon font
│                                     - Contains custom Tailwind color/spacing/font extensions
│                                     - Entry point: <script type="module" src="/src/main.jsx">
│
├── vite.config.js                 ← Vite build configuration
│                                     - Plugin: @vitejs/plugin-react (JSX via Oxc)
│                                     - Dev proxy: /api/* → http://localhost:5000
│
├── package.json                   ← Frontend npm manifest
│                                     Scripts: dev, build, lint (oxlint), preview
│                                     Dependencies: react, react-dom, react-router-dom, gsap, three
│                                     DevDeps: @vitejs/plugin-react, vite, oxlint, @types/react*
│
├── .oxlintrc.json                 ← Oxlint (Rust linter) config
│                                     - Plugins: react, oxc
│                                     - react/rules-of-hooks: error
│                                     - react/only-export-components: warn
│
├── .gitignore                     ← Git exclusions:
│                                     node_modules, dist, dist-ssr, *.local
│                                     .env, WORK_LOG.txt, log files, editor dirs
│
├── .env                           ← ⚠️ WRONG LOCATION
│                                     Contains MongoDB URI — should ONLY be in backend/.env
│                                     Frontend .env should only hold VITE_* prefixed vars
│
├── WORK_LOG.txt                   ← Development diary (gitignored)
├── server.py                      ← ⚠️ DEAD CODE — Python Flask auth server (unused)
├── mongodb.py                     ← ⚠️ DEAD CODE — Python MongoDB test script (unused)
│
├── src/
│   │
│   ├── main.jsx                   ← React entry point
│   │                                 Creates React root, wraps App in StrictMode + BrowserRouter
│   │
│   ├── App.jsx                    ← Route table + global context providers
│   │                                 Provider order (outer → inner):
│   │                                   TransitionProvider → CardModalProvider → Routes
│   │                                 Renders: Navbar, Routes, TransitionOverlay, CardModal, GlobalCursor
│   │
│   ├── index.css                  ← Global CSS (758 lines)
│   │                                 - CSS reset
│   │                                 - Design tokens (CSS custom properties)
│   │                                 - LiquidImage WebGL canvas styles
│   │                                 - Geometric wipe transition keyframes
│   │                                 - Card animation classes (lift-glow, tilt-reveal, etc.)
│   │                                 - Article card hover-reveal styles
│   │                                 - CardModal styles (portal overlay)
│   │                                 - Profile card styles
│   │                                 - Scroll reveal animation (.reveal → .reveal.active)
│   │                                 - Global cursor styles
│   │
│   ├── assets/
│   │   └── kailasa_bg.png         ← Background for Login + Register left panel
│   │                                 Kailasa cave painting (dark editorial aesthetic)
│   │
│   ├── data/
│   │   └── artifacts.js           ← ⚠️ TEMPORARY MOCKS (ALL static content)
│   │       ├── COLLECTION_ARTIFACTS  [6 items] — Home page featured collection
│   │       ├── BROWSE_ARTIFACTS      [8 items] — Browse grid with filter tags
│   │       ├── RELATED_ARTIFACTS     [4 items] — ArtifactDetail sidebar
│   │       ├── HERO_IMAGES           [4 items] — Home page parallax images
│   │       ├── FILTER_COUNTS         [7 keys]  — Browse sidebar count display
│   │       ├── CHAT_RESPONSES        [4 items] — Explore page AI chat (mock)
│   │       ├── WARLI_ARTIFACTS       [4 items] — Culture page artifact grid
│   │       ├── RELATED_CULTURES      [3 items] — Culture page sidebar
│   │       └── SIMILAR_ARTIFACTS     [4 items] — Identify page results (mock)
│   │
│   ├── components/
│   │   │
│   │   ├── Navbar.jsx             ← Fixed navigation bar (187 lines)
│   │   │                             - Scroll detection (scrolled state at 40px)
│   │   │                             - Mobile hamburger menu (menuOpen state)
│   │   │                             - Auth state from localStorage.getItem('user')
│   │   │                             - Logout: clears localStorage + location.href = '/'
│   │   │                             - Nav items: Explore, Cultures, Browse, Identify, Ask Arkana
│   │   │                             - Uses TransitionNavLink for animated navigation
│   │   │
│   │   ├── ArtifactCard.jsx       ← Hover-reveal artifact card (61 lines)
│   │   │                             - Props: artifact { id, title, type, period, description, image }, index
│   │   │                             - On click: openCard(artifact, el) → CardModal
│   │   │                             - Even/odd index → CSS offset stagger class
│   │   │                             - Accessible: role="button", tabIndex, onKeyDown
│   │   │                             - Used by: Home, Culture
│   │   │
│   │   ├── ArticleCard.jsx        ← Browse grid card (47 lines)
│   │   │                             - Near-identical to ArtifactCard (candidate for merge)
│   │   │                             - Props: article, index
│   │   │                             - Used by: Browse
│   │   │
│   │   ├── CardModal.jsx          ← Full-screen modal portal (164 lines)
│   │   │                             - Rendered via createPortal(document.body)
│   │   │                             - Scales from clicked card position to fullscreen
│   │   │                             - Left: large image with 3D mouse-tracking tilt
│   │   │                             - Right: staggered content reveal (type → title → divider → period → desc)
│   │   │                             - Escape key closes modal
│   │   │                             - Accessible: role="dialog", aria-modal, aria-label
│   │   │
│   │   ├── CardModalContext.jsx   ← Context for CardModal (43 lines)
│   │   │                             - State: { isOpen, artifact, originX, originY }
│   │   │                             - openCard(artifact, el): computes transform-origin from el.getBoundingClientRect()
│   │   │                             - closeCard(): restores body scroll
│   │   │                             - Custom hook: useCardModal()
│   │   │
│   │   ├── GlobalCursor.jsx       ← Custom "READ" cursor (53 lines)
│   │   │                             - Tracks pointermove for position
│   │   │                             - Activates (adds class) when over .article-card
│   │   │                             - Alternates pink/teal by card DOM index
│   │   │                             - aria-hidden (decorative only)
│   │   │
│   │   ├── LiquidImage.jsx        ← WebGL liquid distortion (247 lines)
│   │   │                             - Three.js OrthographicCamera + WebGLRenderer
│   │   │                             - Custom GLSL fragment shader: layered sine/cosine noise
│   │   │                             - GSAP animates uDistortion uniform: 1.0 → 0.0 on scroll entry
│   │   │                             - IntersectionObserver triggers effect on viewport entry
│   │   │                             - Graceful fallback: shows <img> if WebGL fails
│   │   │                             - Props: src, alt, className, imgClass
│   │   │                             - Used by: Home page
│   │   │
│   │   ├── ProfileCard.jsx        ← Expanding poster card (69 lines)
│   │   │                             ⚠️ CURRENTLY UNUSED — imported nowhere
│   │   │                             - Props: artifact, dark
│   │   │                             - On click: triggerCardExpand('/artifact', el)
│   │   │                             - Follow/save toggle with aria-pressed
│   │   │
│   │   ├── ScrollReveal.jsx       ← IntersectionObserver fade-in wrapper (45 lines)
│   │   │                             - Adds 'active' class when element enters viewport (threshold: 10%)
│   │   │                             - Unobserves after first reveal (one-shot)
│   │   │                             - CSS in index.css: .reveal → opacity:0, translateY(30px)
│   │   │                             - Props: children, className, delay
│   │   │                             - Used by: Home, Browse, Culture, ArtifactDetail, Identify
│   │   │
│   │   ├── TransitionContext.jsx  ← Page transition orchestrator (126 lines)
│   │   │                             Two transition modes:
│   │   │                             1. Geometric Wipe: triggerWipe(path) — 4-panel horizontal sweep
│   │   │                             2. Card Expand: triggerCardExpand(path, el) — card scales to fullscreen
│   │   │                             Exports: TransitionProvider, TransitionLink, TransitionNavLink, useTransition()
│   │   │
│   │   └── TransitionOverlay.jsx  ← Transition overlay renderer (82 lines)
│   │                               - Wipe: 4 × .wipe-piece divs with staggered CSS transitions
│   │                               - Card expand: single div that grows from card rect to 100vw×100vh
│   │
│   └── pages/
│       │
│       ├── Home.jsx               ← Landing page (266 lines)
│       │                             Section 1: Hero — parallax floating images + headline + CTA
│       │                             Section 2: Featured Collection — ArtifactCard grid (6 items)
│       │                             Section 3: Explore features (LiquidImage, editorial layout)
│       │                             Section 4: Newsletter signup (UI only, no backend)
│       │                             Effect: mousemove parallax on .floating-element
│       │
│       ├── Explore.jsx            ← Discovery page (230 lines)
│       │                             Left panel: AI-style chat interface (mocked round-robin responses)
│       │                             Right panel: SVG India map with 5 regional pins
│       │                             Timeline slider: 1000 BCE → 2024 (computed yearVal)
│       │
│       ├── Browse.jsx             ← Collection browser (199 lines)
│       │                             Sidebar: accordion (Region, Period, Art Form, Institution)
│       │                             Filters: chip buttons (All, Warli, Gond, Mughal, Buddhist, Chola, Rajput)
│       │                             Search: live text filter on title + type + period
│       │                             Grid: ArticleCard with CardModal on click
│       │
│       ├── Culture.jsx            ← Culture deep-dive (225 lines)
│       │                             ⚠️ HARDCODED to Warli culture only
│       │                             Hero: parallax image with gradient overlay
│       │                             About: narrative text sections
│       │                             Artifacts: WARLI_ARTIFACTS grid (4 items)
│       │                             Related: RELATED_CULTURES sidebar (3 items)
│       │
│       ├── ArtifactDetail.jsx     ← Artifact detail view (193 lines)
│       │                             ⚠️ HARDCODED to Dancing Nataraja (Chola, 11th century)
│       │                             Left: Large image with zoom + 360° buttons (UI only)
│       │                             Right: Metadata panel (type, period, dynasty, medium, dimensions)
│       │                             Bottom: Related Artifacts grid (4 items)
│       │
│       ├── Identify.jsx           ← Artifact identification (268 lines)
│       │                             ⚠️ MOCKED — no real AI backend
│       │                             Upload area: drag-and-drop UI (no actual upload)
│       │                             Confidence bar: animates to 87% on mount
│       │                             Results: SIMILAR_ARTIFACTS grid (4 items with match %)
│       │                             Cards have 3D tilt on hover (ref-based mouse tracking)
│       │
│       ├── Login.jsx              ← Login page (401 lines)
│       │                             Split-screen: left (dark editorial with kailasa_bg.png) + right (form)
│       │                             Entry animation: RevealLine clip-reveal stagger
│       │                             Form: email + password (LineInput component, inline)
│       │                             Auth: fetch('/api/auth/login') → localStorage + redirect
│       │                             Guard: redirects to / if already logged in
│       │
│       └── Register.jsx           ← Register page (431 lines)
│                                     Same split-screen layout as Login
│                                     Form: name + email + password + confirm password
│                                     Validation: field presence, password match, min length (6)
│                                     Auth: fetch('/api/auth/register') → localStorage + redirect
│                                     Guard: redirects to / if already logged in
│
├── public/
│   ├── favicon.svg                ← Custom ARKANA favicon (SVG format)
│   └── icons.svg                  ← SVG icon sprite (not currently referenced in JSX)
│
├── dist/                          ← ⚠️ Vite build output — should be in .gitignore
│   ├── index.html
│   └── assets/                    ← Hashed JS/CSS bundles
│
└── .dist/                         ← ⚠️ Empty directory — no purpose, can be deleted
│
├── ─────────────────────────────────────
│   BACKEND
│   ─────────────────────────────────────
│
└── backend/
    │
    ├── index.js                   ← Server entry point (17 lines)
    │                                 1. require('dotenv').config() — loads .env
    │                                 2. connectDB() — connects to MongoDB Atlas
    │                                 3. app.listen(PORT) — starts HTTP server
    │                                 Exits process on DB connection failure
    │
    ├── app.js                     ← Express application factory (28 lines)
    │                                 Configures: cors, express.json, express.urlencoded, cookieParser
    │                                 Registers: /api/auth router, /api/health GET
    │                                 Exports: app (consumed by index.js)
    │
    ├── constants.js               ← Shared constants (10 lines)
    │                                 DB_NAME = 'arkana'
    │                                 COOKIE_OPTIONS = { httpOnly: true, secure: false, sameSite: 'lax' }
    │                                 ⚠️ secure: false must be true in production
    │
    ├── package.json               ← Backend npm manifest
    │                                 Scripts: start (node), dev (nodemon)
    │                                 Dependencies: express, mongoose, bcryptjs, jsonwebtoken,
    │                                               cookie-parser, cors, dotenv
    │                                 DevDeps: nodemon
    │
    ├── .env                       ← ✅ Correctly gitignored (backend-only secrets)
    │                                 PORT, MONGODB_URI, DATABASE_NAME
    │                                 ACCESS_TOKEN_SECRET, ACCESS_TOKEN_EXPIRY
    │                                 REFRESH_TOKEN_SECRET, REFRESH_TOKEN_EXPIRY
    │                                 CORS_ORIGIN
    │
    ├── db/
    │   └── index.js               ← MongoDB connection (19 lines)
    │                                 mongoose.connect(`${MONGODB_URI}/${DB_NAME}`)
    │                                 Logs connected host on success
    │                                 process.exit(1) on failure
    │
    ├── models/
    │   └── user.model.js          ← Mongoose User schema (62 lines)
    │                                 Fields: name, email (unique), password, refreshToken, timestamps
    │                                 Pre-save hook: bcrypt.hash(password, 12) — only if modified
    │                                 Instance method: isPasswordCorrect(candidate) → bcrypt.compare
    │                                 Instance method: generateAccessToken() → jwt.sign (1d)
    │                                 Instance method: generateRefreshToken() → jwt.sign (7d)
    │
    ├── controllers/
    │   └── auth.controller.js     ← Auth route handlers (168 lines)
    │                                 Private helper: generateAccessAndRefreshTokens(userId)
    │                                 Exports: registerUser, loginUser, logoutUser,
    │                                          refreshAccessToken, getProfile
    │
    ├── routes/
    │   └── auth.routes.js         ← Route→handler mapping (23 lines)
    │                                 POST /register    → registerUser
    │                                 POST /login       → loginUser
    │                                 POST /refresh-token → refreshAccessToken
    │                                 POST /logout      → [verifyJWT] → logoutUser
    │                                 GET  /profile     → [verifyJWT] → getProfile
    │
    └── middleware/
        └── auth.middleware.js     ← JWT guard (37 lines)
                                      Reads token from: cookies.accessToken OR Authorization: Bearer
                                      Verifies: jwt.verify(token, ACCESS_TOKEN_SECRET)
                                      Fetches: User.findById().select('-password -refreshToken')
                                      Attaches: req.user = user → next()
                                      Error handling: TokenExpiredError → 401, other → 401
