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
  },
  {
    kind: "user",
    id: "safe-colon-label",
    title: "Безопасная метка ID",
    subtitle: "ID: 1001",
    href: "/users?selected=1001"
  }
];

const unsafeSearchResults: Array<Record<string, unknown>> = [
  {
    kind: "node",
    id: "privacy-01",
    title: "Проверка адреса четыре",
    subtitle: "Источник 192.0.2.44",
    href: "/nodes?selected=privacy-01"
  },
  {
    kind: "node",
    id: "privacy-02",
    title: "Проверка адреса шесть кратко",
    subtitle: "Источник 2001:db8::44",
    href: "/nodes?selected=privacy-02"
  },
  {
    kind: "node",
    id: "privacy-03",
    title: "Проверка адреса шесть полно",
    subtitle: "Источник 2001:0db8:0000:0000:0000:0000:0000:0044",
    href: "/nodes?selected=privacy-03"
  },
  {
    kind: "user",
    id: "privacy-04",
    title: "Проверка веб-ссылки",
    subtitle: "https://example.invalid/profile",
    href: "/users?selected=privacy-04"
  },
  {
    kind: "user",
    id: "privacy-05",
    title: "Проверка сетевого пути",
    subtitle: "//host/path",
    href: "/users?selected=privacy-05"
  },
  {
    kind: "user",
    id: "privacy-06",
    title: "Проверка доменного пути",
    subtitle: "example.invalid/path",
    href: "/users?selected=privacy-06"
  },
  {
    kind: "key",
    id: "privacy-07",
    title: "Проверка схемы",
    subtitle: "vless:",
    href: "/users?selected=privacy-07"
  },
  {
    kind: "key",
    id: "privacy-08",
    title: "Проверка английского слова",
    subtitle: "token",
    href: "/users?selected=privacy-08"
  },
  {
    kind: "key",
    id: "privacy-09",
    title: "Проверка русского слова",
    subtitle: "токен",
    href: "/users?selected=privacy-09"
  },
  {
    kind: "key",
    id: "privacy-10",
    title: "Проверка маркера один",
    subtitle: "subscription",
    href: "/users?selected=privacy-10"
  },
  {
    kind: "key",
    id: "privacy-11",
    title: "Проверка маркера два",
    subtitle: "подписка",
    href: "/users?selected=privacy-11"
  },
  {
    kind: "key",
    id: "privacy-12",
    title: "Проверка маркера три",
    subtitle: "private_key",
    href: "/users?selected=privacy-12"
  },
  {
    kind: "key",
    id: "privacy-13",
    title: "Проверка маркера четыре",
    subtitle: "secret",
    href: "/users?selected=privacy-13"
  },
  {
    kind: "user",
    id: "privacy-14",
    title: "Проверка структуры",
    subtitle: "Публичное описание",
    href: "/users?selected=privacy-14",
    internal_value: "поле вне публичного контракта"
  },
  {
    kind: "user",
    id: "privacy-15",
    title: "Проверка фрагмента",
    subtitle: "Публичное описание",
    href: "/users?selected=privacy-15#details"
  },
  {
    kind: "user",
    id: "privacy-16",
    title: "Проверка внешнего адреса",
    subtitle: "Публичное описание",
    href: "https://outside.invalid/users"
  },
  {
    kind: "user",
    id: "privacy-17",
    title: "Проверка обратной черты",
    subtitle: "Публичное описание",
    href: "/\\outside.invalid/users"
  },
  {
    kind: "user",
    id: "privacy-18",
    title: "Проверка двойного слеша",
    subtitle: "Публичное описание",
    href: "//outside/users"
  },
  {
    kind: "user",
    id: "privacy-19",
    title: "Проверка ключа запроса",
    subtitle: "Публичное описание",
    href: "/users?token_hint=safe"
  },
  {
    kind: "user",
    id: "privacy-20",
    title: "Проверка значения запроса",
    subtitle: "Публичное описание",
    href: "/users?selected=secret"
  },
  {
    kind: "user",
    id: "privacy-21",
    title: "Проверка IDN-домена",
    subtitle: "пример.рф/путь",
    href: "/users?selected=privacy-21"
  }
];

type AdminApiMockOptions = {
  includeUnsafeSearchResults?: boolean;
  overviewStatus?: number;
  searchStatus?: number;
  trafficStatus?: number;
  failAllLegacyRequests?: boolean;
  delayFirstOverviewFailure?: boolean;
};

const LEGACY_GET_PATHS = new Set([
  "/api/admin/ops/overview",
  "/api/admin/alerts",
  "/api/admin/free-tier/users",
  "/api/admin/traffic/summary",
  "/api/admin/nodes/timeseries",
  "/api/admin/provider-quotas",
  "/api/admin/nodes/health",
  "/api/admin/nodes/runtime",
  "/api/admin/online/users",
  "/api/admin/payments/summary",
  "/api/admin/payments/orders",
  "/api/admin/keys/pressure",
  "/api/admin/tickets",
  "/api/admin/live-updates",
  "/api/admin/funnel/summary",
  "/api/admin/users",
  "/api/admin/promos",
  "/api/admin/referrals/pending"
]);

const FOCUSED_GET_PATHS = new Set([...LEGACY_GET_PATHS, "/api/admin/search"]);

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
  options: AdminApiMockOptions = {}
): Promise<{
  calls: AdminApiCall[];
  overviewResponses: number[];
  releaseFirstOverview: () => void;
}> {
  const calls: AdminApiCall[] = [];
  const overviewResponses: number[] = [];
  let releaseFirstOverview: () => void = () => undefined;
  const firstOverviewGate = new Promise<void>((resolve) => {
    releaseFirstOverview = () => resolve();
  });
  let overviewRequestCount = 0;
  await page.route("**/api/admin/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const method = request.method();
    calls.push({ method, path: `${url.pathname}${url.search}` });

    const knownPath = FOCUSED_GET_PATHS.has(url.pathname) || url.pathname === "/api/admin/auth/session";
    const knownRequest =
      (method === "GET" && FOCUSED_GET_PATHS.has(url.pathname)) ||
      (method === "POST" && url.pathname === "/api/admin/auth/session") ||
      (method === "OPTIONS" && knownPath);
    if (!knownRequest) {
      await fulfillJson(
        route,
        {
          detail: "Focused fixture contract rejected the request",
          code: "fixture_contract_error",
          method,
          path: url.pathname
        },
        501
      );
      return;
    }

    if (method === "OPTIONS") {
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

    if (options.failAllLegacyRequests && method === "GET" && LEGACY_GET_PATHS.has(url.pathname)) {
      await fulfillJson(route, { detail: "Legacy request failed", code: "legacy_test_failure" }, 500);
      if (url.pathname === "/api/admin/ops/overview") overviewResponses.push(500);
      return;
    }

    if (url.pathname === "/api/admin/ops/overview") {
      const requestNumber = overviewRequestCount;
      overviewRequestCount += 1;
      const delayedFailure = options.delayFirstOverviewFailure && requestNumber === 0;
      if (delayedFailure) await firstOverviewGate;
      const overviewStatus = delayedFailure ? 500 : options.overviewStatus;
      if (overviewStatus && overviewStatus !== 200) {
        await fulfillJson(
          route,
          {
            detail: "Сессия отклонена",
            code: "admin_session_rejected",
            correlation_id: "test-correlation-id"
          },
          overviewStatus
        );
        overviewResponses.push(overviewStatus);
        return;
      }
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
      overviewResponses.push(200);
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

    if (url.pathname === "/api/admin/traffic/summary") {
      if (options.trafficStatus && options.trafficStatus !== 200) {
        await fulfillJson(
          route,
          { detail: "Доступ к сводке отклонён", code: "traffic_access_rejected", correlation_id: "traffic-test-id" },
          options.trafficStatus
        );
        return;
      }
      await fulfillJson(route, { rows: [] });
      return;
    }

    if (url.pathname === "/api/admin/search") {
      if (options.searchStatus === 404) {
        await fulfillJson(route, { detail: "Сервис временно выключен" }, 404);
        return;
      }
      await fulfillJson(
        route,
        { results: options.includeUnsafeSearchResults ? [...searchResults, ...unsafeSearchResults] : searchResults },
        options.searchStatus ?? 200
      );
      return;
    }

    const minimalPayloads: Record<string, unknown> = {
      "/api/admin/alerts": { alerts: [] },
      "/api/admin/free-tier/users": { users: [] },
      "/api/admin/nodes/timeseries": { rows: [] },
      "/api/admin/provider-quotas": { quotas: [] },
      "/api/admin/nodes/health": { nodes: [] },
      "/api/admin/nodes/runtime": { ok: true, nodes: [] },
      "/api/admin/online/users": { ok: true, generated_at: generatedAt, rows: [] },
      "/api/admin/payments/orders": { orders: [] },
      "/api/admin/keys/pressure": { rows: [] },
      "/api/admin/tickets": { tickets: [] },
      "/api/admin/live-updates": { updates: [] },
      "/api/admin/funnel/summary": { stages: [], sources: [] },
      "/api/admin/users": { page: 1, page_size: 80, total: 0, sort: "created_desc", users: [] },
      "/api/admin/promos": { promos: [] },
      "/api/admin/referrals/pending": { rows: [] }
    };
    const payload = minimalPayloads[url.pathname];
    if (payload !== undefined) {
      await fulfillJson(route, payload);
      return;
    }

    await fulfillJson(
      route,
      { detail: "Focused fixture response missing", code: "fixture_contract_error", method, path: url.pathname },
      501
    );
  });

  return { calls, overviewResponses, releaseFirstOverview };
}
