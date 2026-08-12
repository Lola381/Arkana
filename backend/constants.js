const DB_NAME = "arkana";

const COOKIE_OPTIONS = {
  httpOnly: true,
  secure: false, // set true in production (HTTPS)
  sameSite: "lax",
};

module.exports = { DB_NAME, COOKIE_OPTIONS };
