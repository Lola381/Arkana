const express = require("express");
const cors = require("cors");
const cookieParser = require("cookie-parser");

const app = express();

// ── Core middleware ────────────────────────────────────────────────────
app.use(
  cors({
    origin: process.env.CORS_ORIGIN?.split(",") || "http://localhost:5173",
    credentials: true,
  })
);
app.use(express.json({ limit: "16kb" }));
app.use(express.urlencoded({ extended: true, limit: "16kb" }));
app.use(cookieParser());

// ── Routes ─────────────────────────────────────────────────────────────
const authRoutes = require("./routes/auth.routes");
app.use("/api/auth", authRoutes);

// ── Health check ───────────────────────────────────────────────────────
app.get("/api/health", (req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

module.exports = app;
