# ARKANA — Project Structure

A complete file-by-file breakdown of every folder and significant file in the project.

---

## Repository Root (`d:\SPD2\`)

This is the parent git repository (`github.com/Lola381/Arkana`).

```
d:\SPD2\
├── .env.example               ← Example environment variables
├── .gitignore                 ← Git ignore rules
├── .oxlintrc.json             ← Oxlint configuration
├── CHANGELOG.md               ← Version history
├── CONTRIBUTING.md            ← Contribution guidelines
├── PROJECT_STRUCTURE.md       ← This file
├── README.md                  ← Main project landing page & documentation
├── package.json               ← Main Node.js/React project dependencies
├── package-lock.json          ← Dependency lockfile
├── vite.config.js             ← Vite configuration for React build
├── index.html                 ← Entry HTML for React application
│
├── src/                       ← MAIN REACT FRONTEND APPLICATION
│   ├── App.jsx                ← Main React router & provider wrapper
│   ├── index.css              ← Global CSS (Tailwind + custom animations)
│   ├── main.jsx               ← React DOM entry point
│   ├── components/            ← Reusable UI components (Nav, Cards, Modals, Overlays)
│   ├── data/                  ← Dummy data (artifacts.js, chatResponses.js)
│   ├── pages/                 ← Main route pages (Home, Browse, Explore, Culture, etc.)
│   ├── hooks/                 ← Custom React hooks
│   └── assets/                ← Static images & icons
│
├── backend/                   ← MAIN NODE.JS EXPRESS BACKEND (Auth Server)
│   ├── index.js               ← Server entry point
│   ├── app.js                 ← Express app & middleware setup
│   ├── constants.js           ← Backend constants
│   ├── package.json           ← Backend dependencies
│   ├── controllers/           ← Route logic (auth.controller.js)
│   ├── db/                    ← MongoDB connection setup
│   ├── middleware/            ← Express middleware (auth.middleware.js)
│   ├── models/                ← Mongoose schemas (user.model.js)
│   └── routes/                ← API routing (auth.routes.js)
│
├── ai/                        ← MAIN PYTHON FASTAPI AI BACKEND (Echolore)
│   ├── ai/                    
│   │   ├── FUTURE_WORK.md     ← AI Integration roadmap & next steps
│   │   ├── PRESENT_WORK.md    ← Current AI architecture & active data pipelines
│   │   ├── pipeline.py        ← Unified AI orchestration pipeline
│   │   ├── verify_models.py   ← Verification script for models
│   │   ├── backend/           ← API routes & server
│   │   ├── chunking/          ← Text chunking logic
│   │   ├── embedding/         ← Vectorization & db indexing
│   │   ├── evaluation/        ← RAG evaluation
│   │   ├── generation/        ← LLM inference & prompts
│   │   ├── ner/               ← Named entity recognition
│   │   ├── reranking/         ← Cross-encoder reranking
│   │   └── visual/            ← Visual similarity logic (CLIP)
│
├── docs/                      ← PROJECT DOCUMENTATION
│   ├── frontend/              
│   │   └── FRONTEND_MASTER.md ← Master React UI & Node.js API architecture docs
│   ├── architecture/          ← AI & Backend architecture deep dives
│   ├── integration/           ← Integration reports
│   └── LEGACY_ARCHIVE/        ← Old reports & historical documents
│
├── public/                    ← Public static assets
│   ├── favicon.svg            
│   └── icons.svg              
│
├── [Legacy/Archived Prototypes & Data]
│   ├── arkana/                ← Legacy vanilla HTML/JS/CSS prototype
│   ├── arkana_implementation_plan.html
│   ├── heritage_editorial/    ← Old design system specs
│   ├── *_arkana/              ← Legacy HTML prototype pages
│   ├── *.avif / *.mp4         ← Legacy media assets
│   ├── cardanimations.txt / trans.txt
│   ├── server.py / mongodb.py ← Dead python scripts
│   └── ai.zip                 ← Backup zip
```

---

## Active Application Details

### Frontend (`src/`)
- Uses React 19 + Vite.
- Styling via Tailwind CSS + Custom CSS (`index.css`) for complex animations (GSAP, Three.js).
- Routing handled by React Router DOM.
- Currently heavily reliant on mocked data in `src/data/`, awaiting integration with the AI FastAPI service.

### Node.js Auth Backend (`backend/`)
- Express server running on port 5000.
- Handles user registration, login, and JWT token rotation.
- Connected to MongoDB Atlas.

### AI RAG Backend (`ai/`)
- Python FastAPI server handling the complex semantic search and generative AI features.
- Interacts with a Qdrant Vector database and PostgreSQL (PostGIS) database.
- Uses `llama-3.1-8b-instant` via Groq for AI RAG Generation.
