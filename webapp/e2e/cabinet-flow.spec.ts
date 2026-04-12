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

const ACTIVE_USERS_LABEL = "\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439 \u043f\u043e IP \u0441\u0435\u0439\u0447\u0430\u0441";
const ACTIVE_USERS_HINT =
  "\u041e\u0446\u0435\u043d\u043a\u0430 \u043f\u043e \u0436\u0438\u0432\u044b\u043c IP, \u043d\u043e \u043d\u0435 \u0432\u044b\u0448\u0435 \u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u044b\u0445 IP \u0437\u0430 24 \u0447\u0430\u0441\u0430. \u041d\u0435 \u0442\u043e\u0447\u043d\u043e\u0435 \u0447\u0438\u0441\u043b\u043e \u043b\u044e\u0434\u0435\u0439.";

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

async function registerCabinetMocks(page: Page): Promise<void> {
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
  const dashboard = mockDashboard();
  let tickets = [...mockTickets()];

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

  test("shows a single connect link flow on the dashboard", async ({ page }) => {
    await page.goto("dashboard/");
    await expect(page.locator("main")).toContainText("Пользователей по IP сейчас");

    await expect(page.getByRole("heading", { name: "Показать ссылку подключения или открыть QR" })).toBeVisible();
    await page.getByRole("button", { name: "Показать", exact: true }).click();
    await expect(page.locator("main")).toContainText("https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token");
    await expect(page.locator("main")).not.toContainText("?format=plain");
    await expect(page.locator("main")).not.toContainText("Обычная ссылка");

    await page.getByRole("button", { name: "Показать QR" }).click();
    await expect(page.getByAltText("QR-код ссылки подключения")).toBeVisible();
  });

  test("keeps the subscription page on one public connection link plus QR", async ({ page }) => {
    await page.goto("subscription/");

    await expect(page.getByRole("heading", { name: "Одна ссылка для всех подключений" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Откройте на втором устройстве" })).toBeVisible();
    await expect(page.locator("main")).toContainText("https://connect.pokrov.space/s8Kx2mP7qR4wT/mock_token");
    await expect(page.locator("main")).not.toContainText("резервная ссылка");
    await expect(page.locator("main")).not.toContainText("?format=plain");

    await page.getByRole("button", { name: "Скопировать" }).click();
    await expect(page.getByRole("button", { name: "Скопировано" })).toBeVisible();
  });

  test("renders runtime connections on devices and keeps statistics actionable", async ({ page }) => {
    await page.goto("devices/");
    await expect(page.getByRole("heading", { name: "Устройства и подключения" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Подключений сейчас");
    await expect(page.locator("main")).toContainText("2 / 5");
    await expect(page.locator("main")).toContainText("Пользователей по IP сейчас");
    await expect(page.locator("main")).toContainText("Нод с активностью");
    await expect(page.locator("main")).toContainText("1 / 2");

    await page.goto("statistics/");
    await expect(page.locator("main")).toContainText("Пользователей по IP сейчас");
    await expect(page.getByRole("heading", { name: "Сводка по использованию" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Что доступно сейчас" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Ссылка подключения: готова");
    await expect(page.locator("main")).toContainText("Трафик: безлимитный");
    await expect(page.locator("main")).not.toContainText("Объём профиля: 0 ГБ");
  });

  test("keeps downloads and support flows usable without the app", async ({ page }) => {
    await page.goto("dashboard/downloads/");
    await expect(page.getByRole("heading", { name: "Приложения и быстрый старт" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Google Play" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Скачать EXE" })).toBeVisible();

    await page.goto("support/");
    await expect(page.getByRole("heading", { name: "Служба заботы" })).toBeVisible();
    await page.getByRole("button", { name: "Создать обращение" }).click();
    await page.getByPlaceholder("Расскажите, что произошло").fill("Нужна помощь с импортом");
    await page.getByPlaceholder("Опишите вашу ситуацию во всех подробностях").fill("Тестовый сценарий без приложения.");
    await page.getByRole("button", { name: "Отправить" }).click();
    await expect(page.locator("main")).toContainText("Обращение #");
    await expect(page.locator("main")).toContainText("Нужна помощь с импортом");
  });

  test("stays inside a narrow mobile viewport for core cabinet pages", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    for (const route of ["dashboard/", "subscription/", "devices/", "support/"]) {
      await page.goto(route);
      await expect(page.locator("main")).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow).toBeLessThanOrEqual(1);
    }
  });
});
