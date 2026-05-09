import { expect, test, type Page, type Route } from "@playwright/test";

type TicketMessageMock = {
  id: number;
  sender_role: "user" | "admin";
  body: string;
  created_at?: string | null;
  media_type?: string | null;
  media_file_id?: string | null;
  media_payload?: string | null;
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

type CabinetMockOptions = {
  authSession?: unknown;
  clientApps?: unknown;
  dashboard?: Record<string, unknown>;
  paymentProviders?: unknown;
  checkoutOrderResponse?: unknown;
  checkoutRequests?: unknown[];
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
      channel_bonus: { premium_days: 10, claimed_at: null, can_claim: true },
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
    payment_orders: [],
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
          media_type: "image",
          media_file_id: "support/e2e-screen.png",
          media_payload: JSON.stringify({
            url: "/uploads/support/e2e-screen.png",
            name: "screen.png",
            content_type: "image/png",
            size: 16,
          }),
        },
      ],
    },
  ];
}

async function registerCabinetMocks(page: Page, options: CabinetMockOptions = {}): Promise<void> {
  await page.addInitScript(() => {
    if (!window.localStorage.getItem("portal_web_session_token")) {
      window.localStorage.setItem("portal_web_session_token", "e2e_mock_token");
    }
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => undefined,
      },
    });
  });

  const sessionUser = mockSessionUser();
  const dashboard = { ...mockDashboard(), ...(options.dashboard || {}) };
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
      return json(options.authSession || { ok: true, user: { id: 1001, username: "qa_user" } });
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
      return json(options.clientApps || {
        android: {
          play_url: "",
          apk_url: "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk",
          mirror_url: "",
        },
        windows: {
          exe_url: "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
          mirror_url: "",
        },
        docs_url: "https://pokrov.space/install/",
        updated_at: "2030-01-01T00:00:00",
      });
    }
    if (path === "/api/client/route-policy") {
      return json({
        ok: true,
        route_mode: "selected_apps",
        selected_apps: ["telegram.exe", "browser.exe"],
        requires_elevated_privileges: true,
        route_policy: {
          mode: "selected_apps",
          selected_apps: ["telegram.exe", "browser.exe"],
          requires_elevated_privileges: true,
        },
      });
    }
    if (path === "/api/channel/subscriber/check") {
      return json({
        ok: true,
        subscriber: true,
        claim_required: true,
        already_claimed: false,
        bonus_days: 10,
      });
    }
    if (path === "/api/bonuses/channel/claim") {
      sessionUser.bonuses.channel_bonus = {
        premium_days: 10,
        claimed_at: "2030-01-01T00:10:00",
        can_claim: false,
      };
      sessionUser.channel.subscriber = true;
      return json({
        ok: true,
        already_claimed: false,
        premium_days: 10,
        claimed_at: "2030-01-01T00:10:00",
        expiry_at: "2030-01-11T00:00:00",
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
    if (path === "/api/payments/providers") {
      return json(
        options.paymentProviders || {
          ok: true,
          providers: [],
          blocked: true,
          blocked_reasons: ["checkout_disabled"],
          blocked_reason_texts: ["Платная касса пока закрыта."],
        },
      );
    }
    if (path === "/api/payments/orders/create") {
      options.checkoutRequests?.push(JSON.parse(request.postData() || "{}"));
      return json(
        options.checkoutOrderResponse || {
          ok: true,
          provider: "lavatop",
          order_id: "blocked-order-should-not-happen",
          payment_url: "https://checkout.lava.top/pay/blocked-order-should-not-happen",
          amount_rub: 249,
          currency: "RUB",
          status: "created",
        },
      );
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

async function forceNoWebSession(page: Page): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.removeItem("portal_web_session_token");
  });
  await page.route("**/api/auth/session", async (route) =>
    route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({ detail: "missing web session" }),
    }),
  );
}

async function registerEmailAuthMocks(page: Page) {
  const requests = {
    register: [] as unknown[],
    verify: [] as unknown[],
    login: [] as unknown[],
    recoveryStart: [] as unknown[],
    recoveryFinish: [] as unknown[],
  };

  const json = (route: Route, payload: unknown, status = 200) =>
    route.fulfill({
      status,
      contentType: "application/json",
      body: JSON.stringify(payload),
    });
  const body = (route: Route): unknown => {
    try {
      return route.request().postDataJSON();
    } catch {
      return null;
    }
  };
  const authResult = (token: string) => ({
    ok: true,
    token,
    expires_in: 604800,
    user: { id: 1001, username: "qa_user", email: "reader@pokrov.test" },
  });

  await page.route("**/api/auth/email/status", async (route) =>
    json(route, {
      ok: true,
      enabled: true,
      public_enabled: true,
      delivery_configured: true,
      delivery_url_configured: true,
      delivery_secret_configured: true,
      debug_echo: false,
      mode: "public",
      blocked_reasons: [],
    }),
  );
  await page.route("**/api/auth/email/register", async (route) => {
    requests.register.push(body(route));
    return json(route, {
      ok: true,
      verification_required: true,
      delivery: { status: "sent", kind: "verify", email: "reader@pokrov.test", mode: "relay" },
      identity: { email: "reader@pokrov.test", verified: false, linked_tg_id: null },
    });
  });
  await page.route("**/api/auth/email/verify", async (route) => {
    requests.verify.push(body(route));
    return json(route, authResult("email_verify_session"));
  });
  await page.route("**/api/auth/email/login", async (route) => {
    requests.login.push(body(route));
    return json(route, authResult("email_login_session"));
  });
  await page.route("**/api/auth/email/recovery/start", async (route) => {
    requests.recoveryStart.push(body(route));
    return json(route, {
      ok: true,
      recovery_requested: true,
      delivery: { status: "sent", kind: "reset", email: "reader@pokrov.test", mode: "relay" },
    });
  });
  await page.route("**/api/auth/email/recovery/finish", async (route) => {
    requests.recoveryFinish.push(body(route));
    return json(route, authResult("email_recovery_session"));
  });

  return requests;
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
    await expect(sidebar.locator("nav")).toContainText("Статистика");
    await expect(sidebar.locator("nav")).toContainText("Настройки");

    const siteLink = page.getByRole("link", { name: /^На сайт/i });
    await expect(siteLink).toBeVisible();
    await expect(siteLink).toHaveAttribute("href", /https:\/\/pokrov\.space\/?$/);
  });

  test("keeps mobile cabinet navigation focused on beta downloads", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/dashboard/");

    const mobileNav = page.getByRole("navigation", { name: "Навигация кабинета" });
    await expect(mobileNav).toBeVisible();
    await expect(mobileNav).toContainText("Загрузки");
    await expect(mobileNav).not.toContainText("Статистика");

    await mobileNav.getByRole("link", { name: /Загрузки/i }).click();
    await expect(page).toHaveURL(/\/downloads\/?$/);
  });

  test("shows an honest email-unavailable state on the root auth entry", async ({ page }) => {
    await forceNoWebSession(page);

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Telegram подтверждает кабинет" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Проверяем доставку" })).toBeVisible();
    await expect(page.locator("main")).toContainText(
      "Email-вход скрыт, пока доставка писем на проде недоступна. Сейчас для браузера используйте Telegram",
    );
    await expect(page.getByRole("button", { name: /Продолжить через email/i })).toHaveCount(0);
  });

  test("keeps the email entry truthful when live delivery is not configured", async ({ page }) => {
    await forceNoWebSession(page);

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Проверяем доставку" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Недоступно");
    await expect(page.locator("main")).toContainText("используйте Telegram");
    await expect(page.getByRole("button", { name: /^Email$/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Регистрация/i })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Войти/i })).toHaveCount(0);
  });

  test("keeps the email entry unavailable when the relay secret is missing", async ({ page }) => {
    await forceNoWebSession(page);
    await page.route("**/api/auth/email/status", async (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          enabled: true,
          public_enabled: true,
          delivery_configured: true,
          delivery_url_configured: true,
          delivery_secret_configured: false,
          debug_echo: false,
          blocked_reasons: ["delivery_webhook_secret_missing"],
        }),
      }),
    );

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Проверяем доставку" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Недоступно");
    await expect(page.getByRole("button", { name: "Создать аккаунт" })).toHaveCount(0);
  });

  test("supports enabled email register verify login and recovery from the auth entry", async ({ page }) => {
    const requests = await registerEmailAuthMocks(page);

    await page.goto("/?clear_web_session=1");

    await expect(page.getByRole("heading", { name: "Email-вход" })).toBeVisible();
    await expect(page.locator("main")).not.toContainText("Email-продолжение пока честно помечено как готовящееся");
    await expect(page.getByPlaceholder("Пароль")).toHaveAttribute("autocomplete", "current-password");

    await page.getByRole("button", { name: "Создать аккаунт" }).first().click();
    await page.getByPlaceholder("email@example.com").fill("reader@pokrov.test");
    await page.getByPlaceholder("Имя").fill("Reader");
    await expect(page.getByPlaceholder("Пароль")).toHaveAttribute("autocomplete", "new-password");
    await page.getByPlaceholder("Пароль").fill("StrongPass123!");
    await page.getByRole("button", { name: "Создать аккаунт" }).last().click();

    await expect(page.locator("main")).toContainText("Письмо для подтверждения отправлено.");
    expect(requests.register).toEqual([
      { email: "reader@pokrov.test", password: "StrongPass123!", display_name: "Reader" },
    ]);

    await page.getByPlaceholder("Код подтверждения").fill("  verify-token  ");
    await page.getByRole("button", { name: "Подтвердить" }).last().click();
    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect(page.getByRole("heading", { name: "Ваш трафик защищён" })).toBeVisible();
    expect(await page.evaluate(() => window.localStorage.getItem("portal_web_session_token"))).toBe(
      "email_verify_session",
    );
    expect(requests.verify).toEqual([{ token: "verify-token" }]);

    await page.goto("/?clear_web_session=1");
    await page.getByPlaceholder("email@example.com").fill("reader@pokrov.test");
    await page.getByPlaceholder("Пароль").fill("StrongPass123!");
    await page.getByRole("button", { name: "Войти" }).last().click();
    await expect(page).toHaveURL(/\/dashboard\/?$/);
    expect(await page.evaluate(() => window.localStorage.getItem("portal_web_session_token"))).toBe(
      "email_login_session",
    );
    expect(requests.login).toEqual([{ email: "reader@pokrov.test", password: "StrongPass123!" }]);

    await page.goto("/?clear_web_session=1");
    await page.getByRole("button", { name: "Восстановить доступ" }).click();
    await page.getByPlaceholder("email@example.com").fill("reader@pokrov.test");
    await page.getByRole("button", { name: "Отправить письмо" }).click();
    await expect(page.locator("main")).toContainText("Письмо для восстановления отправлено.");
    expect(requests.recoveryStart).toEqual([{ email: "reader@pokrov.test" }]);

    await page.getByPlaceholder("Код восстановления").fill("  reset-token  ");
    await expect(page.getByPlaceholder("Новый пароль")).toHaveAttribute("autocomplete", "new-password");
    await page.getByPlaceholder("Новый пароль").fill("FreshPass456!");
    await page.getByRole("button", { name: "Сбросить пароль и войти" }).click();
    await expect(page).toHaveURL(/\/dashboard\/?$/);
    expect(await page.evaluate(() => window.localStorage.getItem("portal_web_session_token"))).toBe(
      "email_recovery_session",
    );
    expect(requests.recoveryFinish).toEqual([{ token: "reset-token", password: "FreshPass456!" }]);
  });

  test("keeps email verification and recovery tokens separate", async ({ page }) => {
    const requests = await registerEmailAuthMocks(page);

    await page.goto("/?clear_web_session=1");

    await page.getByRole("button", { name: "Подтвердить" }).first().click();
    await page.getByPlaceholder("Код подтверждения").fill("stale-verify-token");
    await page.getByRole("button", { name: "Восстановить доступ" }).click();

    await expect(page.getByPlaceholder("Код восстановления")).toHaveValue("");
    await expect(page.getByRole("button", { name: "Отправить письмо" })).toBeVisible();

    await page.getByPlaceholder("email@example.com").fill("reader@pokrov.test");
    await page.getByRole("button", { name: "Отправить письмо" }).click();

    await expect(page.locator("main")).toContainText("Письмо для восстановления отправлено.");
    expect(requests.recoveryStart).toEqual([{ email: "reader@pokrov.test" }]);
    expect(requests.recoveryFinish).toEqual([]);
  });

  test("prefills email tokens from relay links without leaving them in the URL", async ({ page }) => {
    const requests = await registerEmailAuthMocks(page);

    await page.goto("/?clear_web_session=1&email_token=verify-from-link");

    await expect(page.getByPlaceholder("Код подтверждения")).toHaveValue("verify-from-link");
    await expect(page.locator("main")).toContainText("Код подтверждения из письма уже подставлен.");
    await expect(page).not.toHaveURL(/email_token=/);

    await page.getByRole("button", { name: "Подтвердить" }).last().click();
    await expect(page).toHaveURL(/\/dashboard\/?$/);
    expect(requests.verify).toEqual([{ token: "verify-from-link" }]);

    await page.goto("/?clear_web_session=1&email_reset_token=reset-from-link");

    await expect(page.getByPlaceholder("Код восстановления")).toHaveValue("reset-from-link");
    await expect(page.locator("main")).toContainText("Код восстановления из письма уже подставлен.");
    await expect(page).not.toHaveURL(/email_reset_token=/);
    await expect(page.getByPlaceholder("email@example.com")).not.toHaveAttribute("required", "");

    await page.getByPlaceholder("Новый пароль").fill("FreshPass456!");
    await page.getByRole("button", { name: "Сбросить пароль и войти" }).click();
    await expect(page).toHaveURL(/\/dashboard\/?$/);
    expect(requests.recoveryFinish).toEqual([{ token: "reset-from-link", password: "FreshPass456!" }]);
    expect(requests.recoveryStart).toEqual([]);
  });

  test("reuses an existing web session and lands in the cabinet without showing auth entry again", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect(page.getByRole("heading", { name: "Ваш трафик защищён" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Telegram подтверждает кабинет" })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "Проверяем доставку" })).toHaveCount(0);
  });

  test("stores a silently refreshed web session returned from Telegram auth", async ({ page }) => {
    await page.unroute("**/api/**");
    await registerCabinetMocks(page, {
      authSession: {
        ok: true,
        session_token: "refreshed_from_telegram",
        expires_in: 2592000,
        user: { id: 1001, username: "qa_user" },
      },
    });

    await page.goto("/dashboard/");

    await expect(page.locator("main h1").first()).toBeVisible();
    expect(await page.evaluate(() => window.localStorage.getItem("portal_web_session_token"))).toBe(
      "refreshed_from_telegram",
    );
  });

  test("shows a human reauth CTA when the browser session is expired", async ({ page }) => {
    await page.route("**/api/auth/session", async (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        headers: { "x-pokrov-auth-error": "web_session_expired" },
        body: JSON.stringify({
          detail: "Сессия в браузере устарела. Обновите вход через Telegram или email, и кабинет откроется снова.",
        }),
      }),
    );

    await page.goto("/dashboard/");

    await expect(page.locator("main")).toContainText("Сессия в браузере устарела");
    await expect(page.getByRole("button", { name: "Открыть Telegram для входа" })).toBeVisible();
  });

  test("keeps the dashboard on consumer-safe access actions", async ({ page }) => {
    await page.goto("/dashboard/");

    await expect(page.getByRole("heading", { name: "Ваш трафик защищён" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Приложение");
    await expect(page.getByRole("heading", { name: "Что нужно сделать?" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Скачать приложение" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Поддержка", exact: true }).first()).toBeVisible();
    await expect(page.locator("main")).not.toContainText("QR");
    await expect(page.locator("main")).not.toContainText("?format=plain");
    await expect(page.locator("main")).not.toContainText("mock_token");
    await expect(page.getByRole("button", { name: "Показать", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Показать QR" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Скопировать" })).toHaveCount(0);
  });

  test("keeps cabinet navigation on native Next.js routing", async ({ page }) => {
    await page.goto("/dashboard/");
    await page.evaluate(() => {
      (window as Window & { __routeMarker?: string }).__routeMarker = "persist-me";
    });

    await page.locator("aside nav a[href='/subscription/']").click();
    await expect(page).toHaveURL(/\/subscription\/?$/);
    await expect(page.getByRole("heading", { name: "Продление и режимы" })).toBeVisible();

    await page.locator("aside nav a[href='/downloads/']").click();
    await expect(page).toHaveURL(/\/downloads\/?$/);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main")).not.toContainText("Google Play");

    const markerPersisted = await page.evaluate(
      () => Boolean((window as Window & { __routeMarker?: string }).__routeMarker),
    );
    expect(markerPersisted).toBe(true);
  });

  test("shows branded root and cabinet not-found recovery screens", async ({ page }) => {
    await page.goto("/no-such-route/");
    await expect(page.getByRole("heading", { name: /Страница не найдена/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /В кабинет/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /В поддержку/i })).toBeVisible();

    await page.goto("/dashboard/no-such-route/");
    await expect(page.getByRole("heading", { name: /Страница не найдена/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /В кабинет/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /В поддержку/i })).toBeVisible();
  });

  test("shows subscription manual connection only as an explicit fallback", async ({ page }) => {
    await page.goto("/subscription/");

    await expect(page.getByRole("heading", { name: "Продление и режимы" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Проверить статус продления" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Поддержка", exact: true }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: "Ручное подключение только как запасной путь" })).toBeVisible();
    const manualConnection = page.locator("section").filter({ has: page.getByRole("heading", { name: "Ручное подключение только как запасной путь" }) });
    await expect(manualConnection).toContainText("не показываем ее первой");
    await expect(manualConnection).not.toContainText("mock_token");
    await manualConnection.getByRole("button", { name: "Показать ручной вариант" }).click();
    await expect(manualConnection).toContainText("mock_token");
    await expect(manualConnection.getByRole("button", { name: "Скопировать ссылку" })).toBeVisible();
    await expect(manualConnection.getByRole("link", { name: "Открыть ссылку" })).toBeVisible();
    await expect(page.locator("main")).not.toContainText("?format=plain");
  });

  test("renders runtime connections on devices and keeps statistics as its own safe-summary page", async ({ page }) => {
    await page.goto("/devices/");

    await expect(page.getByRole("heading", { name: "Что уже связано с профилем" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Подключений сейчас");
    await expect(page.locator("main")).toContainText("2 из 5");
    await expect(page.locator("main")).toContainText("Людей онлайн");
    await expect(page.locator("main")).toContainText("Точек доступа");
    await expect(page.locator("main")).toContainText("1 из 2");
    await expect(page.locator("main")).toContainText("Режим маршрутизации");
    await expect(page.locator("main")).toContainText("Выбранные приложения");
    await expect(page.locator("main")).toContainText("2 приложения");
    await expect(page.locator("main")).toContainText("Меняется в приложении");

    await page.goto("/statistics/");
    await expect(page).toHaveURL(/\/statistics\/?$/);
    await expect(page.getByRole("heading", { name: "Статистика без лишних деталей" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Людей онлайн");
    await expect(page.locator("main")).not.toContainText("pl.pokrov.space");
    await expect(page.locator("main")).not.toContainText("mock_token");
  });

  test("keeps cabinet copy human and hides node internals", async ({ page }) => {
    await page.goto("/devices/");
    await expect(page.locator("main")).not.toContainText("pl.pokrov.space");
    await expect(page.locator("main")).not.toContainText("us.pokrov.space");
    await expect(page.locator("main")).not.toContainText(":443");
    await expect(page.locator("main")).not.toContainText("IP");

    await page.goto("/subscription/");
    await expect(page.locator("main")).not.toContainText("?format=plain");

    await page.goto("/support/");
    await expect(page.locator("main")).not.toContainText("Network");
  });

  test("settings exposes clear Telegram bonus actions without raw account details", async ({ page }) => {
    await page.goto("/settings/");

    await expect(page.getByRole("heading", { name: "Настройки и бонусы" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Telegram-бонус");
    await page.getByRole("button", { name: /Проверить подписку/i }).click();
    await expect(page.locator("main")).toContainText("Подписка подтверждена");
    await page.getByRole("button", { name: /Забрать \+10 дней/i }).click();
    await expect(page.locator("main")).toContainText("Бонус +10 дней добавлен");
    await expect(page.locator("main")).not.toContainText("mock_token");

    await page.goto("/profile/");
    await expect(page).toHaveURL(/\/settings\/?$/);
  });

  test("shows honest payment history and Russian checkout continuation copy", async ({ page }) => {
    await page.goto("/subscription/");
    await expect(page.getByRole("heading", { name: "История оплат" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Истории оплат пока нет");

    await page.goto("/subscription/checkout/?plan=1_month&promo=POKROV10");
    await expect(page.getByRole("heading", { name: "Оплата временно недоступна" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Проверить статус оплаты");
    await expect(page.locator("main button.btn-primary").first()).toBeDisabled();
    await expect(page.locator("main")).not.toContainText("Hosted checkout");
    await expect(page.locator("main")).not.toContainText("activation key");
    await expect(page.locator("main")).not.toContainText("Free fallback");
    await expect(page.locator("main")).not.toContainText("accessState");
    await expect(page.locator("main")).not.toContainText("managed profile");
    await expect(page.locator("main")).not.toContainText("premium trial");
    await expect(page.locator("main")).not.toContainText("Email signup");
  });

  test("renders safe user payment history from dashboard orders", async ({ page }) => {
    await page.unroute("**/api/**");
    await registerCabinetMocks(page, {
      dashboard: {
        payment_orders: [
          {
            order_id: "lavatop_1001_safe",
            provider: "lavatop",
            plan_code: "standard",
            amount: 199,
            currency: "RUB",
            status: "paid",
            source: "webapp",
            created_at: "2030-01-01T00:00:00",
            paid_at: "2030-01-01T00:00:00",
          },
        ],
      },
    });

    await page.goto("/subscription/");

    await expect(page.getByRole("heading", { name: "История оплат" })).toBeVisible();
    await expect(page.locator("main")).toContainText("lavatop_1001_safe");
    await expect(page.locator("main")).toContainText("199");
    await expect(page.locator("main")).toContainText("Оплачено");
    await expect(page.locator("main")).not.toContainText("raw-provider-payload");
    await expect(page.locator("main")).not.toContainText("POKROV-SECRET-KEY");
  });

  test("keeps checkout disabled when payment providers are configured but launch evidence is blocked", async ({ page }) => {
    const checkoutRequests: unknown[] = [];
    await page.unroute("**/api/**");
    await registerCabinetMocks(page, {
      checkoutRequests,
      paymentProviders: {
        ok: false,
        providers: [
          {
            code: "lavatop",
            label: "Lava.top",
            supports_webapp: true,
            checkout_hint: "Launch evidence is incomplete",
          },
        ],
        blocked: true,
        blocked_reasons: ["paid_checkout_launch_evidence_blocked"],
        blocked_reason_texts: [
          "RUB checkout is disabled",
          "CHECKOUT_TICKET_SECRET is empty",
          "Paid checkout launch evidence is not green",
        ],
        checkout_mode: "blocked_by_launch_evidence",
        telegram_fallback_available: false,
      },
    });

    await page.goto("/subscription/checkout/?plan=1_month");

    const payButton = page.locator("main button.btn-primary").first();
    await expect(page.getByRole("heading", { name: "Оплата временно недоступна" })).toBeVisible();
    await expect(payButton).toBeDisabled();
    await expect(page.locator("main")).toContainText("Оплата пока закрыта: мы включим продление после финальной проверки Lava.top и доставки ключей на email.");
    await expect(page.locator("main")).not.toContainText("Launch evidence is incomplete");
    await expect(page.locator("main")).not.toContainText("RUB checkout is disabled");
    await expect(page.locator("main")).not.toContainText("CHECKOUT_TICKET_SECRET");
    await expect(page.locator("main")).not.toContainText("Paid checkout launch evidence is not green");
    await expect(page.locator("main")).not.toContainText("backend");
    await payButton.click({ force: true });
    expect(checkoutRequests).toEqual([]);
  });

  test("keeps checkout start failures public and Russian", async ({ page }) => {
    const checkoutRequests: unknown[] = [];
    await page.unroute("**/api/**");
    await registerCabinetMocks(page, {
      checkoutRequests,
      paymentProviders: {
        ok: true,
        providers: [
          {
            code: "lavatop",
            label: "Lava.top",
            supports_webapp: true,
            checkout_hint: "Internal provider ready text",
          },
        ],
        blocked: false,
        blocked_reasons: [],
        blocked_reason_texts: [],
        checkout_mode: "live",
        telegram_fallback_available: false,
      },
      checkoutOrderResponse: {
        ok: true,
        provider: "lavatop",
        order_id: "malformed-order",
        payment_url: "",
        amount_rub: 249,
        currency: "RUB",
        status: "created",
      },
    });

    await page.goto("/subscription/checkout/?plan=1_month");

    const payButton = page.locator("main button.btn-primary").first();
    await expect(page.getByRole("heading", { name: "Продлить доступ" })).toBeVisible();
    await expect(payButton).toBeEnabled();
    await payButton.click();
    await expect(page.locator("main")).toContainText("Не удалось открыть оплату. Проверьте статус чуть позже или напишите в поддержку.");
    await expect(page.locator("main")).not.toContainText("Payment URL is missing.");
    await expect(page.locator("main")).not.toContainText("Checkout is not available.");
    await expect(page.locator("main")).not.toContainText("Internal provider ready text");
    expect(checkoutRequests).toHaveLength(1);
  });

  test("checks and redeems access keys from the cabinet redeem route", async ({ page }) => {
    const requests: unknown[] = [];
    const statusRequests: string[] = [];
    const statusPayload = {
      key: "POKROV-GIFT-2026",
      exists: true,
      redeemed: false,
      redeemed_at: null,
      issued_at: "2030-01-01T00:00:00",
      plan: {
        code: "1_month",
        label: "1 месяц",
        amount_rub: 249,
        amount_stars: 249,
        days: 30,
        device_limit: 5,
        node_policy: "managed_premium",
      },
      kind: "legacy_gift",
      legacy_type: "standard",
      days: 30,
      device_limit: 5,
      node_policy: "managed_premium",
    };

    await page.route("**/api/access-keys/status/*", async (route) => {
      statusRequests.push(new URL(route.request().url()).pathname);
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(statusPayload),
      });
    });
    await page.route("**/api/access-keys/redeem", async (route) => {
      try {
        requests.push(route.request().postDataJSON());
      } catch {
        requests.push(null);
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          key: "POKROV-GIFT-2026",
          status: { ...statusPayload, redeemed: true, redeemed_at: "2030-01-02T00:00:00" },
          plan: statusPayload.plan,
          access: { sub_type: "PAID", current_plan_code: "1_month", expiry_at: "2030-02-01T00:00:00" },
          sync_ok: true,
        }),
      });
    });

    await page.goto("/redeem/?key=pokrov%E2%80%91gift%E2%88%922026");

    await expect(page.getByRole("heading", { name: "Применить ключ" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Ключ найден");
    await expect(page.locator("main")).not.toContainText("9999");

    await page.getByRole("button", { name: "Применить", exact: true }).last().click();

    await expect(page.locator("main")).toContainText("Ключ POKROV-GIFT-2026 применен");
    expect(statusRequests).toContain("/api/access-keys/status/POKROV-GIFT-2026");
    expect(requests).toEqual([{ key: "POKROV-GIFT-2026" }]);
    await expect(page.locator("main")).not.toContainText("created_by");
    await expect(page.locator("main")).not.toContainText("redeemed_by");
  });

  test("redeems the current access key after the user edits a previously checked key", async ({ page }) => {
    const redeemed: unknown[] = [];

    await page.route("**/api/access-keys/status/*", async (route) => {
      const key = decodeURIComponent(new URL(route.request().url()).pathname.split("/").pop() || "");
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          key,
          exists: true,
          redeemed: false,
          redeemed_at: null,
          issued_at: "2030-01-01T00:00:00",
          plan: {
            code: "1_month",
            label: "1 месяц",
            amount_rub: 249,
            amount_stars: 249,
            days: 30,
            device_limit: 5,
            node_policy: "managed_premium",
          },
          kind: "legacy_gift",
          legacy_type: "standard",
          days: 30,
          device_limit: 5,
          node_policy: "managed_premium",
        }),
      });
    });
    await page.route("**/api/access-keys/redeem", async (route) => {
      const payload = route.request().postDataJSON();
      redeemed.push(payload);
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          key: payload.key,
          status: { key: payload.key, exists: true, redeemed: true, redeemed_at: "2030-01-02T00:00:00" },
          access: { sub_type: "PAID", current_plan_code: "1_month", expiry_at: "2030-02-01T00:00:00" },
          sync_ok: true,
        }),
      });
    });

    await page.goto("/redeem/?key=pokrov%20old%201111");
    await expect(page.locator("main")).toContainText("POKROV-OLD-1111");
    await page.getByPlaceholder("Например: POKROV-XXXX-XXXX").fill("pokrov new 2222");
    await page.getByRole("button", { name: "Применить", exact: true }).last().click();

    expect(redeemed).toEqual([{ key: "POKROV-NEW-2222" }]);
    await expect(page.locator("main")).toContainText("Ключ POKROV-NEW-2222 применен");
  });

  test("keeps access key redeem failures public and Russian", async ({ page }) => {
    const statusPayload = {
      key: "POKROV-GIFT-2026",
      exists: true,
      redeemed: false,
      redeemed_at: null,
      issued_at: "2030-01-01T00:00:00",
      plan: {
        code: "1_month",
        label: "1 месяц",
        amount_rub: 249,
        amount_stars: 249,
        days: 30,
        device_limit: 5,
        node_policy: "managed_premium",
      },
      kind: "legacy_gift",
      legacy_type: "standard",
      days: 30,
      device_limit: 5,
      node_policy: "managed_premium",
    };

    await page.route("**/api/access-keys/status/*", async (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(statusPayload),
      }),
    );
    await page.route("**/api/access-keys/redeem", async (route) =>
      route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Access key already redeemed" }),
      }),
    );

    await page.goto("/redeem/?key=pokrov%20gift%202026");
    await page.getByRole("button", { name: "Применить", exact: true }).last().click();

    await expect(page.locator("main")).toContainText("Ключ уже был использован");
    await expect(page.locator("main")).not.toContainText("Access key already redeemed");
    await expect(page.locator("main")).not.toContainText("API error");
  });

  test("redeems promo codes from the cabinet redeem route", async ({ page }) => {
    const redeemed: unknown[] = [];

    await page.route("**/api/promo/redeem", async (route) => {
      redeemed.push(route.request().postDataJSON());
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: true,
          code: "WELCOME14",
          days: 14,
          expiry_at: "2030-02-01T00:00:00",
        }),
      });
    });

    await page.goto("/redeem/");
    await page.getByLabel("Промокод").fill("welcome14");
    await page.getByRole("button", { name: "Применить промокод" }).click();

    expect(redeemed).toEqual([{ code: "WELCOME14" }]);
    await expect(page.locator("main")).toContainText("Промокод WELCOME14 применен");
  });

  test("keeps downloads and support flows usable without the app", async ({ page }) => {
    await page.goto("/dashboard/downloads/");

    await expect(page).toHaveURL(/\/downloads\/?$/);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main")).toContainText("Бета-доступ");
    await expect(page.locator("main")).not.toContainText("Google Play");
    await expect(page.locator("main a[href*='play.google.com']")).toHaveCount(0);
    await expect(page.locator("main a[href*='pokrov-android-universal.apk']").first()).toBeVisible();
    await expect(page.locator("main")).toContainText("Windows");
    await expect(page.locator("main")).toContainText("неподписанный");
    await expect(page.locator("main a[href*='pokrov-windows-setup-x64.exe']").first()).toBeVisible();

    await page.goto("/support/");
    await expect(page.getByRole("heading", { name: "Один кейс на весь вопрос" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Безопасная диагностика");
    await expect(page.locator("main")).not.toContainText("public IP");
    await expect(page.locator("main")).not.toContainText("subscription_url");
    await page.getByRole("button", { name: "Новый кейс" }).first().click();
    await page.getByPlaceholder("Коротко: что случилось").fill("Нужна помощь с импортом");
    await page
      .getByPlaceholder("Опишите ситуацию так, чтобы нам было понятно, с чего начать.")
      .fill("Тестовый сценарий без приложения.");
    await page.getByRole("button", { name: "Создать кейс" }).click();
    await expect(page.locator("main")).toContainText("Открыт · #");
    await expect(page.locator("main")).toContainText("Нужна помощь с импортом");
  });

  test("keeps downloads honest when runtime app links are not enabled yet", async ({ page }) => {
    await page.unroute("**/api/**");
    await registerCabinetMocks(page, {
      clientApps: {
        android: { play_url: "", apk_url: "", mirror_url: "" },
        windows: { exe_url: "", mirror_url: "" },
        docs_url: "https://pokrov.space/install/",
        updated_at: "2030-01-01T00:00:00",
      },
    });

    await page.goto("/downloads/?platform=android");

    await expect(page.locator("main h1")).toContainText("Загрузки появятся после финального разрешения");
    await expect(page.locator("main h2").filter({ hasText: "Часть ссылок подтянем позже" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Ссылки появятся");
    await expect(page.locator("main")).toContainText("Короткая инструкция");
    await expect(page.locator("main a[href='https://pokrov.space/install/']").first()).toBeVisible();
    await expect(page.locator("main a[href*='pokrov-android-universal.apk']")).toHaveCount(0);
    await expect(page.locator("main a[href*='pokrov-windows-setup-x64.exe']")).toHaveCount(0);
    await expect(page.locator("main")).not.toContainText("Открыть первую ссылку");
  });

  test("honors platform query when opening cabinet downloads", async ({ page }) => {
    await page.goto("/downloads/?platform=windows");

    await expect(page).toHaveURL(/\/downloads\/\?platform=windows$/);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main a.btn-primary").first()).toHaveAttribute(
      "href",
      /pokrov-windows-setup-x64\.exe/,
    );
    await expect(page.locator("main a[href*='github.com/Kiwunaka/POKROV-app/releases/download/']").first()).toHaveAttribute(
      "href",
      /pokrov-windows-setup-x64\.exe/,
    );
  });

  test("loads protected support attachments through authenticated blob fetch", async ({ page }) => {
    const attachmentRequests: string[] = [];
    await page.route("**/uploads/support/e2e-screen.png", async (route) => {
      attachmentRequests.push(route.request().headers().authorization || "");
      return route.fulfill({
        status: 200,
        contentType: "image/png",
        body: Buffer.from("e2e-protected-image"),
      });
    });

    await page.goto("/support/thread/?id=11");

    await expect(page.locator("img[alt='screen.png']")).toBeVisible();
    await expect.poll(async () => attachmentRequests.length).toBeGreaterThan(0);
    expect(attachmentRequests[0]).toBe("Bearer e2e_mock_token");
    await expect(page.locator("img[src*='/uploads/support/']")).toHaveCount(0);
    await expect(page.locator("img[src^='blob:']")).toHaveCount(1);
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

  test("opens cabinet settings from the Telegram Mini App SettingsButton", async ({ page }) => {
    await page.route("https://telegram.org/js/telegram-web-app.js", async (route) =>
      route.fulfill({ status: 200, contentType: "application/javascript", body: "" }),
    );
    await page.addInitScript(() => {
      const state = {
        hidden: 0,
        impact: "",
        settingsHandler: null as null | (() => void),
        shown: 0,
      };
      (window as Window & { __pokrovTgSettingsButton?: typeof state }).__pokrovTgSettingsButton = state;
      (window as Window & { Telegram?: unknown }).Telegram = {
        WebApp: {
          initData: "query_id=mock&user=%7B%22id%22%3A1001%7D&auth_date=1800000&hash=mock",
          initDataUnsafe: { user: { id: 1001, username: "qa_user" } },
          platform: "android",
          colorScheme: "light",
          themeParams: {
            bg_color: "#ffffff",
            secondary_bg_color: "#f5f5f5",
            text_color: "#111111",
            button_color: "#20845f",
            button_text_color: "#ffffff",
          },
          viewportHeight: 844,
          viewportStableHeight: 844,
          safeAreaInset: { top: 0, right: 0, bottom: 16, left: 0 },
          BackButton: { show: () => undefined, hide: () => undefined, onClick: () => undefined, offClick: () => undefined },
          SettingsButton: {
            show: () => {
              state.shown += 1;
            },
            hide: () => {
              state.hidden += 1;
            },
            onClick: (handler: () => void) => {
              state.settingsHandler = handler;
            },
            offClick: () => {
              state.settingsHandler = null;
            },
          },
          HapticFeedback: {
            impactOccurred: (style: string) => {
              state.impact = style;
            },
          },
          ready: () => undefined,
          expand: () => undefined,
          disableVerticalSwipes: () => undefined,
          enableClosingConfirmation: () => undefined,
          setHeaderColor: () => undefined,
          setBackgroundColor: () => undefined,
          onEvent: () => undefined,
          offEvent: () => undefined,
        },
      };
    });

    await page.goto("/dashboard/");
    await expect(page.locator("main h1").first()).toBeVisible();
    await expect
      .poll(() => page.evaluate(() => (window as Window & { __pokrovTgSettingsButton?: { shown: number } }).__pokrovTgSettingsButton?.shown || 0))
      .toBeGreaterThan(0);

    await page.evaluate(() => (window as Window & { __pokrovTgSettingsButton?: { settingsHandler: null | (() => void) } }).__pokrovTgSettingsButton?.settingsHandler?.());

    await expect(page).toHaveURL(/\/settings\/?$/);
    await expect(page.locator("main h1").first()).toBeVisible();
    await expect(page.evaluate(() => (window as Window & { __pokrovTgSettingsButton?: { impact: string } }).__pokrovTgSettingsButton?.impact)).resolves.toBe("light");
  });
});
