const jwt = require("jsonwebtoken");
const User = require("../models/user.model");

const verifyJWT = async (req, res, next) => {
  try {
    // 1. Try cookie first, then Authorization header
    const token =
      req.cookies?.accessToken ||
      (req.header("Authorization") || "").replace("Bearer ", "");

    if (!token) {
      return res.status(401).json({ message: "Unauthorized — no token provided" });
    }

    // 2. Decode
    const decoded = jwt.verify(token, process.env.ACCESS_TOKEN_SECRET);

    // 3. Find user (exclude password and refreshToken from the result)
    const user = await User.findById(decoded._id).select("-password -refreshToken");

    if (!user) {
      return res.status(401).json({ message: "Unauthorized — user not found" });
    }

    // 4. Attach to request
    req.user = user;
    next();
  } catch (error) {
    if (error.name === "TokenExpiredError") {
      return res.status(401).json({ message: "Access token expired" });
    }
    return res.status(401).json({ message: "Invalid access token" });
  }
};

module.exports = verifyJWT;
