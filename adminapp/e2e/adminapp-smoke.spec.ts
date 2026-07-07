import { expect, type Page, type Route, test } from "@playwright/test";

type ApiCall = {
  method: string;
  path: string;
  auth: string;
  initData: string;
  body: unknown;
};

const generatedAt = "2026-07-06T10:00:00Z";

const activeAlert = {
  id: 501,
  fingerprint: "provider_cap:NL-free",
  source: "provider_cap",
  severity: "warning",
  status: "active",
  title: "NL-free traffic near provider cap",
  body: "812 GB of 1000 GB used",
  node_code: "NL-free",
  first_seen_at: generatedAt,
  last_seen_at: generatedAt
};

const providerQuotaStatus = {
  node_code: "NL-free",
  node_name: "Netherlands free",
  configured: true,
  enabled: true,
  state: "near_cap",
  included_gb: 1000,
  used_gb: 812,
  remaining_gb: 188,
  used_pct: 81.2,
  cycle_start: "2026-07-01T00:00:00Z",
  cycle_end: "2026-08-01T00:00:00Z",
  reset_day: 1,
  timezone: "UTC",
  warning_ratio: 0.8,
  critical_ratio: 0.95,
  source: "manual"
};

const providerQuotaConfig = {
  id: 7,
  node_code: "NL-free",
  included_bytes: 1_073_741_824_000,
  included_gb: 1000,
  reset_day: 1,
  timezone: "UTC",
  warning_ratio: 0.8,
  critical_ratio: 0.95,
  enabled: true,
  notes: "mock quota",
  updated_by: 9999,
  created_at: generatedAt,
  updated_at: generatedAt
};

const overview = {
  ok: true,
  generated_at: generatedAt,
  summary: {
    users: {
      total: 120,
      active: 88,
      free: 32,
      paid: 56,
      unique_install_ids_24h: 11,
      unique_install_ids_7d: 44
    },
    tickets: { open: 3 },
    nodes: { total: 3, healthy: 3 },
    errors: {},
    observer: { watch_users: 4, suspicious_users: 1 }
  },
  metrics: {
    status: "fresh",
    age_seconds: 42,
    alerts: {},
    nodes: [
      {
        node_code: "NL-free",
        status: "fresh",
        cpu_percent: 18,
        network_total_mbps: 92,
        capacity_score: 0.72
      }
    ]
  },
  capacity: {
    nodes: [
      {
        code: "NL-free",
        node_code: "NL-free",
        capacity_state: "ok",
        capacity_score: 0.72,
        tx_ratio: 0.24,
        cpu_percent: 18,
        reject_reason: null
      }
    ]
  },
  free_tier: {
    free_users: 32,
    sampled_users: 28,
    limit_gb_per_user: 5,
    cycle_days: 30,
    used_gb: 91.5,
    limit_gb_total: 160,
    remaining_gb: 68.5,
    used_pct: 57.2,
    near_cap_users: 5,
    over_cap_users: 1,
    burn_rate_gb_per_day: 3.1,
    source: "mock"
  },
  provider_quotas: [providerQuotaStatus],
  alerts: {
    active: [activeAlert],
    active_count: 1,
    critical_count: 0,
    warning_count: 1
  }
};

function jsonResponse(route: Route, data: unknown, status = 200) {
  const origin = route.request().headers().origin || "http://127.0.0.1:3107";
  return route.fulfill({
    status,
    contentType: "application/json",
    headers: {
      "access-control-allow-origin": origin,
      "access-control-allow-credentials": "true",
      "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
      "access-control-allow-headers": "authorization,content-type,x-telegram-init-data,x-web-auth-token"
    },
    body: JSON.stringify(data)
  });
}

async function mockAdminApi(page: Page, options: { requireInitDataForSession?: boolean } = {}): Promise<ApiCall[]> {
  const calls: ApiCall[] = [];
  await page.route("**/api/admin/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    const rawBody = request.postData();
    let body: unknown = null;
    if (rawBody) {
      try {
        body = JSON.parse(rawBody);
      } catch {
        body = rawBody;
      }
    }
    calls.push({
      method,
      path: `${url.pathname}${url.search}`,
      auth: request.headers().authorization || "",
      initData: request.headers()["x-telegram-init-data"] || "",
      body
    });

    if (method === "OPTIONS") {
      await jsonResponse(route, {}, 204);
      return;
    }

    if (url.pathname === "/api/admin/auth/session") {
      if (options.requireInitDataForSession && !request.headers()["x-telegram-init-data"]) {
        await jsonResponse(route, { detail: "Telegram auth required" }, 401);
        return;
      }
      await jsonResponse(route, {
        ok: true,
        token: "mock-admin-token",
        token_transport: "bearer",
        expires_in: 3600,
        user: { id: 9999, username: "owner", role: "superadmin" }
      });
      return;
    }

    if (url.pathname === "/api/admin/ops/overview") {
      await jsonResponse(route, overview);
      return;
    }

    if (url.pathname === "/api/admin/free-tier/users") {
      await jsonResponse(route, {
        ok: true,
        users: [
          {
            tg_id: 1001,
            username: "free_needle",
            display_name: "Free Needle",
            is_active: true,
            used_gb: 4.8,
            limit_gb: 5,
            remaining_gb: 0.2,
            used_pct: 96,
            state: "near_cap",
            cycle_start: "2026-07-01T00:00:00Z",
            cycle_end: "2026-07-31T00:00:00Z",
            source: "mock"
          }
        ]
      });
      return;
    }

    if (url.pathname === "/api/admin/traffic/summary") {
      await jsonResponse(route, {
        ok: true,
        rows: [
          { date: "2026-07-04", node_code: "NL-free", pool_code: "free", traffic_bytes: 6_442_450_944, traffic_gb: 6, samples: 12 },
          { date: "2026-07-04", node_code: "DE-1", pool_code: "premium", traffic_bytes: 10_737_418_240, traffic_gb: 10, samples: 12 }
        ]
      });
      return;
    }

    if (url.pathname === "/api/admin/nodes/timeseries") {
      await jsonResponse(route, {
        ok: true,
        rows: [
          {
            sampled_at: "2026-07-06T09:55:00Z",
            node_code: "NL-free",
            cpu_percent: 18,
            network_total_mbps: 92,
            capacity_score: 0.72
          }
        ]
      });
      return;
    }

    if (url.pathname === "/api/admin/provider-quotas" && method === "GET") {
      await jsonResponse(route, { ok: true, quotas: [providerQuotaConfig] });
      return;
    }

    if (url.pathname === "/api/admin/provider-quotas" && method === "POST") {
      await jsonResponse(route, { ok: true, quota: { ...providerQuotaConfig, ...(body as object) } });
      return;
    }

    if (url.pathname.startsWith("/api/admin/provider-quotas/") && method === "PATCH") {
      await jsonResponse(route, { ok: true, quota: { ...providerQuotaConfig, ...(body as object) } });
      return;
    }

    if (url.pathname.startsWith("/api/admin/provider-quotas/") && method === "DELETE") {
      await jsonResponse(route, { ok: true });
      return;
    }

    if (url.pathname === "/api/admin/alerts") {
      await jsonResponse(route, { ok: true, alerts: [activeAlert] });
      return;
    }

    if (url.pathname.endsWith("/ack")) {
      await jsonResponse(route, { ok: true, alert: { ...activeAlert, acknowledged_at: generatedAt } });
      return;
    }

    if (url.pathname.endsWith("/silence")) {
      await jsonResponse(route, { ok: true, alert: { ...activeAlert, status: "silenced", silence_until: "2026-07-06T12:00:00Z" } });
      return;
    }

    if (url.pathname === "/api/admin/broadcast" && method === "POST") {
      await jsonResponse(route, { ok: true, sent: 12, skipped: 0, segment: "active" });
      return;
    }

    if (url.pathname === "/api/admin/users") {
      await jsonResponse(route, { ok: true, users: [{ tg_id: 1001, username: "operator_user", status: "active" }] });
      return;
    }

    if (url.pathname === "/api/admin/tickets") {
      await jsonResponse(route, { ok: true, tickets: [{ id: 2001, status: "open", subject: "Need help" }] });
      return;
    }

    if (url.pathname === "/api/admin/payments/orders") {
      await jsonResponse(route, { ok: true, orders: [{ provider: "lavatop", order_id: "ord_1", status: "pending" }] });
      return;
    }

    if (url.pathname === "/api/admin/promos") {
      await jsonResponse(route, { ok: true, promos: [{ code: "HELLO", promo_type: "discount", value: 15 }] });
      return;
    }

    if (url.pathname === "/api/admin/referrals/pending") {
      await jsonResponse(route, { ok: true, rows: [{ id: 1, referrer_tg_id: 1001, status: "pending" }] });
      return;
    }

    if (url.pathname === "/api/admin/live-updates") {
      await jsonResponse(route, { ok: true, updates: [{ id: 1, title: "Beta patch", is_active: true }] });
      return;
    }

    await jsonResponse(route, { ok: true });
  });
  return calls;
}

async function authenticate(page: Page) {
  await expect(page.getByText("Admin auth")).toBeVisible();
  await page.getByPlaceholder("query_id=...&user=...&auth_date=...&hash=...").fill("query_id=test&user=%7B%22id%22%3A9999%7D&auth_date=1&hash=test");
  await page.getByRole("button", { name: /Войти по initData/ }).click();
  await expect(page.getByRole("button", { name: /Refresh/ })).toBeVisible();
}

async function gotoWithAdminSession(page: Page, path: string) {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("pokrov_admin_session_token", "mock-admin-token");
  });
  await page.goto(path);
  await expect(page.getByRole("button", { name: /Refresh/ })).toBeVisible();
}

test("dashboard reuses an existing browser session and renders overview", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Refresh/ })).toBeVisible();

  expect(calls.some((call) => call.method === "POST" && call.path === "/api/admin/auth/session")).toBe(true);
  expect(calls.some((call) => call.path === "/api/admin/ops/overview" && call.auth === "Bearer mock-admin-token")).toBe(true);
  await expect(page.getByText("Users active")).toBeVisible();
  await expect(page.getByText("NL-free traffic near provider cap")).toBeVisible();
});

test("dashboard exchanges initData when browser session is missing", async ({ page }) => {
  const calls = await mockAdminApi(page, { requireInitDataForSession: true });
  await page.goto("/");
  await authenticate(page);

  expect(calls.some((call) => call.method === "POST" && call.path === "/api/admin/auth/session" && call.initData.includes("query_id=test"))).toBe(true);
  await expect(page.getByText("Users active")).toBeVisible();
});

test("provider caps saves configured quota through mock API", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await gotoWithAdminSession(page, "/provider-caps");

  await expect(page.getByRole("main").getByRole("heading", { name: "Provider caps" })).toBeVisible();
  await expect(page.getByText("NL-free")).toBeVisible();
  await page.locator("label").filter({ hasText: "included_gb" }).locator("input").fill("1200");
  await page.getByRole("button", { name: /Save/ }).click();
  await expect
    .poll(() => calls.some((call) => call.method === "PATCH" && call.path.startsWith("/api/admin/provider-quotas/") && (call.body as { included_gb?: number } | null)?.included_gb === 1200))
    .toBe(true);
});

test("alerts can be acknowledged and silenced", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await gotoWithAdminSession(page, "/alerts");

  await page.getByRole("button", { name: /Ack/ }).click();
  await expect.poll(() => calls.some((call) => call.method === "POST" && call.path.endsWith("/ack"))).toBe(true);
  await page.getByRole("button", { name: /2h/ }).click();
  await expect.poll(() => calls.some((call) => call.method === "POST" && call.path.endsWith("/silence"))).toBe(true);
});

test("free-tier page renders user cap table", async ({ page }) => {
  await mockAdminApi(page);
  await gotoWithAdminSession(page, "/free-tier");

  await expect(page.getByRole("main").getByRole("heading", { name: "Free tier" })).toBeVisible();
  await expect(page.getByText("free_needle")).toBeVisible();
  await expect(page.getByText("near_cap")).toBeVisible();
});

test("broadcast submits active segment message", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await gotoWithAdminSession(page, "/broadcast");

  await page.locator("textarea").fill("Ops smoke broadcast");
  await page.getByRole("button", { name: /Send active 100/ }).click();
  await expect.poll(() => calls.some((call) => call.method === "POST" && call.path === "/api/admin/broadcast")).toBe(true);
  await expect(page.getByText(/"sent":12/)).toBeVisible();
});
