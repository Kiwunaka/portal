import { expect, test, type Page } from "@playwright/test";

type MockOptions = {
  isAdmin: boolean;
};

function mockUser(isAdmin: boolean) {
  return {
    tg_id: 1001,
    username: "qa_admin",
    subscription_url: "https://kiwunaka.space/s8Kx2mP7qR4wT/mock_token",
    is_active: true,
    is_admin: isAdmin,
    sub_type: "PAID",
    segment: "PAID",
    expiry_at: "2030-01-01T00:00:00",
    family_slots: 0,
    nodes: [],
    limits: { device_limit: 5, total_gb: 0, speed_mbps: 100 },
    traffic: { used_gb: 0, total_gb: 0, remaining_gb: 0 },
    support: {
      username: "portal_privacy_helpbot",
      link: "https://t.me/portal_privacy_helpbot",
      new_ticket_link: "https://t.me/portal_privacy_helpbot?start=ticket_new",
    },
    bonuses: {
      wheel: { last_spin_at: null, streak_months: 0 },
      referral_count: 0,
      channel_bonus: { premium_days: 0, claimed_at: null, can_claim: false },
    },
    referral: { code: "mock", link: "https://t.me/net4ebur_bot?start=ref_mock", bonus_days: 0 },
    channel: { username: "portal_privacy", link: "https://t.me/portal_privacy", subscriber: true, speed_bump_active: false },
    actions: {
      open_helpbot: "https://t.me/portal_privacy_helpbot",
      open_channel: "https://t.me/portal_privacy",
      pay_via_bot: "https://t.me/net4ebur_bot?start=pay",
    },
    points: { available: 0, expiring_soon: 0, monthly_cap: 300, expires_days: 90 },
    features: { haptic: true, lottie: true },
  };
}

function mockDashboard() {
  return {
    tg_id: 1001,
    sub_type: "PAID",
    current_plan_code: "1_month",
    segment: "PAID",
    is_active: true,
    expiry_at: "2030-01-01T00:00:00",
    used_gb: 0,
    total_gb: 0,
    remaining_gb: 0,
    active_sessions: 0,
    device_limit: 5,
    speed_limit_mbps: 100,
    free_next_reset_at: null,
    family_slots: 0,
    subscription_url: "https://kiwunaka.space/s8Kx2mP7qR4wT/mock_token",
    active_offer: null,
    points: { available: 0, expiring_soon: 0, monthly_cap: 300, expires_days: 90 },
    features: { haptic: true, lottie: true },
  };
}

async function registerApiMocks(page: Page, opts: MockOptions): Promise<void> {
  await page.addInitScript(() => {
    window.localStorage.setItem("portal_web_session_token", "e2e_mock_token");
  });

  const user = mockUser(opts.isAdmin);
  const dashboard = mockDashboard();

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

    if (path === "/api/dashboard") return json(dashboard);
    if (path.startsWith("/api/user/")) return json(user);

    if (path === "/api/admin/summary") {
      return json({
        users: { total: 1, active: 1 },
        tickets: { open: 0 },
        nodes: { healthy: 0, total: 0 },
        top_nodes: [],
      });
    }
    if (path === "/api/admin/metrics/status") return json({ status: "fresh", last_sample_at: "2030-01-01T00:00:00" });
    if (path === "/api/admin/metrics/timeseries") return json({ points: [] });
    if (path === "/api/admin/nodes/health") return json({ nodes: [] });
    if (path === "/api/admin/nodes/traffic") return json({ rows: [] });
    if (path === "/api/admin/users") return json({ users: [] });
    if (path.startsWith("/api/admin/users/")) return json({ user, tickets: [] });
    if (path === "/api/admin/tickets") return json({ tickets: [] });
    if (path.startsWith("/api/admin/tickets/")) return json({ ticket: { id: 1, user_tg_id: 1001, status: "open", status_title: "Открыт", messages: [] } });
    if (path === "/api/admin/promos") return json({ promos: [] });
    if (path === "/api/admin/gift-codes") return json({ gift_codes: [] });
    if (path === "/api/admin/plans") return json({ plans: [] });
    if (path === "/api/admin/live-updates") return json({ updates: [] });
    if (path === "/api/admin/start-links") return json({ start_links: [] });
    if (path === "/api/admin/wheel-config") {
      return json({ wheel_config: { preset: "balanced", cooldown_hours: 168, weights: [{ days: 1, weight: 100 }] } });
    }
    if (path === "/api/admin/campaign-links/build") {
      return json({ ok: true, bot_start_link: "https://t.me/net4ebur_bot?start=x", checkout_link: "https://portal-privacy.online/webapp/subscription/checkout/", webapp_link: "https://portal-privacy.online/webapp/" });
    }

    return json({ ok: true });
  });
}

test.describe("Admin gate", () => {
  test("redirects non-admin from /admin/* to /dashboard", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: false });
    await page.goto("admin/dashboard/");
    await expect(page).toHaveURL(/\/webapp\/dashboard\/?$/);
  });

  test("allows admin to open all admin sections", async ({ page }) => {
    await registerApiMocks(page, { isAdmin: true });

    const sections = [
      "admin/dashboard/",
      "admin/users/",
      "admin/nodes/",
      "admin/tickets/",
      "admin/promos/",
      "admin/broadcast/",
      "admin/referrals/",
      "admin/bonuses/",
    ];

    for (const section of sections) {
      await page.goto(section);
      await expect(page).toHaveURL(new RegExp(`/webapp/${section.replace(/\//g, "\\/")}$`));
      await expect(page.getByText("Панель управления")).toBeVisible();
    }
  });
});
