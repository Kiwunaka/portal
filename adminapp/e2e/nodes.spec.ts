import { expect, test, type Browser, type Page } from "@playwright/test";

import { installAdminApiMock, type RuScenario } from "./fixtures/admin-api";

async function openScenario(browser: Browser, scenario: RuScenario, path = "/nodes?selected=nl&tab=ru") {
  const context = await browser.newContext();
  const page = await context.newPage();
  const api = await installAdminApiMock(page, { ruScenario: scenario });
  await page.goto(path);
  return { context, page, api };
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
  const overview = page.getByRole("tabpanel", { name: "Обзор" });
  await expect(overview.getByText("Текущий контур", { exact: true })).toBeVisible();
  await expect(overview.getByText("Brain-origin", { exact: true })).toBeVisible();
  await expect(overview.getByText("RU-origin", { exact: true })).toBeVisible();
  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/nodes/nl/observability?include_ru_history=false")).toBe(true);
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

test("review-контракт: live wire, независимые RU-блоки, полные данные и доступная навигация", async ({ browser }) => {
  const review = await openScenario(browser, "review-findings", "/nodes");
  const reviewApi = review.api;

  const table = review.page.getByRole("table", { name: "Список нод" });
  await expect(table).toBeVisible();
  const brainRow = table.getByRole("row").filter({ has: review.page.getByRole("button", { name: "Открыть ноду BRAIN" }) });
  const deRow = table.getByRole("row").filter({ has: review.page.getByRole("button", { name: "Открыть ноду DE" }) });
  const nlRow = table.getByRole("row").filter({ has: review.page.getByRole("button", { name: "Открыть ноду NL" }) });
  await expect(brainRow).toContainText("DE");
  await expect(deRow).toContainText("—");
  await expect(nlRow).toContainText("RU-проверка завершилась сбоем");
  await expect(review.page.getByRole("button", { name: "Открыть ноду NL" })).toBeVisible();

  const headerHelp = review.page.getByRole("button", { name: "Показать пояснение" }).first();
  await headerHelp.focus();
  await expect(review.page.getByRole("tooltip").first()).toBeVisible();

  await review.page.getByRole("button", { name: "Открыть ноду NL" }).click();
  await expect(review.page.getByText("Запрет новых размещений", { exact: true })).toBeVisible();
  await expect(review.page.getByText("Последний пакет Observer", { exact: true }).first()).toBeVisible();
  await expect(review.page.getByText("Не сопоставлено: 1", { exact: true })).toBeVisible();
  await expect(review.page.getByText("Ошибки разбора: 0", { exact: true })).toBeVisible();

  const overviewTab = review.page.getByRole("tab", { name: "Обзор" });
  await expect(overviewTab).toHaveAttribute("aria-controls", /node-panel-overview/);
  await overviewTab.press("ArrowRight");
  await expect(review.page).toHaveURL(/tab=ru/);
  await expect(review.page.getByRole("tabpanel")).toHaveAttribute("aria-labelledby", /node-tab-ru/);
  await review.page.getByRole("button", { name: "Показать ещё" }).click();
  await expect.poll(() => reviewApi.calls.some((call) => call.path.includes("cursor=cursor-safe-next"))).toBe(true);

  await review.page.getByRole("tab", { name: "Нагрузка" }).click();
  await expect(review.page.getByText("Задержка панели", { exact: true }).first()).toBeVisible();
  await expect(review.page.getByText("Ошибки панели", { exact: true }).first()).toBeVisible();
  await expect(review.page.getByText("Приём · 1 мин", { exact: true }).first()).toBeVisible();
  await expect(review.page.getByText("Передача · 5 мин", { exact: true }).first()).toBeVisible();

  await review.page.getByRole("tab", { name: "Алерты" }).click();
  await expect(review.page.getByText("Высокая задержка панели", { exact: true })).toBeVisible();
  await expect(review.page.getByText("Источник: метрики ноды", { exact: true })).toBeVisible();
  await expect(review.page.getByText("Node nl metric alert: panel_latency", { exact: true })).toHaveCount(0);
  await review.context.close();

  const missing = await openScenario(browser, "selected-missing");
  await expect(missing.page.getByText("В последнем RU-снимке нет результата выбранной ноды", { exact: true })).toBeVisible();
  await expect(missing.page.getByText("RU: Норма", { exact: true })).toHaveCount(0);
  await missing.context.close();

  const partialContext = await browser.newContext();
  const partialPage = await partialContext.newPage();
  const partialApi = await installAdminApiMock(partialPage, { ruScenario: "fresh-pass", ruHistoryStatus: 503, ruUploaderStatus: 503 });
  await partialPage.goto("/nodes?selected=nl&tab=ru");
  await expect(partialPage.getByText("Последняя полученная попытка", { exact: true })).toBeVisible();
  await expect(partialPage.getByText("История RU-origin недоступна", { exact: true })).toBeVisible();
  await expect(partialPage.getByText("Статус загрузчика недоступен", { exact: true })).toBeVisible();
  await partialPage.getByRole("button", { name: "Повторить историю" }).click();
  await partialPage.getByRole("button", { name: "Повторить статус загрузчика" }).click();
  await expect.poll(() => partialApi.calls.filter((call) => call.path.startsWith("/api/admin/probes/ru-origin/runs")).length).toBeGreaterThan(1);
  await expect.poll(() => partialApi.calls.filter((call) => call.path === "/api/admin/probes/ru-origin/uploader-status").length).toBeGreaterThan(1);
  await partialContext.close();

  const latestContext = await browser.newContext();
  const latestPage = await latestContext.newPage();
  const latestApi = await installAdminApiMock(latestPage, { ruScenario: "fresh-pass", ruLatestStatus: 503 });
  await latestPage.goto("/nodes?selected=nl&tab=ru");
  await expect(latestPage.getByRole("region", { name: "История проверок из РФ" })).toBeVisible();
  await latestPage.getByRole("button", { name: "Повторить текущий RU-origin" }).click();
  await expect.poll(() => latestApi.calls.filter((call) => call.path === "/api/admin/probes/ru-origin/latest").length).toBeGreaterThan(1);
  await latestContext.close();

  const uploader = await openScenario(browser, "uploader-fresh-failure");
  await expect(uploader.page.getByText("Архив не подтверждён", { exact: true })).toBeVisible();
  await expect(uploader.page.getByText("Диск требует внимания", { exact: true })).toBeVisible();
  await expect(uploader.page.getByText("Последняя ошибка загрузчика", { exact: true })).toBeVisible();
  await uploader.context.close();

  const mobile404Context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mobile404Page = await mobile404Context.newPage();
  await installAdminApiMock(mobile404Page, { ruScenario: "fresh-pass", nodeObservabilityStatus: 404 });
  await mobile404Page.goto("/nodes?selected=nl");
  await mobile404Page.getByRole("button", { name: "Назад к нодам" }).click();
  await expect(mobile404Page).not.toHaveURL(/selected=/);
  await expect(mobile404Page.getByRole("table", { name: "Список нод" })).toBeVisible();
  await mobile404Context.close();

  const mobileLoadingContext = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const mobileLoadingPage = await mobileLoadingContext.newPage();
  await installAdminApiMock(mobileLoadingPage, { ruScenario: "fresh-pass", nodeObservabilityDelayMs: 5_000 });
  await mobileLoadingPage.goto("/nodes?selected=nl");
  await expect(mobileLoadingPage.getByRole("button", { name: "Назад к нодам" })).toBeVisible();
  await mobileLoadingContext.close();
});
