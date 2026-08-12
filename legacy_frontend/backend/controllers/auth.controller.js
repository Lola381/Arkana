const User = require("../models/user.model");
const jwt = require("jsonwebtoken");
const { COOKIE_OPTIONS } = require("../constants");

// ── Helper: generate both tokens and persist refresh token ─────────────
const generateAccessAndRefreshTokens = async (userId) => {
  const user = await User.findById(userId);
  const accessToken = user.generateAccessToken();
  const refreshToken = user.generateRefreshToken();

  user.refreshToken = refreshToken;
  await user.save({ validateBeforeSave: false });

  return { accessToken, refreshToken };
};

// ── REGISTER ───────────────────────────────────────────────────────────
const registerUser = async (req, res) => {
  try {
    const { name, email, password } = req.body;

    // Validate fields
    if (!name?.trim() || !email?.trim() || !password?.trim()) {
      return res.status(400).json({ message: "Please fill in all fields" });
    }

    // Check duplicate
    const existingUser = await User.findOne({ email: email.toLowerCase() });
    if (existingUser) {
      return res.status(409).json({ message: "Email address already registered" });
    }

    // Create user (password hashed by pre-save hook)
    const user = await User.create({
      name: name.trim(),
      email: email.toLowerCase().trim(),
      password,
    });

    // Generate tokens
    const { accessToken, refreshToken } = await generateAccessAndRefreshTokens(user._id);

    // Set cookies
    res
      .status(201)
      .cookie("accessToken", accessToken, { ...COOKIE_OPTIONS, maxAge: 24 * 60 * 60 * 1000 })
      .cookie("refreshToken", refreshToken, { ...COOKIE_OPTIONS, maxAge: 7 * 24 * 60 * 60 * 1000 })
      .json({
        message: "User registered successfully",
        token: accessToken,
        user: { name: user.name, email: user.email },
      });
  } catch (error) {
    console.error("Register error:", error);
    res.status(500).json({ message: "Error creating account", error: error.message });
  }
};

// ── LOGIN ──────────────────────────────────────────────────────────────
const loginUser = async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email?.trim() || !password?.trim()) {
      return res.status(400).json({ message: "Please enter both email and password" });
    }

    // Find user
    const user = await User.findOne({ email: email.toLowerCase().trim() });
    if (!user) {
      return res.status(401).json({ message: "Invalid email or password" });
    }

    // Verify password
    const isMatch = await user.isPasswordCorrect(password);
    if (!isMatch) {
      return res.status(401).json({ message: "Invalid email or password" });
    }

    // Generate tokens
    const { accessToken, refreshToken } = await generateAccessAndRefreshTokens(user._id);

    res
      .status(200)
      .cookie("accessToken", accessToken, { ...COOKIE_OPTIONS, maxAge: 24 * 60 * 60 * 1000 })
      .cookie("refreshToken", refreshToken, { ...COOKIE_OPTIONS, maxAge: 7 * 24 * 60 * 60 * 1000 })
      .json({
        message: "Login successful",
        token: accessToken,
        user: { name: user.name, email: user.email },
      });
  } catch (error) {
    console.error("Login error:", error);
    res.status(500).json({ message: "Server error", error: error.message });
  }
};

// ── LOGOUT ─────────────────────────────────────────────────────────────
const logoutUser = async (req, res) => {
  try {
    // Clear refresh token in DB
    await User.findByIdAndUpdate(req.user._id, { $unset: { refreshToken: 1 } });

    res
      .status(200)
      .clearCookie("accessToken", COOKIE_OPTIONS)
      .clearCookie("refreshToken", COOKIE_OPTIONS)
      .json({ message: "Logged out successfully" });
  } catch (error) {
    console.error("Logout error:", error);
    res.status(500).json({ message: "Server error" });
  }
};

// ── REFRESH ACCESS TOKEN ───────────────────────────────────────────────
const refreshAccessToken = async (req, res) => {
  try {
    const incomingRefreshToken = req.cookies?.refreshToken || req.body?.refreshToken;

    if (!incomingRefreshToken) {
      return res.status(401).json({ message: "No refresh token provided" });
    }

    // Verify
    const decoded = jwt.verify(incomingRefreshToken, process.env.REFRESH_TOKEN_SECRET);
    const user = await User.findById(decoded._id);

    if (!user || user.refreshToken !== incomingRefreshToken) {
      return res.status(401).json({ message: "Refresh token is invalid or expired" });
    }

    // Rotate tokens
    const { accessToken, refreshToken: newRefreshToken } =
      await generateAccessAndRefreshTokens(user._id);

    res
      .status(200)
      .cookie("accessToken", accessToken, { ...COOKIE_OPTIONS, maxAge: 24 * 60 * 60 * 1000 })
      .cookie("refreshToken", newRefreshToken, { ...COOKIE_OPTIONS, maxAge: 7 * 24 * 60 * 60 * 1000 })
      .json({
        message: "Access token refreshed",
        token: accessToken,
      });
  } catch (error) {
    console.error("Refresh error:", error);
    res.status(401).json({ message: "Invalid refresh token" });
  }
};

// ── GET PROFILE ────────────────────────────────────────────────────────
const getProfile = async (req, res) => {
  res.status(200).json({
    user: {
      _id: req.user._id,
      name: req.user.name,
      email: req.user.email,
    },
  });
};

module.exports = {
  registerUser,
  loginUser,
  logoutUser,
  refreshAccessToken,
  getProfile,
};
