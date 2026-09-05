import assert from "node:assert/strict";
import test from "node:test";
import { capture } from "./collect-browser-performance.mjs";

const target = new URL("http://127.0.0.1:43121/dashboard/");
const metric = "page.webapp_route_content_ms";

function fixture({ status = 200, body = { is_active: true }, content = true } = {}) {
  const calls = [];
  const page = {
    waitForResponse: async (predicate) => {
      calls.push("response-listener");
      assert.equal(predicate({ url: () => "http://127.0.0.1:43121/api/other" }), false);
      assert.equal(predicate({ url: () => "http://127.0.0.1:43121/api/dashboard" }), true);
      return { ok: () => status === 200, json: async () => body };
    },
    goto: async () => { calls.push("navigation"); },
    url: () => target.href,
    locator: () => ({
      first: () => ({ waitFor: async () => { calls.push("main"); } }),
      getByRole: () => ({ waitFor: async () => { calls.push("account-heading"); } }),
    }),
    getByTestId: (id) => ({ waitFor: async () => {
      assert.equal(id, "launch-checklist-open");
      if (!content) throw new Error("dashboard content absent");
      calls.push("dashboard-content");
    } }),
    waitForTimeout: async () => {},
    evaluate: async () => ({ lcp: 25, cls: 0, tbt: 0 }),
  };
  return { page, calls };
}

test("cabinet sample waits for successful API and rendered account content", async () => {
  const { page, calls } = fixture();
  assert.ok(Number.isFinite(await capture(page, target, metric)));
  assert.deepEqual(calls, ["response-listener", "navigation", "main", "dashboard-content", "account-heading"]);
});

test("a login/shell main cannot produce a cabinet sample", async () => {
  const { page } = fixture({ content: false });
  await assert.rejects(capture(page, target, metric), /dashboard content absent/);
});

test("failed API and successful non-account JSON cannot produce samples", async () => {
  for (const options of [{ status: 401 }, { body: { ok: true } }]) {
    const { page } = fixture(options);
    await assert.rejects(capture(page, target, metric), /cabinet dashboard API/);
  }
});

test("marketing metrics do not require a cabinet API or account DOM", async () => {
  const { page, calls } = fixture({ content: false });
  assert.equal(await capture(page, target, "page.marketing_home_lcp_ms"), 25);
  assert.deepEqual(calls, ["navigation", "main"]);
});
