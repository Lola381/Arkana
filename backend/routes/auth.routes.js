const { Router } = require("express");
const {
  registerUser,
  loginUser,
  logoutUser,
  refreshAccessToken,
  getProfile,
} = require("../controllers/auth.controller");
const verifyJWT = require("../middleware/auth.middleware");

const router = Router();

// Public routes
router.post("/register", registerUser);
router.post("/login", loginUser);
router.post("/refresh-token", refreshAccessToken);

// Protected routes (require valid access token)
router.post("/logout", verifyJWT, logoutUser);
router.get("/profile", verifyJWT, getProfile);

module.exports = router;
