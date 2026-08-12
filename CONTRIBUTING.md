# Contributing to ARKANA

Thank you for your interest in contributing to ARKANA! This guide covers everything you need
to get from a fresh clone to a running local environment and your first pull request.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Setting Up Locally](#setting-up-locally)
3. [Project Structure Quick Reference](#project-structure-quick-reference)
4. [Development Workflow](#development-workflow)
5. [Code Style Guidelines](#code-style-guidelines)
6. [Architecture Guidelines](#architecture-guidelines)
7. [Security Rules](#security-rules)
8. [Testing](#testing)
9. [Pull Request Process](#pull-request-process)
10. [Common Tasks](#common-tasks)

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Node.js | 18+ LTS | Use [nvm](https://github.com/nvm-sh/nvm) or [fnm](https://github.com/Schniz/fnm) |
| npm | 9+ | Included with Node.js |
| Git | Any recent | — |
| MongoDB Atlas | Free M0 | [Create account](https://cloud.mongodb.com/) |

---

## Setting Up Locally

### 1. Fork and Clone

```bash
# Fork the repo on GitHub first, then:
git clone https://github.com/<your-username>/Arkana.git
cd Arkana/arkana-react
```

### 2. Install Frontend Dependencies

```bash
# From arkana-react/
npm install
```

### 3. Install Backend Dependencies

```bash
cd backend
npm install
```

### 4. Configure Environment Variables

```bash
# Copy the safe template
cp .env.example backend/.env

# Open backend/.env and fill in:
# - Your MongoDB Atlas connection string
# - Strong random JWT secrets (see command below)
```

**Generate cryptographically strong JWT secrets:**
```bash
node -e "console.log(require('crypto').randomBytes(64).toString('hex'))"
# Run this TWICE — once for ACCESS_TOKEN_SECRET, once for REFRESH_TOKEN_SECRET
```

**Get your MongoDB Atlas connection string:**
1. Log in to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Click your cluster → Connect → Drivers
3. Copy the `mongodb+srv://...` string
4. Replace `<password>` with your actual password

### 5. Verify Setup

**Terminal 1 — Start Backend:**
```bash
cd backend
npm run dev
```
Expected output:
```
✓ Server is running on http://localhost:5000
✓ MongoDB connected. Host: arkana-cluster.csv6ioe.mongodb.net
```

**Terminal 2 — Start Frontend:**
```bash
# From arkana-react/
npm run dev
```
Expected output:
```
  VITE v8.x.x  ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

Open `http://localhost:5173` in your browser. You should see the ARKANA home page.

---

## Project Structure Quick Reference

```
arkana-react/
├── src/
│   ├── components/    ← 11 shared React components
│   ├── data/          ← artifacts.js (static data — all artifact/culture content)
│   ├── pages/         ← 8 page components (one per route)
│   ├── assets/        ← Local images
│   ├── App.jsx        ← Routes + context providers
│   ├── index.css      ← Design tokens + animation classes
│   └── main.jsx       ← React entry point
└── backend/
    ├── controllers/   ← Route handler logic
    ├── db/            ← MongoDB connection
    ├── middleware/    ← JWT auth guard
    ├── models/        ← Mongoose schemas
    ├── routes/        ← Express route definitions
    ├── app.js         ← Express configuration
    └── index.js       ← Server entry point
```

See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for a complete breakdown.

---

## Development Workflow

### Branch Strategy

Always branch from `main`:

```bash
git checkout main
git pull origin main

# Feature branches
git checkout -b feature/artifact-detail-api

# Bug fix branches
git checkout -b fix/navbar-mobile-overflow

# Documentation branches
git checkout -b docs/update-contributing
```

**Branch naming conventions:**

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<description>` | `feature/artifact-search-api` |
| Bug fix | `fix/<description>` | `fix/token-refresh-loop` |
| Documentation | `docs/<description>` | `docs/api-endpoints` |
| Refactor | `refactor/<description>` | `refactor/merge-artifact-cards` |
| Chore | `chore/<description>` | `chore/update-dependencies` |

### Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add GET /api/artifacts/:id endpoint
fix: correct refresh token validation check
docs: add curl examples to API.md
refactor: merge ArtifactCard and ArticleCard components
chore: update mongoose to 8.12.2
style: fix trailing whitespace in auth controller
test: add register endpoint unit tests
```

### Before Every Commit

```bash
# Run the linter
npm run lint

# Check for obvious issues
# - Does the backend still start? (npm run dev in backend/)
# - Does the frontend still compile? (npm run dev in arkana-react/)
# - Does login/register still work?
```

---

## Code Style Guidelines

### Frontend (React)

- **Components:** One component per file, named identically to the file
- **File naming:** PascalCase for components (`ArtifactCard.jsx`), camelCase for utilities
- **Hooks:** Only call hooks at the top level — never inside loops, conditions, or nested functions
- **State:** Prefer local `useState` for UI state; use Context only for truly global state
- **Effects:** Always return cleanup functions from `useEffect` if you add event listeners
- **Accessibility:** All interactive non-button elements must have `role`, `tabIndex`, and `onKeyDown`
- **Comments:** Write JSDoc blocks on complex components (see `LiquidImage.jsx` as a model)

```jsx
// ✅ Good — cleanup, memoized handler, accessible
const handleClick = useCallback((e) => {
  openCard(artifact, e.currentTarget);
}, [artifact, openCard]);

<article
  role="button"
  tabIndex={0}
  onKeyDown={(e) => { if (e.key === 'Enter') handleClick(e); }}
  onClick={handleClick}
>

// ❌ Avoid — full page reload, breaks React state
window.location.href = '/';

// ✅ Use instead
const navigate = useNavigate();
navigate('/');
```

### Backend (Node.js/Express)

- **Module system:** CommonJS (`require`/`module.exports`) — must match existing code
- **Controllers:** Each route handler follows the pattern: validate → query DB → respond
- **Error handling:** Always wrap async controllers in `try/catch`; never let errors bubble silently
- **Passwords:** Always use `bcryptjs` — never `md5`, `sha1`, or plaintext
- **JWT:** Always read from `req.cookies` first, then headers — never from query strings

```javascript
// ✅ Good — try/catch, specific error messages
const registerUser = async (req, res) => {
  try {
    // logic...
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ message: 'Error creating account', error: error.message });
  }
};

// ❌ Avoid — no error handling
const badHandler = async (req, res) => {
  const user = await User.create(req.body); // will crash on error
  res.json(user);
};
```

---

## Architecture Guidelines

### Adding a New Page

1. Create `src/pages/NewPage.jsx`
2. Add route to `src/App.jsx`:
   ```jsx
   <Route path="/new-page" element={<NewPage />} />
   ```
3. Import and add to Navbar if it should appear in navigation

### Adding a New API Endpoint

1. Add handler to `backend/controllers/auth.controller.js` (or create new controller)
2. Add route to `backend/routes/auth.routes.js` (or create new route file)
3. Register new route files in `backend/app.js`
4. Document the endpoint in `API.md`

### Adding New Static Data

Until the Artifacts MongoDB collection is built, add to `src/data/artifacts.js`:
```javascript
export const MY_NEW_DATA = [
  { id: 'unique-id', title: '...', ... },
];
```

### Navigation Between Pages

**Always** use `TransitionLink` (not `<a>` or `window.location.href`) for internal links:
```jsx
import { TransitionLink } from '../components/TransitionContext';

<TransitionLink to="/browse">Browse Collection</TransitionLink>
```

---

## Security Rules

> These are non-negotiable. Violations will block PRs.

- 🔴 **NEVER commit `.env` files** — they are gitignored for a reason
- 🔴 **NEVER expose JWT secrets in source code** — must come from `process.env`
- 🔴 **NEVER store passwords in plaintext** — always use `bcryptjs`
- 🟠 **NEVER accept raw `req.body` without validation** — at minimum check field presence
- 🟠 **NEVER use `Authorization: Bearer` tokens from URL query strings** — headers or cookies only
- 🟡 All new protected routes **must** use the `verifyJWT` middleware

---

## Testing

> The project currently has no tests. Adding tests is actively encouraged!

**Recommended setup:**

```bash
# Frontend unit tests
npm install -D vitest @testing-library/react @testing-library/jest-dom

# Backend unit/integration tests
cd backend
npm install -D jest supertest
```

**Testing checklist for any PR:**

1. ✅ Backend starts without errors: `npm run dev` in `backend/`
2. ✅ Frontend compiles without errors: `npm run dev` in `arkana-react/`
3. ✅ Lint passes: `npm run lint` in `arkana-react/`
4. ✅ Register flow works: create a new account end-to-end
5. ✅ Login flow works: sign in and verify user appears in Navbar
6. ✅ Logout flow works: user clears from Navbar, cookies cleared
7. ✅ Pages load without console errors

---

## Pull Request Process

1. **Push** your branch to your fork:
   ```bash
   git push origin feature/your-feature
   ```

2. **Open a Pull Request** on GitHub against `Lola381/Arkana main`

3. **PR Title:** Use Conventional Commit format: `feat: add artifact detail API`

4. **PR Description** must include:
   - What was changed and why
   - How to test the change
   - Screenshots for any UI changes
   - `Closes #<issue-number>` if applicable

5. **Checklist:**
   - [ ] Lint passes (`npm run lint`)
   - [ ] Backend starts cleanly
   - [ ] Frontend builds without errors
   - [ ] Manual smoke test of auth flow
   - [ ] No `.env` files committed
   - [ ] No hardcoded secrets

6. Request a review from a maintainer.

---

## Common Tasks

### Reset your local database (development only)

```bash
# In MongoDB Atlas → Collections → Drop the 'users' collection
# Or via mongosh:
use arkana
db.users.drop()
```

### Check what's listening on port 5000

```bash
# Windows
netstat -ano | findstr :5000

# macOS/Linux
lsof -i :5000
```

### Clear auth state in browser

```javascript
// Open browser console and run:
localStorage.removeItem('token');
localStorage.removeItem('user');
location.reload();
```

### View backend logs live

```bash
cd backend
npm run dev
# nodemon auto-restarts on file changes and streams logs to terminal
```

---

## Getting Help

- Open a GitHub Issue describing your problem
- Tag it with `question`, `bug`, or `enhancement`
- Include: Node.js version, OS, error message, and steps to reproduce
