import { expect, test, type Page } from "@playwright/test";

type TicketMessageMock = {
  id: number;
  sender_role: "user" | "admin";
  body: string;
  created_at?: string | null;
};

type TicketMock = {
  id: number;
  user_tg_id: number;
  status: "open" | "in_progress" | "closed";
  status_title: string;
  subject?: string | null;
  updated_at?: string | null;
  last_message_preview?: string | null;
  messages: TicketMessageMock[];
};

function mockSessionUser() {
  return {
    tg_id: 1001,
    username: "qa_user",
    subscription_url: "https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token",
    is_active: true,
    is_admin: false,
    sub_type: "PAID",
    segment: "PAID",
    access_state: "paid_unlimited",
    expiry_at: "2030-01-01T00:00:00",
    family_slots: 1,
    devices: [
      {
        id: "android-1",
        name: "Pixel 8",
        platform: "android",
        app_version: "1.0.0",
        last_seen_at: "2030-01-01T00:00:00",
        is_active: true,
        is_current: true,
      },
    ],
    sync: {
      app_identity_known: true,
      telegram_linked: true,
      subscription_ready: true,
      device_count: 1,
    },
    nodes: [
      { code: "pl", name: "Poland", host: "pl.pokrov.space", port: 443, enabled: true },
      { code: "us", name: "United States", host: "us.pokrov.space", port: 443, enabled: true },
    ],
    limits: { device_limit: 5, total_gb: 0, speed_mbps: 100 },
    traffic: { used_gb: 12.4, used_bytes: 0, total_gb: 0, remaining_gb: 0, source: "panel_runtime" },
    traffic_policy: {
      kind: "unlimited",
      label: "Безлимитный трафик",
      limit_gb: null,
      remaining_gb: null,
      next_reset_at: null,
      soft_mode_active: false,
    },
    traffic_limit_gb: null,
    traffic_remaining_gb: null,
    next_reset_at: null,
    soft_mode_active: false,
    connections: {
      status: "online",
      active_connections: 2,
      active_users_estimate: 1,
      active_users_source: "panel_ip_count_capped_by_unique_ip_24h",
      active_nodes: 1,
      known_nodes: 2,
      last_online_at: "2030-01-01T00:00:00",
      last_online_age_seconds: 45,
      source: "panel_runtime",
    },
    support: {
      username: "pokrov_supportbot",
      link: "https://t.me/pokrov_supportbot",
      new_ticket_link: "https://t.me/pokrov_supportbot?start=ticket_new",
    },
    bonuses: {
      wheel: { last_spin_at: null, streak_months: 2 },
      referral_count: 1,
      channel_bonus: { premium_days: 10, claimed_at: "2030-01-01T00:00:00", can_claim: false },
    },
    referral: { code: "mock", link: "https://t.me/pokrov_vpnbot?start=ref_mock", bonus_days: 10 },
    channel: { username: "pokrov_vpn", link: "https://t.me/pokrov_vpn", subscriber: true, speed_bump_active: true },
    actions: {
      open_helpbot: "https://t.me/pokrov_supportbot",
      open_channel: "https://t.me/pokrov_vpn",
      pay_via_bot: "https://t.me/pokrov_vpnbot?start=pay",
    },
    points: { available: 90, expiring_soon: 0, monthly_cap: 300, expires_days: 90 },
    features: { haptic: true, lottie: true },
  };
}

function mockDashboard() {
  return {
    tg_id: 1001,
    sub_type: "PAID",
    current_plan_code: "1_month",
    segment: "PAID",
    access_state: "paid_unlimited",
    is_active: true,
    expiry_at: "2030-01-01T00:00:00",
    used_gb: 12.4,
    total_gb: 0,
    remaining_gb: 0,
    active_sessions: 2,
    active_sessions_source: "panel_ip_count",
    device_limit: 5,
    speed_limit_mbps: 100,
    free_next_reset_at: null,
    traffic_policy: {
      kind: "unlimited",
      label: "Безлимитный трафик",
      limit_gb: null,
      remaining_gb: null,
      next_reset_at: null,
      soft_mode_active: false,
    },
    traffic_limit_gb: null,
    traffic_remaining_gb: null,
    next_reset_at: null,
    soft_mode_active: false,
    family_slots: 1,
    subscription_url: "https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token",
    connection_snapshot: {
      status: "online",
      active_connections: 2,
      active_users_estimate: 1,
      active_users_source: "panel_ip_count_capped_by_unique_ip_24h",
      active_nodes: 1,
      known_nodes: 2,
      last_online_at: "2030-01-01T00:00:00",
      last_online_age_seconds: 45,
      source: "panel_runtime",
    },
    active_offer: null,
    points: { available: 90, expiring_soon: 0, monthly_cap: 300, expires_days: 90 },
    features: { haptic: true, lottie: true },
  };
}

function mockTickets(): TicketMock[] {
  return [
    {
      id: 11,
      user_tg_id: 1001,
      status: "open",
      status_title: "Открыт",
      subject: "Подключение после оплаты",
      updated_at: "2030-01-01T00:00:00",
      last_message_preview: "Помогите проверить импорт конфигурации.",
      messages: [
        {
          id: 1,
          sender_role: "user",
          body: "Помогите проверить импорт конфигурации.",
          created_at: "2030-01-01T00:00:00",
        },
      ],
    },
  ];
}

async function registerCabinetMocks(
  page: Page,
  options: { emptyDevices?: boolean; emptyTickets?: boolean } = {},
): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem("portal_web_session_token", "e2e_mock_token");
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => undefined,
      },
    });
  });

  const sessionUser = mockSessionUser();
  if (options.emptyDevices) {
    sessionUser.devices = [];
    sessionUser.sync.device_count = 0;
    sessionUser.connections.active_connections = 0;
    sessionUser.connections.active_nodes = 0;
  }
  const dashboard = mockDashboard();
  if (options.emptyDevices) {
    dashboard.active_sessions = 0;
    dashboard.connection_snapshot.active_connections = 0;
    dashboard.connection_snapshot.active_nodes = 0;
  }
  let tickets = options.emptyTickets ? [] : [...mockTickets()];

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const json = (payload: unknown, status = 200) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(payload),
      });

    if (path === "/api/auth/session") {
      return json({ ok: true, user: { id: 1001, username: "qa_user" } });
    }
    if (path === "/api/dashboard") return json(dashboard);
    if (path.startsWith("/api/user/")) return json(sessionUser);
    if (path === "/api/nodes/status") {
      return json({
        nodes: [
          {
            code: "pl",
            country: "Poland",
            host: "pl.pokrov.space",
            ping_ms: 42,
            port_open: true,
            dns_sni_status: "ok",
            is_healthy: true,
            updated_at: "2030-01-01T00:00:00",
          },
          {
            code: "us",
            country: "United States",
            host: "us.pokrov.space",
            ping_ms: 58,
            port_open: true,
            dns_sni_status: "ok",
            is_healthy: true,
            updated_at: "2030-01-01T00:00:00",
          },
        ],
      });
    }
    if (path === "/api/client/apps") {
      return json({
        android: {
          play_url: "https://play.google.com/store/apps/details?id=space.pokrov.vpn",
          apk_url: "https://downloads.pokrov.space/pokrov-vpn-android.apk",
          mirror_url: "https://mirror.pokrov.space/pokrov-vpn-android.apk",
        },
        windows: {
          exe_url: "https://downloads.pokrov.space/pokrov-vpn-windows.exe",
          mirror_url: "https://mirror.pokrov.space/pokrov-vpn-windows.exe",
        },
        docs_url: "https://pokrov.space/news/",
        updated_at: "2030-01-01T00:00:00",
      });
    }
    if (path === "/api/public/plans") {
      return json({
        widget_enabled: true,
        plans: [
          {
            code: "1_month",
            label: "1 месяц",
            amount_rub: 249,
            amount_stars: 249,
            days: 30,
            device_limit: 5,
            node_policy: "paid_pool",
            badge: "Базовый",
            is_active: true,
            sort_order: 1,
          },
          {
            code: "12_months",
            label: "12 месяцев",
            amount_rub: 1644,
            amount_stars: 1644,
            days: 365,
            device_limit: 5,
            node_policy: "paid_pool",
            badge: "-45%",
            is_active: true,
            sort_order: 2,
          },
        ],
      });
    }
    if (path === "/api/tickets" && request.method() === "GET") {
      return json({ tickets });
    }
    if (path === "/api/tickets" && request.method() === "POST") {
      const payload = JSON.parse(request.postData() || "{}");
      const nextTicket: TicketMock = {
        id: tickets.length + 20,
        user_tg_id: 1001,
        status: "open",
        status_title: "Открыт",
        subject: String(payload.subject || "Новое обращение"),
        updated_at: "2030-01-01T00:05:00",
        last_message_preview: String(payload.body || ""),
        messages: [
          {
            id: 1,
            sender_role: "user",
            body: String(payload.body || ""),
            created_at: "2030-01-01T00:05:00",
          },
        ],
      };
      tickets = [nextTicket, ...tickets];
      return json({ ticket: nextTicket });
    }
    if (path === "/api/tickets/uploads") {
      return json({
        attachment: {
          media_type: "text/plain",
          media_file_id: "mock-upload",
          media_payload: "attachment.bin",
        },
      });
    }
    if (path.startsWith("/api/tickets/")) {
      const ticketId = Number(path.split("/").pop() || 0);
      const ticket = tickets.find((row) => row.id === ticketId) || tickets[0];
      return json({ ticket });
    }

    return json({ ok: true });
  });
}

test.describe("Cabinet flow", () => {
  test.beforeEach(async ({ page }) => {
    await registerCabinetMocks(page);
  });

  test("shows shared POKROV cabinet branding and a site return link", async ({ page }) => {
    await page.goto("/dashboard/");

    await expect(page.getByLabel("POKROV logo").first()).toBeVisible();
    const sidebar = page.getByRole("complementary").first();
    await expect(sidebar).toContainText("Доступ, устройства и помощь в одном спокойном кабинете.");
    await expect(sidebar.locator("nav")).toContainText("Главная");
    await expect(sidebar.locator("nav")).toContainText("Аккаунт");

    const siteLink = page.getByRole("link", { name: /^На сайт/i });
    await expect(siteLink).toBeVisible();
    await expect(siteLink).toHaveAttribute("href", /https:\/\/pokrov\.space\/?$/);
  });

  test("exposes system light and dark theme controls in the shell and profile settings", async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.removeItem("pokrov-theme");
      window.localStorage.removeItem("portal-theme");
      window.localStorage.removeItem("theme");
    });

    await page.goto("/profile/");

    const headerTheme = page.getByRole("banner").getByRole("button", { name: /Тема: системная/i });
    await expect(headerTheme).toBeVisible();

    const settings = page.getByRole("region", { name: "Настройки кабинета" });
    await expect(settings).toContainText("Системная");
    await expect(settings).toContainText("Светлая");
    await expect(settings).toContainText("Темная");

    await settings.getByRole("button", { name: "Темная тема", exact: true }).click();
    await expect(page.locator("html")).toHaveClass(/dark/);
    await expect.poll(() => page.evaluate(() => window.localStorage.getItem("pokrov-theme"))).toBe("dark");

    await settings.getByRole("button", { name: "Системная тема", exact: true }).click();
    await expect.poll(() => page.evaluate(() => window.localStorage.getItem("pokrov-theme"))).toBe("system");
    await expect(headerTheme).toBeVisible();
  });

  test("shows an honest email-soon state on the root auth entry", async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
    });

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Telegram уже работает" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Скоро подключим" })).toBeVisible();
    await expect(page.locator("main")).toContainText(
      "Email-вход для кабинета еще не открыт. Когда он будет готов, он попадет в тот же кабинетный сценарий. Сейчас используйте Telegram.",
    );
    await expect(page.getByRole("button", { name: /Продолжить через email/i })).toHaveCount(0);
  });

  test("keeps the email entry truthful when live delivery is not configured", async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
    });

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Скоро подключим" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Пока недоступно");
    await expect(page.locator("main")).toContainText("используйте Telegram");
    await expect(page.getByRole("button", { name: /^Email$/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Регистрация/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Войти/i })).toHaveCount(0);
  });

  test("reuses an existing web session and lands in the cabinet without showing auth entry again", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect(page.getByRole("heading", { name: "Статус и следующий шаг" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Telegram уже работает" })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Скоро подключим" })).toHaveCount(0);
  });

  test("keeps the dashboard on consumer-safe access actions", async ({ page }) => {
    await page.goto("/dashboard/");

    await expect(page.getByRole("heading", { name: "Статус и следующий шаг" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Активных подключений");
    await expect(page.locator("main")).toContainText("Шаг 1");
    await expect(page.getByRole("link", { name: "Загрузки" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Поддержка", exact: true }).first()).toBeVisible();
    await expect(page.locator("main")).not.toContainText("QR");
    await expect(page.locator("main")).not.toContainText("?format=plain");
    await expect(page.locator("main")).not.toContainText("mock_token");
    await expect(page.getByRole("button", { name: "Показать", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Показать QR" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Скопировать" })).toHaveCount(0);
  });

  test("keeps cabinet navigation on native Next.js routing", async ({ page }) => {
    const stableRequests: Record<string, number> = {
      authSession: 0,
      dashboard: 0,
      user: 0,
      publicPlans: 0,
      clientApps: 0,
    };
    page.on("request", (request) => {
      const url = new URL(request.url());
      if (url.pathname === "/api/auth/session") stableRequests.authSession += 1;
      if (url.pathname === "/api/dashboard") stableRequests.dashboard += 1;
      if (url.pathname.startsWith("/api/user/")) stableRequests.user += 1;
      if (url.pathname === "/api/public/plans") stableRequests.publicPlans += 1;
      if (url.pathname === "/api/client/apps") stableRequests.clientApps += 1;
    });

    await page.goto("/dashboard/");
    await page.evaluate(() => {
      (window as Window & { __routeMarker?: string }).__routeMarker = "persist-me";
    });

    await page.locator("aside nav a[href='/subscription/']").click();
    await expect(page).toHaveURL(/\/subscription\/?$/);
    await expect(page.getByRole("heading", { name: "Продление и режимы" })).toBeVisible();

    await page.locator("aside nav a[href='/downloads/']").click();
    await expect(page).toHaveURL(/\/downloads\/?$/);
    await expect(page.getByRole("heading", { name: "Все нужные загрузки под рукой" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Google Play");

    await page.locator("aside nav a[href='/subscription/']").click();
    await expect(page).toHaveURL(/\/subscription\/?$/);
    await expect(page.getByRole("heading", { name: "Продление и режимы" })).toBeVisible();

    const markerPersisted = await page.evaluate(
      () => Boolean((window as Window & { __routeMarker?: string }).__routeMarker),
    );
    expect(markerPersisted).toBe(true);
    expect(stableRequests).toMatchObject({
      authSession: 1,
      dashboard: 1,
      user: 1,
      publicPlans: 1,
      clientApps: 1,
    });
  });

  test("shows branded root and cabinet not-found recovery screens", async ({ page }) => {
    await page.goto("/no-such-route/");
    await expect(page.getByRole("heading", { name: /Такой страницы .* нет/i })).toBeVisible();
    await expect(page.getByRole("link", { name: "Главная", exact: true }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Поддержка", exact: true }).first()).toBeVisible();

    await page.goto("/dashboard/no-such-route/");
    await expect(page.getByRole("heading", { name: /Такой страницы .* нет/i })).toBeVisible();
    await expect(page.getByRole("link", { name: "Главная", exact: true }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Поддержка", exact: true }).first()).toBeVisible();
  });

  test("keeps the subscription page on renewal and support instead of raw connection sharing", async ({ page }) => {
    await page.goto("/subscription/");

    await expect(page.getByRole("heading", { name: "Продление и режимы" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Перейти к оплате" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Поддержка", exact: true }).first()).toBeVisible();
    await expect(page.locator("main")).not.toContainText("?format=plain");
    await expect(page.locator("main")).not.toContainText("mock_token");
    await expect(page.locator("main")).not.toContainText("QR");
    await expect(page.getByRole("button", { name: "Скопировать" })).toHaveCount(0);
  });

  test("renders runtime connections on devices and redirects statistics into the dashboard", async ({ page }) => {
    await page.goto("/devices/");

    await expect(page.getByRole("heading", { name: "Что уже связано с профилем" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Подключений сейчас");
    await expect(page.locator("main")).toContainText("2 из 5");
    await expect(page.locator("main")).toContainText("Известных устройств");
    await expect(page.locator("main")).toContainText("Маршрут");
    await expect(page.locator("main")).toContainText("1 из 2");

    await page.goto("/statistics/").catch(async () => {
      await page.waitForTimeout(300);
      await page.goto("/statistics/");
    });
    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect(page.getByRole("heading", { name: "Статус и следующий шаг" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Активных подключений");
  });

  test("uses honest empty states when devices or support tickets are not loaded yet", async ({ page }) => {
    await registerCabinetMocks(page, { emptyDevices: true, emptyTickets: true });

    await page.goto("/devices/");
    await expect(page.locator("main")).toContainText("Пока устройств нет");
    await expect(page.locator("main")).toContainText("Скачать приложение");
    await expect(page.locator("main")).toContainText("Поддержка");

    await page.goto("/support/");
    await expect(page.locator("main")).toContainText("Пока обращений нет");
    await expect(page.locator("main")).toContainText("Создать кейс");
    await expect(page.locator("main")).toContainText("Telegram");
  });

  test("keeps cabinet copy human and hides node internals", async ({ page }) => {
    await page.goto("/devices/");
    await expect(page.getByRole("heading", { name: "Что уже связано с профилем" })).toBeVisible();
    await expect(page.getByRole("main")).not.toContainText("pl.pokrov.space");
    await expect(page.getByRole("main")).not.toContainText("us.pokrov.space");
    await expect(page.getByRole("main")).not.toContainText(":443");
    await expect(page.getByRole("main")).not.toContainText("IP");

    await page.goto("/subscription/");
    await expect(page.getByRole("heading", { name: "Продление и режимы" })).toBeVisible();
    await expect(page.getByRole("main")).not.toContainText("mock_token");

    await page.goto("/support/");
    await expect(page.getByRole("heading", { name: "Один кейс на весь вопрос" })).toBeVisible();
    await expect(page.getByRole("main")).not.toContainText("Network");
  });

  test("keeps downloads and support flows usable without the app", async ({ page }) => {
    await page.goto("/dashboard/downloads/");

    await expect(page).toHaveURL(/\/downloads\/?$/);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main")).toContainText("Google Play");
    await expect(page.locator("main a[href*='play.google.com']").first()).toBeVisible();
    await expect(page.locator("main")).toContainText("Windows");
    await expect(page.locator("main a[href*='windows.exe']").first()).toBeVisible();

    await page.goto("/support/");
    await expect(page.getByRole("heading", { name: "Один кейс на весь вопрос" })).toBeVisible();
    await page.getByRole("button", { name: "Новый кейс" }).first().click();
    await page.getByPlaceholder("Коротко: что случилось").fill("Нужна помощь с импортом");
    await page
      .getByPlaceholder("Опишите ситуацию так, чтобы нам было понятно, с чего начать.")
      .fill("Тестовый сценарий без приложения.");
    await page.getByRole("button", { name: "Создать кейс" }).click();
    await expect(page.locator("main")).toContainText("Открыт · #");
    await expect(page.locator("main")).toContainText("Нужна помощь с импортом");
  });

  test("stays inside a narrow mobile viewport for core cabinet pages", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    for (const route of ["/dashboard/", "/subscription/", "/devices/", "/support/"]) {
      await page.goto(route);
      await expect(page.locator("main")).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow).toBeLessThanOrEqual(1);
    }
  });
});
