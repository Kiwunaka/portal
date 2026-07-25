import { expect, test, type Page } from "@playwright/test";

type RewardMockOptions = {
  sectors?: unknown;
  omitSectors?: boolean;
  wheelStatus?: number;
  calendarStatus?: number;
  calendarDay?: number;
  spinRewardDays?: number;
  subType?: "PAID" | "FREE" | "TRIAL" | "BONUS";
  isActive?: boolean;
  eligible?: boolean;
  wheelEnabled?: boolean;
  calendarEnabled?: boolean;
  checkedToday?: boolean;
  calendarMutationAlreadyChecked?: boolean;
};

type RewardMockCounts = {
  dashboard: number;
  user: number;
  wheelState: number;
  calendarState: number;
};

function rewardSessionUser(options: RewardMockOptions) {
  const subType = options.subType ?? "PAID";
  const isActive = options.isActive ?? true;
  return {
    tg_id: 1001,
    username: "reward_user",
    display_name: "Reward QA",
    email: null,
    subscription_url: "https://connect.pokrov.space/mock-reward-token",
    is_active: isActive,
    is_admin: false,
    sub_type: subType,
    current_plan_code: subType === "PAID" ? "1_month" : subType.toLowerCase(),
    access_state: isActive && subType === "PAID" ? "paid_unlimited" : subType.toLowerCase(),
    expiry_at: isActive ? "2030-01-01T00:00:00" : "2020-01-01T00:00:00",
    nodes: [],
    limits: { device_limit: 5, total_gb: 0 },
    traffic: { used_gb: 0, total_gb: 0, remaining_gb: 0 },
    support: {
      username: "pokrov_supportbot",
      link: "https://t.me/pokrov_supportbot",
      new_ticket_link: "https://t.me/pokrov_supportbot?start=ticket_new",
    },
    bonuses: {
      wheel: { last_spin_at: null, streak_months: 0 },
      referral_count: 0,
    },
    referral: { code: "", link: "", bonus_days: 10 },
    channel: { username: "pokrov_vpn", link: "https://t.me/pokrov_vpn" },
    actions: {
      open_helpbot: "https://t.me/pokrov_supportbot",
      open_channel: "https://t.me/pokrov_vpn",
      pay_via_bot: "https://t.me/pokrov_vpnbot?start=pay",
    },
    features: { haptic: true, lottie: true },
  };
}

function rewardDashboard(options: RewardMockOptions) {
  const subType = options.subType ?? "PAID";
  const isActive = options.isActive ?? true;
  return {
    tg_id: 1001,
    sub_type: subType,
    current_plan_code: subType === "PAID" ? "1_month" : subType.toLowerCase(),
    access_state: isActive && subType === "PAID" ? "paid_unlimited" : subType.toLowerCase(),
    is_active: isActive,
    expiry_at: isActive ? "2030-01-01T00:00:00" : "2020-01-01T00:00:00",
    used_gb: 0,
    total_gb: 0,
    remaining_gb: 0,
    active_sessions: 0,
    device_limit: 5,
    subscription_url: "https://connect.pokrov.space/mock-reward-token",
    features: { haptic: true, lottie: true },
  };
}

async function registerRewardMocks(
  page: Page,
  options: RewardMockOptions = {},
): Promise<RewardMockCounts> {
  await page.addInitScript(() => {
    window.localStorage.setItem("portal_web_session_token", "reward_e2e_token");
  });

  const counts: RewardMockCounts = {
    dashboard: 0,
    user: 0,
    wheelState: 0,
    calendarState: 0,
  };
  const user = rewardSessionUser(options);
  const dashboard = rewardDashboard(options);
  const eligible = options.eligible ?? ((options.subType ?? "PAID") === "PAID" && (options.isActive ?? true));
  const wheelEnabled = options.wheelEnabled ?? true;
  const calendarEnabled = options.calendarEnabled ?? true;
  const configuredSectors = Object.prototype.hasOwnProperty.call(options, "sectors")
    ? options.sectors
    : [1, 3, 7, 30];
  let wheelCommitted = false;
  let calendarCommitted = Boolean(options.checkedToday);
  let historyItems: Array<Record<string, unknown>> = [];

  const wheelState = () => {
    const state: Record<string, unknown> = {
      ok: true,
      enabled: wheelEnabled,
      eligible: wheelEnabled && eligible,
      reason: !wheelEnabled ? "bonus_feature_disabled" : eligible ? (wheelCommitted ? "wheel_cooldown_active" : "eligible") : "active_paid_required",
      state: !wheelEnabled ? "disabled_until_feature_flag" : eligible ? (wheelCommitted ? "cooldown" : "ready") : "ineligible",
      can_spin: wheelEnabled && eligible && !wheelCommitted,
      cooldown_hours: 168,
      last_spin_at: wheelCommitted ? "2030-01-01T00:00:00" : null,
      next_spin_at: wheelCommitted ? "2030-01-08T00:00:00" : null,
      last_reward_days: wheelCommitted ? (options.spinRewardDays ?? 1) : null,
      sync_state: wheelCommitted ? "sync_pending" : "not_required",
    };
    if (!options.omitSectors) state.sectors = wheelEnabled ? configuredSectors : [];
    return state;
  };

  const calendarState = () => ({
    ok: true,
    enabled: calendarEnabled,
    eligible: calendarEnabled && eligible,
    reason: !calendarEnabled ? "bonus_feature_disabled" : eligible ? "eligible" : "active_paid_required",
    state: !calendarEnabled ? "disabled_until_feature_flag" : eligible ? (calendarCommitted ? "checked_in_today" : "ready") : "ineligible",
    checked_in_today: calendarCommitted,
    can_checkin: calendarEnabled && eligible && !calendarCommitted,
    cycle_started_on: eligible ? "2030-01-01" : null,
    cycle_day: options.calendarDay ?? 6,
    calendar_cycle_day: options.calendarDay ?? 6,
    next_milestone: 7,
    achievements: { first_checkin: calendarCommitted, streak_7: false },
    sync_state: "not_required",
  });

  await page.route("**/api/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const json = (payload: unknown, status = 200) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(payload),
      });

    if (path === "/api/auth/session") {
      return json({ ok: true, user: { id: 1001, username: "reward_user" } });
    }
    if (path === "/api/dashboard") {
      counts.dashboard += 1;
      return json(dashboard);
    }
    if (path.startsWith("/api/user/")) {
      counts.user += 1;
      return json(user);
    }
    if (path === "/api/bonuses/wheel/state") {
      counts.wheelState += 1;
      if (options.wheelStatus && options.wheelStatus !== 200) {
        return json({ detail: { code: "reward_state_unavailable" } }, options.wheelStatus);
      }
      return json(wheelState());
    }
    if (path === "/api/bonuses/calendar") {
      counts.calendarState += 1;
      if (options.calendarStatus && options.calendarStatus !== 200) {
        return json({ detail: { code: "reward_state_unavailable" } }, options.calendarStatus);
      }
      return json(calendarState());
    }
    if (path === "/api/bonuses/history") {
      return json({ ok: true, tg_id: 1001, items: historyItems, limit: 20, next_cursor: null });
    }
    if (path === "/api/bonuses/summary") {
      return json({
        ok: true,
        achievements: {
          items: [],
          quests: [
            {
              id: "second_device",
              title: "Добавить второе устройство",
              description: "Свяжите ещё одно устройство.",
              progress: 1,
              target: 2,
              completed: false,
              action_href: "/devices/",
              verification: "active_account_devices",
            },
          ],
        },
      });
    }
    if (path === "/api/bonuses/referral/summary") {
      return json({
        ok: true,
        code: "rewardqa",
        link: "https://t.me/pokrov_vpnbot?start=ref_rewardqa",
        bonus_days: 10,
        conversion: { invited: 3, activated: 2, paid: 1, rewarded: 1, activation_pct: 66.7, paid_pct: 33.3 },
        history: [
          { id: "ref-1", status: "rewarded", created_at: "2030-01-01T00:00:00", activated_at: "2030-01-02T00:00:00", paid_at: "2030-01-03T00:00:00", hold_until: null, rewarded_at: "2030-01-04T00:00:00" },
        ],
        privacy: "Имена и аккаунты приглашённых не показываются.",
      });
    }
    if (path === "/api/bonuses/wheel/spin" && request.method() === "POST") {
      const rewardDays = options.spinRewardDays ?? 1;
      wheelCommitted = true;
      historyItems = [
        {
          kind: "wheel_spin",
          title: "Рулетка: бонус получен",
          days: rewardDays,
          occurred_at: "2030-01-01T00:00:00",
        },
        ...historyItems,
      ];
      return json({
        ok: true,
        feature: "wheel",
        reward_days: rewardDays,
        grant_id: "00000000-0000-4000-8000-000000000777",
        sync_state: "sync_pending",
        state: wheelState(),
      });
    }
    if (path === "/api/bonuses/calendar/checkin" && request.method() === "POST") {
      const alreadyChecked = Boolean(options.calendarMutationAlreadyChecked);
      calendarCommitted = true;
      const rewardDays = alreadyChecked ? 0 : (options.calendarDay ?? 6) === 6 ? 1 : 0;
      historyItems = [
        {
          kind: "calendar_checkin",
          title: "Активность отмечена",
          days: rewardDays,
          occurred_at: "2030-01-01T00:00:00",
        },
        ...historyItems,
      ];
      return json({
        ok: true,
        feature: "calendar",
        reward_days: rewardDays,
        grant_id: rewardDays ? "00000000-0000-4000-8000-000000000778" : null,
        sync_state: rewardDays ? "sync_pending" : "not_required",
        already_checked_in: alreadyChecked,
        calendar_cycle_started_on: "2030-01-01",
        calendar_cycle_day: options.calendarDay ?? 6,
        state: calendarState(),
      });
    }
    return json({ detail: "not mocked" }, 404);
  });

  return counts;
}

test.describe("rewards fail-closed cabinet surface", () => {
  test("shows anonymized referral conversion and history", async ({ page }) => {
    await registerRewardMocks(page);
    await page.goto("/rewards/");

    await expect(page.getByTestId("referral-center")).toContainText("Приглашены");
    await expect(page.getByTestId("referral-center")).toContainText("Оплатили 33.3%");
    await expect(page.getByTestId("referral-center")).toContainText("Начислено");
    await expect(page.getByTestId("referral-center")).not.toContainText("username");
    await expect(page.getByTestId("reward-quest-second_device")).toContainText("Добавить второе устройство");
    const questProgress = page.getByRole("progressbar", {
      name: "Прогресс задачи «Добавить второе устройство»",
    });
    await expect(questProgress).toHaveAttribute("aria-valuemin", "0");
    await expect(questProgress).toHaveAttribute("aria-valuemax", "2");
    await expect(questProgress).toHaveAttribute("aria-valuenow", "1");
    await expect(questProgress).toHaveAttribute("aria-valuetext", "1 из 2");
  });

  test("keeps calendar usable when wheel state fails", async ({ page }) => {
    await registerRewardMocks(page, { wheelStatus: 503, calendarDay: 6 });
    await page.goto("/rewards/");

    await expect(page.getByText("Колесо временно недоступно")).toBeVisible();
    await expect(page.getByRole("button", { name: "Отметить день" })).toBeEnabled();
  });

  test("keeps wheel usable when calendar state fails", async ({ page }) => {
    await registerRewardMocks(page, { calendarStatus: 503 });
    await page.goto("/rewards/");

    await expect(page.getByText("Календарь временно недоступен")).toBeVisible();
    await expect(page.getByRole("button", { name: "Крутить колесо" })).toBeEnabled();
  });

  test("does not invent sectors or animate an unknown committed reward", async ({ page }) => {
    await registerRewardMocks(page, { sectors: [1, 3, 7], spinRewardDays: 30 });
    await page.goto("/rewards/");
    await page.getByRole("button", { name: "Крутить колесо" }).click();

    await expect(page.getByText("Начислено +30 дней")).toBeVisible();
    await expect(page.getByText("Не удалось синхронизировать сектора")).toBeVisible();
    await expect(page.locator('[data-spinning="true"]')).toHaveCount(0);
  });

  test("renders one sector as a guaranteed reward card", async ({ page }) => {
    await registerRewardMocks(page, { sectors: [1] });
    await page.goto("/rewards/");

    await expect(page.getByText("Награда в этом секторе: +1 день")).toBeVisible();
    await expect(page.locator("svg[data-wheel]")).toHaveCount(0);
  });

  for (const scenario of [
    { name: "missing sectors", options: { omitSectors: true } },
    { name: "duplicate sectors", options: { sectors: [1, 1, 7] } },
    { name: "non-positive sectors", options: { sectors: [0, 3, 7] } },
    { name: "too many sectors", options: { sectors: Array.from({ length: 13 }, (_, index) => index + 1) } },
    { name: "excessive reward", options: { sectors: [1, 366] } },
  ]) {
    test(`fails closed for ${scenario.name}`, async ({ page }) => {
      await registerRewardMocks(page, scenario.options);
      await page.goto("/rewards/");

      await expect(page.getByText("Не удалось синхронизировать сектора")).toBeVisible();
      await expect(page.getByRole("button", { name: "Крутить колесо" })).toBeDisabled();
    });
  }

  for (const subType of ["FREE", "TRIAL", "BONUS"] as const) {
    test(`keeps ${subType} rewards ineligible`, async ({ page }) => {
      await registerRewardMocks(page, { subType, eligible: false });
      await page.goto("/rewards/");

      await expect(page.getByText("Нужна активная платная подписка").first()).toBeVisible();
      await expect(page.getByRole("button", { name: "Крутить колесо" })).toBeDisabled();
      await expect(page.getByRole("button", { name: "Отметить день" })).toBeDisabled();
    });
  }

  test("keeps expired rewards ineligible", async ({ page }) => {
    await registerRewardMocks(page, { isActive: false, eligible: false });
    await page.goto("/rewards/");

    await expect(page.getByText("Нужна активная платная подписка").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "Крутить колесо" })).toBeDisabled();
  });

  test("renders disabled features without mutation controls", async ({ page }) => {
    await registerRewardMocks(page, { wheelEnabled: false, calendarEnabled: false });
    await page.goto("/rewards/");

    await expect(page.getByText("Колесо пока выключено")).toBeVisible();
    await expect(page.getByText("Календарь пока выключен")).toBeVisible();
    await expect(page.getByRole("button", { name: "Крутить колесо" })).toBeDisabled();
    await expect(page.getByRole("button", { name: "Отметить день" })).toBeDisabled();
  });

  test("accepts the server same-day calendar response", async ({ page }) => {
    await registerRewardMocks(page, { calendarMutationAlreadyChecked: true });
    await page.goto("/rewards/");
    await page.getByRole("button", { name: "Отметить день" }).click();

    await expect(page.getByText("Сегодня уже отмечено")).toBeVisible();
    await expect(page.getByRole("button", { name: "Отметить день" })).toBeDisabled();
  });

  test("refetches wheel state and entitlement after committed reward", async ({ page }) => {
    const counts = await registerRewardMocks(page, { spinRewardDays: 1 });
    await page.goto("/rewards/");
    await expect(page.getByRole("button", { name: "Крутить колесо" })).toBeEnabled();
    const dashboardBefore = counts.dashboard;
    const wheelBefore = counts.wheelState;

    await page.getByRole("button", { name: "Крутить колесо" }).click();
    await expect(page.getByText("Начислено +1 день")).toBeVisible();
    await expect.poll(() => counts.dashboard).toBeGreaterThan(dashboardBefore);
    await expect.poll(() => counts.wheelState).toBeGreaterThan(wheelBefore);
  });

  test("refetches calendar state and entitlement after check-in", async ({ page }) => {
    const counts = await registerRewardMocks(page, { calendarDay: 6 });
    await page.goto("/rewards/");
    const dashboardBefore = counts.dashboard;
    const calendarBefore = counts.calendarState;

    await page.getByRole("button", { name: "Отметить день" }).click();
    await expect(page.getByText("Начислено +1 день")).toBeVisible();
    await expect.poll(() => counts.dashboard).toBeGreaterThan(dashboardBefore);
    await expect.poll(() => counts.calendarState).toBeGreaterThan(calendarBefore);
  });
});
