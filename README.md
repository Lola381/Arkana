# 🏛️ ARKANA — Indian Cultural Heritage & AI Exploration Platform

<p align="center">
  <img src="public/favicon.svg" width="80" alt="ARKANA Logo"/>
</p>

<p align="center">
  <strong>A cinematic digital museum & AI-powered exploration platform for India's 5,000-year artistic legacy.</strong><br/>
  Inspired by Google Arts &amp; Culture · Built with React 19, Leaflet, Node.js/Express, and MongoDB Atlas.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-19.2-61dafb?logo=react&style=flat-square" alt="React 19"/>
  <img src="https://img.shields.io/badge/Vite-8.1-646cff?logo=vite&style=flat-square" alt="Vite 8"/>
  <img src="https://img.shields.io/badge/Leaflet-1.9-199900?logo=leaflet&style=flat-square" alt="Leaflet"/>
  <img src="https://img.shields.io/badge/Node.js-Express_4.21-339933?logo=nodedotjs&style=flat-square" alt="Node.js"/>
  <img src="https://img.shields.io/badge/server.py-Legacy_Flask-lightgrey?logo=python&style=flat-square" alt="Legacy"/>
  <img src="https://img.shields.io/badge/MongoDB-Atlas_8.12-47A248?logo=mongodb&style=flat-square" alt="MongoDB"/>
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License"/>
</p>

---

## 📌 Project Overview

**ARKANA** (derived from *arcana* — sacred mysteries) is an editorial digital museum and AI-driven spatial exploration platform designed to preserve, digitize, and interactively present India's cultural heritage. Spanning from the Indus Valley Civilisation (2600 BCE) to modern living tribal traditions (Warli, Gond, Bhil, Pithora), ARKANA treats digital artifacts with the reverence of physical museum exhibits while offering interactive WebGL visuals, multi-filter archive browsing, and AI-guided GIS mapping.

---

## 🏗️ System Architecture

```
                                  ┌────────────────────────┐
                                  │      Client Browser    │
                                  │  React 19 SPA (Vite)   │
                                  │  http://localhost:5173 │
                                  └───────────┬────────────┘
                                              │
                                       /api/* Vite Proxy
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │     Backend API        │
                                  │   (Port 5000)          │
                                  ├────────────────────────┤
                                  │ Node.js/Express OR     │
                                  │ Python Flask           │
                                  └───────────┬────────────┘
                                              │
                                     Mongoose / PyMongo
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │   MongoDB Atlas Cloud  │
                                  │   Database: `arkana`   │
                                  └────────────────────────┘
```

---

## ⚡ Tech Stack & Tools

### Frontend
| Framework / Tool | Version | Purpose |
| :--- | :--- | :--- |
| **React** | `19.2.7` | User Interface Component Framework |
| **Vite** | `8.1.0` | Next-generation Frontend Build Tool & Dev Server |
| **React Router DOM** | `7.18.0` | Client-side SPA Routing & Navigation |
| **Leaflet / React-Leaflet** | `1.9.4` / `5.0.0` | Interactive Map Rendering & GeoJSON Polygon Layers |
| **Three.js** | `0.185.0` | WebGL Shader & 3D Interactive Viewer |
| **GSAP** | `3.15.0` | Smooth Animation & Liquid Image Transitions |
| **Tailwind CSS** | CDN / Utility | Layout & Utility Styling |

### Backend
| Technology | Stack | Key Packages / Modules |
| :--- | :--- | :--- |
| **Node.js + Express** | Canonical backend | `express` (4.21), `mongoose` (8.12), `jsonwebtoken` (9.0), `bcryptjs` (2.4), `cookie-parser` (1.4), `dotenv` |
| ~~Python Flask (`server.py`)~~ | **Legacy — do not use** | Superseded by the Node.js backend. Kept for historical reference only. |

### Database
* **MongoDB Atlas**: Cloud-hosted NoSQL cluster (`arkana-cluster.csv6ioe.mongodb.net`, DB: `arkana`).

---

## 📂 Folder Structure

```
arkana-react/
├── backend/                   # Node.js + Express REST API Server
│   ├── controllers/           # Auth controllers (register, login, logout, refresh, profile)
│   ├── db/                    # MongoDB Mongoose connection handler
│   ├── middleware/            # JWT authentication guard middleware
│   ├── models/                # Mongoose User model schema
│   ├── routes/                # Express auth route definitions (/api/auth)
│   ├── app.js                 # Express core application configuration
│   ├── index.js               # Node backend server entry point (Port 5000)
│   └── package.json
├── src/                       # React 19 Application Source
│   ├── assets/                # Background images & visual assets
│   ├── components/            # Reusable UI components
│   │   ├── ArticleCard.jsx    # Universal card with hover zoom & custom cursor trigger
│   │   ├── CardModal.jsx      # photography-style card expand modal with 3D tilt
│   │   ├── CardModalContext.jsx# React Context for expanded card state
│   │   ├── GlobalCursor.jsx   # Custom circular "READ" cursor follower
│   │   ├── Navbar.jsx         # Navigation bar (Desktop & Mobile drawer)
│   │   └── TransitionContext.jsx # Page transition manager
│   ├── data/
│   │   ├── artifacts.js       # Complete collection dataset with metadata & filters
│   │   └── chatResponses.js   # Knowledge base for Ask Arkana AI & map GeoJSON
│   ├── pages/
│   │   ├── Home.jsx           # Editorial hero section & floating parallax gallery
│   │   ├── Browse.jsx         # Multi-filter search & collection archive grid
│   │   ├── Culture.jsx        # Cultural deep-dive profile (Warli, Gond, Bhil)
│   │   ├── AskArkana.jsx      # AI Map Chat & Interactive Leaflet GeoJSON viewer
│   │   ├── Identify.jsx       # Visual artifact identifier & similarity matcher
│   │   ├── ArtifactDetail.jsx # Deep artifact metadata, 360 viewer & related works
│   │   ├── Login.jsx          # Secure sign-in form with clip-reveal animation
│   │   └── Register.jsx       # User registration form with clip-reveal animation
│   ├── App.jsx                # Main route table & provider wrapper
│   ├── main.jsx               # React DOM root mounting
│   └── index.css              # Global design tokens, keyframes, & custom CSS
├── server.py                  # [LEGACY] Python Flask server — superseded by backend/ (Node.js)
├── mongodb.py                 # [LEGACY] PyMongo connection test script
├── vite.config.js             # Vite configuration with /api proxy to 5000
└── package.json
```

---

## 🚀 Installation & Setup

### Running Backend (Port 5000)

```bash
cd backend
npm install
npm run dev
```

### Running Frontend (Port 5173)

```bash
npm install
npm run dev
```

---

## 🔑 API Reference

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new user account | No |
| `POST` | `/api/auth/login` | Authenticate user & receive JWT | No |
| `GET` | `/api/auth/profile` | Retrieve current user profile | Yes (Bearer Token) |

---

## 📄 License

MIT License © 2026 ARKANA
