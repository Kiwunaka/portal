import { expect, test, type Browser, type Page } from "@playwright/test";

import { installAdminApiMock, type RuScenario } from "./fixtures/admin-api";

async function openScenario(browser: Browser, scenario: RuScenario, path = "/nodes?selected=nl&tab=ru") {
  const context = await browser.newContext();
  const page = await context.newPage();
  await installAdminApiMock(page, { ruScenario: scenario });
  await page.goto(path);
  return { context, page };
}

async function openRuTab(page: Page) {
  await page.getByRole("tab", { name: "Проверки из РФ" }).click();
  await expect(page).toHaveURL(/tab=ru/);
}

test("карточка ноды открывается за два действия, разделяет источники и лениво загружает RU-историю", async ({ page }) => {
  const api = await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  await page.goto("/nodes");

  const row = page.getByRole("row", { name: /NL/ });
  await expect(row).toBeVisible();
  expect(api.calls.some((call) => call.path.includes("/observability"))).toBe(false);
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/probes/ru-origin/runs"))).toBe(false);

  await row.click();
  await expect(page).toHaveURL(/selected=nl/);
  await expect(page.getByRole("heading", { name: "Нода NL" })).toBeVisible();
  await expect(page.getByText("Текущий контур", { exact: true })).toBeVisible();
  await expect(page.getByText("Brain-origin", { exact: true })).toBeVisible();
  await expect(page.getByText("RU-origin", { exact: true })).toBeVisible();
  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/nodes/nl/observability")).toBe(true);
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/probes/ru-origin/runs"))).toBe(false);

  await openRuTab(page);
  await expect.poll(() => api.calls.some((call) => call.path.startsWith("/api/admin/probes/ru-origin/runs?"))).toBe(true);
  await page.getByRole("button", { name: "7 дней" }).click();
  await expect(page).toHaveURL(/range=7d/);
});

test("фильтры живут в URL, а отсутствующие числа не становятся нулём", async ({ page }) => {
  await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  await page.goto("/nodes");

  const missingRow = page.getByRole("row", { name: /DE/ });
  await expect(missingRow).toContainText("—");
  await page.getByRole("searchbox", { name: "Поиск по нодам" }).fill("nl");
  await page.getByLabel("Состояние ноды").selectOption("enabled");
  await page.getByLabel("Свежесть данных").selectOption("fresh");
  await page.getByLabel("Страна").selectOption("NL");
  await page.getByLabel("Хостер").selectOption("timeweb");
  await page.getByLabel("Транспорт").selectOption("legacy_reality_fallback");
  await page.getByLabel("Активный алерт").selectOption("with");

  await expect(page).toHaveURL(/q=nl/);
  await expect(page).toHaveURL(/state=enabled/);
  await expect(page).toHaveURL(/freshness=fresh/);
  await expect(page).toHaveURL(/country=NL/);
  await expect(page).toHaveURL(/hoster=timeweb/);
  await expect(page).toHaveURL(/transport=legacy_reality_fallback/);
  await expect(page).toHaveURL(/alert=with/);
  await expect(page.getByRole("row", { name: /NL/ })).toBeVisible();
  await expect(page.getByRole("row", { name: /DE/ })).toHaveCount(0);
});

test("RU-origin честно показывает недоступную среду, устаревание, отсутствие и прошлый manifest", async ({ browser }) => {
  const cases: Array<{ scenario: RuScenario; expected: RegExp | string }> = [
    { scenario: "google-down", expected: "Google не подтвердил рабочую среду" },
    { scenario: "stale", expected: "Последний пригодный результат старше 7 часов" },
    { scenario: "missing", expected: "Пригодный запуск ещё не получен" },
    { scenario: "superseded-manifest", expected: "Последняя попытка выполнена по прежней конфигурации" }
  ];

  for (const item of cases) {
    const { context, page } = await openScenario(browser, item.scenario);
    await expect(page.getByText(item.expected, { exact: true })).toBeVisible();
    if (item.scenario === "google-down") {
      await expect(page.getByText("Среда проверки из РФ недоступна", { exact: true })).toBeVisible();
    }
    if (item.scenario === "stale") {
      await expect(page.getByText("Устарело", { exact: true }).first()).toBeVisible();
    }
    await context.close();
  }
});

test("неполная новая попытка показана отдельно от последнего пригодного результата", async ({ browser }) => {
  const { context, page } = await openScenario(browser, "incomplete-latest-with-last-good");

  await expect(page.getByText("Последняя попытка не завершила обязательные проверки", { exact: true })).toBeVisible();
  await expect(page.getByText("Последняя полученная попытка", { exact: true })).toBeVisible();
  await expect(page.getByText("Последний пригодный результат", { exact: true })).toBeVisible();
  await expect(page.getByText("00000000-0000-4000-8000-000000000403", { exact: true })).not.toBeVisible();

  await context.close();
});

test("стадии сохраняют пройдено, сбой, не выполнялась и не требуется", async ({ page }) => {
  await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  await page.goto("/nodes?selected=nl&tab=ru");

  const history = page.getByRole("region", { name: "История проверок из РФ" });
  await expect(history).toBeVisible();
  await history.locator("summary").first().click();
  await expect(history.getByText("Пройдено", { exact: true }).first()).toBeVisible();
  await expect(history.getByText("Сбой", { exact: true }).first()).toBeVisible();
  await expect(history.getByText("Не выполнялась", { exact: true }).first()).toBeVisible();
  await expect(history.getByText("Не требуется", { exact: true }).first()).toBeVisible();
});

test("загрузчик различает свежую очередь и потерю heartbeat без догадок о причине", async ({ browser }) => {
  const backlog = await openScenario(browser, "uploader-backlog");
  await expect(backlog.page.getByText("Очередь отправки: 4", { exact: true })).toBeVisible();
  await expect(backlog.page.getByText("Заблокировано: 1", { exact: true })).toBeVisible();
  await expect(backlog.page.getByText("Карантин: 2", { exact: true })).toBeVisible();
  await backlog.context.close();

  const stale = await openScenario(browser, "uploader-heartbeat-stale");
  await expect(stale.page.getByText("Нет свежей связи с загрузчиком", { exact: true })).toBeVisible();
  await expect(stale.page.getByText(/Ошибка авторизации|Сбой сети|Проблема диска/)).toHaveCount(0);
  await stale.context.close();
});

test("на мобильном детали открываются последовательным экраном и возвращают к списку", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  await page.goto("/nodes");

  const table = page.getByRole("table", { name: "Список нод" });
  await expect(table).toBeVisible();
  await page.getByRole("row", { name: /NL/ }).click();
  await expect(page.getByRole("button", { name: "Назад к нодам" })).toBeVisible();
  await expect(table).not.toBeVisible();

  await page.getByRole("button", { name: "Назад к нодам" }).click();
  await expect(page).not.toHaveURL(/selected=/);
  await expect(table).toBeVisible();
});
