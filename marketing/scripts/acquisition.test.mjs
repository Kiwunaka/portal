import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const source = ts.transpileModule(
  readFileSync(new URL("../src/lib/acquisition.ts", import.meta.url), "utf8"),
  { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } },
).outputText;
const key = "pokrov-acquisition-v1";

function browser({ referrer = "", search = "", stored } = {}) {
  const storage = new Map(stored ? [[key, JSON.stringify(stored)]] : []);
  const exports = {};
  const requests = [];
  vm.runInNewContext(source, {
    exports, URL, URLSearchParams, AbortController,
    require: (name) => {
      assert.equal(name, "./pokrov");
      return { CANONICAL_API_BASE_URL: "https://api.example.test" };
    },
    document: { referrer },
    window: {
      location: new URL(`https://site.example.test/install/${search}`),
      crypto: { randomUUID: () => "browser-session-fixture" },
      localStorage: { getItem: (k) => storage.get(k) ?? null, setItem: (k, v) => storage.set(k, v) },
      setTimeout, clearTimeout,
    },
    fetch: async (_url, options) => {
      requests.push(JSON.parse(options.body));
      return { ok: true, json: async () => ({ handle: "fixture".repeat(8), purpose: "checkout" }) };
    },
  });
  return { api: exports, storage, requests };
}

test("IP referrers and explicit IP sources never reach storage or a handoff", async () => {
  for (const host of ["203.0.113.42", "[2001:db8::42]"]) {
    const { api, storage, requests } = browser({
      referrer: `https://${host}/private?value=hidden`,
      search: `?utm_source=${encodeURIComponent(host)}`,
    });
    assert.ok(await api.mintAcquisitionHandoff("checkout"));
    const saved = JSON.parse(storage.get(key));
    assert.equal(saved.first.source, "direct");
    assert.equal(saved.first.referrerHost, "");
    assert.equal(requests[0].source, "direct");
    assert.equal(requests[0].referrer, undefined);
    assert.equal(storage.get(key).includes(host), false);
  }
});

test("previously stored IP attribution is cleaned before reuse and rewritten", async () => {
  const touch = { source: "203.0.113.42", referrerHost: "203.0.113.42", campaign: "autumn", content: "banner", ref: "", entryRoute: "/" };
  const { api, storage, requests } = browser({ stored: {
    version: 1, sessionId: "existing-browser-session", first: touch, last: touch,
    expiresAt: Date.now() + 60_000,
  } });
  await api.mintAcquisitionHandoff("checkout");
  const saved = JSON.parse(storage.get(key));
  assert.equal(saved.sessionId, "existing-browser-session");
  for (const item of [saved.first, saved.last]) {
    assert.equal(item.source, "direct");
    assert.equal(item.referrerHost, "");
    assert.equal(item.campaign, "autumn");
  }
  assert.equal(requests[0].referrer, undefined);
  assert.equal(requests[0].source, "direct");
  assert.equal(storage.get(key).includes("203.0.113.42"), false);
});

test("named campaigns and domain referrers retain first touch across visits", async () => {
  const first = browser({ referrer: "https://news.example.test/article?private=value", search: "?utm_source=newsletter&utm_campaign=autumn" });
  first.api.getAcquisitionContext();
  const next = browser({ stored: JSON.parse(first.storage.get(key)), search: "?utm_source=partner" });
  await next.api.mintAcquisitionHandoff("checkout");
  const saved = JSON.parse(next.storage.get(key));
  assert.equal(saved.first.source, "newsletter");
  assert.equal(saved.first.campaign, "autumn");
  assert.equal(saved.first.referrerHost, "news.example.test");
  assert.equal(saved.last.source, "partner");
  assert.equal(next.requests[0].source, "partner");
});
