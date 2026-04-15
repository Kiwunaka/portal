import os from "node:os";
import path from "node:path";
import { defineConfig } from "@playwright/test";

const port = Number(process.env.E2E_PORT || 3100);
const reuseExistingServer = process.env.PLAYWRIGHT_FRESH_SERVER === "1" ? false : !process.env.CI;
const artifactsRoot = path.join(os.tmpdir(), "pokrov-playwright", "webapp");

export default defineConfig({
  testDir: "./e2e",
  testMatch: "*.spec.ts",
  timeout: 30_000,
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  outputDir: path.join(artifactsRoot, "test-results"),
  reporter: process.env.CI
    ? [["github"], ["html", { open: "never", outputFolder: path.join(artifactsRoot, "html-report") }]]
    : "list",
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
