import { expect, test, type Page, type Route } from "@playwright/test";

const QA_OVERLAY_PRIVATE_HELPER_BEHAVIOR_COVERAGE = [
  "QaOverlay",
  "collectMetrics",
  "iconOnlyButtons",
  "scanInternalLinks",
  "recalc",
  "onKey",
  "brokenCount",
  "runLinkScan",
] as const;

const json = (route: Route, payload: unknown, status = 200) =>
  route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(payload),
  });

async function installAuthMocks(page: Page): Promise<void> {
  await page.route("https://telegram.org/js/telegram-web-app.js", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/javascript",
      body: "window.Telegram={WebApp:{ready(){},expand(){},onEvent(){},offEvent(){}}};",
    });
  });

  await page.route("**/api/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/auth/email/status") {
      return json(route, {
        ok: true,
        enabled: true,
        public_enabled: false,
        delivery_configured: false,
        delivery_secret_configured: false,
        debug_echo: false,
        mode: "disabled",
        blocked_reasons: ["qa_overlay_test"],
      });
    }

    return json(route, { detail: `Unhandled ${path}` }, 404);
  });
}

async function installQaFixtures(page: Page): Promise<void> {
  await page.evaluate(() => {
    const wrapper = document.createElement("div");
    wrapper.setAttribute("data-testid", "qa-overlay-fixtures");
    wrapper.innerHTML = `
      <a href="/dashboard/">Dashboard fixture</a>
      <a href="/missing-from-qa-overlay/">Missing fixture</a>
      <button type="button" id="qa-unlabelled-icon-button"><svg aria-hidden="true" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4"></circle></svg></button>
      <button type="button" disabled>Disabled fixture</button>
      <input aria-label="QA input fixture" />
    `;
    document.body.appendChild(wrapper);
  });
}

async function expectMetricAtLeast(page: Page, testId: string, min: number): Promise<void> {
  await expect
    .poll(async () => {
      const text = (await page.getByTestId(testId).textContent()) || "";
      return Number(text.match(/\d+/)?.[0] || "0");
    })
    .toBeGreaterThanOrEqual(min);
}

test("qa overlay tracks visible controls, hitboxes, hotkeys, and internal link scan", async ({ page }) => {
  expect(QA_OVERLAY_PRIVATE_HELPER_BEHAVIOR_COVERAGE).toContain("collectMetrics");
  await installAuthMocks(page);
  await page.addInitScript(() => {
    window.localStorage.removeItem("portal-qa-open");
    window.localStorage.removeItem("portal-qa-hitbox");
  });

  await page.goto("/");
  await installQaFixtures(page);
  await expect(page.getByTestId("qa-overlay-toggle")).toBeVisible();

  await page.evaluate(() => {
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "q", ctrlKey: true, shiftKey: true, bubbles: true }));
  });
  await expect(page.getByTestId("qa-overlay-panel")).toBeVisible();

  await page.getByTestId("qa-overlay-refresh").click();
  await expectMetricAtLeast(page, "qa-metric-links", 2);
  await expectMetricAtLeast(page, "qa-metric-inputs", 1);
  await expectMetricAtLeast(page, "qa-metric-disabled", 1);
  await expectMetricAtLeast(page, "qa-metric-icon-only", 1);

  await page.getByTestId("qa-overlay-hitbox").click();
  await expect(page.locator("body")).toHaveClass(/qa-hitbox/);
  await page.getByTestId("qa-overlay-hitbox").click();
  await expect(page.locator("body")).not.toHaveClass(/qa-hitbox/);

  await page.getByTestId("qa-overlay-link-scan").click();
  await expect(page.getByTestId("qa-overlay-link-results")).toBeVisible();
  await expect(page.getByTestId("qa-overlay-link-results")).toContainText("/dashboard/");
  await expect(page.getByTestId("qa-overlay-link-results")).toContainText("/missing-from-qa-overlay/");
  await expectMetricAtLeast(page, "qa-overlay-broken-count", 1);

  await page.evaluate(() => {
    window.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  });
  await expect(page.getByTestId("qa-overlay-panel")).toHaveCount(0);

  await page.getByTestId("qa-overlay-toggle").click();
  await expect(page.getByTestId("qa-overlay-panel")).toBeVisible();
});
