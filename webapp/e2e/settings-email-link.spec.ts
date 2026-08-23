import { expect, test, type Page, type Route } from "@playwright/test";

const json = (route: Route, payload: unknown, status = 200) =>
  route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(payload),
  });

const TELEGRAM_WEBAPP_STUB = `
  window.Telegram = window.Telegram || {};
  window.Telegram.WebApp = window.Telegram.WebApp || {
    initData: "",
    initDataUnsafe: {},
    colorScheme: "light",
    themeParams: {},
    ready() {},
    expand() {},
    onEvent() {},
    offEvent() {},
    setHeaderColor() {},
    setBackgroundColor() {},
    BackButton: {
      show() {},
      hide() {},
      onClick() {},
      offClick() {},
    },
    HapticFeedback: {
      impactOccurred() {},
    },
  };
`;

const TELEGRAM_WEBAPP_INIT_PRIVATE_HELPER_BEHAVIOR_COVERAGE = [
  "setRootVar",
  "applyInsets",
  "applyViewport",
  "applyTheme",
  "resolveBackFallback",
  "detectHapticStyle",
  "readStoredThemePreference",
  "onThemeChanged",
  "onViewportChanged",
  "onKeyboardResize",
  "onPointerUp",
  "onBack",
] as const;

test.beforeEach(async ({ page }) => {
  await page.route("**/telegram-web-app.js", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: TELEGRAM_WEBAPP_STUB,
    });
  });
});

function dashboardPayload(emailLinked: boolean) {
  return {
    tg_id: 1001,
    sub_type: "TRIAL",
    current_plan_code: "trial",
    access_state: "trial_premium",
    is_active: true,
    expiry_at: "2030-01-01T00:00:00",
    used_gb: 1,
    total_gb: 100,
    remaining_gb: 99,
    active_sessions: 1,
    device_limit: 5,
    subscription_url: "",
    features: { haptic: true, lottie: true },
    linked_identities: {
      telegram: { id: 1001, username: "qa_user" },
      email: emailLinked ? { email: "reader@pokrov.test", verified: true, linked_tg_id: 1001 } : null,
    },
  };
}

function userPayload(emailLinked: boolean) {
  return {
    tg_id: 1001,
    username: "qa_user",
    subscription_url: "",
    is_active: true,
    is_admin: false,
    sub_type: "TRIAL",
    current_plan_code: "trial",
    access_state: "trial_premium",
    expiry_at: "2030-01-01T00:00:00",
    nodes: [],
    limits: { device_limit: 5, total_gb: 100 },
    traffic: { used_gb: 1, total_gb: 100, remaining_gb: 99 },
    support: { username: "pokrov_supportbot", link: "/support/", new_ticket_link: "/support/" },
    bonuses: {
      wheel: { last_spin_at: null, streak_months: 0 },
      referral_count: 0,
      channel_bonus: { premium_days: 5, offer_days: 5, claimed_days: 0, claimed_at: null, can_claim: false },
    },
    referral: { code: "QA", link: "", bonus_days: 7 },
    channel: { username: "pokrov_vpn", link: "https://t.me/pokrov_vpn" },
    actions: { open_helpbot: "", open_channel: "https://t.me/pokrov_vpn", pay_via_bot: "" },
    linked_identities: {
      telegram: { id: 1001, username: "qa_user" },
      email: emailLinked ? { email: "reader@pokrov.test", verified: true, linked_tg_id: 1001 } : null,
    },
  };
}

function bonusPayload() {
  return {
    tg_id: 1001,
    referral_count: 0,
    referral_code: "QA",
    referral_bonus_days: 7,
    streak_months: 0,
    last_wheel_spin: null,
    channel_bonus_premium_days: 5,
    channel_bonus_claimed_at: null,
    channel_username: "pokrov_vpn",
    channel: {
      offer_days: 5,
      claimed_days: 0,
      claimed: false,
      claimed_at: null,
      channel_username: "pokrov_vpn",
    },
  };
}

async function registerSettingsMocks(
  page: Page,
  options: { emailStatus?: Record<string, unknown> } = {},
) {
  const requests = {
    register: [] as unknown[],
    verify: [] as unknown[],
    authHeaders: [] as string[],
  };
  let emailLinked = false;
  const emailStatus = {
    ok: true,
    enabled: true,
    public_enabled: true,
    delivery_configured: true,
    delivery_secret_configured: true,
    debug_echo: false,
    mode: "public",
    blocked_reasons: [],
    ...options.emailStatus,
  };

  await page.addInitScript(() => {
    window.localStorage.setItem("portal_web_session_token", "e2e_mock_token");
  });

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path === "/api/auth/session") {
      return json(route, {
        ok: true,
        user: {
          id: 1001,
          username: "qa_user",
          email: emailLinked ? "reader@pokrov.test" : null,
          linked_identities: userPayload(emailLinked).linked_identities,
        },
      });
    }
    if (path === "/api/dashboard") return json(route, dashboardPayload(emailLinked));
    if (path === "/api/user/1001") return json(route, userPayload(emailLinked));
    if (path === "/api/bonuses") return json(route, bonusPayload());
    if (path === "/api/auth/email/status") {
      return json(route, emailStatus);
    }
    if (path === "/api/auth/email/register") {
      requests.register.push(request.postDataJSON());
      requests.authHeaders.push(request.headers().authorization || "");
      return json(route, {
        ok: true,
        verification_required: true,
        delivery: { status: "sent", kind: "verify", email: "reader@pokrov.test", mode: "relay" },
        identity: { email: "reader@pokrov.test", verified: false, linked_tg_id: 1001 },
      });
    }
    if (path === "/api/auth/email/verify") {
      requests.verify.push(request.postDataJSON());
      requests.authHeaders.push(request.headers().authorization || "");
      emailLinked = true;
      return json(route, {
        ok: true,
        token: "settings_email_session",
        expires_in: 604800,
        user: { id: 1001, username: "qa_user", email: "reader@pokrov.test" },
      });
    }
    if (path === "/api/channel/subscriber/check") {
      return json(route, { ok: true, subscriber: false, already_claimed: false, bonus_days: 5 });
    }

    return json(route, { detail: `Unhandled ${path}` }, 404);
  });

  return requests;
}

async function installTelegramWebAppInitHarness(page: Page) {
  await page.addInitScript(() => {
    window.localStorage.removeItem("pokrov-theme");
    window.localStorage.setItem("portal-theme", "light");

    type Handler = () => void;
    const events: Record<string, Handler[]> = {};
    const backHandlers: Handler[] = [];
    const calls: string[] = JSON.parse(window.sessionStorage.getItem("tg-init-calls") || "[]");
    const haptics: string[] = JSON.parse(window.sessionStorage.getItem("tg-init-haptics") || "[]");
    const headerColors: string[] = [];
    const backgroundColors: string[] = [];
    const visualViewportTarget = new EventTarget() as EventTarget & { height: number };

    function recordCall(value: string): void {
      calls.push(value);
      window.sessionStorage.setItem("tg-init-calls", JSON.stringify(calls));
    }

    function recordHaptic(value: string): void {
      haptics.push(value);
      window.sessionStorage.setItem("tg-init-haptics", JSON.stringify(haptics));
    }

    Object.defineProperty(window, "innerHeight", { value: 720, writable: true, configurable: true });
    Object.defineProperty(visualViewportTarget, "height", {
      value: 420,
      writable: true,
      configurable: true,
    });
    Object.defineProperty(window, "visualViewport", {
      value: visualViewportTarget,
      configurable: true,
    });

    const harness = {
      calls,
      haptics,
      headerColors,
      backgroundColors,
      trigger(eventType: string) {
        for (const handler of events[eventType] || []) handler();
      },
      setViewportHeight(value: number) {
        visualViewportTarget.height = value;
        visualViewportTarget.dispatchEvent(new Event("resize"));
      },
      clickBack() {
        for (const handler of [...backHandlers]) handler();
      },
    };

    const webApp = {
      initData: "query_id=mock",
      platform: "tdesktop",
      colorScheme: "dark" as const,
      themeParams: {
        bg_color: "#f2fff7",
        secondary_bg_color: "#e6fff6",
        text_color: "#11251a",
        button_color: "#0f7a4f",
      },
      viewportHeight: 620.4,
      viewportStableHeight: 612.6,
      safeAreaInset: { top: 9, bottom: 21, left: 3, right: 5 },
      contentSafeAreaInset: { top: 99, bottom: 99, left: 99, right: 99 },
      ready() {
        recordCall("ready");
      },
      expand() {
        recordCall("expand");
      },
      disableVerticalSwipes() {
        recordCall("disableVerticalSwipes");
      },
      enableClosingConfirmation() {
        recordCall("enableClosingConfirmation");
      },
      setHeaderColor(color: string) {
        headerColors.push(color);
      },
      setBackgroundColor(color: string) {
        backgroundColors.push(color);
      },
      onEvent(eventType: string, handler: Handler) {
        recordCall(`onEvent:${eventType}`);
        events[eventType] = [...(events[eventType] || []), handler];
      },
      offEvent(eventType: string, handler: Handler) {
        recordCall(`offEvent:${eventType}`);
        events[eventType] = (events[eventType] || []).filter((item) => item !== handler);
      },
      BackButton: {
        show() {
          recordCall("back.show");
        },
        hide() {
          recordCall("back.hide");
        },
        onClick(handler: Handler) {
          recordCall("back.onClick");
          backHandlers.push(handler);
        },
        offClick(handler: Handler) {
          recordCall("back.offClick");
          const index = backHandlers.indexOf(handler);
          if (index >= 0) backHandlers.splice(index, 1);
        },
      },
      HapticFeedback: {
        impactOccurred(style: "light" | "medium" | "heavy" | "rigid" | "soft") {
          recordHaptic(style);
        },
      },
    };

    const browserWindow = window as typeof window & {
      Telegram?: { WebApp?: unknown };
      __telegramWebAppInitHarness?: typeof harness;
    };
    browserWindow.__telegramWebAppInitHarness = harness;
    browserWindow.Telegram = { WebApp: webApp };
  });
}

test("settings links email to the current Telegram account", async ({ page }) => {
  const requests = await registerSettingsMocks(page);

  await page.goto("/settings/");

  await expect(page.getByRole("heading", { name: "Подключить email к текущему аккаунту" })).toBeVisible();
  await page.getByPlaceholder("name@example.com").fill("reader@pokrov.test");
  await page.getByPlaceholder("Как обращаться").fill("Reader");
  await page.getByPlaceholder("Минимум 10 символов").fill("StrongPass123!");
  await page.getByRole("button", { name: "Отправить письмо" }).click();

  await expect(page.locator("main")).toContainText("Письмо отправлено");
  await expect(page.locator("#email-link input[type='password']")).toHaveValue("");
  await page.getByPlaceholder("Код подтверждения").fill("verify-settings-token");
  await page.getByRole("button", { name: "Подтвердить email" }).click();

  await expect(page.locator("main")).toContainText("Email подтвержден");
  await expect(page.locator("main")).toContainText("reader@pokrov.test");
  await expect
    .poll(() => page.evaluate(() => window.localStorage.getItem("portal_web_session_token")))
    .toBe("settings_email_session");
  expect(requests.register).toEqual([
    { email: "reader@pokrov.test", password: "StrongPass123!", display_name: "Reader" },
  ]);
  expect(requests.verify).toEqual([{ token: "verify-settings-token" }]);
  expect(requests.authHeaders).toEqual(["Bearer e2e_mock_token", "Bearer e2e_mock_token"]);
});

test("settings shows the current five-day Telegram offer", async ({ page }) => {
  await registerSettingsMocks(page);

  await page.goto("/settings/");

  await expect(page.locator("main")).toContainText("Бонус +5 дней");
  await expect(page.getByRole("button", { name: "Забрать +5 дней", exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Забрать \+10 дней/i })).toHaveCount(0);
});

test("Telegram WebApp init applies viewport, theme, haptics, and settings back navigation", async ({ page }) => {
  expect(TELEGRAM_WEBAPP_INIT_PRIVATE_HELPER_BEHAVIOR_COVERAGE).toHaveLength(12);
  await installTelegramWebAppInitHarness(page);
  await registerSettingsMocks(page);

  await page.goto("/settings/");

  await expect(page.locator("main")).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(() => {
        const harness = (window as typeof window & { __telegramWebAppInitHarness?: { calls: string[] } })
          .__telegramWebAppInitHarness;
        return harness?.calls.includes("ready") || false;
      }),
    )
    .toBe(true);

  const initialState = await page.evaluate(() => {
    const style = getComputedStyle(document.documentElement);
    const harness = (window as typeof window & {
      __telegramWebAppInitHarness: {
        calls: string[];
        headerColors: string[];
        backgroundColors: string[];
      };
    }).__telegramWebAppInitHarness;
    return {
      htmlTelegramClass: document.documentElement.classList.contains("tg-webapp"),
      bodyTelegramClass: document.body.classList.contains("tg-webapp"),
      dark: document.documentElement.classList.contains("dark"),
      keyboardOpen: document.body.classList.contains("tg-keyboard-open"),
      viewportHeight: style.getPropertyValue("--tg-viewport-height").trim(),
      safeTop: style.getPropertyValue("--tg-safe-area-top").trim(),
      safeBottom: style.getPropertyValue("--tg-safe-area-bottom").trim(),
      safeLeft: style.getPropertyValue("--tg-safe-area-left").trim(),
      safeRight: style.getPropertyValue("--tg-safe-area-right").trim(),
      themeBg: style.getPropertyValue("--tg-theme-bg").trim(),
      themeText: style.getPropertyValue("--tg-theme-text").trim(),
      themeButton: style.getPropertyValue("--tg-theme-button").trim(),
      storedTheme: window.localStorage.getItem("pokrov-theme"),
      legacyTheme: window.localStorage.getItem("portal-theme"),
      calls: harness.calls,
      headerColors: harness.headerColors,
      backgroundColors: harness.backgroundColors,
    };
  });

  expect(initialState).toMatchObject({
    htmlTelegramClass: true,
    bodyTelegramClass: true,
    dark: false,
    keyboardOpen: true,
    viewportHeight: "613px",
    safeTop: "9px",
    safeBottom: "21px",
    safeLeft: "3px",
    safeRight: "5px",
    themeBg: "#f2fff7",
    themeText: "#11251a",
    themeButton: "#0f7a4f",
    storedTheme: "light",
    legacyTheme: "light",
  });
  expect(initialState.calls).toEqual(
    expect.arrayContaining([
      "ready",
      "expand",
      "disableVerticalSwipes",
      "enableClosingConfirmation",
      "onEvent:themeChanged",
      "onEvent:viewportChanged",
      "back.onClick",
      "back.show",
    ]),
  );
  expect(initialState.headerColors).toContain("#e6fff6");
  expect(initialState.backgroundColors).toContain("#f2fff7");

  const eventState = await page.evaluate(() => {
    const browserWindow = window as typeof window & {
      Telegram: {
        WebApp: {
          colorScheme: "light" | "dark";
          themeParams: Record<string, string>;
          safeAreaInset: Record<string, number>;
          viewportStableHeight: number;
        };
      };
      __telegramWebAppInitHarness: {
        trigger: (eventType: string) => void;
        setViewportHeight: (value: number) => void;
        haptics: string[];
        headerColors: string[];
        backgroundColors: string[];
      };
    };
    browserWindow.Telegram.WebApp.colorScheme = "light";
    browserWindow.Telegram.WebApp.themeParams = {
      bg_color: "#111111",
      secondary_bg_color: "#222222",
      text_color: "#eeeeee",
      button_color: "#00aa66",
    };
    browserWindow.Telegram.WebApp.safeAreaInset = { top: 11, bottom: 12, left: 13, right: 14 };
    browserWindow.Telegram.WebApp.viewportStableHeight = 501.2;
    browserWindow.__telegramWebAppInitHarness.trigger("themeChanged");
    browserWindow.__telegramWebAppInitHarness.trigger("viewportChanged");
    browserWindow.__telegramWebAppInitHarness.setViewportHeight(700);

    const button = document.createElement("button");
    button.setAttribute("data-haptic", "heavy");
    button.textContent = "haptic";
    document.body.appendChild(button);
    button.dispatchEvent(new PointerEvent("pointerup", { bubbles: true }));

    const style = getComputedStyle(document.documentElement);
    return {
      dark: document.documentElement.classList.contains("dark"),
      keyboardOpen: document.body.classList.contains("tg-keyboard-open"),
      viewportHeight: style.getPropertyValue("--tg-viewport-height").trim(),
      safeTop: style.getPropertyValue("--tg-safe-area-top").trim(),
      safeBottom: style.getPropertyValue("--tg-safe-area-bottom").trim(),
      safeLeft: style.getPropertyValue("--tg-safe-area-left").trim(),
      safeRight: style.getPropertyValue("--tg-safe-area-right").trim(),
      themeBg: style.getPropertyValue("--tg-theme-bg").trim(),
      themeText: style.getPropertyValue("--tg-theme-text").trim(),
      themeButton: style.getPropertyValue("--tg-theme-button").trim(),
      haptics: browserWindow.__telegramWebAppInitHarness.haptics,
      headerColors: browserWindow.__telegramWebAppInitHarness.headerColors,
      backgroundColors: browserWindow.__telegramWebAppInitHarness.backgroundColors,
    };
  });

  expect(eventState).toMatchObject({
    dark: false,
    keyboardOpen: false,
    viewportHeight: "501px",
    safeTop: "11px",
    safeBottom: "12px",
    safeLeft: "13px",
    safeRight: "14px",
    themeBg: "#111111",
    themeText: "#eeeeee",
    themeButton: "#00aa66",
  });
  expect(eventState.haptics).toContain("heavy");
  expect(eventState.headerColors.at(-1)).toBe("#222222");
  expect(eventState.backgroundColors.at(-1)).toBe("#111111");

  const backHaptics = await page.evaluate(() => {
    const harness = (window as typeof window & {
      __telegramWebAppInitHarness: { clickBack: () => void };
    }).__telegramWebAppInitHarness;
    harness.clickBack();
    return JSON.parse(window.sessionStorage.getItem("tg-init-haptics") || "[]") as string[];
  });
  expect(backHaptics).toContain("light");

  await expect(page).toHaveURL(/\/dashboard\/?$/);
  const backState = await page.evaluate(() => {
    return {
      calls: JSON.parse(window.sessionStorage.getItem("tg-init-calls") || "[]") as string[],
      haptics: JSON.parse(window.sessionStorage.getItem("tg-init-haptics") || "[]") as string[],
    };
  });
  expect(backState.calls).toEqual(expect.arrayContaining(["back.offClick", "back.hide"]));
});

test("settings keeps email linking unavailable when delivery proof is incomplete", async ({ page }) => {
  await registerSettingsMocks(page, {
    emailStatus: {
      delivery_secret_configured: false,
      blocked_reasons: ["delivery_webhook_secret_missing"],
    },
  });

  await page.goto("/settings/");

  await expect(page.getByRole("heading", { name: "Подключить email к текущему аккаунту" })).toHaveCount(0);
  await expect(page.locator("main")).toContainText("Email-вход временно недоступен");
  await expect(page.locator("#email-link")).toHaveCount(0);
  await expect(page.locator("main")).toContainText("недоступен");
});

test("root auth clears the password field after an email login attempt", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.removeItem("portal_web_session_token");
  });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/email/status") {
      return json(route, {
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
    if (path === "/api/auth/email/login") {
      return json(route, { detail: "Invalid credentials" }, 401);
    }
    return json(route, { detail: `Unhandled ${path}` }, 404);
  });

  await page.goto("/?clear_web_session=1");

  const passwordInput = page.locator("input[type='password'][autocomplete='current-password']");
  await page.getByPlaceholder("name@example.com").fill("reader@pokrov.test");
  await passwordInput.fill("StrongPass123!");
  await page.locator("form").filter({ has: passwordInput }).locator("button[type='submit']").click();

  await expect(passwordInput).toHaveValue("");
});

test("settings starts Telegram linking for an email-only account", async ({ page }) => {
  const linked_identities = {
    telegram: { id: 8000000000000, username: null },
    email: { email: "reader@pokrov.test", verified: true, linked_tg_id: null },
  };
  await page.addInitScript(() => {
    window.localStorage.setItem("portal_web_session_token", "email_only_token");
  });
  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;

    if (path === "/api/auth/session") {
      return json(route, {
        ok: true,
        user: { id: 1001, username: null, email: "reader@pokrov.test", linked_identities },
      });
    }
    if (path === "/api/dashboard") {
      return json(route, { ...dashboardPayload(true), linked_identities });
    }
    if (path === "/api/user/1001") {
      return json(route, { ...userPayload(true), username: null, linked_identities });
    }
    if (path === "/api/bonuses") {
      return json(route, bonusPayload());
    }
    if (path === "/api/auth/email/status") {
      return json(route, {
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
    if (path === "/api/client/telegram/link") {
      return json(route, {
        ok: true,
        linked: false,
        linked_telegram_id: null,
        linked_telegram_username: null,
        start_code: "tg_link_mock",
        bot_url: "https://t.me/pokrov_vpnbot?start=tg_link_mock",
        channel_url: "https://t.me/pokrov_vpn",
      });
    }
    if (path === "/api/channel/subscriber/check") {
      return json(route, { ok: true, subscriber: false, already_claimed: false, bonus_days: 5 });
    }

    return json(route, { detail: `Unhandled ${path}` }, 404);
  });

  await page.goto("/settings/");
  await page.getByRole("button", { name: "Подключить Telegram" }).click();

  await expect(page.locator("main")).toContainText("Откройте бота");
  await expect(page.locator("main a[href='https://t.me/pokrov_vpnbot?start=tg_link_mock']")).toBeVisible();
});

test("root auth keeps email hidden when delivery proof is incomplete", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.removeItem("portal_web_session_token");
  });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/email/status") {
      return json(route, {
        ok: true,
        enabled: true,
        public_enabled: true,
        delivery_configured: true,
        delivery_secret_configured: false,
        debug_echo: false,
        mode: "public",
        blocked_reasons: ["delivery_webhook_secret_missing"],
      });
    }
    return json(route, { detail: `Unhandled ${path}` }, 404);
  });

  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Кабинет POKROV" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Создать аккаунт" })).toHaveCount(0);
  await expect(page.getByPlaceholder("name@example.com")).toHaveCount(0);
  await expect(page.getByPlaceholder("Пароль")).toHaveCount(0);
  await expect(page.locator("main")).toContainText("Email-вход временно недоступен");
  await expect(page.getByRole("button", { name: "Войти через Telegram" })).toBeVisible();
});

test("root auth prefills email relay tokens and keeps verify recovery inputs separate", async ({ page }) => {
  await page.addInitScript(() => {
    window.localStorage.removeItem("portal_web_session_token");
  });
  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/email/status") {
      return json(route, {
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
    return json(route, { detail: `Unhandled ${path}` }, 404);
  });

  await page.goto("/?clear_web_session=1&email_token=verify-from-link");

  await expect(page.getByPlaceholder("Код подтверждения")).toHaveValue("verify-from-link");
  await expect(page.locator("main")).toContainText("Код подтверждения уже подставлен.");
  await expect(page).not.toHaveURL(/email_token=/);

  await page.getByRole("button", { name: "Вернуться ко входу" }).click();
  await page.getByRole("button", { name: "Забыли пароль?" }).click();

  await expect(page.getByPlaceholder("Заполните, когда письмо придет")).toHaveValue("");

  await page.goto("/?clear_web_session=1&email_reset_token=reset-from-link");

  await expect(page.getByPlaceholder("Заполните, когда письмо придет")).toHaveValue("reset-from-link");
  await expect(page.locator("main")).toContainText("Код восстановления уже подставлен.");
  await expect(page).not.toHaveURL(/email_reset_token=/);
});
