import { expect, test, type Page } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

async function openControl(page: Page, path: "/release" | "/broadcast") {
  await page.goto(path);
}

test("release checklist binds exact candidate and keeps origins honest", async ({ page }) => {
  await installAdminApiMock(page);
  await openControl(page, "/release");

  const firstCandidate = "a".repeat(64);
  const secondCandidate = "b".repeat(64);
  await expect(page).toHaveURL(new RegExp(`candidate=${firstCandidate}`));
  await expect(page.getByText(firstCandidate, { exact: true }).first()).toBeVisible();
  await expect(page.getByText("2".repeat(64), { exact: true }).first()).toBeVisible();
  await expect(page.getByText("current-origin", { exact: true })).toBeVisible();
  await expect(page.getByText("brain-origin", { exact: true })).toBeVisible();
  await expect(page.getByText("RU-origin", { exact: true })).toBeVisible();

  const attested = page.getByText(/OPERATOR_ATTESTED/, { exact: false }).first();
  const blocked = page.getByText(/BLOCKED_BY_ACCESS/, { exact: false }).first();
  const missing = page.getByText(/MISSING/, { exact: false }).first();
  await expect(attested).toHaveClass(/status-warning/);
  await expect(blocked).toHaveClass(/status-danger/);
  await expect(missing).toHaveClass(/status-warning/);

  await page.getByRole("button", { name: "Открыть релиз portal_bot 2026.07.17.2" }).click();
  await expect(page).toHaveURL(new RegExp(`candidate=${secondCandidate}`));
  await expect(page.getByText(secondCandidate, { exact: true }).first()).toBeVisible();
  await expect(page.getByText("4".repeat(64), { exact: true }).first()).toBeVisible();
  await expect(page.getByText(/Проверки cockpit: Подтверждено · PASS/)).toBeVisible();
  await expect(page.getByText(/Политика cockpit: pokrov.operator-cockpit-gates\/v2/)).toBeVisible();
  await expect(page.getByRole("note").filter({ hasText: "Gate F: решение о выпуске не загружено" })).toBeVisible();
  await page.getByText("Соответствие 11 проверок cockpit и 19 условий Gate F", { exact: true }).click();
  const mapping = page.getByRole("table", { name: "Соответствие cockpit и Gate F" });
  await expect(mapping.locator("tbody tr")).toHaveCount(19);
  await expect(mapping.getByRole("row").filter({ hasText: "android_physical_device" })).toContainText("android_proof");
  await expect(mapping.getByRole("row").filter({ hasText: "android_ldplayer_rehearsal" })).toContainText("android_proof");
  await expect(mapping.getByText("Отдельная проверка; входа cockpit нет", { exact: true })).toHaveCount(4);
  await expect(page.getByText(/Фактическое переключение артефакта: NOT_EVALUATED/)).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("broadcast draft survives a 401 prepare error", async ({ page }) => {
  const api = await installAdminApiMock(page, { actionIntentPrepareStatus: 401 });
  await openControl(page, "/broadcast");

  await expect(page.getByText(/Ссылка уйдёт без большой карточки предпросмотра/)).toBeVisible();
  await expect(page.getByText(/не ставьте эмодзи вместо логотипа/)).toBeVisible();

  const draft = "Черновик после 401";
  await page.getByLabel("Текст рассылки").fill(draft);
  await page.getByRole("button", { name: "Подготовить защищённый предпросмотр" }).click();
  await expect(page.getByText("Предпросмотр недоступен", { exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => window.sessionStorage.getItem("pokrov_admin_broadcast_draft_v1"))).toContain(draft);
  await expect(page).toHaveURL(/\/broadcast$/);
  expect(api.calls.filter((call) => call.path === "/api/admin/broadcast")).toHaveLength(0);

  await page.reload();
  await expect(page.getByLabel("Текст рассылки")).toHaveValue(draft);
});

test("broadcast preview freezes count and hash before exact confirmation", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await openControl(page, "/broadcast");

  await page.getByLabel("Текст рассылки").fill("Плановые работы");
  await page.getByRole("button", { name: "Подготовить защищённый предпросмотр" }).click();
  await expect(page.getByText("Зафиксировано получателей", { exact: true })).toBeVisible();
  await expect(page.getByText("12", { exact: true })).toBeVisible();
  await expect(page.getByText("9".repeat(64), { exact: true })).toBeVisible();
  await expect(page.getByText("8".repeat(64), { exact: true })).toBeVisible();

  const execute = page.getByRole("button", { name: "Выполнить" });
  await expect(execute).toBeDisabled();
  await page.getByLabel("Подтверждение").fill("ОТПРАВИТЬ");
  await expect(execute).toBeEnabled();
  await execute.click();
  await expect(page.getByText("Действие выполнено", { exact: true })).toBeVisible();
  await expect.poll(() => api.calls.filter((call) => /\/api\/admin\/v2\/growth\/action-intents\/[0-9a-f-]{36}\/execute/.test(call.path) && call.method === "POST").length).toBe(1);
  const send = api.calls.find((call) => /\/api\/admin\/v2\/growth\/action-intents\/[0-9a-f-]{36}\/execute/.test(call.path) && call.method === "POST");
  expect(send?.headers?.["x-admin-intent-id"]).toBeTruthy();
  expect(send?.headers?.["x-admin-idempotency-key"]).toBeTruthy();
  expect(send?.headers?.["x-admin-confirmation-sha256"]).toHaveLength(64);
  await expect.poll(() => page.evaluate(() => window.sessionStorage.getItem("pokrov_admin_broadcast_draft_v1"))).toBeNull();
});

test("uncertain broadcast offers status check and never retry-send", async ({ page }) => {
  const api = await installAdminApiMock(page, { broadcastOutcome: "uncertain", broadcastStatusOutcome: "prepared" });
  await openControl(page, "/broadcast");

  const draft = "Сообщение с неопределённым исходом";
  await page.getByLabel("Текст рассылки").fill(draft);
  await page.getByRole("button", { name: "Подготовить защищённый предпросмотр" }).click();
  await page.getByLabel("Подтверждение").fill("ОТПРАВИТЬ");
  await page.getByRole("button", { name: "Выполнить" }).click();

  await expect(page.getByText("Итог действия неясен", { exact: true })).toBeVisible();
  const statusCheck = page.getByRole("button", { name: "Проверить текущее состояние" });
  await expect(statusCheck).toBeVisible();
  await expect(page.getByRole("button", { name: /повтор/i })).toHaveCount(0);
  await statusCheck.click();
  await expect.poll(() => api.calls.filter((call) => call.method === "GET" && /\/api\/admin\/v2\/growth\/action-intents\//.test(call.path)).length).toBe(1);
  await expect(page.getByRole("button", { name: "Подготовить защищённый предпросмотр" })).toBeDisabled();
  expect(api.calls.filter((call) => call.method === "POST" && /\/api\/admin\/v2\/growth\/action-intents\/[0-9a-f-]{36}\/execute/.test(call.path))).toHaveLength(1);
  await expect.poll(() => page.evaluate(() => window.sessionStorage.getItem("pokrov_admin_broadcast_draft_v1"))).toContain(draft);
});

test("execute timeout keeps the result uncertain and offers readback without resending", async ({ page }) => {
  await page.clock.install();
  const api = await installAdminApiMock(page, { broadcastStatusOutcome: "prepared" });
  let releaseResponse!: () => void;
  const response = new Promise<void>((resolve) => { releaseResponse = resolve; });
  let executes = 0;
  await page.route("**/api/admin/v2/growth/action-intents/*/execute", async (route) => {
    executes += 1;
    await response;
    await route.fallback();
  });
  try {
    await openControl(page, "/broadcast");
    await page.getByLabel("Текст рассылки").fill("Черновик при потере ответа");
    await page.getByRole("button", { name: "Подготовить защищённый предпросмотр" }).click();
    await page.getByLabel("Подтверждение").fill("ОТПРАВИТЬ");
    await page.getByRole("button", { name: "Выполнить", exact: true }).click();
    await expect.poll(() => executes).toBe(1);
    await page.clock.runFor(46_000);
    await expect(page.getByText("Итог действия неясен", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: /повтор/i })).toHaveCount(0);
    await page.getByRole("button", { name: "Проверить текущее состояние" }).click();
    await expect.poll(() => api.calls.filter((call) => call.method === "GET" && /\/growth\/action-intents\//.test(call.path)).length).toBe(1);
    expect(executes).toBe(1);
  } finally {
    releaseResponse();
  }
});
