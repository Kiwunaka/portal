#!/usr/bin/env node

import { writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const METRICS = Object.freeze({
  "page.marketing_home_lcp_ms": {
    path: "/",
    value: "lcp",
  },
  "page.marketing_checkout_lcp_ms": {
    path: "/checkout/",
    value: "lcp",
  },
  "page.marketing_cls": {
    path: "/",
    value: "cls",
  },
  "page.marketing_tbt_ms": {
    path: "/",
    value: "tbt",
  },
  "page.webapp_route_content_ms": {
    path: "/dashboard/",
    value: "routeContent",
  },
});

function parseArguments(argv) {
  const values = new Map();
  for (let index = 0; index < argv.length; index += 2) {
    const name = argv[index];
    const value = argv[index + 1];
    if (!name?.startsWith("--") || value === undefined) {
      throw new Error("arguments must be --name value pairs");
    }
    values.set(name.slice(2), value);
  }
  const metric = values.get("metric");
  const baseUrl = values.get("base-url");
  const output = values.get("output");
  if (!METRICS[metric] || !baseUrl || !output) {
    throw new Error("--metric, --base-url and --output are required");
  }
  const parsedBase = new URL(baseUrl);
  const localHttp =
    parsedBase.protocol === "http:" &&
    ["127.0.0.1", "localhost", "[::1]"].includes(parsedBase.hostname);
  if (parsedBase.protocol !== "https:" && !localHttp) {
    throw new Error("base URL must use HTTPS or localhost HTTP");
  }
  if (parsedBase.username || parsedBase.password || parsedBase.search || parsedBase.hash) {
    throw new Error("base URL cannot contain credentials, query or fragment");
  }
  const samples = Number.parseInt(values.get("samples") ?? "20", 10);
  const warmups = Number.parseInt(values.get("warmups") ?? "3", 10);
  if (!Number.isInteger(samples) || samples < 20) {
    throw new Error("--samples must be an integer >= 20");
  }
  if (!Number.isInteger(warmups) || warmups < 3) {
    throw new Error("--warmups must be an integer >= 3");
  }
  return {
    baseUrl: parsedBase,
    metric,
    output,
    samples,
    warmups,
  };
}

export async function installObservers(page) {
  await page.addInitScript(() => {
    globalThis.__pokrovBrowserPerformance = {
      cls: 0,
      lcp: 0,
      longTasks: [],
    };
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          globalThis.__pokrovBrowserPerformance.lcp = entry.startTime;
        }
      }).observe({ type: "largest-contentful-paint", buffered: true });
    } catch {}
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!entry.hadRecentInput) {
            globalThis.__pokrovBrowserPerformance.cls += entry.value;
          }
        }
      }).observe({ type: "layout-shift", buffered: true });
    } catch {}
    try {
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          globalThis.__pokrovBrowserPerformance.longTasks.push(entry.duration);
        }
      }).observe({ type: "longtask", buffered: true });
    } catch {}
  });
}

export async function capture(page, target, metric) {
  // A shell/login <main> is not authenticated, hydrated cabinet content.
  // Register before navigation so a fast response cannot be missed.
  const dashboardReady = metric === "page.webapp_route_content_ms"
    ? page.waitForResponse(
        (response) => new URL(response.url()).pathname === "/api/dashboard",
        { timeout: 15_000 },
      ).then(async (response) => {
        if (!response.ok()) throw new Error("cabinet dashboard API was not successful");
        const body = await response.json();
        if (typeof body?.is_active !== "boolean") {
          throw new Error("cabinet dashboard API did not return account data");
        }
        return body.is_active;
      })
    : null;
  // Observe early rejection while goto is pending; the awaited promise below
  // still propagates it and prevents a numeric sample.
  dashboardReady?.catch(() => {});
  const started = performance.now();
  await page.goto(target.toString(), { waitUntil: "domcontentloaded" });
  await page.locator("main").first().waitFor({ state: "visible", timeout: 15_000 });
  if (dashboardReady) {
    const active = await dashboardReady;
    if (new URL(page.url()).pathname.replace(/\/$/, "") !== "/dashboard") {
      throw new Error("cabinet navigation did not remain on dashboard");
    }
    await page.getByTestId("launch-checklist-open").waitFor({ state: "visible", timeout: 15_000 });
    await page.locator("main").getByRole("heading", {
      name: active
        ? /^(Доступ активен|Доступ скоро закончится|Скорость ограничена)$/
        : "Доступ закончился",
      exact: true,
    }).waitFor({ state: "visible", timeout: 15_000 });
  }
  const routeContent = performance.now() - started;
  await page.waitForTimeout(1_000);
  const observed = await page.evaluate(() => {
    const state = globalThis.__pokrovBrowserPerformance;
    return {
      cls: state.cls,
      lcp: state.lcp,
      tbt: state.longTasks.reduce(
        (total, duration) => total + Math.max(0, duration - 50),
        0,
      ),
    };
  });
  const key = METRICS[metric].value;
  const value = key === "routeContent" ? routeContent : observed[key];
  if (!Number.isFinite(value) || value < 0 || (key === "lcp" && value === 0)) {
    throw new Error(`browser did not produce ${key}`);
  }
  return value;
}

async function main() {
  const { chromium } = await import("playwright");
  const options = parseArguments(process.argv.slice(2));
  const definition = METRICS[options.metric];
  const target = new URL(definition.path, options.baseUrl);
  const browser = await chromium.launch({ headless: true });
  const retained = [];
  try {
    for (let index = 0; index < options.warmups + options.samples; index += 1) {
      const context = await browser.newContext({
        reducedMotion: "reduce",
        serviceWorkers: "block",
        viewport: { width: 390, height: 844 },
      });
      try {
        const page = await context.newPage();
        await installObservers(page);
        const value = await capture(page, target, options.metric);
        if (index >= options.warmups) {
          retained.push(Number(value.toFixed(3)));
        }
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  await writeFile(options.output, `${JSON.stringify(retained, null, 2)}\n`, "utf8");
  process.stdout.write(
    `${JSON.stringify({ metric: options.metric, samples: retained.length, warmups: options.warmups })}\n`,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().catch((error) => {
    process.stderr.write(`BROWSER_PERFORMANCE_COLLECTION_FAILED: ${error.message}\n`);
    process.exitCode = 2;
  });
}
