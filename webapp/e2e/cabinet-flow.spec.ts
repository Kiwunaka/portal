import { expect, test, type Page } from "@playwright/test";

type TicketMessageMock = {
  id: number;
  sender_role: "user" | "admin";
  body: string;
  media_type?: string | null;
  media_payload?: string | null;
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

type ExperienceMock = {
  onboarding: {
    version: number;
    status: "pending" | "completed" | "skipped";
    should_show: boolean;
    updated_at: string | null;
  };
  first_connection: {
    state: "none" | "reported" | "verified";
    reported_at: string | null;
    verified_at: string | null;
  };
  next_step: "install" | "connect" | "complete";
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
      channel_bonus: { premium_days: 5, offer_days: 5, claimed_days: 0, claimed_at: null, can_claim: true },
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
        {
          id: 2,
          sender_role: "admin",
          body: "Прикрепили короткий файл диагностики без личных ключей.",
          media_type: "file",
          media_payload: JSON.stringify({
            url: "/uploads/support/20260714-e2ediagnostic.txt",
            name: "diagnostic.txt",
            size: 2048,
            content_type: "text/plain",
          }),
          created_at: "2030-01-01T00:03:00",
        },
        {
          id: 3,
          sender_role: "admin",
          body: "External attachment references are not rendered.",
          media_type: "file",
          media_payload: JSON.stringify({
            url: "https://evil.example/unsafe.txt",
            name: "unsafe.txt",
            size: 12,
            content_type: "text/plain",
          }),
          created_at: "2030-01-01T00:04:00",
        },
        {
          id: 4,
          sender_role: "admin",
          body: "Non-canonical private paths are not rendered.",
          media_type: "file",
          media_payload: JSON.stringify({
            url: "/api/tickets/attachments/not-canonical.txt",
            name: "invalid-private.txt",
            size: 12,
            content_type: "text/plain",
          }),
          created_at: "2030-01-01T00:05:00",
        },
      ],
    },
  ];
}

type HandoffMockMode = "ok" | "expired" | "used" | "invalid" | "rate_limited";

async function registerCabinetMocks(
  page: Page,
  options: {
    seedWebSession?: boolean;
    handoff?: HandoffMockMode;
    handoffTargetPath?: string;
    subscriptionUrl?: string;
    isActive?: boolean;
    channelClaimedDays?: number;
    channelClaimedAt?: string | null;
    onboardingShouldShow?: boolean;
  } = {},
): Promise<void> {
  const seedWebSession = options.seedWebSession ?? true;
  const handoffMode = options.handoff ?? "ok";
  const handoffTargetPath = options.handoffTargetPath ?? "/dashboard/";
  await page.addInitScript((shouldSeedWebSession) => {
    if (shouldSeedWebSession) {
      window.localStorage.setItem("portal_web_session_token", "e2e_mock_token");
    }
    Object.defineProperty(window.navigator, "clipboard", {
      configurable: true,
      value: {
        writeText: async () => undefined,
      },
    });
  }, seedWebSession);

  const sessionUser: ReturnType<typeof mockSessionUser> & { experience?: ExperienceMock } = mockSessionUser();
  if (options.onboardingShouldShow !== undefined) {
    sessionUser.experience = {
      onboarding: {
        version: 1,
        status: options.onboardingShouldShow ? "pending" : "completed",
        should_show: options.onboardingShouldShow,
        updated_at: options.onboardingShouldShow ? null : "2030-01-01T00:00:00",
      },
      first_connection: {
        state: "none",
        reported_at: null,
        verified_at: null,
      },
      next_step: "install",
    };
  }
  const dashboard = mockDashboard();
  const initialChannelClaimedDays = options.channelClaimedDays ?? 0;
  const initialChannelClaimedAt =
    options.channelClaimedAt === undefined && initialChannelClaimedDays > 0
      ? "2029-12-20T00:00:00"
      : options.channelClaimedAt ?? null;
  sessionUser.bonuses.channel_bonus = {
    premium_days: initialChannelClaimedDays || 5,
    offer_days: 5,
    claimed_days: initialChannelClaimedDays,
    claimed_at: initialChannelClaimedAt,
    can_claim: !initialChannelClaimedAt,
  };
  if (options.subscriptionUrl !== undefined) {
    sessionUser.subscription_url = options.subscriptionUrl;
    dashboard.subscription_url = options.subscriptionUrl;
  }
  if (options.isActive !== undefined) {
    sessionUser.is_active = options.isActive;
    dashboard.is_active = options.isActive;
  }
  let tickets = [...mockTickets()];
  let programApplications: Array<Record<string, unknown>> = [];

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
    if (path === "/api/auth/email/status") {
      return json({
        ok: true,
        enabled: true,
        public_enabled: true,
        delivery_configured: true,
        delivery_secret_configured: true,
        debug_echo: false,
        mode: "public",
        blocked_reasons: [],
      });
    }
    if (path === "/api/auth/cabinet-handoff/exchange" && request.method() === "POST") {
      const payload = JSON.parse(request.postData() || "{}");
      if (payload.handoff_token !== "e2e_handoff_token" || handoffMode === "invalid") {
        return json({ detail: { code: "cabinet_handoff_invalid" } }, 401);
      }
      if (handoffMode === "expired") {
        return json({ detail: { code: "cabinet_handoff_expired" } }, 410);
      }
      if (handoffMode === "used") {
        return json({ detail: { code: "cabinet_handoff_already_used" } }, 409);
      }
      if (handoffMode === "rate_limited") {
        return json({ detail: { code: "rate_limited", scope: "cabinet_handoff_exchange" } }, 429);
      }
      return json({
        ok: true,
        token: "e2e_exchanged_session_token",
        target_path: handoffTargetPath,
        auth_origin: "app_cabinet_handoff",
      });
    }
    if (path === "/api/dashboard") return json(dashboard);
    if (path === "/api/account/experience/onboarding" && request.method() === "POST") {
      const payload = JSON.parse(request.postData() || "{}");
      const status = payload.status === "completed" ? "completed" : "skipped";
      sessionUser.experience = {
        onboarding: {
          version: 1,
          status,
          should_show: false,
          updated_at: "2030-01-01T00:05:00",
        },
        first_connection: sessionUser.experience?.first_connection || {
          state: "none",
          reported_at: null,
          verified_at: null,
        },
        next_step: sessionUser.experience?.next_step || "install",
      };
      return json({ ok: true, experience: sessionUser.experience });
    }
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
          play_url: "",
          apk_url: "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-android-universal.apk",
          mirror_url: "https://mirror.pokrov.space/pokrov-vpn-android.apk",
        },
        windows: {
          exe_url: "https://github.com/Kiwunaka/POKROV-app/releases/download/v0.2.0-beta.1/pokrov-windows-setup-x64.exe",
          mirror_url: "https://mirror.pokrov.space/pokrov-vpn-windows.exe",
        },
        docs_url: "https://pokrov.space/news/",
        updated_at: "2030-01-01T00:00:00",
      });
    }
    if (path === "/api/client/device-pairing/codes" && request.method() === "POST") {
      return json({
        ok: true,
        pairing: {
          id: "pairing-e2e-1",
          status: "active",
          code_hint: "9XYZ",
          code: "ABCD-9XYZ",
          pairing_uri: "pokrov://pair?code=ABCD-9XYZ",
          expires_at: "2035-01-01T00:10:00Z",
          created_at: "2035-01-01T00:00:00Z",
          claimed_at: null,
          ttl_seconds: 600,
        },
      });
    }
    if (path === "/api/client/device-pairing/codes" && request.method() === "GET") {
      return json({ ok: true, items: [] });
    }
    if (path === "/api/client/device-pairing/codes/pairing-e2e-1" && request.method() === "DELETE") {
      return json({ ok: true, pairing: { id: "pairing-e2e-1", status: "cancelled", code_hint: "9XYZ" } });
    }
    if (path === "/api/client/programs" && request.method() === "GET") {
      return json({
        ok: true,
        capabilities: [
          { kind: "competitor_switch", title: "Переход от другого VPN", enabled: true, review: "manual", reward: "После проверки" },
          { kind: "research", title: "Исследования и качественные баг-репорты", enabled: true, review: "manual", reward: "1, 3 или 7 дней" },
          { kind: "team_pack", title: "Набор для команды", enabled: true, review: "manual", reward: "Персональное предложение" },
          { kind: "affiliate", title: "Партнёрская программа", enabled: false, review: "not_accepting", reward: "Пока закрыта" },
        ],
        applications: programApplications,
      });
    }
    if (path === "/api/client/programs/applications" && request.method() === "POST") {
      const payload = JSON.parse(request.postData() || "{}");
      const application = {
        id: "program-e2e-1",
        kind: payload.kind,
        status: "submitted",
        source_name: payload.source_name || null,
        seats: payload.seats || null,
        summary: payload.summary,
        contact: payload.contact || null,
        reward_days: 0,
        rewarded: false,
        decision_note: null,
        created_at: "2030-01-01T00:00:00Z",
        updated_at: "2030-01-01T00:00:00Z",
        reviewed_at: null,
      };
      programApplications = [application];
      return json({ ok: true, application });
    }
    if (path === "/api/client/programs/applications/program-e2e-1" && request.method() === "DELETE") {
      programApplications = programApplications.map((row) => ({ ...row, status: "cancelled" }));
      return json({ ok: true, application: programApplications[0] });
    }
    if (path === "/api/bonuses") {
      const channelBonus = sessionUser.bonuses.channel_bonus;
      return json({
        tg_id: sessionUser.tg_id,
        referral_count: sessionUser.bonuses.referral_count,
        referral_code: sessionUser.referral.code,
        referral_bonus_days: sessionUser.referral.bonus_days,
        streak_months: sessionUser.bonuses.wheel.streak_months,
        last_wheel_spin: sessionUser.bonuses.wheel.last_spin_at,
        channel_bonus_premium_days: channelBonus.offer_days,
        channel_bonus_claimed_at: channelBonus.claimed_at,
        channel_username: sessionUser.channel.username,
        channel: {
          offer_days: channelBonus.offer_days,
          claimed_days: channelBonus.claimed_days,
          claimed: Boolean(channelBonus.claimed_at),
          claimed_at: channelBonus.claimed_at,
          channel_username: sessionUser.channel.username,
        },
      });
    }
    if (path === "/api/channel/subscriber/check") {
      const channelBonus = sessionUser.bonuses.channel_bonus;
      return json({
        ok: true,
        subscriber: true,
        claim_required: !channelBonus.claimed_at,
        already_claimed: Boolean(channelBonus.claimed_at),
        bonus_days: channelBonus.offer_days,
      });
    }
    if (path === "/api/bonuses/channel/claim") {
      sessionUser.bonuses.channel_bonus = {
        premium_days: 5,
        offer_days: 5,
        claimed_days: 5,
        claimed_at: "2030-01-01T00:10:00",
        can_claim: false,
      };
      sessionUser.channel.subscriber = true;
      return json({
        ok: true,
        already_claimed: false,
        premium_days: 5,
        claimed_at: "2030-01-01T00:10:00",
        expiry_at: "2030-01-06T00:00:00",
      });
    }
    if (path === "/api/public/plans") {
      return json({
        widget_enabled: true,
        plans: [
          {
            code: "1_month",
            label: "1 месяц",
            amount_rub: 239,
            amount_stars: 239,
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
            amount_rub: 1999,
            amount_stars: 1999,
            days: 365,
            device_limit: 5,
            node_policy: "paid_pool",
            badge: "-30%",
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
        ok: true,
        attachment_id: "20260714-e2estagedattachment.txt",
        attachment: {
          media_type: "file",
          media_file_id: "support/20260714-e2estagedattachment.txt",
          media_payload: JSON.stringify({
            url: "/api/tickets/attachments/20260714-e2estagedattachment.txt",
            name: "attachment.txt",
            size: 10,
            content_type: "text/plain",
            private: true,
          }),
        },
        attachment_payload: {
          url: "/api/tickets/attachments/20260714-e2estagedattachment.txt",
          name: "attachment.txt",
          size: 10,
          content_type: "text/plain",
          private: true,
        },
      });
    }
    if (path === "/api/tickets/attachments/20260714-e2ediagnostic.txt") {
      return route.fulfill({
        status: 200,
        contentType: "text/plain; charset=utf-8",
        body: "private diagnostic body",
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

test.describe("Cabinet session persistence", () => {
  test("exchanges an app handoff token once and removes it from the URL", async ({ page }) => {
    await registerCabinetMocks(page, { seedWebSession: false });
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
    });

    await page.goto("/dashboard/?handoff_token=e2e_handoff_token");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect
      .poll(() => page.evaluate(() => window.localStorage.getItem("portal_web_session_token")))
      .toBe("e2e_exchanged_session_token");
    await expect(page.locator("main")).toContainText("Доступ активен");
  });

  test("uses the exchanged cabinet target path", async ({ page }) => {
    await registerCabinetMocks(page, { seedWebSession: false, handoffTargetPath: "/settings/" });
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
    });

    await page.goto("/dashboard/?handoff_token=e2e_handoff_token");

    await expect(page).toHaveURL(/\/settings\/?$/);
    await expect
      .poll(() => page.evaluate(() => window.localStorage.getItem("portal_web_session_token")))
      .toBe("e2e_exchanged_session_token");
  });

  test("explains a reused app handoff link and removes it from the URL", async ({ page }) => {
    await registerCabinetMocks(page, { seedWebSession: false, handoff: "used" });
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
    });

    await page.goto("/dashboard/?handoff_token=e2e_handoff_token");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect
      .poll(() => page.evaluate(() => window.localStorage.getItem("portal_web_session_token")))
      .toBeNull();
    await expect(page.locator("main")).toContainText("Эта ссылка уже использована");
  });

  test("reuses an email web session from the cookie fallback", async ({ page }) => {
    await registerCabinetMocks(page, { seedWebSession: false });
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
      document.cookie = "portal_web_session_token=e2e_mock_token; Path=/; SameSite=Lax";
    });

    await page.goto("/");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect(page.locator("main")).toContainText("Доступ активен");
    await expect(page.getByRole("heading", { name: "Вход в аккаунт" })).toHaveCount(0);
  });
});

test("settings preserves a grandfathered claimed Telegram bonus", async ({ page }) => {
  await registerCabinetMocks(page, { channelClaimedDays: 10, channelClaimedAt: "2029-12-20T00:00:00" });

  await page.goto("/settings/");

  await expect(page.locator("main")).toContainText("Получено +10 дней");
  await expect(page.getByRole("button", { name: "Получено", exact: true })).toBeDisabled();
  await expect(page.getByRole("button", { name: /Забрать \+10 дней/i })).toHaveCount(0);
});

test("persists first-run onboarding in the account instead of local storage", async ({ page }) => {
  await registerCabinetMocks(page, { onboardingShouldShow: true });
  await page.goto("/dashboard/");

  const tour = page.getByTestId("onboarding-tour");
  await expect(tour).toBeVisible();
  await expect(tour.getByRole("heading", { name: "Добро пожаловать в POKROV" })).toBeVisible();
  await tour.getByRole("button", { name: "Пропустить" }).click();
  await expect(tour).toHaveCount(0);

  await page.reload();
  await expect(page.getByTestId("onboarding-tour")).toHaveCount(0);
  const storedKeys = await page.evaluate(() => Object.keys(window.localStorage));
  expect(storedKeys).not.toContain("pokrov-onboarding-v1");
});

test.describe("Cabinet flow", () => {
  test.beforeEach(async ({ page }) => {
    await registerCabinetMocks(page);
  });

  test("shows shared POKROV cabinet branding and a site return link", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard/");

    await expect(page.getByLabel("POKROV logo").first()).toBeVisible();
    const sidebar = page.getByRole("complementary").first();
    await expect(sidebar).toBeVisible();
    await expect(sidebar.locator("nav")).toContainText("Главная");
    await expect(sidebar.locator("nav")).toContainText("Доступ");
    await expect(sidebar.locator("nav")).toContainText("Защита");
    await expect(sidebar.locator("nav")).toContainText("Помощь");
    await expect(sidebar.locator("nav")).toContainText("Аккаунт");
    await expect(sidebar.locator("nav")).not.toContainText("Статистика");
    await expect(sidebar.locator("nav")).not.toContainText("Загрузки");

    const siteLink = page.getByRole("link", { name: /^На сайт/i });
    await expect(siteLink).toBeVisible();
    await expect(siteLink).toHaveAttribute("href", /https:\/\/pokrov\.space\/?$/);
  });

  test("keeps server and device protection checks distinct", async ({ page }) => {
    await page.goto("/protection/");

    await expect(page.getByRole("heading", { name: "Подключение этого аккаунта не подтверждено" })).toBeVisible();
    await expect(page.locator("main")).not.toContainText("2 активн.");
    await expect(page.locator("main")).toContainText("Туннель");
    await expect(page.locator("main")).toContainText("DNS");
    await expect(page.locator("main")).toContainText("Интернет / HTTPS");
    await expect(page.locator("main")).toContainText("не выдаются за внешний leak-тест");
    await expect(page.locator("main")).toContainText("Автоматических бесконечных повторов нет");
  });

  test("uses desktop navigation at 1280px without mobile navigation chrome", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/dashboard/");

    await expect(page.getByRole("complementary").first()).toBeVisible();
    await expect(page.locator(".mobile-nav-root")).toHaveCount(0);
    await page.locator("aside nav a[href='/subscription/']").click();
    await expect(page).toHaveURL(/\/subscription\/?$/);
    await expect(page.locator("main h1", { hasText: "Продлить доступ" })).toBeVisible();
  });

  test("deduplicates rapid same-section left clicks", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    const supportRscRequests: string[] = [];
    page.on("request", (request) => {
      const url = request.url();
      const isPrefetch =
        Boolean(request.headers()["next-router-prefetch"]) || request.headers()["purpose"] === "prefetch";
      if (url.includes("/support") && url.includes("_rsc=") && !isPrefetch) {
        supportRscRequests.push(url);
      }
    });

    await page.goto("/dashboard/");
    const supportLink = page.locator("aside nav a[href='/support/']").first();
    await expect(supportLink).toBeVisible();
    await supportLink.evaluate((element) => {
      for (let index = 0; index < 3; index += 1) {
        element.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 }));
      }
    });

    await expect(page).toHaveURL(/\/support\/?$/);
    expect(supportRscRequests.length).toBeLessThanOrEqual(1);
  });

  test("shows email and Telegram entry on the root auth entry", async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
    });

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Вход в аккаунт" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Войдите по email или через Telegram");
    await expect(page.getByRole("button", { name: "Вход" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Регистрация" })).toBeVisible();
    await expect(page.getByPlaceholder("name@example.com")).toBeVisible();
    await expect(page.getByPlaceholder("Пароль")).toBeVisible();
    await expect(page.getByRole("button", { name: "Войти через Telegram" })).toBeVisible();

    await page.getByRole("button", { name: "Регистрация" }).click();
    await expect(page.getByRole("heading", { name: "Создать аккаунт" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Зарегистрируйтесь по email");
    await expect(page.getByRole("heading", { name: "Вход в аккаунт" })).toHaveCount(0);
    await expect(page.locator("main")).not.toContainText("Войдите по email или через Telegram");
  });

  test("keeps the email entry available alongside Telegram", async ({ page }) => {
    await page.addInitScript(() => {
      window.localStorage.removeItem("portal_web_session_token");
    });

    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Вход в аккаунт" })).toBeVisible();
    await expect(page.getByPlaceholder("name@example.com")).toBeVisible();
    await expect(page.getByRole("button", { name: "Войти через Telegram" })).toBeVisible();
  });

  test("reuses an existing web session and lands in the cabinet without showing auth entry again", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveURL(/\/dashboard\/?$/);
    await expect(page.getByRole("heading", { name: "Доступ активен" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Вход в аккаунт" })).toHaveCount(0);
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
    await expect(page.getByRole("button", { name: "Войти через Telegram" })).toBeVisible();
  });

  test("maps raw Telegram deprecated auth errors to a reauth CTA", async ({ page }) => {
    await page.route("**/api/auth/session", async (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        headers: { "x-pokrov-auth-error": "telegram_login_deprecated" },
        body: JSON.stringify({ detail: "telegram_login_deprecated" }),
      }),
    );

    await page.goto("/dashboard/");

    await expect(page.locator("main")).toContainText("Вход устарел");
    await expect(page.locator("main")).not.toContainText("telegram_login_deprecated");
    await expect(page.getByRole("button", { name: "Войти через Telegram" })).toBeVisible();
  });

  test("keeps the dashboard on consumer-safe access actions", async ({ page }) => {
    await page.goto("/dashboard/");

    await expect(page.getByRole("heading", { name: "Доступ активен" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Скачайте приложение POKROV");
    await expect(page.getByRole("link", { name: "Скачать приложение" })).toHaveCount(1);
    await expect(page.locator("main")).toContainText("Сводка");
    await expect(page.locator("main")).toContainText("Активировать код");
    await expect(page.locator("main")).not.toContainText("Что нужно сейчас?");
    await expect(page.locator("main")).not.toContainText("Следующий шаг");
    await expect(page.locator("main")).not.toContainText("Ручная настройка");
    await expect(page.locator("main")).not.toContainText("?format=plain");
    await expect(page.locator("main")).not.toContainText("mock_token");
    await expect(page.getByRole("button", { name: "Показать", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Показать QR" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Скопировать" })).toHaveCount(0);
  });

  test("uses the side drawer as the only mobile cabinet navigation", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/dashboard/");

    await expect(page.locator(".mobile-nav-root")).toHaveCount(0);
    const menuButton = page.getByRole("button", { name: "Открыть меню" });
    await expect(menuButton).toBeVisible();
    await expect(page.getByRole("heading", { name: "Доступ активен" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Скачать приложение" })).toHaveCount(1);
    await expect(page.locator("main")).toContainText("Трафик");
    await expect(page.locator("main")).toContainText("Устройства");
    await expect(page.locator("main")).not.toContainText("Что нужно сейчас?");
    await expect(page.locator("main")).not.toContainText("Следующий шаг");
    await expect(page.locator("main")).not.toContainText("Ручная настройка");
    await expect(page.locator("main")).not.toContainText("mock_token");

    await menuButton.click();

    const drawer = page.getByTestId("mobile-cabinet-drawer");
    await expect(drawer).toBeVisible();
    const drawerNav = drawer.getByRole("navigation", { name: "Навигация кабинета" });
    await expect(drawerNav.locator("a")).toHaveCount(5);
    await expect(drawerNav).toContainText("Главная");
    await expect(drawerNav).toContainText("Доступ");
    await expect(drawerNav).toContainText("Защита");
    await expect(drawerNav).toContainText("Помощь");
    await expect(drawerNav).toContainText("Аккаунт");
    await expect(drawerNav).not.toContainText("Статистика");
    await expect(drawerNav).not.toContainText("Устройства");
    await drawerNav.locator("a[href='/subscription/']").click();
    await expect(page).toHaveURL(/\/subscription\/?$/);
    await expect(drawer).toHaveCount(0);

    await expect(page.locator("main h1", { hasText: "Продлить доступ" })).toBeVisible();

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("keeps cabinet navigation usable with left-click browser routing", async ({ page }) => {
    await page.goto("/dashboard/");

    await page.locator("aside nav a[href='/subscription/']").click();
    await expect(page).toHaveURL(/\/subscription\/?$/);
    await expect(page.locator("main h1", { hasText: "Продлить доступ" })).toBeVisible();

    await expect(page.locator("aside nav a[href='/downloads/']")).toHaveCount(0);
    await page.goto("/downloads/");
    await expect(page).toHaveURL(/\/downloads\/?$/);
    await expect(page.locator("main h1")).toBeVisible();
    await expect(page.locator("main")).toContainText("Приложение для Android");
  });

  test("keeps all six canonical plans when the public plan request fails", async ({ page }) => {
    await page.route("**/api/public/plans", (route) =>
      route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ detail: "unavailable" }) }),
    );

    await page.goto("/subscription/");

    await expect(page.locator("details", { hasText: "Все тарифы" })).toHaveCount(1);
    await expect(page.getByTestId("subscription-plan-grid")).not.toBeVisible();
    await page.getByText("Все тарифы", { exact: true }).click();
    const grid = page.getByTestId("subscription-plan-grid");
    await expect(page.locator("main")).toContainText("Часть тарифов не обновилась");
    await expect(grid.locator("article")).toHaveCount(6);
    for (const [code, price] of [
      ["start_99", 99],
      ["1_month", 239],
      ["3_months", 669],
      ["6_months", 1199],
      ["9_months", 1699],
      ["12_months", 1999],
    ] as const) {
      await expect(grid.locator(`[data-plan-code='${code}']`)).toContainText(`${price} ₽`);
    }
  });

  test("gives secondary APK downloads a mobile-safe touch target", async ({ page }) => {
    await page.route("**/api/client/apps", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          android: {
            apk_url: "https://downloads.pokrov.space/pokrov-android-universal.apk",
            apk_variants: [
              { abi: "arm64-v8a", url: "https://downloads.pokrov.space/pokrov-android-arm64.apk" },
              { abi: "armeabi-v7a", url: "https://downloads.pokrov.space/pokrov-android-armv7.apk" },
            ],
            mirror_url: "",
          },
          windows: { exe_url: "", mirror_url: "" },
          docs_url: "",
        }),
      }),
    );
    await page.setViewportSize({ width: 390, height: 844 });

    await page.goto("/downloads/");

    const secondaryApk = page.locator("main a[href='https://downloads.pokrov.space/pokrov-android-armv7.apk']");
    await expect(secondaryApk).toBeVisible();
    const box = await secondaryApk.boundingBox();
    expect(box?.height ?? 0).toBeGreaterThanOrEqual(44);
    expect(await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth)).toBeLessThanOrEqual(1);
  });

  test("keeps download instructions compact until requested", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/downloads/");

    const disclosure = page.getByText("Как подключиться за 3 шага", { exact: true });
    await expect(disclosure).toBeVisible();
    await expect(page.getByText("Берите файл только на этой странице.")).not.toBeVisible();
    await disclosure.click();
    await expect(page.getByText("Берите файл только на этой странице.")).toBeVisible();
  });

  test("links a trial entitlement to compact checkout", async ({ page }) => {
    const trialExpiry = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000).toISOString();
    await page.route("**/api/dashboard", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...mockDashboard(),
          sub_type: "TRIAL",
          segment: "TRIAL",
          access_state: "trial_premium",
          current_plan_code: "trial_premium",
          expiry_at: trialExpiry,
        }),
      }),
    );
    await page.route("**/api/user/1001", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ...mockSessionUser(),
          sub_type: "TRIAL",
          segment: "TRIAL",
          access_state: "trial_premium",
          expiry_at: trialExpiry,
        }),
      }),
    );

    await page.goto("/dashboard/");

    const trialLink = page.getByRole("link", { name: "5 дней → тарифы" });
    await expect(trialLink).toHaveAttribute("href", "/subscription/checkout/?plan=start_99");
    expect((await trialLink.boundingBox())?.height ?? 0).toBeGreaterThanOrEqual(44);
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

    await expect(page.locator("main h1", { hasText: "Продлить доступ" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Оплатить" }).first()).toBeVisible();
    await expect(page.getByRole("link", { name: "Активировать код" }).first()).toBeVisible();
    await expect(page.locator("main")).not.toContainText("История оплат");
    await expect(page.locator("main")).not.toContainText("Коротко о режимах");

    const manualConnection = page.locator("#manual-setup");
    await expect(manualConnection).toContainText("Ручная настройка");
    await expect(manualConnection).not.toContainText("mock_token");
    await expect(manualConnection).not.toContainText("Совместимые клиенты");
    await manualConnection.getByRole("button", { name: "Показать" }).click();
    await expect(manualConnection).toContainText("mock_token");
    await expect(manualConnection).toContainText("Совместимые клиенты");
    await expect(manualConnection.getByRole("button", { name: "Скопировать ссылку" })).toBeVisible();
    await expect(manualConnection.getByRole("link", { name: "Открыть ссылку" })).toBeVisible();
    await expect(page.locator("main")).not.toContainText("?format=plain");
  });

  test("builds the Happ URL without leaking it to third parties", async ({ page }) => {
    const privateUrl = "https://connect.pokrov.space/token-value?existing=1#manual";
    const telemetryPayloads: string[] = [];
    page.on("request", (request) => {
      if (/analytics|beacon|collect|telemetry/i.test(request.url())) {
        telemetryPayloads.push(`${request.url()}\n${request.postData() || ""}`);
      }
    });
    await registerCabinetMocks(page, { subscriptionUrl: privateUrl });

    await page.goto("/subscription/#manual-setup");
    const manualConnection = page.locator("#manual-setup");
    await expect(manualConnection.getByRole("button", { name: "Скрыть" })).toBeVisible();

    await expect(page.getByTestId("happ-subscription-url")).toContainText("existing=1&format=happ");
    await expect(page.getByRole("button", { name: "Скопировать для Happ" })).toBeVisible();
    await expect(page.locator("main")).not.toContainText("Karing");

    const externalLinks = page.locator('a[target="_blank"]');
    for (let index = 0; index < await externalLinks.count(); index += 1) {
      const href = (await externalLinks.nth(index).getAttribute("href")) || "";
      expect(href).not.toContain("token-value");
      expect(href).not.toContain("connect.pokrov.space");
    }
    expect(telemetryPayloads.join("\n")).not.toContain("token-value");
    expect(telemetryPayloads.join("\n")).not.toContain("connect.pokrov.space");
  });

  test("keeps manual setup closed from a direct hash when no active link exists", async ({ page }) => {
    await registerCabinetMocks(page, { subscriptionUrl: "" });

    await page.goto("/subscription/#manual-setup");

    const manualConnection = page.locator("#manual-setup");
    await expect(manualConnection).toContainText("Появится после активации");
    await expect(manualConnection).toContainText("скрыто");
    await expect(manualConnection).not.toContainText("Совместимые клиенты");
    await expect(manualConnection).not.toContainText("connect.pokrov.space");
    await expect(manualConnection.getByRole("button", { name: "Скопировать ссылку" })).toHaveCount(0);
    await expect(manualConnection.getByRole("link", { name: "Открыть ссылку" })).toHaveCount(0);
  });

  test("keeps paid plan cards selectable for a free monthly account", async ({ page }) => {
    const freeUser = {
      ...mockSessionUser(),
      sub_type: "FREE_MONTHLY",
      segment: "FREE",
      access_state: "free_monthly",
      current_plan_code: "1_month",
      is_active: true,
      limits: { device_limit: 1, total_gb: 5, speed_mbps: 50 },
      traffic: { used_gb: 0.4, used_bytes: 0, total_gb: 5, remaining_gb: 4.6, source: "free_policy" },
      traffic_policy: {
        kind: "monthly_limit",
        label: "5 ГБ на 30 дней",
        limit_gb: 5,
        remaining_gb: 4.6,
        next_reset_at: "2030-02-01T00:00:00",
        soft_mode_active: false,
      },
      traffic_limit_gb: 5,
      traffic_remaining_gb: 4.6,
      next_reset_at: "2030-02-01T00:00:00",
      device_limit: 1,
    };
    const freeDashboard = {
      ...mockDashboard(),
      sub_type: "FREE_MONTHLY",
      segment: "FREE",
      access_state: "free_monthly",
      current_plan_code: "1_month",
      is_active: true,
      total_gb: 5,
      remaining_gb: 4.6,
      device_limit: 1,
      speed_limit_mbps: 50,
      traffic_policy: {
        kind: "monthly_limit",
        label: "5 ГБ на 30 дней",
        limit_gb: 5,
        remaining_gb: 4.6,
        next_reset_at: "2030-02-01T00:00:00",
        soft_mode_active: false,
      },
      traffic_limit_gb: 5,
      traffic_remaining_gb: 4.6,
      next_reset_at: "2030-02-01T00:00:00",
    };

    await page.route("**/api/dashboard", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(freeDashboard) }),
    );
    await page.route("**/api/user/1001", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(freeUser) }),
    );
    await page.setViewportSize({ width: 1440, height: 900 });

    await page.goto("/subscription/");

    await page.getByText("Все тарифы", { exact: true }).click();
    const firstPaidPlanAction = page.locator("main a[href='/subscription/checkout/?plan=1_month']");
    await expect(firstPaidPlanAction).toBeVisible();
    const box = await firstPaidPlanAction.boundingBox();
    expect(box?.y ?? 9999).toBeLessThan(900);
  });

  test("renders runtime connections on devices and keeps statistics as its own safe-summary page", async ({ page }) => {
    await page.goto("/devices/");

    await expect(page.getByRole("heading", { name: "Устройства" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Сводка");
    await expect(page.locator("main")).toContainText("Список");
    await expect(page.locator("main")).toContainText("Сессий в сети");
    await expect(page.locator("main")).toContainText("Общий счётчик, не ваши устройства");
    await expect(page.locator("main")).not.toContainText("2 из 5");
    await expect(page.locator("main")).not.toContainText("Главное сейчас");
    await expect(page.locator("main")).toContainText("Добавить устройство");

    await page.goto("/statistics/");
    await expect(page).toHaveURL(/\/statistics\/?$/);
    await expect(page.getByRole("heading", { name: "Статистика" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Безопасная сводка");
    await expect(page.locator("main")).toContainText("Сессий в сети");
    await expect(page.locator("main")).toContainText("Людей онлайн");
    await expect(page.locator("main")).not.toContainText("Короткая картина");
    await expect(page.locator("main")).not.toContainText("pl.pokrov.space");
    await expect(page.locator("main")).not.toContainText("mock_token");
  });

  test("issues a one-time device code without exposing the subscription URL", async ({ page }) => {
    await page.goto("/devices/");
    await page.getByTestId("device-pairing-issue").click();

    await expect(page.getByTestId("device-pairing-code")).toHaveText("ABCD-9XYZ");
    await expect(page.locator("main")).toContainText("На новом устройстве откройте POKROV");
    await expect(page.locator("main")).not.toContainText("mock_token");
  });

  test("searches fallback guides and the POKROV screen atlas on mobile", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/guides/");

    await expect(page.getByRole("heading", { name: "Инструкции POKROV" })).toBeVisible();
    const guideSearch = page.getByRole("searchbox", { name: "Найти задачу, кнопку или клиент" });
    await guideSearch.fill("Happ");
    await expect(page.getByText("Найдено:").locator("..")).toContainText("2");

    const happGuide = page.locator("#fallback-happ");
    await happGuide.getByText("Подключиться через Happ", { exact: true }).click();
    await expect(happGuide).toContainText("Что делает каждая кнопка");
    await expect(happGuide).toContainText("Provider ID");

    await page.getByRole("button", { name: "Очистить поиск" }).click();
    await page.getByRole("button", { name: "Fallback 7", exact: true }).click();
    await expect(page.getByText("Найдено:").locator("..")).toContainText("7");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      await page.evaluate(() => document.documentElement.clientWidth),
    );

    await page.getByRole("link", { name: /Все экраны и кнопки POKROV/ }).click();
    await expect(page).toHaveURL(/\/guides\/pokrov-app\/?$/);
    await expect(page.getByRole("heading", { name: "Весь POKROV по экранам и кнопкам" })).toBeVisible();
    await expect(page.getByText("Показано:").locator("..")).toContainText("20 из 20");

    await page.getByRole("searchbox", { name: "Найти экран или кнопку" }).fill("DNS");
    await expect(page.getByText("Показано:").locator("..")).toContainText("3 из 20");
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      await page.evaluate(() => document.documentElement.clientWidth),
    );
  });

  test("submits a competitor-switch application without automatic reward", async ({ page }) => {
    await page.goto("/programs/");
    const competitorSelector = page.getByRole("button", { name: /Переход от другого VPN/ });
    const researchSelector = page.getByRole("button", { name: /Исследования и качественные баг-репорты/ });
    const affiliateSelector = page.getByRole("button", { name: /Партнёрская программа/ });
    await expect(competitorSelector).toHaveAttribute("aria-pressed", "true");
    await expect(researchSelector).toHaveAttribute("aria-pressed", "false");
    await expect(affiliateSelector).toHaveAttribute("aria-pressed", "false");
    await expect(affiliateSelector).toBeDisabled();
    await researchSelector.click();
    await expect(researchSelector).toHaveAttribute("aria-pressed", "true");
    await competitorSelector.click();
    const form = page.getByTestId("program-application-form");
    await form.getByPlaceholder("Название сервиса").fill("Hiro VPN");
    await form.getByPlaceholder("Кратко опишите задачу и ожидаемый результат").fill("Хочу перенести два устройства и сохранить быстрый видеомаршрут.");
    await form.getByRole("button", { name: "Отправить на проверку" }).click();

    await expect(page.locator("main")).toContainText("Заявка принята");
    await expect(page.locator("main")).toContainText("Принята");
    await expect(page.locator("main")).not.toContainText("+7 дн.");
  });

  test("keeps redeem as a compact activation task", async ({ page }) => {
    await page.goto("/redeem/");

    await expect(page.getByRole("heading", { name: "Активировать код" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Код");
    await expect(page.locator("main")).toContainText("Что дальше");
    await expect(page.getByPlaceholder("Код активации")).toBeVisible();
    await expect(page.getByRole("button", { name: "Проверить" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Активировать" })).toBeVisible();
    await expect(page.locator("main")).not.toContainText("Что делать сейчас");
    await expect(page.locator("main")).not.toContainText("Шаг 1");
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

    await expect(page.getByRole("heading", { name: "Аккаунт", exact: true })).toBeVisible();
    await expect(page.locator("main")).toContainText("Профиль");
    await expect(page.locator("main")).toContainText("Вход и восстановление");
    await expect(page.locator("main")).toContainText("Telegram-бонус");
    await expect(page.locator("main")).toContainText("Действия");
    await page.getByRole("button", { name: /Проверить подписку/i }).click();
    await expect(page.locator("main")).toContainText("Подписка подтверждена");
    await page.getByRole("button", { name: /Забрать \+5 дней/i }).click();
    await expect(page.locator("main")).toContainText("Бонус +5 дней добавлен");
    await expect(page.locator("main")).not.toContainText("mock_token");

    await page.goto("/profile/");
    await expect(page).toHaveURL(/\/settings\/?$/);
  });

  test("shows honest payment history and a compact Russian checkout", async ({ page }) => {
    await page.goto("/subscription/");
    await expect(page.locator("main")).not.toContainText("История оплат");
    await expect(page.locator("main")).not.toContainText("Оплаты появятся здесь");

    await page.route("**/api/payments/providers", async (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          ok: false,
          providers: [],
          blocked: true,
          blocked_reasons: ["paid_checkout_launch_evidence_missing"],
          blocked_reason_texts: ["Lava.top ещё ждёт финальную проверку."],
        }),
      }),
    );

    await page.goto("/subscription/checkout/?plan=1_month&promo=POKROV10");
    await expect(page.getByRole("heading", { name: "Продлить доступ" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Оформление");
    await expect(page.locator("main")).toContainText("1 месяц");
    await expect(page.locator("main")).toContainText("Способ оплаты");
    await page.getByRole("button", { name: /1 месяц.*239 ₽/ }).click();
    await expect(page.getByRole("radiogroup", { name: "Срок доступа" }).getByRole("radio")).toHaveCount(6);
    await expect(page.locator("main")).toContainText("К оплате");
    await expect(page.getByRole("button", { name: /Оплатить \d+ ₽/ }).first()).toBeDisabled();
    await expect(page.locator("main")).toContainText("Разовая оплата · без автосписаний");
    await expect(page.locator("main")).not.toContainText("Что дальше");
    await expect(page.locator("main")).toContainText("Оплата временно недоступна. Попробуйте позже или откройте поддержку.");
    await expect(page.locator("main")).not.toContainText("Из личного кабинета");
    await expect(page.locator("main")).not.toContainText("Покупка проходит на платежной странице");
    await expect(page.locator("main")).not.toContainText("Hosted checkout");
    await expect(page.locator("main")).not.toContainText("activation key");
    await expect(page.locator("main")).not.toContainText("Free fallback");
    await expect(page.locator("main")).not.toContainText("accessState");
    await expect(page.locator("main")).not.toContainText("managed profile");
    await expect(page.locator("main")).not.toContainText("premium trial");
    await expect(page.locator("main")).not.toContainText("Email signup");
  });

  test("keeps downloads and support flows usable without the app", async ({ page }) => {
    await page.goto("/dashboard/downloads/");

    await expect(page).toHaveURL(/\/downloads\/?$/);
    await expect(page.getByRole("heading", { name: "Загрузки" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Файлы");
    await expect(page.locator("main")).toContainText("После скачивания");
    await expect(page.locator("main")).toContainText("Публичная бета");
    await expect(page.locator("main")).toContainText("Приложение для Android");
    await expect(page.locator("main a[href*='github.com'][href$='pokrov-android-universal.apk']").first()).toBeVisible();
    await expect(page.locator("main")).toContainText("Windows");
    await expect(page.locator("main")).toContainText("предупреждение");
    await expect(page.locator("main a[href*='github.com'][href$='pokrov-windows-setup-x64.exe']").first()).toBeVisible();
    await expect(page.locator("main")).not.toContainText("Что делать сейчас");

    await page.goto("/support/");
    await expect(page.getByRole("heading", { name: "Помощь" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Последнее обращение");
    await expect(page.locator("main")).toContainText("Быстрые действия");
    await expect(page.locator("main")).toContainText("Диагностика");
    await expect(page.locator("main")).not.toContainText("У меня есть личная ссылка");
    await expect(page.locator("main")).not.toContainText("Длинная ссылка подключения туда не подходит");
    await expect(page.locator("main")).not.toContainText("public IP");
    await expect(page.locator("main")).not.toContainText("subscription_url");
    await page.getByRole("button", { name: "Новый вопрос" }).first().click();
    await page.getByPlaceholder("Коротко: что случилось").fill("Нужна помощь с импортом");
    await page
      .getByPlaceholder("Опишите, что делали, где сломалось и что видите сейчас.")
      .fill("Тестовое обращение без приложения.");
    await page.getByRole("button", { name: "Отправить вопрос" }).click();
    await expect(page.locator("main")).toContainText("Открыт · #");
    await expect(page.locator("main")).toContainText("Нужна помощь с импортом");
  });

  test("renders support thread attachments without exposing private access data", async ({ page }) => {
    await page.context().addCookies([
      {
        name: "portal_web_session",
        value: "e2e-cookie-session",
        domain: "127.0.0.1",
        path: "/",
      },
      {
        name: "portal_web_session",
        value: "e2e-cookie-session",
        domain: "localhost",
        path: "/",
      },
      {
        name: "portal_web_session",
        value: "e2e-cookie-session",
        url: "https://api.pokrov.space/",
        sameSite: "None",
        secure: true,
      },
    ]);
    const attachmentRequests: string[] = [];
    page.on("request", (request) => {
      if (request.url().includes("/api/tickets/attachments/20260714-e2ediagnostic.txt")) {
        attachmentRequests.push(request.url());
      }
    });
    await page.goto("/support/thread/?id=11");

    await expect(page).toHaveURL(/\/support\/thread\/\?id=11$/);
    await expect(page.getByRole("heading", { name: /Обращение #11|Подключение после оплаты/ })).toBeVisible();
    await expect(page.locator("main")).toContainText("История");
    await expect(page.locator("main")).toContainText("Ответ");
    await expect(page.locator("main")).toContainText("diagnostic.txt");
    await page.waitForTimeout(200);
    expect(attachmentRequests).toHaveLength(0);

    const blobRequestPromise = page.waitForRequest((request) =>
      request.url().includes("/api/tickets/attachments/20260714-e2ediagnostic.txt"),
    );
    await page.getByRole("button", { name: "Загрузить diagnostic.txt" }).click();
    const blobRequest = await blobRequestPromise;
    expect(blobRequest.headers()["authorization"]).toBe("Bearer e2e_mock_token");
    expect(blobRequest.headers()["cookie"]).toContain("portal_web_session=e2e-cookie-session");
    const attachment = page.locator('main a[href^="blob:"]').first();
    await expect(attachment).toBeVisible();
    await expect(attachment).toContainText("diagnostic.txt");
    await expect(attachment).toContainText("2.0 КБ");
    await expect(page.locator("main")).not.toContainText("unsafe.txt");
    await expect(page.locator("main")).not.toContainText("invalid-private.txt");
    await expect(page.locator("main")).not.toContainText("Диалог");
    await expect(page.locator("main")).not.toContainText("Продолжайте это обращение");
    await expect(page.locator("main")).not.toContainText("mock_token");
    await expect(page.locator("main")).not.toContainText("subscription_url");
  });

  test("sends staged attachment id without the private media triplet", async ({ page }) => {
    await page.addInitScript(() => {
      const originalArrayBuffer = File.prototype.arrayBuffer;
      Object.defineProperty(window, "__supportAttachmentArrayBufferCalls", {
        configurable: true,
        value: 0,
        writable: true,
      });
      File.prototype.arrayBuffer = function arrayBuffer() {
        const state = window as Window & { __supportAttachmentArrayBufferCalls?: number };
        state.__supportAttachmentArrayBufferCalls =
          (state.__supportAttachmentArrayBufferCalls || 0) + 1;
        return originalArrayBuffer.call(this);
      };
    });
    await page.goto("/support/");
    await page.getByRole("button", { name: "Новый вопрос" }).first().click();
    await page.getByPlaceholder("Коротко: что случилось").fill("Вложение из кабинета");
    await page
      .getByPlaceholder("Опишите, что делали, где сломалось и что видите сейчас.")
      .fill("Проверяем staged upload contract.");
    const picker = page.locator('input[type="file"]');
    await expect(picker).toHaveAttribute(
      "accept",
      "image/png,image/jpeg,image/webp,application/pdf,text/plain,.png,.jpg,.jpeg,.webp,.pdf,.txt",
    );
    await picker.setInputFiles({
      name: "oversized.txt",
      mimeType: "text/plain",
      buffer: Buffer.alloc(20 * 1024 * 1024 + 1, "a"),
    });
    await page.getByRole("button", { name: "Отправить вопрос" }).click();
    await expect(page.locator("main")).toContainText("Размер файла не должен превышать 20 МиБ.");
    expect(
      await page.evaluate(
        () =>
          (window as Window & { __supportAttachmentArrayBufferCalls?: number })
            .__supportAttachmentArrayBufferCalls,
      ),
    ).toBe(0);
    await picker.setInputFiles({
      name: "mismatched.pdf",
      mimeType: "text/plain",
      buffer: Buffer.from("not a PDF"),
    });
    await page.getByRole("button", { name: "Отправить вопрос" }).click();
    await expect(page.locator("main")).toContainText("Можно приложить PNG, JPEG, WebP, PDF или TXT.");
    await picker.setInputFiles({
      name: "attachment.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("attachment"),
    });
    const createRequestPromise = page.waitForRequest(
      (request) => new URL(request.url()).pathname === "/api/tickets" && request.method() === "POST",
    );
    await page.getByRole("button", { name: "Отправить вопрос" }).click();
    const createRequest = await createRequestPromise;
    const payload = createRequest.postDataJSON();
    expect(payload.attachment_id).toBe("20260714-e2estagedattachment.txt");
    expect(payload).not.toHaveProperty("media_type");
    expect(payload).not.toHaveProperty("media_file_id");
    expect(payload).not.toHaveProperty("media_payload");

    await page.goto("/support/thread/?id=11");
    await page.getByPlaceholder("Напишите ответ...").fill("Reply with staged upload.");
    await page.locator('input[type="file"]').setInputFiles({
      name: "reply.txt",
      mimeType: "text/plain",
      buffer: Buffer.from("reply attachment"),
    });
    const replyRequestPromise = page.waitForRequest(
      (request) =>
        new URL(request.url()).pathname === "/api/tickets/11/messages" && request.method() === "POST",
    );
    await page.getByRole("button", { name: "Отправить", exact: true }).click();
    const replyPayload = (await replyRequestPromise).postDataJSON();
    expect(replyPayload.attachment_id).toBe("20260714-e2estagedattachment.txt");
    expect(replyPayload).not.toHaveProperty("media_type");
    expect(replyPayload).not.toHaveProperty("media_file_id");
    expect(replyPayload).not.toHaveProperty("media_payload");
  });

  test("keeps legal documents as compact support rows", async ({ page }) => {
    await page.goto("/support/legal/");

    await expect(page.getByRole("heading", { name: "Документы" })).toBeVisible();
    await expect(page.locator("main")).toContainText("Ссылки");
    await expect(page.locator("main")).toContainText("Оферта");
    await expect(page.locator("main")).toContainText("Политика");
    await expect(page.locator("main")).toContainText("Вопрос по документам");
    await expect(page.locator("main")).not.toContainText("Юридическая информация");
    await expect(page.locator("main")).not.toContainText("Коротко");
    await expect(page.locator("main")).not.toContainText("Что можно открыть");
  });

  test("stays inside a narrow mobile viewport for core cabinet pages", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });

    for (const route of ["/dashboard/", "/subscription/", "/devices/", "/protection/", "/support/"]) {
      await page.goto(route);
      await expect(page.locator("main")).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
      expect(overflow).toBeLessThanOrEqual(1);
    }
  });
});
