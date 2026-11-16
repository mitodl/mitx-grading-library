const { defineConfig, devices } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./browser-tests",
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "github" : "list",
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
