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

const nodesHealth = [
  {
    code: "NL-free",
    name: "Netherlands free",
    enabled: true,
    accepting_new_clients: true,
    is_draining: false,
    is_healthy: true,
    health_score: 88,
    panel_latency_ms: 84,
    panel_error_rate: 0,
    dataplane_ok: true,
    dataplane_rtt_ms: 42,
    capacity_state: "degraded",
    capacity_score: 64,
    capacity_reject_reason: "provider_cap_near",
    freshness_status: "fresh",
    freshness_age_seconds: 60,
    last_probe_stage: "ok",
    last_probe_error_kind: null,
    ipv4_health: "ok",
    ipv6_health: "missing",
    transport_health: { reality: { ok: true }, xhttp: { ok: false } },
    observer_is_stale: false,
    mapped_users: 32,
    online_keys_now: 12,
    online_connections_now: 18
  },
  {
    code: "DE-1",
    name: "Germany premium",
    enabled: true,
    accepting_new_clients: true,
    is_draining: false,
    is_healthy: true,
    health_score: 96,
    panel_latency_ms: 34,
    panel_error_rate: 0,
    dataplane_ok: true,
    dataplane_rtt_ms: 20,
    capacity_state: "ok",
    capacity_score: 92,
    freshness_status: "fresh",
    ipv4_health: "ok",
    ipv6_health: "ok",
    observer_is_stale: false,
    mapped_users: 78,
    online_keys_now: 24,
    online_connections_now: 31
  }
];

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
    nodes: { total: 2, healthy: 1 },
    errors: {},
    observer: { watch_users: 4, suspicious_users: 1 }
  },
  metrics: {
    status: "fresh",
    age_seconds: 42,
    alerts: {},
    nodes: []
  },
  capacity: {
    nodes: []
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

const onlineUsers = {
  ok: true,
  generated_at: generatedAt,
  rows: [
    {
      row_id: "user:1001",
      tg_id: 1001,
      username: "operator_user",
      display_name: "Operator User",
      sub_type: "PAID",
      status: "active",
      nodes_online: ["NL-free", "DE-1"],
      online_keys_now: 2,
      online_connections_now: 3,
      ip_count: 2,
      risk_flags: ["multi_ip", "manual_review"],
      last_online_at: generatedAt
    }
  ],
  total: 1,
  limit: 200,
  summary: {
    online_identities: 1,
    known_users_online: 1,
    unknown_online_keys: 0,
    online_keys_now: 2,
    online_connections_now: 3,
    nodes_with_panel_errors: 0,
    raw_ip_exposed: false
  },
  panel_errors: []
};

const paymentSummary = {
  ok: true,
  period: { key: "7d", from: "2026-07-01T00:00:00Z", to: generatedAt },
  revenue: { currency: "RUB", paid_count: 4, amount: 3960, by_currency: [{ currency: "RUB", paid_count: 4, revenue: 3960 }] },
  status_counts: { paid: 4, pending: 2, manual_review: 1, failed: 1 },
  attention: { pending_count: 2, manual_review_count: 1, failed_count: 1, problem_count: 4 },
  abandoned: {
    buy_clicks: 17,
    checkout_started: 12,
    paid: 4,
    buy_click_not_paid: 13,
    checkout_not_paid: 8
  },
  problem_orders: [
    { provider: "lavatop", order_id: "ord_pending", status: "pending", amount: 990, currency: "RUB", plan_code: "1_month", tg_id: 1001, created_at: generatedAt }
  ]
};

const funnelPayload = {
  period: { from: "2026-07-01", to: "2026-07-06" },
  totals: { visitors: 100, app_opens: 52, checkouts: 22, paid: 9, connected: 7 },
  stages: [
    { key: "site_to_app", label: "Сайт → кабинет или бот", entered: 100, reached_next: 52, dropped: 48, conversion_pct: 52 },
    { key: "app_to_checkout", label: "Кабинет/бот → оплата", entered: 52, reached_next: 22, dropped: 30, conversion_pct: 42.3 },
    { key: "checkout_to_paid", label: "Оплата → подтверждение", entered: 22, reached_next: 9, dropped: 13, conversion_pct: 40.9 },
    { key: "paid_to_connected", label: "Оплачено → подключение", entered: 9, reached_next: 7, dropped: 2, conversion_pct: 77.8 }
  ],
  drop_reasons: [
    { reason: "Открыли кабинет/бот, но не начали оплату", count: 30 }
  ],
  by_source: [
    { source: "site", visitors: 100, app_opens: 24, checkouts: 12, paid: 5, connected: 4 },
    { source: "webapp", visitors: 0, app_opens: 28, checkouts: 10, paid: 4, connected: 3 }
  ],
  recent: [
    { kind: "site", created_at: generatedAt, session_id: "s1", event_name: "checkout_start", stage: "checkout_start", source: "site", path: "/checkout" }
  ]
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

async function mockAdminApi(page: Page, options: { requireInitDataForSession?: boolean; delayMs?: number } = {}): Promise<ApiCall[]> {
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

    if (url.pathname === "/api/admin/search") {
      await jsonResponse(route, {
        results: [
          {
            kind: "user",
            id: "1001",
            title: "Operator User",
            subtitle: "Активный доступ · профиль проверен",
            href: "/users?selected=1001"
          }
        ]
      });
      return;
    }

    if (options.delayMs) {
      await new Promise((resolve) => setTimeout(resolve, options.delayMs));
    }

    if (url.pathname === "/api/admin/ops/overview") {
      await jsonResponse(route, overview);
      return;
    }

    if (url.pathname === "/api/admin/nodes/health") {
      await jsonResponse(route, { ok: true, nodes: nodesHealth });
      return;
    }

    if (url.pathname === "/api/admin/nodes/runtime") {
      await jsonResponse(route, { ok: true, updated_at: generatedAt, nodes: [{ node_code: "NL-free", online_clients: 12 }] });
      return;
    }

    if (url.pathname === "/api/admin/online/users") {
      await jsonResponse(route, onlineUsers);
      return;
    }

    if (url.pathname === "/api/admin/payments/summary") {
      const period = url.searchParams.get("period") || "7d";
      await jsonResponse(route, { ...paymentSummary, period: { ...paymentSummary.period, key: period }, revenue: { ...paymentSummary.revenue, amount: period === "today" ? 990 : period === "30d" ? 9900 : 3960 } });
      return;
    }

    if (url.pathname === "/api/admin/keys/pressure") {
      await jsonResponse(route, {
        ok: true,
        keys: [
          {
            key_id: 7001,
            tg_id: 1001,
            node_code: "NL-free",
            panel_email: "operator@example.test",
            state: "watch",
            pressure_score: 72,
            reasons: ["multi_ip"],
            manual_review_required: true,
            updated_at: generatedAt
          }
        ]
      });
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
            capacity_score: 72
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
      const dryRun = Boolean((body as { dry_run?: boolean } | null)?.dry_run);
      await jsonResponse(route, { ok: true, dry_run: dryRun, attempted: 12, sent: dryRun ? 0 : 12, failed: 0, segment: "all_active" });
      return;
    }

    if (/^\/api\/admin\/users\/\d+$/.test(url.pathname)) {
      const requestedTgId = Number(url.pathname.split("/").pop());
      const isOperatorUser = requestedTgId === 1001;
      await jsonResponse(route, {
        user: {
          tg_id: requestedTgId,
          username: isOperatorUser ? "operator_user" : "first_user",
          display_name: isOperatorUser ? "Operator User" : "First User",
          status: "active",
          sub_type: "PAID",
          expiry_at: "2026-08-01T00:00:00Z",
          app_install_id: `install-${requestedTgId}`,
          observer_state: "watch"
        },
        summary: {
          nodes_online: 2,
          online_keys_now: 2,
          online_connections_now: 3,
          subid_mismatch_count: 0,
          traffic_total_gb: 4.5
        },
        keys: [
          { node_code: "NL-free", exists: true, enabled: true, online: true, current_connections: 2, total_gb: 3.1, sub_id_match: true },
          { node_code: "DE-1", exists: true, enabled: true, online: true, current_connections: 1, total_gb: 1.4, sub_id_match: true }
        ],
        observer: {
          state: "watch",
          observed_ip_count_24h: isOperatorUser ? 2 : 0,
          recent_ips: isOperatorUser
            ? [{ source_ip_raw: "203.0.113.77", node_code: "NL-free", counts_for_suspicion: true, last_seen_at: generatedAt }]
            : [],
          recent_nodes: []
        },
        risk: { state: "watch" },
        tickets: [{ id: 2001, status: "open", subject: "Need help", updated_at: generatedAt }],
        payment_orders: [{ provider: "lavatop", order_id: `ord_${requestedTgId}`, status: "pending", amount: 990, currency: "RUB", created_at: generatedAt }],
        key_history: [{ action: "key_sync", node_code: "NL-free", actor_tg_id: 9999, created_at: generatedAt }],
        admin_actions: [{ action: "admin_note", actor_tg_id: 9999, created_at: generatedAt }]
      });
      return;
    }

    if (url.pathname === "/api/admin/users") {
      await jsonResponse(route, {
        page: 1,
        page_size: 80,
        total: 2,
        sort: "created_desc",
        users: [
          {
            tg_id: 2002,
            username: "first_user",
            display_name: "First User",
            status: "active",
            sub_type: "PAID",
            expiry_at: "2026-08-01T00:00:00Z",
            observer_state: "watch",
            app_install_id: "install-2002"
          },
          {
            tg_id: 1001,
            username: "operator_user",
            display_name: "Operator User",
            status: "active",
            sub_type: "PAID",
            expiry_at: "2026-08-01T00:00:00Z",
            observer_state: "watch",
            app_install_id: "install-1001"
          }
        ]
      });
      return;
    }

    if (url.pathname === "/api/admin/tickets") {
      await jsonResponse(route, { ok: true, tickets: [{ id: 2001, user_tg_id: 1001, status: "open", subject: "Need help", updated_at: generatedAt }] });
      return;
    }

    if (url.pathname === "/api/admin/payments/orders") {
      await jsonResponse(route, { ok: true, orders: [{ provider: "lavatop", order_id: "ord_1", status: "pending", amount: 990, currency: "RUB", plan_code: "1_month", tg_id: 1001, created_at: generatedAt }] });
      return;
    }

    if (url.pathname === "/api/admin/promos") {
      await jsonResponse(route, { ok: true, promos: [{ id: 1, code: "HELLO", promo_type: "discount", value: 15, status: "active", created_at: generatedAt }] });
      return;
    }

    if (url.pathname === "/api/admin/referrals/pending") {
      await jsonResponse(route, { ok: true, rows: [{ id: 1, referrer_tg_id: 1001, status: "pending", created_at: generatedAt }] });
      return;
    }

    if (url.pathname === "/api/admin/live-updates") {
      await jsonResponse(route, { ok: true, updates: [{ id: 1, title: "Beta patch", summary: "APK/EXE checksum refreshed", is_active: true, published_at: generatedAt, sort_order: 10 }] });
      return;
    }

    if (url.pathname === "/api/admin/funnel/summary") {
      await jsonResponse(route, funnelPayload);
      return;
    }

    if (/^\/api\/admin\/nodes\/[^/]+\/(drain|enable|undrain|disable|resync)$/.test(url.pathname) && method === "POST") {
      await jsonResponse(route, { ok: true, dry_run: Boolean((body as { dry_run?: boolean } | null)?.dry_run), node_code: url.pathname.split("/")[4], node: nodesHealth[0] });
      return;
    }

    await jsonResponse(route, { ok: true });
  });
  return calls;
}

async function authenticate(page: Page) {
  await expect(page.getByText("Вход в админку")).toBeVisible();
  await page.getByPlaceholder("query_id=...&user=...&auth_date=...&hash=...").fill("query_id=test&user=%7B%22id%22%3A9999%7D&auth_date=1&hash=test");
  await page.getByRole("button", { name: /Войти по initData/ }).click();
  await expect(page.getByRole("button", { name: /Обновить/ })).toBeVisible();
}

async function gotoWithAdminSession(page: Page, path: string) {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("pokrov_admin_session_token", "mock-admin-token");
  });
  const target = path === "/" || path.endsWith("/") || path.includes("?") ? path : `${path}/`;
  await page.goto(target);
  await expect(page.getByRole("button", { name: /Обновить/ })).toBeVisible();
}

test("dashboard reuses browser session and renders action-first overview", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Обновить/ })).toBeVisible();

  await expect.poll(() => calls.some((call) => call.method === "POST" && call.path === "/api/admin/auth/session")).toBe(true);
  await expect
    .poll(() => calls.some((call) => call.path === "/api/admin/ops/overview" && call.auth === "Bearer mock-admin-token"))
    .toBe(true);
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
  await expect(page.getByText("NL-free traffic near provider cap")).toBeVisible();
  await expect(page.getByText("Активные пользователи", { exact: true })).toBeVisible();
  await expect(page.getByText("Выручка сегодня", { exact: true })).toHaveCount(0);
});

test("dashboard exchanges initData when browser session is missing", async ({ page }) => {
  const calls = await mockAdminApi(page, { requireInitDataForSession: true });
  await page.goto("/");
  await authenticate(page);

  await expect
    .poll(() => calls.some((call) => call.method === "POST" && call.path === "/api/admin/auth/session" && call.initData.includes("query_id=test")))
    .toBe(true);
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
});

test("node detail requires text confirmation for lifecycle actions", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await gotoWithAdminSession(page, "/nodes");

  await expect(page.getByRole("heading", { name: "Health-first ноды" })).toBeVisible();
  await page.getByRole("button", { name: /^drain$/ }).click();
  await page.getByLabel("введи node_code").fill("NL-free");
  await page.getByRole("button", { name: /Выполнить/ }).click();

  await expect.poll(() => calls.some((call) => call.method === "POST" && call.path === "/api/admin/nodes/NL-free/drain")).toBe(true);
});

test("payments screen renders summaries, abandoned counts and orders", async ({ page }) => {
  await mockAdminApi(page);
  await gotoWithAdminSession(page, "/payments");

  await expect(page.getByText("Кликнул, но не оплатил")).toBeVisible();
  await expect(page.getByText("ord_pending")).toBeVisible();
  await expect(page.getByText("checkout not paid")).toBeVisible();
  await expect(page.getByText("ord_1")).toBeVisible();
});

test("funnel screen renders stages and source breakdown without raw JSON", async ({ page }) => {
  await mockAdminApi(page);
  await gotoWithAdminSession(page, "/funnel");

  await expect(page.getByRole("heading", { name: "Stages" })).toBeVisible();
  await expect(page.getByText("Сайт → кабинет или бот")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Source breakdown" })).toBeVisible();
  await expect(page.locator("pre")).toHaveCount(0);
});

test("provider caps saves configured quota through mock API", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await gotoWithAdminSession(page, "/provider-caps");

  await expect(page.getByRole("main").getByRole("heading", { name: "Лимиты провайдеров" })).toBeVisible();
  await expect(page.getByText("NL-free")).toBeVisible();
  await page.getByRole("button", { name: /NL-free/ }).first().click();
  await page.locator("label").filter({ hasText: "included_gb" }).locator("input").fill("1200");
  await page.getByRole("button", { name: /Сохранить/ }).click();
  await expect
    .poll(() => calls.some((call) => call.method === "PATCH" && call.path.startsWith("/api/admin/provider-quotas/") && (call.body as { included_gb?: number } | null)?.included_gb === 1200))
    .toBe(true);
});

test("alerts can be acknowledged and silenced", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await gotoWithAdminSession(page, "/alerts");

  await page.getByRole("button", { name: /Ack/ }).click();
  await expect.poll(() => calls.some((call) => call.method === "POST" && call.path.endsWith("/ack"))).toBe(true);
  await page.getByRole("button", { name: /1ч/ }).click();
  await expect.poll(() => calls.some((call) => call.method === "POST" && call.path.endsWith("/silence"))).toBe(true);
});

test("free-tier page renders user cap table", async ({ page }) => {
  await mockAdminApi(page);
  await gotoWithAdminSession(page, "/free-tier");

  await expect(page.getByRole("main").getByRole("heading", { name: "Free tier" })).toBeVisible();
  await expect(page.getByText("Free Needle")).toBeVisible();
  await expect(page.getByText("near_cap")).toBeVisible();
});

test("broadcast requires dry-run preview before sending", async ({ page }) => {
  const calls = await mockAdminApi(page);
  await gotoWithAdminSession(page, "/broadcast");

  await page.locator("textarea").fill("Ops smoke broadcast");
  await page.getByRole("button", { name: /Dry-run/ }).click();
  await expect(page.getByText(/dry-run: 12/)).toBeVisible();
  await page.getByPlaceholder("SEND").fill("SEND");
  await page.getByRole("button", { name: /Отправить/ }).click();

  await expect.poll(() => calls.filter((call) => call.method === "POST" && call.path === "/api/admin/broadcast").length).toBe(2);
  const broadcastBodies = calls.filter((call) => call.method === "POST" && call.path === "/api/admin/broadcast").map((call) => call.body as { dry_run?: boolean });
  expect(broadcastBodies[0]?.dry_run).toBe(true);
  expect(broadcastBodies[1]?.dry_run).toBe(false);
});
