import { mkdir, rm } from "node:fs/promises";
import { createServer } from "node:net";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn, spawnSync } from "node:child_process";

import { chromium } from "playwright";

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, "..");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const devCommand = process.platform === "win32" ? "cmd.exe" : npmCommand;

const ROUTES = ["/", "/mobile/", "/devices/", "/telegram/", "/youtube/", "/tiktok/", "/vpn/"];
const VIEWPORTS = [
  { name: "mobile", width: 390, height: 844 },
  { name: "tablet", width: 700, height: 900 },
  { name: "desktop", width: 1180, height: 820 },
];

function findFreePort(start = 3210) {
  return new Promise((resolve, reject) => {
    let port = start;

    function tryPort() {
      const server = createServer();
      server.once("error", (error) => {
        if (error.code === "EADDRINUSE") {
          port += 1;
          tryPort();
          return;
        }
        reject(error);
      });
      server.once("listening", () => {
        server.close(() => resolve(port));
      });
      server.listen(port, "127.0.0.1");
    }

    tryPort();
  });
}

async function waitForServer(baseUrl, timeoutMs = 45_000) {
  const startedAt = Date.now();
  let lastError = "";

  while (Date.now() - startedAt < timeoutMs) {
    try {
      const response = await fetch(baseUrl, { cache: "no-store" });
      if (response.status >= 200 && response.status < 500) return;
      lastError = `HTTP ${response.status}`;
    } catch (error) {
      lastError = String(error?.message || error);
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }

  throw new Error(`Marketing server did not become ready at ${baseUrl}: ${lastError}`);
}

function normalizeRouteName(route) {
  return route === "/" ? "home" : route.replaceAll("/", "-").replace(/^-|-$/g, "");
}

function relevantConsoleMessage(message) {
  const text = message.text();
  if (text.includes("Download the React DevTools")) return false;
  if (text.includes("Fast Refresh")) return false;
  if (text.includes("Failed to load resource: net::ERR_FAILED")) return false;
  return message.type() === "error";
}

function stopServer(server) {
  if (server.killed) return;
  if (process.platform === "win32" && server.pid) {
    spawnSync("taskkill", ["/pid", String(server.pid), "/T", "/F"], { stdio: "ignore" });
    return;
  }
  server.kill();
}

async function run() {
  const port = await findFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const artifactDir = join(projectRoot, `..`, `.tmp-marketing-responsive-${Date.now()}`);
  await mkdir(artifactDir, { recursive: true });

  const serverArgs =
    process.platform === "win32"
      ? ["/d", "/s", "/c", `${npmCommand} run dev -- -p ${port}`]
      : ["run", "dev", "--", "-p", String(port)];

  const server = spawn(devCommand, serverArgs, {
    cwd: projectRoot,
    env: { ...process.env, NEXT_PUBLIC_DISABLE_FUNNEL: "1", PORT: String(port) },
    stdio: ["ignore", "pipe", "pipe"],
  });

  let serverOutput = "";
  server.stdout.on("data", (chunk) => {
    serverOutput += chunk.toString();
  });
  server.stderr.on("data", (chunk) => {
    serverOutput += chunk.toString();
  });

  let browser;
  const failures = [];

  try {
    await waitForServer(baseUrl);
    browser = await chromium.launch({ headless: true });

    for (const viewport of VIEWPORTS) {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
        deviceScaleFactor: 1,
      });

      for (const route of ROUTES) {
        const page = await context.newPage();
        const consoleIssues = [];
        page.on("console", (message) => {
          if (relevantConsoleMessage(message)) {
            consoleIssues.push(`${message.type()}: ${message.text()}`);
          }
        });

        const url = `${baseUrl}${route}`;
        const routeName = normalizeRouteName(route);

        try {
          const response = await page.goto(url, { waitUntil: "domcontentloaded", timeout: 20_000 });
          await page.screenshot({
            path: join(artifactDir, `${viewport.name}-${routeName}.png`),
            fullPage: false,
          });

          const result = await page.evaluate(() => {
            const root = document.documentElement;
            const bodyText = document.body?.innerText || "";
            const overlay = Boolean(document.querySelector("[data-nextjs-dialog-overlay], nextjs-portal"));
            return {
              title: document.title,
              bodyLength: bodyText.trim().length,
              hasBrand: bodyText.includes("POKROV"),
              hasPrimaryCta: Boolean(
                document.querySelector("a.lp-btn--primary, a.btn--primary, a[href*='/install'], a[href*='/checkout']")
              ),
              scrollWidth: root.scrollWidth,
              clientWidth: root.clientWidth,
              overlay,
            };
          });

          if (!response || response.status() >= 500) {
            failures.push(`${viewport.name} ${route}: bad status ${response?.status() ?? "missing"}`);
          }
          if (!result.hasBrand || result.bodyLength < 400) {
            failures.push(`${viewport.name} ${route}: blank or missing brand`);
          }
          if (!result.hasPrimaryCta) {
            failures.push(`${viewport.name} ${route}: missing primary CTA`);
          }
          if (result.overlay) {
            failures.push(`${viewport.name} ${route}: framework overlay visible`);
          }
          if (result.scrollWidth > result.clientWidth + 1) {
            failures.push(`${viewport.name} ${route}: horizontal overflow ${result.scrollWidth}/${result.clientWidth}`);
          }
          if (consoleIssues.length) {
            failures.push(`${viewport.name} ${route}: console ${consoleIssues.join(" | ")}`);
          }
        } catch (error) {
          failures.push(`${viewport.name} ${route}: ${String(error?.message || error)}`);
        } finally {
          await page.close().catch(() => {});
        }
      }

      await context.close();
    }
  } finally {
    if (browser) await browser.close().catch(() => {});
    stopServer(server);
  }

  if (failures.length) {
    console.error("Marketing responsive checks failed:");
    for (const failure of failures) console.error(`- ${failure}`);
    console.error(`Screenshots: ${artifactDir}`);
    console.error(serverOutput.split("\n").slice(-20).join("\n"));
    process.exit(1);
  }

  console.log(`Marketing responsive checks passed. Screenshots: ${artifactDir}`);
  if (process.env.KEEP_MARKETING_RESPONSIVE_ARTIFACTS !== "1") {
    await rm(artifactDir, { recursive: true, force: true });
  }
}

run().catch((error) => {
  console.error(error);
  process.exit(1);
});
