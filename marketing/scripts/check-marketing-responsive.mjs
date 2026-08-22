import { mkdir, readFile, rm } from "node:fs/promises";
import { createServer } from "node:net";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawn, spawnSync } from "node:child_process";

import axe from "axe-core";
import { chromium } from "playwright";

const __dirname = dirname(fileURLToPath(import.meta.url));
const projectRoot = join(__dirname, "..");
const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
const npmShellCommand = process.platform === "win32" ? "cmd.exe" : npmCommand;
const pythonCommand = process.env.PYTHON || (process.platform === "win32" ? "python.exe" : "python3");

const ROUTES = [
  "/",
  "/mobile/",
  "/devices/",
  "/telegram/",
  "/youtube/",
  "/tiktok/",
  "/vpn/",
  "/best-vpn/",
  "/android/",
  "/windows/",
  "/install/",
  "/install/android/",
  "/install/windows/",
  "/trial/no-card/",
  "/billing/no-autosubscription/",
  "/trust/github-releases/",
  "/compare/free-vpn/",
  "/support/install/",
  "/fallback/",
];
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

async function seriousCriticalAxeViolations(page) {
  await page.addScriptTag({ content: axe.source });
  return page.evaluate(async () => {
    const results = await window.axe.run(document, { resultTypes: ["violations"] });
    return results.violations
      .filter((violation) => violation.impact === "serious" || violation.impact === "critical")
      .map((violation) => ({
        id: violation.id,
        impact: violation.impact,
        targets: violation.nodes.flatMap((node) => node.target.map(String)),
        summary: violation.nodes.map((node) => node.failureSummary),
      }));
  });
}

async function checkCheckoutRequestConcurrency(browser, baseUrl, failures) {
  const context = await browser.newContext({ viewport: { width: 1180, height: 820 } });
  const page = await context.newPage();
  const arrivals = new Map();
  const releases = [];
  let released = false;

  const hold = async (route, label) => {
    if (!arrivals.has(label)) arrivals.set(label, Date.now());
    if (!released) {
      await new Promise((resolve) => releases.push(resolve));
    }
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "deliberate concurrency probe" }),
    });
  };

  await page.route("**/api/public/catalog", (route) => hold(route, "catalog"));
  await page.route("**/api/payments/providers", (route) => hold(route, "providers"));
  await page.route("**/api/acquisition/handoffs", (route) => hold(route, "acquisition"));

  try {
    await page.goto(`${baseUrl}/checkout/`, { waitUntil: "domcontentloaded", timeout: 20_000 });
    const deadline = Date.now() + 5_000;
    while (arrivals.size < 3 && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 20));
    }
    if (arrivals.size !== 3) {
      failures.push(`checkout concurrency: expected catalog/providers/acquisition before release, got ${[...arrivals.keys()].join(",") || "none"}`);
    } else {
      const times = [...arrivals.values()];
      const spreadMs = Math.max(...times) - Math.min(...times);
      if (spreadMs >= 500) {
        failures.push(`checkout concurrency: independent request start spread ${spreadMs} ms`);
      }
    }
  } catch (error) {
    failures.push(`checkout concurrency: ${String(error?.message || error)}`);
  } finally {
    released = true;
    releases.splice(0).forEach((release) => release());
    await page.close().catch(() => {});
    await context.close().catch(() => {});
  }
}

async function run() {
  const gateEnv = { ...process.env, NEXT_PUBLIC_DISABLE_FUNNEL: "1" };
  const buildArgs =
    process.platform === "win32"
      ? ["/d", "/s", "/c", `${npmCommand} run build`]
      : ["run", "build"];
  const build = spawnSync(npmShellCommand, buildArgs, {
    cwd: projectRoot,
    env: gateEnv,
    encoding: "utf8",
  });
  if (build.status !== 0) {
    throw new Error(`Marketing production build failed:\n${build.stdout || ""}${build.stderr || ""}`);
  }

  const port = await findFreePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const artifactDir = join(projectRoot, `..`, `.tmp-marketing-responsive-${Date.now()}`);
  await mkdir(artifactDir, { recursive: true });

  const serverArgs = [
    "-m",
    "http.server",
    String(port),
    "--bind",
    "127.0.0.1",
    "--directory",
    join(projectRoot, "out"),
  ];

  const server = spawn(pythonCommand, serverArgs, {
    cwd: projectRoot,
    env: { ...gateEnv, PORT: String(port) },
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
    await checkCheckoutRequestConcurrency(browser, baseUrl, failures);

    const heroSource = await readFile(join(projectRoot, "src", "components", "home", "hero-visual.tsx"), "utf8");
    const revealSource = await readFile(join(projectRoot, "src", "components", "motion", "reveal.tsx"), "utf8");
    const motionProviderSource = await readFile(
      join(projectRoot, "src", "components", "motion", "motion-provider.tsx"),
      "utf8",
    );
    const motionComponentPaths = [
      ["src", "components", "home", "hero-visual.tsx"],
      ["src", "components", "home", "showcase-scroller.tsx"],
      ["src", "components", "install", "platform-tabs.tsx"],
      ["src", "components", "layout", "topbar.tsx"],
      ["src", "components", "ui", "accordion.tsx"],
    ];
    const motionComponentSources = await Promise.all(
      motionComponentPaths.map((parts) => readFile(join(projectRoot, ...parts), "utf8")),
    );
    if (heroSource.includes("repeat: Infinity") || !heroSource.includes("repeat: 1")) {
      failures.push("motion contract: hero decoration must finish after two cycles");
    }
    if (!revealSource.includes("Math.min(index * boundedStep, 240)")) {
      failures.push("motion contract: stagger must stay inside the 240 ms window");
    }
    if (!motionProviderSource.includes("LazyMotion") || !motionProviderSource.includes("strict")) {
      failures.push("motion bundle: strict LazyMotion provider is missing");
    }
    if (motionComponentSources.some((source) => source.includes("motion."))) {
      failures.push("motion bundle: eager motion component bypasses the LazyMotion boundary");
    }
    if (motionComponentSources.some((source) => source.includes("domMax"))) {
      failures.push("motion bundle: domMax requires a new measured layout-motion need");
    }

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
            // Next 16 dev always mounts an empty <nextjs-portal> for devtools; only
            // the error dialog overlay is a real failure signal.
            const overlay = Boolean(document.querySelector("[data-nextjs-dialog-overlay]"));
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

    const noJsContext = await browser.newContext({
      javaScriptEnabled: false,
      viewport: { width: 1180, height: 820 },
    });
    const noJsPage = await noJsContext.newPage();
    try {
      await noJsPage.goto(`${baseUrl}/`, { waitUntil: "domcontentloaded", timeout: 20_000 });
      const noJsReveal = await noJsPage.evaluate(() => {
        const nodes = Array.from(document.querySelectorAll(".reveal"));
        return {
          count: nodes.length,
          hidden: nodes.filter((node) => {
            const style = getComputedStyle(node);
            return style.opacity === "0" || style.visibility === "hidden" || style.display === "none";
          }).length,
        };
      });
      if (noJsReveal.count === 0 || noJsReveal.hidden > 0) {
        failures.push(`no-JS home: reveal content hidden ${noJsReveal.hidden}/${noJsReveal.count}`);
      }
    } finally {
      await noJsPage.close().catch(() => {});
      await noJsContext.close().catch(() => {});
    }

    const reducedContext = await browser.newContext({
      reducedMotion: "reduce",
      viewport: { width: 1180, height: 820 },
    });
    const reducedPage = await reducedContext.newPage();
    try {
      await reducedPage.goto(`${baseUrl}/`, { waitUntil: "networkidle", timeout: 20_000 });
      await reducedPage
        .waitForFunction(
          () =>
            window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
            Boolean(document.querySelector('[data-showcase-mode="static"]')),
          undefined,
          { timeout: 5_000 },
        )
        .catch(() => {});
      const reduced = await reducedPage.evaluate(() => ({
        staticShowcase: Boolean(document.querySelector('[data-showcase-mode="static"]')),
        stickyShowcase: Boolean(document.querySelector('[data-showcase-mode="sticky"]')),
        hiddenReveal: Array.from(document.querySelectorAll(".reveal")).filter(
          (node) => getComputedStyle(node).opacity === "0",
        ).length,
        spatialChip: Array.from(document.querySelectorAll('[data-floating-chip-motion="finite"]')).some(
          (node) => getComputedStyle(node).transform !== "none",
        ),
      }));
      if (!reduced.staticShowcase || reduced.stickyShowcase) {
        failures.push("reduced-motion home: showcase did not replace sticky track with static flow");
      }
      if (reduced.hiddenReveal > 0 || reduced.spatialChip) {
        failures.push("reduced-motion home: hidden reveal or spatial hero motion remains");
      }
    } finally {
      await reducedPage.close().catch(() => {});
      await reducedContext.close().catch(() => {});
    }

    const mobileControlContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const mobileControlPage = await mobileControlContext.newPage();
    try {
      await mobileControlPage.goto(`${baseUrl}/`, { waitUntil: "networkidle", timeout: 20_000 });
      const controls = await mobileControlPage.evaluate(() => ({
        previous: Boolean(document.querySelector('[aria-label="Предыдущий экран приложения"]')),
        next: Boolean(document.querySelector('[aria-label="Следующий экран приложения"]')),
        position: Array.from(document.querySelectorAll('[aria-live="polite"]')).some((node) =>
          /Экран 1 из 4/.test(node.textContent || ""),
        ),
      }));
      if (!controls.previous || !controls.next || !controls.position) {
        failures.push("mobile showcase: previous/next controls or announced position missing");
      }
    } finally {
      await mobileControlPage.close().catch(() => {});
      await mobileControlContext.close().catch(() => {});
    }

    const accessibilityContext = await browser.newContext({ viewport: { width: 1180, height: 820 } });
    const accessibilityPage = await accessibilityContext.newPage();
    try {
      for (const route of ["/", "/install/"]) {
        await accessibilityPage.goto(`${baseUrl}${route}`, { waitUntil: "networkidle", timeout: 20_000 });
        const violations = await seriousCriticalAxeViolations(accessibilityPage);
        if (violations.length) {
          failures.push(`axe ${route}: ${JSON.stringify(violations)}`);
        }
      }

      await accessibilityPage.goto(`${baseUrl}/install/`, { waitUntil: "networkidle", timeout: 20_000 });
      const androidTab = accessibilityPage.getByRole("tab", { name: "Android" });
      const windowsTab = accessibilityPage.getByRole("tab", { name: "Windows" });
      await androidTab.focus();
      await androidTab.press("End");
      if (
        (await windowsTab.getAttribute("aria-selected")) !== "true" ||
        !(await windowsTab.evaluate((node) => node === document.activeElement))
      ) {
        failures.push("install tabs: End did not select and focus the last tab");
      }
      await windowsTab.press("Home");
      await androidTab.press("ArrowRight");
      await windowsTab.press("ArrowLeft");
      if (
        (await androidTab.getAttribute("aria-selected")) !== "true" ||
        !(await androidTab.evaluate((node) => node === document.activeElement)) ||
        (await androidTab.getAttribute("tabindex")) !== "0" ||
        (await windowsTab.getAttribute("tabindex")) !== "-1"
      ) {
        failures.push("install tabs: Arrow/Home/End or roving tabindex contract failed");
      }
    } finally {
      await accessibilityPage.close().catch(() => {});
      await accessibilityContext.close().catch(() => {});
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
