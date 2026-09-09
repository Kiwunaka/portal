import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

const apiCorsHeaders = {
  "access-control-allow-origin": "http://127.0.0.1:3107",
  "access-control-allow-credentials": "true",
  "access-control-allow-methods": "GET,POST,PATCH,DELETE,OPTIONS",
  "access-control-allow-headers": "authorization,content-type,x-telegram-init-data,x-web-auth-token"
};

const expectedGroups = [
  {
    label: "Моя смена",
    links: [["Моя смена", "/shift"], ["Главная", "/"]]
  },
  {
    label: "Пользователи и поддержка",
    links: [
      ["Пользователи и поддержка", "/support"],
      ["Пользователи", "/users"],
      ["Сейчас онлайн", "/online"],
      ["Тикеты", "/tickets"]
    ]
  },
  {
    label: "Сеть и инциденты",
    links: [
      ["Сеть и инциденты", "/network"],
      ["Ноды", "/nodes"],
      ["Трафик", "/traffic"],
      ["Алерты", "/alerts"],
      ["Incident Room", "/incidents"],
      ["Лимиты провайдеров", "/provider-caps"],
      ["Экстренная сеть", "/emergency-network"]
    ]
  },
  {
    label: "Деньги и доступ",
    links: [
      ["Деньги и доступ", "/money"],
      ["Платежи", "/payments"],
      ["Доступ", "/access"],
      ["Архив FREE", "/free-tier"],
      ["Промокоды", "/promos"]
    ]
  },
  {
    label: "Рост и коммуникации",
    links: [
      ["Рост и коммуникации", "/growth"],
      ["Воронка", "/funnel"],
      ["Бонусы", "/bonuses"],
      ["Программы", "/programs"],
      ["Рефералы", "/referrals"],
      ["Рассылка", "/broadcast"],
      ["Новости", "/news"]
    ]
  },
  {
    label: "Релизы и клиенты",
    links: [
      ["Релизы и клиенты", "/releases"],
      ["Релиз", "/release"]
    ]
  },
  {
    label: "Управление системой",
    links: [["Управление системой", "/governance"]]
  }
] as const;

function isShellIdentityGet(path: string): boolean {
  return path === "/api/admin/v2/auth/me" || path === "/api/admin/v2/meta";
}

test("серверная cookie-сессия проверяется без чтения legacy bearer из Web Storage", async ({ page }) => {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("pokrov_admin_session_token", "forbidden-session-token");
    window.localStorage.setItem("pokrov_admin_init_data", "forbidden-init-data");
  });
  const api = await installAdminApiMock(page);

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
  await expect.poll(() => api.calls.some((call) => (
    call.method === "GET"
    && call.path === "/api/admin/v2/auth/me"
    && !call.headers?.authorization
  ))).toBe(true);
  await expect.poll(() => page.evaluate(() => ({
    token: window.sessionStorage.getItem("pokrov_admin_session_token"),
    initData: window.localStorage.getItem("pokrov_admin_init_data")
  }))).toEqual({ token: null, initData: null });
  expect(api.calls.some((call) => call.method === "POST" && call.path === "/api/admin/v2/auth/bootstrap")).toBe(false);
  expect(api.calls.some((call) => call.method === "POST" && call.path === "/api/admin/auth/session")).toBe(false);
});

test("Telegram runtime initData доступен только через явный compatibility-вход", async ({ page }) => {
  const initData = "query_id=test&user=%7B%22id%22%3A9999%7D&auth_date=1&hash=test";
  await page.addInitScript((runtimeInitData) => {
    (window as typeof window & { Telegram?: { WebApp?: { initData?: string } } }).Telegram = {
      WebApp: { initData: runtimeInitData }
    };
  }, initData);
  const api = await installAdminApiMock(page, { requireInitDataForSession: true });
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Вход в админку" })).toBeVisible();
  expect(api.calls.some((call) => call.method === "POST" && call.path === "/api/admin/v2/auth/bootstrap")).toBe(false);
  await page.getByRole("button", { name: "Compatibility-вход" }).click();
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
  await expect(page.getByLabel("Telegram WebApp initData")).toHaveCount(0);
  await expect.poll(() => api.calls.some((call) => (
    call.method === "POST"
    && call.path === "/api/admin/v2/auth/bootstrap"
    && call.headers?.["x-telegram-init-data"] === initData
  ))).toBe(true);
  expect(await page.evaluate(() => window.sessionStorage.getItem("pokrov_admin_init_data"))).toBeNull();
});

test("OIDC callback открывает cookie-сессию и удаляет code/state из URL", async ({ page }) => {
  const api = await installAdminApiMock(page, { operatorSessionInitiallyMissing: true });
  await page.goto("/?code=operator-code-1234&state=operator-oidc-state-123456");

  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
  await expect.poll(() => api.calls.some((call) => (
    call.method === "POST"
    && call.path === "/api/admin/v2/auth/oidc/finish"
    && (call.body as { code?: string; state?: string })?.code === "operator-code-1234"
    && (call.body as { code?: string; state?: string })?.state === "operator-oidc-state-123456"
  ))).toBe(true);
  await expect(page).toHaveURL(/\/$/);
  expect(api.calls.some((call) => call.headers?.authorization)).toBe(false);
});

test("оболочка группирует семь рабочих областей и открывает палитру с клавиатуры", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  const navigation = page.getByRole("navigation", { name: "Рабочие области центра управления" });
  const groups = navigation.getByRole("region");
  await expect(groups).toHaveCount(expectedGroups.length);
  for (const [groupIndex, group] of expectedGroups.entries()) {
    const region = groups.nth(groupIndex);
    await expect(region).toHaveAccessibleName(group.label);
    const links = region.getByRole("link");
    await expect(links).toHaveCount(group.links.length);
    for (const [index, [label, href]] of group.links.entries()) {
      await expect(links.nth(index)).toHaveAccessibleName(label);
      await expect(links.nth(index)).toHaveAttribute("href", href);
    }
  }
  const commandsButton = page.getByRole("button", { name: "Команды" });
  await commandsButton.focus();
  await expect(commandsButton).toBeFocused();
  await page.keyboard.press("Control+k");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeVisible();
  await expect(page.getByRole("searchbox", { name: "Глобальный поиск" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeHidden();
  await expect(commandsButton).toBeFocused();
});

test("верхняя панель показывает фактический статус API, сессии и timestamp источника", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  const banner = page.getByRole("banner");
  await expect(page.getByLabel("Состояние API: Норма")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Норма")).toBeVisible();
  await expect(banner.locator('time[datetime="2026-07-15T09:50:00Z"]')).toBeVisible();
  await expect(page.getByText(/Старейший источник:/)).not.toContainText("Нет данных");
  await expect(banner.getByText("Среда", { exact: true }).locator("..")).toContainText("test");
  await expect(banner.getByText("FE", { exact: true }).locator("..").locator("dd")).toHaveText(/^[a-f0-9]{8}$/);
  await expect(banner.getByText("API", { exact: true }).locator("..").locator("dd")).toHaveText("admin-v2.1");
  await expect(banner.getByText("Клиент", { exact: true }).locator("..")).toContainText("1.2.0-rc.1");
  await expect(banner.locator('time[datetime="2026-07-15T10:30:00Z"]')).toBeVisible();
  await expect(banner.getByText("Source", { exact: true }).locator("..").locator("dd")).toHaveText(/^(clean|dirty)$/);
});

test("несовпадение frontend/API identity блокирующе видно в оболочке", async ({ page }) => {
  await installAdminApiMock(page, { apiSchema: "admin-v2.99" });
  await page.goto("/");

  const mismatch = page.getByRole("alert").filter({ hasText: "Несовпадение кандидата" });
  await expect(mismatch).toBeVisible();
  await expect(mismatch).toContainText("api_schema_mismatch");
  await expect(mismatch).toContainText("Остановите cutover");
});

test("главная не загружает данные скрытых разделов", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/");
  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/v2/shift/overview")).toBe(true);

  expect(api.calls.map((call) => call.path)).not.toContain("/api/admin/users?page_size=50");
  expect(api.calls.map((call) => call.path)).not.toContain("/api/admin/nodes/runtime");
  expect(api.calls.map((call) => call.path)).not.toContain("/api/admin/payments/orders?limit=80");
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
});

test("каждый раздел запрашивает только собственные источники", async ({ page }) => {
  const api = await installAdminApiMock(page);
  const routes: ReadonlyArray<{ href: string; label: string; paths: readonly RegExp[] }> = [
    { href: "/", label: "Главная", paths: [/^\/api\/admin\/v2\/shift\/overview$/, /^\/api\/admin\/v2\/network\/ru\/latest$/] },
    { href: "/shift", label: "Моя смена", paths: [/^\/api\/admin\/v2\/shift$/] },
    { href: "/nodes", label: "Ноды", paths: [/^\/api\/admin\/v2\/network\/fleet$/, /^\/api\/admin\/v2\/network\/ru\/latest$/] },
    { href: "/traffic", label: "Трафик", paths: [/^\/api\/admin\/v2\/network\/traffic\?from=.+&to=.+$/] },
    { href: "/alerts", label: "Алерты", paths: [/^\/api\/admin\/v2\/network\/alerts\?status=active$/] },
    { href: "/incidents", label: "Incident Room", paths: [/^\/api\/admin\/v2\/incidents$/] },
    { href: "/provider-caps", label: "Лимиты провайдеров", paths: [/^\/api\/admin\/v2\/network\/providers$/] },
    { href: "/emergency-network", label: "Экстренная сеть", paths: [/^\/api\/admin\/v2\/network\/emergency$/] },
    { href: "/free-tier", label: "Архив FREE", paths: [/^\/api\/admin\/v2\/money\/free-archive\?limit=500$/] },
    { href: "/access", label: "Доступ", paths: [/^\/api\/admin\/v2\/money\/access$/] },
    { href: "/users", label: "Пользователи", paths: [/^\/api\/admin\/users\?page_size=80&offset=0&sort=created_desc$/, /^\/api\/admin\/v2\/support\/online\?limit=200$/] },
    { href: "/online", label: "Сейчас онлайн", paths: [/^\/api\/admin\/v2\/support\/online\?limit=200$/] },
    { href: "/tickets", label: "Тикеты", paths: [/^\/api\/admin\/v2\/support\/tickets\?status=&limit=100$/] },
    { href: "/payments", label: "Платежи", paths: [/^\/api\/admin\/v2\/money\/payments\/summary\?period=7d$/, /^\/api\/admin\/v2\/money\/payments\/orders\?limit=80$/] },
    { href: "/funnel", label: "Воронка", paths: [/^\/api\/admin\/v2\/growth\/funnel\?from=.+&to=.+$/] },
    { href: "/promos", label: "Промокоды", paths: [/^\/api\/admin\/v2\/money\/promos\?limit=100$/, /^\/api\/admin\/promo-slots$/, /^\/api\/admin\/campaigns\?limit=200$/] },
    { href: "/bonuses", label: "Бонусы", paths: [/^\/api\/admin\/v2\/growth\/bonuses$/] },
    { href: "/programs", label: "Программы", paths: [/^\/api\/admin\/v2\/growth\/programs\?limit=200$/] },
    { href: "/referrals", label: "Рефералы", paths: [/^\/api\/admin\/v2\/growth\/referrals\?limit=100&status=pending$/, /^\/api\/admin\/v2\/growth\/referrals\?limit=100&status=rewarded$/] },
    { href: "/release", label: "Релиз", paths: [/^\/api\/admin\/v2\/releases\/candidates\?limit=50$/, /^\/api\/admin\/v2\/releases\/candidates\/[a-f0-9]{64}\/cockpit\?hours=24$/] },
    { href: "/broadcast", label: "Рассылка", paths: [] },
    { href: "/news", label: "Новости", paths: [/^\/api\/admin\/v2\/growth\/news-drafts\?status=all&limit=100$/] },
    { href: "/governance", label: "Управление системой", paths: [
      /^\/api\/admin\/v2\/governance\/roles$/,
      /^\/api\/admin\/v2\/governance\/operators\?limit=200$/,
      /^\/api\/admin\/v2\/governance\/operators\/[0-9a-f-]{36}$/,
      /^\/api\/admin\/v2\/governance\/audit\?limit=100$/,
      /^\/api\/admin\/v2\/governance\/privacy$/,
      /^\/api\/admin\/v2\/governance\/sensitive-access\?limit=100$/,
    ] }
  ];

  for (const route of routes) {
    const firstCall = api.calls.length;
    await page.goto(route.href);
    await expect(page.getByRole("heading", { name: route.label, exact: true, level: 1 })).toBeVisible();
    if (route.paths.length) {
      await expect.poll(() => {
        const calls = api.calls.slice(firstCall).filter((call) => call.method === "GET" && !isShellIdentityGet(call.path)).map((call) => call.path);
        return route.paths.every((pattern) => calls.some((path) => pattern.test(path)));
      }).toBe(true);
    } else {
      await page.waitForTimeout(150);
    }
    const calls = api.calls.slice(firstCall).filter((call) => call.method === "GET" && !isShellIdentityGet(call.path)).map((call) => call.path);
    expect(calls.every((path) => route.paths.some((pattern) => pattern.test(path))), `скрытый GET на ${route.href}: ${calls.join(", ")}`).toBe(true);
  }
});

test("клиентская навигация из промо изолирует сбой рефералов и старое состояние", async ({ page }) => {
  await installAdminApiMock(page, {
    promoRows: [{ id: 701, code: "PROMO-ONLY-701", status: "active", promo_type: "days" }],
    referralsStatus: 503
  });
  await page.goto("/promos");
  await expect(page.getByText("PROMO-ONLY-701", { exact: true }).first()).toBeVisible();
  await page.evaluate(() => {
    document.documentElement.dataset.task3ShellInstance = "preserved";
  });

  await page.getByRole("link", { name: "Рефералы", exact: true }).click();

  await expect(page).toHaveURL(/\/referrals$/);
  expect(await page.evaluate(() => document.documentElement.dataset.task3ShellInstance)).toBe("preserved");
  await expect(page.getByRole("heading", { name: "Рефералы", exact: true, level: 1 })).toBeVisible();
  await expect(page.getByText("PROMO-ONLY-701", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("alert").filter({ hasText: "referrals_unavailable" }).first()).toBeVisible();
  await expect(page.getByRole("button", { name: "Повторить очередь" })).toBeVisible();
});

test("раздел без доменных чтений отделяет подтверждённую сессию от локального 401", async ({ page }) => {
  const api = await installAdminApiMock(page, { broadcastStatus: 401 });
  await page.goto("/broadcast");
  await expect(page.getByLabel("Состояние API: Нет данных")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Нет данных")).toBeVisible();
  await expect(page.getByLabel("Состояние API: Норма")).toHaveCount(0);

  await page.getByLabel("Текст рассылки").fill("Проверка локального отказа");
  await page.getByRole("button", { name: "Подготовить защищённый предпросмотр" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("ОТПРАВИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("Действие завершилось с ошибкой", { exact: true })).toBeVisible();
  await expect(dialog.getByText("ID обращения: broadcast-test-id", { exact: true })).toBeVisible();
  await expect.poll(() => api.calls.some((call) => call.method === "POST" && /^\/api\/admin\/v2\/growth\/action-intents\/[0-9a-f-]{36}\/execute$/.test(call.path))).toBe(true);
  await expect(page.getByLabel("Состояние API: Нет данных")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Нет данных")).toBeVisible();
});

test("отключённый ресурс не показывает карточку предыдущего ключа", async ({ page }) => {
  const userQueries: string[] = [];
  await installAdminApiMock(page);
  await page.route("**/api/admin/users**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: apiCorsHeaders, body: "" });
      return;
    }
    if (url.pathname === "/api/admin/users/1001") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: apiCorsHeaders,
        body: JSON.stringify({
          user: { tg_id: 1001, display_name: "Тестовый пользователь", status: "active", sub_type: "paid" },
          summary: {},
          keys: [],
          observer: { state: "ok", recent_nodes: [] },
          risk: {},
          tickets: [],
          payment_orders: [],
          key_history: [],
          admin_actions: []
        })
      });
      return;
    }
    if (url.pathname === "/api/admin/users") {
      const query = url.searchParams.get("q") || "";
      userQueries.push(query);
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: apiCorsHeaders,
        body: JSON.stringify({
          page: 1,
          page_size: 80,
          total: query ? 0 : 1,
          sort: "created_desc",
          users: query ? [] : [{ tg_id: 1001, display_name: "Тестовый пользователь", status: "active", sub_type: "paid" }]
        })
      });
      return;
    }
    await route.fallback();
  });

  await page.goto("/users");
  await page.getByRole("button", { name: /Тестовый пользователь/ }).click();
  await expect(page.getByRole("heading", { name: "Пользователь 1001" })).toBeVisible();
  await page.getByPlaceholder("Telegram ID, имя, ID установки, почта").fill("nobody");
  await page.getByRole("button", { name: "Найти" }).click();
  await expect.poll(() => userQueries.includes("nobody")).toBe(true);

  await expect(page.getByText("Пользователи не найдены", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Пользователь 1001" })).toHaveCount(0);
});

test("polling работает только на видимой активной главной и очищается при уходе", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-07-16T00:00:00Z") });
  await page.addInitScript(() => {
    let visibility: DocumentVisibilityState = "visible";
    Object.defineProperty(document, "visibilityState", {
      configurable: true,
      get: () => visibility
    });
    const controlledWindow = window as typeof window & {
      __setAdminVisibility?: (next: DocumentVisibilityState) => void;
    };
    controlledWindow.__setAdminVisibility = (next) => {
      visibility = next;
      document.dispatchEvent(new Event("visibilitychange"));
    };
  });
  const api = await installAdminApiMock(page);
  const overviewCount = () => api.calls.filter((call) => call.path === "/api/admin/v2/shift/overview").length;
  const ruLatestCount = () => api.calls.filter((call) => call.path === "/api/admin/v2/network/ru/latest").length;

  await page.goto("/");
  await page.clock.runFor(1);
  await expect.poll(overviewCount).toBe(1);
  await expect.poll(ruLatestCount).toBe(1);

  await page.clock.fastForward(60_000);
  await expect.poll(overviewCount).toBe(2);
  await expect.poll(ruLatestCount).toBe(2);

  await page.evaluate(() => {
    (window as typeof window & { __setAdminVisibility?: (next: DocumentVisibilityState) => void }).__setAdminVisibility?.("hidden");
  });
  const countBeforeHiddenWindow = overviewCount();
  const ruCountBeforeHiddenWindow = ruLatestCount();
  await page.clock.fastForward(180_000);
  expect(overviewCount()).toBe(countBeforeHiddenWindow);
  expect(ruLatestCount()).toBe(ruCountBeforeHiddenWindow);

  await page.evaluate(() => {
    (window as typeof window & { __setAdminVisibility?: (next: DocumentVisibilityState) => void }).__setAdminVisibility?.("visible");
  });
  await expect.poll(overviewCount).toBe(countBeforeHiddenWindow + 1);
  await expect.poll(ruLatestCount).toBe(ruCountBeforeHiddenWindow + 1);
  await page.clock.fastForward(60_000);
  await expect.poll(overviewCount).toBe(countBeforeHiddenWindow + 2);
  await expect.poll(ruLatestCount).toBe(ruCountBeforeHiddenWindow + 2);

  await page.getByRole("link", { name: "Ноды", exact: true }).click();
  await expect(page).toHaveURL(/\/nodes$/);
  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/v2/network/fleet")).toBe(true);
  const countAfterUnmount = overviewCount();
  const ruCountAfterUnmount = ruLatestCount();
  await page.clock.fastForward(180_000);
  expect(overviewCount()).toBe(countAfterUnmount);
  expect(ruLatestCount()).toBe(ruCountAfterUnmount);
});

test("главная показывает отдельную свежесть RU-origin с временем, причиной и порогом", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/");

  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/v2/network/ru/latest")).toBe(true);
  const ruRow = page.locator("span", { hasText: /^RU-origin$/ }).locator("xpath=../../..");
  await expect(ruRow).toContainText("Текущий пригодный запуск");
  await expect(ruRow.locator('time[datetime="2026-07-15T09:50:00Z"]').first()).toBeVisible();
  await ruRow.getByRole("button", { name: "Показать пояснение" }).focus();
  await expect(page.getByRole("tooltip").filter({ hasText: "ИсточникRU-origin" })).toContainText("7 ч");
});

test("главная переводит реальные причины сбоя и неполной RU-проверки", async ({ page }) => {
  await installAdminApiMock(page, {
    ruLatestReasonCodes: ["required_target_failed", "required_target_incomplete"]
  });
  await page.goto("/");

  const ruRow = page.locator("span", { hasText: /^RU-origin$/ }).locator("xpath=../../..");
  await expect(ruRow).toContainText("Обязательная цель RU-проверки завершилась сбоем");
  await page.getByRole("main").getByRole("button", { name: "Обновить", exact: true }).click();
  await expect(ruRow).toContainText("Обязательная цель RU-проверки проверена не полностью");
  await expect(ruRow).not.toContainText("required_target_");
});

test("сбой RU-origin не скрывает overview и имеет локальный повтор", async ({ page }) => {
  const api = await installAdminApiMock(page, { ruLatestStatus: 503 });
  await page.goto("/");

  await expect(page.getByText("Активные пользователи", { exact: true })).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "RU-origin не загрузился" })).toBeVisible();
  const retry = page.getByRole("button", { name: "Повторить загрузку RU-origin" });
  await expect(retry).toBeVisible();
  const beforeRetry = api.calls.filter((call) => call.path === "/api/admin/v2/network/ru/latest").length;
  await retry.click();
  await expect.poll(() => api.calls.filter((call) => call.path === "/api/admin/v2/network/ru/latest").length).toBeGreaterThan(beforeRetry);
});

test("очередь действий сортируется детерминированно и не подменяет пропуски нулём", async ({ page }) => {
  await installAdminApiMock(page, {
    overviewAlerts: [
      { id: 30, fingerprint: "critical-late", source: "node", severity: "critical", status: "active", title: "Поздний критичный", affected_count: 5, last_seen_at: "2026-07-15T12:00:00Z" },
      { id: 20, fingerprint: "critical-b", source: "node", severity: "critical", status: "active", title: "Критичный B", affected_count: 5, last_seen_at: "2026-07-15T10:00:00Z" },
      { id: 10, fingerprint: "critical-a", source: "node", severity: "critical", status: "active", title: "Критичный A", affected_count: 5, last_seen_at: "2026-07-15T10:00:00Z" },
      { id: 40, fingerprint: "critical-missing", source: "node", severity: "critical", status: "active", title: "Критичный без охвата", affected_count: null, last_seen_at: "2026-07-15T09:00:00Z" },
      { id: 50, fingerprint: "warning-large", source: "quota", severity: "warning", status: "active", title: "Большое предупреждение", affected_count: 100, last_seen_at: "2026-07-15T08:00:00Z" }
    ]
  });

  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
  await expect.poll(() => page.locator("[data-action-id]").evaluateAll((rows) => rows.map((row) => row.getAttribute("data-action-id")))).toEqual([
    "critical-a",
    "critical-b",
    "critical-late",
    "critical-missing",
    "warning-large"
  ]);
  await expect(page.locator('[data-action-id="critical-missing"]')).toContainText("Нет данных");
  await expect(page.locator('[data-action-id="critical-missing"]')).not.toContainText(/Охват:\s*0/);
});

test("выбор сигнала перестраивает triage локально без нового API-запроса", async ({ page }) => {
  const api = await installAdminApiMock(page, {
    overviewAlerts: [
      {
        id: 61,
        fingerprint: "node_metrics:de:disk_high",
        source: "node_metrics",
        severity: "warning",
        status: "active",
        title: "DE: диск выше порога",
        body: "Первый сигнал",
        node_code: "de",
        affected_count: 1,
        first_seen_at: "2026-07-15T09:00:00Z",
        last_seen_at: "2026-07-15T09:10:00Z"
      },
      {
        id: 62,
        fingerprint: "node_metrics:nl:latency_high",
        source: "node_metrics",
        severity: "warning",
        status: "active",
        title: "NL: Panel API отвечает медленно",
        body: "Второй сигнал",
        node_code: "nl",
        affected_count: 1,
        first_seen_at: "2026-07-15T10:00:00Z",
        last_seen_at: "2026-07-15T10:10:00Z"
      }
    ]
  });

  await page.goto("/");
  await expect(page.getByRole("button", { name: "Открыть сигнал: DE: диск выше порога" })).toHaveAttribute("aria-pressed", "true");
  await expect.poll(() => api.calls.filter((call) => call.method === "GET" && !isShellIdentityGet(call.path)).length).toBe(2);
  const callsBeforeSelection = api.calls.length;

  await page.getByRole("button", { name: "Открыть сигнал: NL: Panel API отвечает медленно" }).click();

  await expect(page.getByRole("button", { name: "Открыть сигнал: NL: Panel API отвечает медленно" })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByRole("button", { name: "Открыть сигнал: DE: диск выше порога" })).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("heading", { name: "NL: Panel API отвечает медленно", level: 2 })).toBeVisible();
  expect(api.calls).toHaveLength(callsBeforeSelection);
});

test("главная использует алерты из overview без второго тяжёлого запроса", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/");
  await expect(page.getByText("Активные пользователи", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Требует реакции" })).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/alerts?status=active")).toBe(false);
});

test("обновление сохраняет последний успешный overview и показывает состояние", async ({ page }) => {
  await installAdminApiMock(page);
  let releaseSecondOverview: () => void = () => undefined;
  const secondOverviewGate = new Promise<void>((resolve) => {
    releaseSecondOverview = resolve;
  });
  let overviewCalls = 0;
  await page.route("**/api/admin/v2/shift/overview", async (route) => {
    overviewCalls += 1;
    if (overviewCalls === 2) await secondOverviewGate;
    await route.fallback();
  });

  await page.goto("/");
  const activeUsers = page.getByText("Активные пользователи", { exact: true }).locator("..");
  await expect(activeUsers).toContainText("88");

  await page.getByRole("banner").getByRole("button", { name: "Обновить" }).click();
  await expect.poll(() => overviewCalls).toBe(2);
  await expect(activeUsers).toContainText("88");
  await expect(page.getByText("Обновляем", { exact: true }).last()).toBeVisible();

  releaseSecondOverview();
  await expect(page.getByText("Обновляем", { exact: true })).toHaveCount(0);
  await expect(activeUsers).toContainText("88");
});

test("ошибка route-scoped refresh сохраняет last-good данные и помечает их деградацию", async ({ page }) => {
  await installAdminApiMock(page);
  let overviewCalls = 0;
  await page.route("**/api/admin/v2/shift/overview", async (route) => {
    overviewCalls += 1;
    if (overviewCalls === 1) {
      await route.fallback();
      return;
    }
    await route.fulfill({
      status: 503,
      headers: { ...apiCorsHeaders, "content-type": "application/json; charset=utf-8" },
      body: JSON.stringify({ detail: "overview temporarily unavailable" })
    });
  });

  await page.goto("/");
  const activeUsers = page.getByText("Активные пользователи", { exact: true }).locator("..");
  await expect(activeUsers).toContainText("88");
  await page.getByRole("banner").getByRole("button", { name: "Обновить" }).click();

  await expect.poll(() => overviewCalls).toBe(2);
  await expect(activeUsers).toContainText("88");
  await expect(page.getByRole("alert").filter({ hasText: "Последние успешные данные сохранены" })).toBeVisible();
  await expect(page.getByLabel("Состояние API: Требует внимания")).toBeVisible();
});

test("битый success envelope Admin API v2 отклоняется без ложного успеха", async ({ page }) => {
  await installAdminApiMock(page);
  await page.route("**/api/admin/v2/shift/overview", async (route) => {
    await route.fulfill({
      status: 200,
      headers: { ...apiCorsHeaders, "content-type": "application/json; charset=utf-8" },
      body: JSON.stringify({
        data: { generated_at: "2026-07-15T09:50:00Z" },
        meta: {
          generated_at: "2026-07-15T09:50:00Z",
          schema_version: "admin-v2.1",
          query_ms: 1,
          trace_id: null
        },
        sources: []
      })
    });
  });

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Источник не ответил" })).toBeVisible();
  await expect(page.getByText(/Технический код: admin_v2_envelope_invalid\./)).toBeVisible();
  await expect(page.getByLabel("Состояние API: Требует внимания")).toBeVisible();
  await expect(page.getByText("Активные пользователи", { exact: true })).toHaveCount(0);
});

test("обычный 401 от overview показывает деградацию и сбой сессии без access-evidence", async ({ page }) => {
  await installAdminApiMock(page, { overviewStatus: 401 });
  await page.goto("/");

  await expect(page.getByLabel("Состояние API: Требует внимания")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Сбой")).toBeVisible();
  await expect(page.getByLabel("Состояние API: Доступ заблокирован")).toHaveCount(0);
  await expect(page.getByLabel("Состояние сессии: Доступ заблокирован")).toHaveCount(0);
  await expect(page.getByLabel("Состояние сессии: Норма")).toHaveCount(0);
});

test("401 выбранного traffic-раздела не выглядит нормой", async ({ page }) => {
  await installAdminApiMock(page, { trafficStatus: 401 });
  await page.goto("/traffic");

  await expect(page.getByLabel("Состояние API: Сбой")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Сбой")).toBeVisible();
  await expect(page.getByLabel("Состояние API: Норма")).toHaveCount(0);
  await expect(page.getByLabel("Состояние сессии: Норма")).toHaveCount(0);
});

test("нулевой реальный успех не маскируется synthetic module result", async ({ page }) => {
  await installAdminApiMock(page, { failAllLegacyRequests: true, overviewStatus: 500, ruLatestStatus: 503 });
  await page.goto("/");

  await expect(page.getByLabel("Состояние API: Сбой")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Недоступно")).toBeVisible();
  await expect(page.getByLabel("Состояние API: Требует внимания")).toHaveCount(0);
  await expect(page.getByLabel("Состояние сессии: Норма")).toHaveCount(0);
});

test("прерванная старая загрузка не перезаписывает новый маршрут", async ({ page }) => {
  const api = await installAdminApiMock(page, { delayFirstOverviewFailure: true, ruScenario: "fresh-pass" });
  const abortedOverview = page.waitForEvent("requestfailed", {
    predicate: (request) => new URL(request.url()).pathname === "/api/admin/v2/shift/overview"
  });
  await page.goto("/");
  await expect.poll(() => api.calls.filter((call) => call.path === "/api/admin/v2/shift/overview").length).toBe(1);

  await page.getByRole("link", { name: "Ноды", exact: true }).click();
  await expect(page).toHaveURL(/\/nodes$/);
  await expect.poll(() => api.calls.filter((call) => call.path === "/api/admin/v2/network/fleet").length).toBe(1);
  expect(api.calls.filter((call) => call.path === "/api/admin/v2/shift/overview")).toHaveLength(1);
  await abortedOverview;
  await expect(page.getByLabel("Состояние API: Норма")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Норма")).toBeVisible();

  api.releaseFirstOverview();
  await page.evaluate(() => new Promise<void>((resolve) => {
    requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
  }));

  await expect(page.getByLabel("Состояние API: Норма")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Норма")).toBeVisible();
  await expect(page.getByRole("banner").locator('time[datetime="2026-07-15T09:50:00Z"]')).toBeVisible();
  await expect(page.getByText("Сессия отклонена", { exact: true })).toHaveCount(0);
});

test("таймаут загрузки с сигналом экрана показывает повтор вместо вечной загрузки", async ({ page }) => {
  await page.clock.install();
  await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  let releaseFirst!: () => void;
  const firstResponse = new Promise<void>((resolve) => { releaseFirst = resolve; });
  let calls = 0;
  await page.route("**/api/admin/v2/network/fleet", async (route) => {
    calls += 1;
    if (calls === 1) await firstResponse;
    await route.fallback();
  });

  try {
    await page.goto("/nodes");
    await expect.poll(() => calls).toBe(1);
    await page.clock.runFor(16_000);
    const retry = page.getByRole("button", { name: "Повторить загрузку нод", exact: true });
    await expect(retry).toBeVisible();
    await retry.click();
    await expect.poll(() => calls).toBe(2);
    await expect(page.getByRole("table", { name: "Список нод" })).toBeVisible();
    await expect(retry).toHaveCount(0);
  } finally {
    releaseFirst();
  }
});

test("поиск начинается с двух символов и ведёт по безопасному canonical href", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/nodes?keep=1");

  const commandsButton = page.getByRole("button", { name: "Команды" });
  await commandsButton.click();
  const search = page.getByRole("searchbox", { name: "Глобальный поиск" });
  await search.fill(" n ");
  await page.waitForTimeout(300);
  expect(api.calls.filter((call) => call.path.startsWith("/api/admin/search?")).length).toBe(0);

  await search.fill(" nl ");
  await expect.poll(() => api.calls.filter((call) => call.path === "/api/admin/search?q=nl").length).toBe(1);
  await page.getByRole("button", { name: /Нода NL/ }).click();

  await expect(page).toHaveURL(/\/nodes\?selected=nl$/);
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeHidden();
  await expect(commandsButton).toBeFocused();
  expect(api.calls.filter((call) => call.path.startsWith("/api/admin/search?")).every((call) => call.method === "GET")).toBe(true);
});

test("глобальный поиск находит opaque support bundle и открывает связанный кейс", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Команды" }).click();
  await page.getByRole("searchbox", { name: "Глобальный поиск" }).fill("bundle_22222222222222222222");

  await expect.poll(() => api.calls.filter((call) => call.path.startsWith("/api/admin/v2/support/search?")).length).toBe(1);
  await page.getByRole("button", { name: /Пакет поддержки · тикет #501/ }).click();

  await expect(page).toHaveURL(/\/tickets\?selected=501$/);
});

test("поисковая строка и результаты не становятся историей после закрытия палитры", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  const commandsButton = page.getByRole("button", { name: "Команды" });
  await commandsButton.click();
  await page.getByRole("searchbox", { name: "Глобальный поиск" }).fill("nl");
  await expect(page.getByRole("button", { name: /Нода NL/ })).toBeVisible();
  await page.keyboard.press("Escape");
  await commandsButton.click();

  await expect(page.getByRole("searchbox", { name: "Глобальный поиск" })).toHaveValue("");
  await expect(page.getByRole("button", { name: /Нода NL/ })).toHaveCount(0);
  await expect.poll(() => page.evaluate(() => ({
    local: Object.entries(window.localStorage),
    session: Object.entries(window.sessionStorage)
  }))).toEqual({ local: [], session: [] });
});

test("поиск 404 оставляет палитру и текущий маршрут рабочими", async ({ page }) => {
  await installAdminApiMock(page, { searchStatus: 404 });
  await page.goto("/nodes?selected=de");
  await page.getByRole("button", { name: "Команды" }).click();
  await page.getByRole("searchbox", { name: "Глобальный поиск" }).fill("de");

  await expect(page.getByText("Поиск пока недоступен", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeVisible();
  await expect(page).toHaveURL(/\/nodes\?selected=de$/);
  await page.getByRole("button", { name: "Главная" }).click();
  await expect(page).toHaveURL(/\/$/);
});

test("поиск не принимает безопасную метку ID за URL-схему", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");
  await page.getByRole("button", { name: "Команды" }).click();
  await page.getByRole("searchbox", { name: "Глобальный поиск" }).fill("safe");

  await expect(page.getByRole("button", { name: /Безопасная метка ID/ })).toBeVisible();
  await expect(page.getByText("ID: 1001", { exact: true })).toBeVisible();
});

test("поиск независимо отбрасывает каждый запрещённый privacy-класс", async ({ page }) => {
  await installAdminApiMock(page, { includeUnsafeSearchResults: true });
  await page.goto("/");
  await page.getByRole("button", { name: "Команды" }).click();
  await page.getByRole("searchbox", { name: "Глобальный поиск" }).fill("safe");

  await expect(page.getByRole("button", { name: /Нода NL/ })).toBeVisible();
  const unsafeTitles = [
    "Проверка адреса четыре",
    "Проверка адреса шесть кратко",
    "Проверка адреса шесть полно",
    "Проверка веб-ссылки",
    "Проверка сетевого пути",
    "Проверка доменного пути",
    "Проверка схемы",
    "Проверка английского слова",
    "Проверка русского слова",
    "Проверка маркера один",
    "Проверка маркера два",
    "Проверка маркера три",
    "Проверка маркера четыре",
    "Проверка структуры",
    "Проверка фрагмента",
    "Проверка внешнего адреса",
    "Проверка обратной черты",
    "Проверка двойного слеша",
    "Проверка ключа запроса",
    "Проверка значения запроса",
    "Проверка IDN-домена"
  ];
  expect(unsafeTitles).toHaveLength(21);
  for (const unsafeTitle of unsafeTitles) {
    await expect(page.getByText(unsafeTitle, { exact: true })).toHaveCount(0);
  }
});

test("focused API fixture отклоняет неизвестный contract path", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  const result = await page.evaluate(async () => {
    const response = await fetch("/api/admin/not-in-focused-contract");
    return { status: response.status, body: await response.json() as Record<string, unknown> };
  });
  expect(result.status).toBe(501);
  expect(result.body).toMatchObject({
    code: "fixture_contract_error",
    method: "GET",
    path: "/api/admin/not-in-focused-contract"
  });
});

test("назад и вперёд восстанавливают маршрут вместе с чужими query-параметрами", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/nodes?selected=nl&keep=yes");

  await page.getByRole("link", { name: "Пользователи", exact: true }).click();
  await expect(page).toHaveURL(/\/users$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/nodes\?selected=nl&keep=yes$/);
  await expect(page.getByRole("heading", { name: "Ноды", exact: true, level: 1 })).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(/\/users$/);
});

test("на узком экране навигация открывается диалогом", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 900 });
  await installAdminApiMock(page);
  await page.goto("/");

  await page.getByRole("button", { name: "Открыть навигацию" }).click();
  const drawer = page.getByRole("dialog", { name: "Навигация по разделам" });
  await expect(drawer).toBeVisible();
  await drawer.getByRole("link", { name: "Ноды", exact: true }).click();
  await expect(drawer).toBeHidden();
  await expect(page).toHaveURL(/\/nodes$/);
});

test("палитра команд вытесняет мобильную навигацию и возвращает фокус живому opener", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 900 });
  await installAdminApiMock(page);
  await page.goto("/");

  const navigationButton = page.getByRole("button", { name: "Открыть навигацию" });
  await navigationButton.click();
  await expect(page.getByRole("dialog", { name: "Навигация по разделам" })).toBeVisible();

  await page.keyboard.press("Control+k");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Навигация по разделам" })).toHaveCount(0);
  await expect(page.getByRole("dialog")).toHaveCount(1);

  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await expect(navigationButton).toBeFocused();
});
