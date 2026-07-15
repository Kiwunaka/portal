import type { Page, Route } from "@playwright/test";

export type AdminApiCall = {
  method: string;
  path: string;
};

export type AdminSearchResult = {
  kind: "user" | "order" | "node" | "key";
  id: string;
  title: string;
  subtitle: string;
  href: string;
};

const generatedAt = "2026-07-15T10:00:00Z";

const searchResults: AdminSearchResult[] = [
  {
    kind: "node",
    id: "nl",
    title: "Нода NL",
    subtitle: "Нидерланды · требуется проверка",
    href: "/nodes?selected=nl"
  },
  {
    kind: "user",
    id: "1001",
    title: "Пользователь 1001",
    subtitle: "Активный доступ · профиль проверен",
    href: "/users?selected=1001"
  }
];

function fulfillJson(route: Route, data: unknown, status = 200) {
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

export async function installAdminApiMock(
  page: Page,
  options: { searchStatus?: number } = {}
): Promise<{ calls: AdminApiCall[] }> {
  const calls: AdminApiCall[] = [];
  await page.route("**/api/admin/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    calls.push({ method: request.method(), path: `${url.pathname}${url.search}` });

    if (request.method() === "OPTIONS") {
      await fulfillJson(route, {}, 204);
      return;
    }

    if (url.pathname === "/api/admin/auth/session") {
      await fulfillJson(route, {
        ok: true,
        token: "mock-admin-token",
        token_transport: "bearer",
        expires_in: 3600,
        user: { id: 9999, username: "owner", role: "superadmin" }
      });
      return;
    }

    if (url.pathname === "/api/admin/ops/overview") {
      await fulfillJson(route, {
        ok: true,
        generated_at: generatedAt,
        summary: {
          users: { total: 120, active: 88, free: 32, paid: 56 },
          tickets: { open: 3 },
          nodes: { total: 2, healthy: 2 },
          errors: {},
          observer: { watch_users: 0, suspicious_users: 0 }
        },
        metrics: { status: "fresh", age_seconds: 42, alerts: {}, nodes: [] },
        capacity: { nodes: [] },
        free_tier: {
          free_users: 32,
          sampled_users: 28,
          limit_gb_per_user: 5,
          cycle_days: 30,
          used_gb: 91.5,
          limit_gb_total: 160,
          remaining_gb: 68.5,
          used_pct: 57.2,
          near_cap_users: 0,
          over_cap_users: 0,
          burn_rate_gb_per_day: 3.1,
          source: "mock"
        },
        provider_quotas: [],
        alerts: { active: [], active_count: 0, critical_count: 0, warning_count: 0 }
      });
      return;
    }

    if (url.pathname === "/api/admin/payments/summary") {
      await fulfillJson(route, {
        ok: true,
        period: { key: url.searchParams.get("period") || "7d", from: generatedAt, to: generatedAt },
        revenue: { currency: "RUB", paid_count: 0, amount: 0, by_currency: [] },
        status_counts: { paid: 0, pending: 0, manual_review: 0, failed: 0 },
        attention: { pending_count: 0, manual_review_count: 0, failed_count: 0, problem_count: 0 },
        abandoned: {
          buy_clicks: 0,
          checkout_started: 0,
          paid: 0,
          buy_click_not_paid: 0,
          checkout_not_paid: 0
        },
        problem_orders: []
      });
      return;
    }

    if (url.pathname === "/api/admin/search") {
      if (options.searchStatus === 404) {
        await fulfillJson(route, { detail: "Not found" }, 404);
        return;
      }
      await fulfillJson(route, { results: searchResults }, options.searchStatus ?? 200);
      return;
    }

    await fulfillJson(route, {});
  });

  return { calls };
}
