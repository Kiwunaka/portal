import { defineConfig } from "@playwright/test";

const port = Number(process.env.E2E_PORT || 3100);
const reuseExistingServer = process.env.PLAYWRIGHT_FRESH_SERVER === "1" ? false : !process.env.CI;

export default defineConfig({
  testDir: "./e2e",
  testMatch: "*.spec.ts",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://localhost:${port}/`,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `npm.cmd run dev -- --port ${port}`,
    url: `http://localhost:${port}/`,
    reuseExistingServer,
    timeout: 120_000,
  },
});
