import { expect, test, type Page, type Route } from "@playwright/test";

const json = (route: Route, payload: unknown, status = 200) =>
  route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(payload),
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
      channel_bonus: { premium_days: 10, claimed_at: null, can_claim: false },
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

async function registerSettingsMocks(page: Page) {
  const requests = {
    register: [] as unknown[],
    verify: [] as unknown[],
    authHeaders: [] as string[],
  };
  let emailLinked = false;

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
      return json(route, { ok: true, subscriber: false, already_claimed: false, bonus_days: 10 });
    }

    return json(route, { detail: `Unhandled ${path}` }, 404);
  });

  return requests;
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
      return json(route, { ok: true, subscriber: false, already_claimed: false, bonus_days: 10 });
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
  await expect(page.getByPlaceholder("name@example.com")).toBeVisible();
  await expect(page.getByPlaceholder("Пароль")).toBeVisible();
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
