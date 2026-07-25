# ARKANA — API Documentation

**Base URL:** `http://localhost:5000/api`  
**Content-Type:** `application/json`  
**Authentication:** `httpOnly` cookie (`accessToken`) automatically sent by browser,
or `Authorization: Bearer <token>` header for programmatic access.

---

## Authentication

All protected endpoints require a valid access token. The token is issued as an `httpOnly` cookie
(`accessToken`) upon login or registration, and is automatically included in subsequent requests by
the browser. For programmatic access (e.g., from a mobile app or Postman), include the token in
the `Authorization` header:

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. Register

**`POST /auth/register`**

Creates a new user account. On success, sets `httpOnly` session cookies and returns the access token.

**Authentication Required:** No

**Request Body:**
```json
{
  "name":     "string — required",
  "email":    "string — required, must be unique",
  "password": "string — required, minimum 6 characters"
}
```

**Validation Rules:**
- All three fields must be non-empty after trimming
- Email is stored in lowercase
- Password is hashed with bcryptjs (12 rounds) before storage

**Success — `201 Created`:**
```json
{
  "message": "User registered successfully",
  "token":   "<JWT access token — 1 day expiry>",
  "user": {
    "name":  "Nilesh Gupta",
    "email": "nilesh@example.com"
  }
}
```

**Cookies Set:**
| Cookie | Value | Options |
|--------|-------|---------|
| `accessToken` | JWT (1 day) | `httpOnly`, `sameSite: lax` |
| `refreshToken` | JWT (7 days) | `httpOnly`, `sameSite: lax` |

**Error Responses:**
| Status | Body | Condition |
|--------|------|-----------|
| `400` | `{ "message": "Please fill in all fields" }` | Any field empty/missing |
| `409` | `{ "message": "Email address already registered" }` | Duplicate email |
| `500` | `{ "message": "Error creating account", "error": "..." }` | Server/DB error |

---

### 2. Login

**`POST /auth/login`**

Authenticates an existing user. On success, sets `httpOnly` session cookies and returns the access token.

**Authentication Required:** No

**Request Body:**
```json
{
  "email":    "string — required",
  "password": "string — required"
}
```

**Success — `200 OK`:**
```json
{
  "message": "Login successful",
  "token":   "<JWT access token — 1 day expiry>",
  "user": {
    "name":  "Nilesh Gupta",
    "email": "nilesh@example.com"
  }
}
```

**Cookies Set:**
| Cookie | Value | Options |
|--------|-------|---------|
| `accessToken` | JWT (1 day) | `httpOnly`, `sameSite: lax` |
| `refreshToken` | JWT (7 days) | `httpOnly`, `sameSite: lax` |

**Error Responses:**
| Status | Body | Condition |
|--------|------|-----------|
| `400` | `{ "message": "Please enter both email and password" }` | Missing field |
| `401` | `{ "message": "Invalid email or password" }` | Wrong email or password |
| `500` | `{ "message": "Server error", "error": "..." }` | Server/DB error |

---

### 3. Logout

**`POST /auth/logout`**

Clears the user's session by removing cookies and revoking the refresh token in the database.

**Authentication Required:** ✅ Yes — valid `accessToken` cookie or Bearer token

**Request Body:** None

**Success — `200 OK`:**
```json
{ "message": "Logged out successfully" }
```

**Cookies Cleared:** `accessToken`, `refreshToken`

**Side Effects:** Sets `refreshToken = null` in the user's MongoDB document via `$unset`.

**Error Responses:**
| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{ "message": "Unauthorized — no token provided" }` | No token in cookie or header |
| `401` | `{ "message": "Access token expired" }` | Token expired |
| `401` | `{ "message": "Invalid access token" }` | Tampered or invalid token |
| `500` | `{ "message": "Server error" }` | DB error |

---

### 4. Refresh Access Token

**`POST /auth/refresh-token`**

Rotates the access token using the refresh token. Both tokens are replaced (refresh token rotation).

**Authentication Required:** No (uses refresh token cookie)

**Request Body (optional — used if cookies are not available):**
```json
{ "refreshToken": "<refresh JWT>" }
```

**Token Priority:** Reads `refreshToken` from `req.cookies?.refreshToken` first, then `req.body?.refreshToken`.

**Success — `200 OK`:**
```json
{
  "message": "Access token refreshed",
  "token":   "<new JWT access token>"
}
```

**Cookies Updated:**
| Cookie | New Value |
|--------|-----------|
| `accessToken` | New JWT (1 day) |
| `refreshToken` | New JWT (7 days) — old one is revoked |

**Security Notes:**
- The incoming refresh token is verified against the stored value in MongoDB
- If they don't match, request is rejected (detects stolen/replayed tokens)
- New refresh token is saved to MongoDB, invalidating the old one

**Error Responses:**
| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{ "message": "No refresh token provided" }` | No refresh token found |
| `401` | `{ "message": "Refresh token is invalid or expired" }` | Bad or expired token |

---

### 5. Get Profile

**`GET /auth/profile`**

Returns the authenticated user's profile information.

**Authentication Required:** ✅ Yes — valid `accessToken` cookie or Bearer token

**Request Body:** None

**Success — `200 OK`:**
```json
{
  "user": {
    "_id":   "64f8a2b3c4d5e6f7a8b9c0d1",
    "name":  "Nilesh Gupta",
    "email": "nilesh@example.com"
  }
}
```

**Security Note:** Password and `refreshToken` are explicitly excluded using Mongoose's `.select('-password -refreshToken')`.

**Error Responses:**
| Status | Body | Condition |
|--------|------|-----------|
| `401` | `{ "message": "Unauthorized — no token provided" }` | No token |
| `401` | `{ "message": "Unauthorized — user not found" }` | Token valid but user deleted |
| `401` | `{ "message": "Access token expired" }` | Expired token |
| `401` | `{ "message": "Invalid access token" }` | Tampered token |

---

### 6. Health Check

**`GET /health`**

Verifies the server is running. Useful for deployment health probes and uptime monitoring.

**Authentication Required:** No

**Success — `200 OK`:**
```json
{
  "status":    "ok",
  "timestamp": "2026-07-11T04:00:00.000Z"
}
```

---

## JWT Token Structure

### Access Token Payload
```json
{
  "_id":   "64f8a2b3c4d5e6f7a8b9c0d1",
  "email": "nilesh@example.com",
  "name":  "Nilesh Gupta",
  "iat":   1720666200,
  "exp":   1720752600
}
```

### Refresh Token Payload
```json
{
  "_id": "64f8a2b3c4d5e6f7a8b9c0d1",
  "iat": 1720666200,
  "exp": 1721271000
}
```

---

## Error Format

All error responses follow this consistent format:
```json
{
  "message": "Human-readable error description",
  "error":   "Technical detail (only on 500 errors)"
}
```

---

## Testing with curl

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"secret123"}' \
  -c cookies.txt

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"secret123"}' \
  -c cookies.txt

# Get Profile (uses saved cookies)
curl http://localhost:5000/api/auth/profile -b cookies.txt

# Refresh Token
curl -X POST http://localhost:5000/api/auth/refresh-token -b cookies.txt -c cookies.txt

# Logout
curl -X POST http://localhost:5000/api/auth/logout -b cookies.txt

# Health Check
curl http://localhost:5000/api/health
```

---

## Planned Future Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/artifacts` | List all artifacts (pagination, filters) |
| `GET` | `/artifacts/:id` | Get single artifact by ID |
| `POST` | `/artifacts` | Create artifact (admin) |
| `PUT` | `/artifacts/:id` | Update artifact (admin) |
| `DELETE` | `/artifacts/:id` | Delete artifact (admin) |
| `GET` | `/cultures` | List all culture profiles |
| `GET` | `/cultures/:id` | Get single culture profile |
| `POST` | `/identify` | Upload image, return similar artifacts |
