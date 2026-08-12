require("dotenv").config();
const connectDB = require("./db");
const app = require("./app");

const PORT = process.env.PORT || 5000;

connectDB()
  .then(() => {
    app.listen(PORT, () => {
      console.log(`\n✓ Server is running on http://localhost:${PORT}`);
    });
  })
  .catch((err) => {
    console.error("✗ Failed to start server:", err);
    process.exit(1);
  });
