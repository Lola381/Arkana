# 🏛️ Arkana — Indian Cultural Heritage Platform

<p align="center">
  <img src="public/favicon.svg" width="72" alt="Arkana"/>
</p>

<p align="center">
  <strong>A cinematic digital museum experience for India's 5,000-year artistic legacy.</strong><br/>
  Inspired by Google Arts & Culture · Built with React 19, Node.js, and MongoDB Atlas.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19-61dafb?logo=react&style=flat-square"/>
  <img src="https://img.shields.io/badge/Vite-8-646cff?logo=vite&style=flat-square"/>
  <img src="https://img.shields.io/badge/Node.js-Express-339933?logo=nodedotjs&style=flat-square"/>
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?logo=mongodb&style=flat-square"/>
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square"/>
</p>

---

## Description

**Arkana** (from *arcana* — hidden mysteries) is a premium digital heritage platform presenting India's
artistic traditions — from Indus Valley seals (2600 BCE) to contemporary folk art. It offers an
editorial museum aesthetic with WebGL animations, smooth page transitions, and a secure authentication system.

## Motivation

India's cultural heritage is vast and under-digitized. Arkana aims to make it discoverable through a
design-first web experience that treats digital artifacts with the same reverence as physical exhibits.

---

## Features

| Feature | Description |
|---------|-------------|
| 🎨 **Hero Gallery** | Parallax floating artifact images with mouse-tracking parallax |
| 🗺️ **Explore** | Interactive India map with cultural pins + AI-style chat interface + timeline slider (1000 BCE → 2024) |
| 🖼️ **Browse** | Filterable artifact grid with search, filter chips (Warli, Gond, Mughal, Chola, Rajput, Buddhist), and accordion sidebar |
| 🏺 **Cultures** | Deep-dive cultural profiles (Warli, Gond, Bhil, Pithora and more) |
| 🔍 **Identify** | Upload an artifact image for visual similarity matching |
| 📜 **Artifact Detail** | Full artifact view with metadata, provenance, 360° viewer, and related works |
| 🔐 **Authentication** | JWT + httpOnly cookie auth (register, login, logout, refresh, profile) |
| ✨ **WebGL Effects** | Three.js + custom GLSL shader liquid distortion on scroll |
| 🎬 **Page Transitions** | Custom geometric wipe + card-expand animations (zero animation library dependencies) |
| 🖱️ **Custom Cursor** | Circular "READ" cursor activates on all article cards |
| 📱 **Responsive** | Mobile-first with Tailwind CSS breakpoints |

---

## Screenshots

> _Full screenshots to be added after deployment_

| Home | Browse | Identify |
|------|--------|----------|
| Hero with parallax floating artifacts | Filterable grid with sidebar | Upload + similarity matching |

---

## Tech Stack

### Frontend
| Tech | Version | Purpose |
|------|---------|---------|
| React | 19.2 | UI framework |
| Vite | 8.1 | Build tool & dev server |
| React Router DOM | 7.18 | Client-side routing |
| Three.js | 0.185 | WebGL / GLSL animations |
| GSAP | 3.15 | Animation (liquid image entry) |
| Tailwind CSS | CDN | Layout utility classes |
| Inter + Playfair Display | Google Fonts | Typography |
| Material Symbols | Google Fonts Icons | Icon set |

### Backend
| Tech | Version | Purpose |
|------|---------|---------|
| Node.js | LTS | Server runtime |
| Express | 4.21 | REST API framework |
| Mongoose | 8.12 | MongoDB ODM |
| bcryptjs | 2.4 | Password hashing (12 rounds) |
| jsonwebtoken | 9.0 | JWT generation & verification |
| cookie-parser | 1.4 | Cookie handling |
| dotenv | 16.4 | Environment config |

### Database
- **MongoDB Atlas** — Cloud-hosted MongoDB (M0 free tier compatible)

---

## Architecture Overview

```
Browser → Vite Dev Server (port 5173) → /api/* proxy → Express (port 5000) → MongoDB Atlas
```

The frontend is a React SPA. All API calls use relative paths (`/api/...`) which Vite proxies to the
Express backend in development. In production, a reverse proxy (Nginx / Vercel rewrites) handles this.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for full system diagrams.

---

## Folder Structure

```
arkana-react/
├── src/
│   ├── assets/             ← Local images (kailasa_bg.png)
│   ├── components/         ← 11 shared React components
│   ├── data/
│   │   └── artifacts.js    ← Static artifact & culture data (9 exports)
│   ├── pages/              ← 8 page components
│   ├── App.jsx             ← Route table + context providers
│   ├── index.css           ← Global styles & CSS design tokens
│   └── main.jsx            ← React entry point
├── backend/
│   ├── controllers/        ← Route handler logic
│   ├── db/                 ← MongoDB connection
│   ├── middleware/         ← JWT auth guard
│   ├── models/             ← Mongoose schemas
│   ├── routes/             ← Express route definitions
│   ├── app.js              ← Express app setup
│   ├── constants.js        ← Shared constants
│   ├── index.js            ← Server entry point
│   └── package.json
├── public/                 ← Static assets (favicon, icons)
├── index.html              ← Vite HTML entry (Tailwind CDN, Google Fonts)
├── vite.config.js          ← Vite config + /api proxy
└── package.json
```

See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for a complete file-by-file breakdown.

---

## Installation

### Prerequisites
- **Node.js** 18+ (LTS recommended)
- **npm** 9+
- **MongoDB Atlas** account (free M0 tier)
- **Git**

### Clone the Repository
```bash
git clone https://github.com/Lola381/Arkana.git
cd Arkana/arkana-react
```

---

## Backend Setup

```bash
cd backend
npm install
```

Copy the environment template and fill in your values:
```bash
cp .env.example .env
# Then edit backend/.env with your MongoDB URI and strong JWT secrets
```

---

## Frontend Setup

```bash
# From arkana-react/
npm install
```

---

## Environment Variables

### Backend — `backend/.env`

| Variable | Description |
|----------|-------------|
| `PORT` | Express server port (default: 5000) |
| `MONGODB_URI` | MongoDB Atlas connection string |
| `DATABASE_NAME` | Database name (default: arkana) |
| `ACCESS_TOKEN_SECRET` | 64-byte random hex string for JWT signing |
| `ACCESS_TOKEN_EXPIRY` | Access token lifetime (e.g., `1d`) |
| `REFRESH_TOKEN_SECRET` | Different 64-byte random hex string |
| `REFRESH_TOKEN_EXPIRY` | Refresh token lifetime (e.g., `7d`) |
| `CORS_ORIGIN` | Comma-separated allowed frontend origins |

See [`.env.example`](./.env.example) for a safe template.

> ⚠️ **Never commit `.env` files. They are gitignored.**

Generate strong JWT secrets:
```bash
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
```

---

## Running Locally

Open **two terminal windows**:

**Terminal 1 — Backend:**
```bash
cd backend
npm run dev
# ✓ Server is running on http://localhost:5000
# ✓ MongoDB connected. Host: arkana-cluster.csv6ioe.mongodb.net
```

**Terminal 2 — Frontend:**
```bash
# From arkana-react/
npm run dev
# → http://localhost:5173
```

Both must run simultaneously for full functionality.

---

## Build Instructions

```bash
# Build frontend for production
npm run build
# Output: dist/

# Run backend in production mode
cd backend
npm start
```

---

## Deployment

| Component | Recommended Platform | Notes |
|-----------|---------------------|-------|
| Frontend | Vercel / Netlify | Deploy `dist/` folder |
| Backend | Render / Railway / Fly.io | Set env vars in platform dashboard |
| Database | MongoDB Atlas | Already cloud-hosted |

### Production Checklist
- [ ] Set `secure: true` in `backend/constants.js` (requires HTTPS)
- [ ] Use cryptographically strong JWT secrets
- [ ] Set `CORS_ORIGIN` to your production frontend domain
- [ ] Add Nginx rewrite rule or Vercel proxy for `/api/*` → backend URL

---

## Authentication

Arkana uses a **JWT dual-token (access + refresh) pattern**:

1. **Register / Login** → Server issues `accessToken` (1d) and `refreshToken` (7d) as `httpOnly` cookies
2. **Protected requests** → Cookie is sent automatically; `verifyJWT` middleware validates
3. **Token expiry** → Client calls `POST /api/auth/refresh-token` to silently rotate tokens
4. **Logout** → Server clears cookies and removes `refreshToken` from MongoDB

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full sequence diagram.

---

## API Documentation

See [API.md](./API.md) for complete endpoint documentation.

**Base URL:** `http://localhost:5000/api`

| Method | Endpoint | Auth Required | Description |
|--------|----------|:---:|-------------|
| POST | `/auth/register` | — | Create new account |
| POST | `/auth/login` | — | Login and receive JWT cookies |
| POST | `/auth/logout` | ✅ | Clear session and revoke token |
| POST | `/auth/refresh-token` | — | Rotate access token |
| GET | `/auth/profile` | ✅ | Get current user profile |
| GET | `/health` | — | Server health check |

---

## Database Collections

### `users`
| Field | Type | Description |
|-------|------|-------------|
| `_id` | ObjectId | Auto-generated primary key |
| `name` | String | User display name |
| `email` | String | Unique email (lowercase) |
| `password` | String | bcrypt hash — never returned in responses |
| `refreshToken` | String | Current refresh JWT; `null` after logout |
| `createdAt` | Date | Auto-timestamp |
| `updatedAt` | Date | Auto-timestamp |

> **Note:** All artifact data currently lives in `src/data/artifacts.js` (static). A MongoDB `artifacts` collection is planned.

---

## Future Improvements

- [ ] **Artifact API** — `GET /api/artifacts`, `GET /api/artifacts/:id` with MongoDB collection
- [ ] **Dynamic routing** — `/artifact/:id` and `/culture/:id` data-driven pages
- [ ] **AI Identify** — Integrate vision AI model for real artifact recognition
- [ ] **Image upload** — Cloudinary/S3 for user-submitted artifact images
- [ ] **Admin panel** — Content management for curators
- [ ] **TypeScript** — Full type safety across frontend and backend
- [ ] **Testing** — Vitest unit tests + Playwright E2E tests
- [ ] **Docker** — `docker-compose.yml` for local development
- [ ] **GitHub Actions** — CI/CD pipeline for lint, build, and deploy
- [ ] **Helmet.js** — HTTP security headers
- [ ] **Rate limiting** — Brute-force protection on auth endpoints
- [ ] **Error boundaries** — Prevent full-app crash on component errors
- [ ] **Tailwind via npm** — Replace CDN with tree-shaken PostCSS build

---

## Contributors

| Name | Student ID | Role |
|------|-----------|------|
| Nilesh Gupta | 2547138 | Full-stack Developer |
| Abhishek Singh | 2547103 | Full-stack Developer |

---

## License

MIT License — open for academic and educational use.

---

*ARKANA — Unlocking the secrets of Indian heritage.*
