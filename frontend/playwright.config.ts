import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 45_000,
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "uv run uvicorn evalforge.main:app --host 127.0.0.1 --port 8000 --app-dir backend",
      cwd: "..",
      url: "http://127.0.0.1:8000/api/v1/health",
      reuseExistingServer: !process.env.CI,
      env: {
        EVALFORGE_DATABASE_URL: "sqlite:////tmp/evalforge-playwright.db",
        EVALFORGE_INLINE_JOBS: "true",
        UV_CACHE_DIR: "/tmp/evalforge-uv-cache",
      },
    },
    {
      command: "npm run dev -- --hostname 127.0.0.1 --port 3000",
      cwd: ".",
      url: "http://127.0.0.1:3000",
      reuseExistingServer: !process.env.CI,
      env: { API_URL: "http://127.0.0.1:8000", NEXT_TELEMETRY_DISABLED: "1" },
    },
  ],
});
