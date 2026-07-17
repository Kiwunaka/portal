import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

test("Сеть: трафик держит общие range/node-фильтры и честный разрыв данных", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/traffic?range=30d");

  await expect(page.getByRole("heading", { name: "Трафик", level: 1 })).toBeVisible();
  const chart = page.getByLabel("График трафика");
  await expect(chart).toBeVisible();
  await expect(chart).toHaveAttribute("data-pools", "free_pool,paid_pool");
  await expect(page.getByText("Разрыв линии означает «Нет данных»; отсутствующее измерение не заменено нулём.", { exact: true })).toBeVisible();
  await expect(page.getByText("paid_pool", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("free_pool", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Нет данных", { exact: true }).first()).toBeVisible();
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/traffic/summary?from=") && call.path.includes("&to="))).toBe(true);

  await page.getByLabel("Нода трафика").selectOption("nl");
  await expect(page).toHaveURL(/node=nl/);
  await expect(page.getByText("paid_pool", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("free_pool", { exact: true })).toHaveCount(0);

  await page.getByLabel("Нода трафика").selectOption("nl-free");
  await expect(page).toHaveURL(/node=nl-free/);
  await expect(page.getByText("free_pool", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("paid_pool", { exact: true })).toHaveCount(0);
});

test("Сеть: до серверного payload нет ложного success или пустой очереди", async ({ page }) => {
  await installAdminApiMock(page, { networkScenario: "populated", networkDelayMs: 800 });

  await page.goto("/traffic?range=30d");
  await expect(page.getByText("Сводка трафика ещё не получена", { exact: true })).toBeVisible();
  await expect(page.getByText("Сводка трафика получена", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Сводка трафика получена", { exact: true })).toBeVisible();

  await page.goto("/alerts?status=active");
  await expect(page.getByText("Данные алертов ещё не получены", { exact: true })).toBeVisible();
  await expect(page.getByText("Очередь пуста", { exact: true })).toHaveCount(0);
  await expect(page.getByText("В очереди: 2", { exact: true })).toBeVisible();

  await page.goto("/provider-caps?selected=nl");
  await expect(page.getByText("Лимиты ещё не получены", { exact: true })).toBeVisible();
  await expect(page.getByText("Лимиты перечитаны", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Лимиты перечитаны", { exact: true })).toBeVisible();
});

test("Сеть: алерты открывают контекст сущности, а L1 ack не требует intent", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/alerts?status=active&selected=81");

  await expect(page.getByRole("heading", { name: "Алерты", level: 1 })).toBeVisible();
  const contextLink = page.getByRole("link", { name: "Открыть лимит NL" });
  await expect(contextLink).toHaveAttribute("href", "/provider-caps?selected=nl");
  await expect(page.getByText("Длительность", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Подтвердить" }).click();
  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/alerts/81/ack")).toBe(true);
  const ack = api.calls.find((call) => call.path === "/api/admin/alerts/81/ack");
  expect(ack?.headers?.["x-admin-intent-id"]).toBe("");
});

test("Сеть: лимит провайдера сохраняется только после server review", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/provider-caps?selected=nl");

  await expect(page.getByRole("heading", { name: "Лимиты провайдеров", level: 1 })).toBeVisible();
  await page.getByRole("button", { name: "Проверить и сохранить" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Сервер пересчитал конфигурацию и прогноз исчерпания.");
  await expect(dialog).toContainText("Прогноз исчерпания");
  await expect(dialog.getByRole("button", { name: "Выполнить" })).toBeDisabled();
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 716", { exact: true })).toBeVisible();

  const previewIndex = api.calls.findIndex((call) => call.path === "/api/admin/action-intents");
  const executeIndex = api.calls.findIndex((call) => call.path === "/api/admin/provider-quotas/nl" && call.method === "PATCH");
  expect(executeIndex).toBeGreaterThan(previewIndex);
  expect(api.calls[executeIndex].headers?.["x-admin-intent-id"]).toBeTruthy();
  expect(api.calls[executeIndex].headers?.["x-admin-confirmation-sha256"]).toMatch(/^[0-9a-f]{64}$/);
});

test("Сеть: пустой лимит не открывает intent, а обновление не стирает dirty-черновик", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/provider-caps?selected=de");

  const limit = page.getByLabel("Лимит квоты в ГиБ");
  await limit.fill("   ");
  await page.getByRole("button", { name: "Проверить и сохранить" }).click();
  await expect(page.getByRole("alert")).toHaveText("Введите лимит квоты в ГиБ: пустое значение нельзя сохранить.");
  expect(api.calls.filter((call) => call.path === "/api/admin/action-intents")).toHaveLength(0);

  await page.goto("/provider-caps?selected=nl");
  await limit.fill("123");
  await expect(page.getByText("Есть несохранённые изменения.", { exact: true })).toBeVisible();
  const initialReads = api.calls.filter((call) => call.path === "/api/admin/provider-quotas").length;
  await page.getByRole("button", { name: "Обновить" }).click();
  await expect.poll(() => api.calls.filter((call) => call.path === "/api/admin/provider-quotas").length).toBeGreaterThan(initialReads);
  await expect(limit).toHaveValue("123");
});

test("Сеть: бесплатный контур показывает burn rate и только FREE-строки", async ({ page }) => {
  await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/free-tier");

  await expect(page.getByRole("heading", { name: "Бесплатный контур", level: 1 })).toBeVisible();
  await expect(page.getByText("Расход в день", { exact: true })).toBeVisible();
  await expect(page.getByText("Анна Бесплатная", { exact: true })).toBeVisible();
  await expect(page.getByText("Илья Бесплатный", { exact: true })).toBeVisible();
  await expect(page.getByText("Платный пул в расчёты и строки этого экрана не входит.", { exact: true })).toBeVisible();
  await expect(page.getByText("paid_pool", { exact: true })).toHaveCount(0);
});

test("Деньги: платежи разделяют order status и callback, держат периоды и guarded reconcile", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/payments?period=today");

  await expect(page.getByRole("heading", { name: "Платежи", level: 1 })).toBeVisible();
  await expect(page.getByText("Зависшие", { exact: true })).toBeVisible();
  await expect(page.getByText("Состояние callback", { exact: true }).first()).toBeVisible();
  await page.getByLabel("Период платежей").selectOption("7d");
  await expect(page).toHaveURL(/period=7d/);
  await page.getByLabel("Период платежей").selectOption("30d");
  await expect(page).toHaveURL(/period=30d/);
  expect(api.calls.some((call) => call.path === "/api/admin/payments/summary?period=today")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/payments/summary?period=7d")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/payments/summary?period=30d")).toBe(true);

  await page.getByRole("button", { name: /order-review-901/ }).first().click();
  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/payments/orders/freekassa/order-review-901")).toBe(true);
  await page.getByLabel("Примечание сверки").fill("Проверено в кабинете провайдера, callback не изменяем.");
  await page.getByRole("button", { name: "Проверить и сверить" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("provider, order, status и callback version");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 717", { exact: true })).toBeVisible();
  const reconcile = api.calls.find((call) => call.path.endsWith("/reconcile"));
  expect(reconcile?.headers?.["x-admin-intent-id"]).toBeTruthy();
  await expect(page.getByText(/payload_json|provider_payload|raw callback/i)).toHaveCount(0);
});

test("Деньги: сбой реестра заказов не скрывает KPI и очередь внимания", async ({ page }) => {
  await installAdminApiMock(page, { revenueScenario: "populated", paymentOrdersStatus: 503 });
  await page.goto("/payments?period=7d");

  await expect(page.getByText("Часть источников недоступна", { exact: true })).toBeVisible();
  await expect(page.getByText("3 885 RUB", { exact: true })).toBeVisible();
  await expect(page.getByText("order-review-901", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Реестр заказов временно недоступен", { exact: true })).toBeVisible();
});

test("Деньги: воронка применяет общий range/source/stage к графику и таблице", async ({ page }) => {
  await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/funnel?range=30d");

  await expect(page.getByRole("heading", { name: "Воронка", level: 1 })).toBeVisible();
  const chart = page.getByLabel("График воронки");
  await expect(chart).toHaveAttribute("data-source", "all");
  await page.getByLabel("Источник воронки").selectOption("site");
  await page.getByLabel("Стадия воронки").selectOption("paid");
  await expect(page).toHaveURL(/source=site/);
  await expect(page).toHaveURL(/stage=paid/);
  await expect(chart).toHaveAttribute("data-source", "site");
  await expect(chart).toHaveAttribute("data-stage", "paid");
  await expect(page.getByText("site", { exact: true })).toBeVisible();
  await expect(page.getByText("bot", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("columnheader", { name: "Оплатили" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Посетители" })).toHaveCount(0);
  await expect(page.getByText("Оплата → подтверждение", { exact: true })).toBeVisible();
  await expect(page.getByText("Кабинет/бот → оплата", { exact: true })).toHaveCount(0);
  await expect(page.getByText(/\{.*\}|payload_json|raw json/i)).toHaveCount(0);
});

test("Деньги: promo edit и delete проходят через L2/L3 server intent", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/promos");

  await page.getByRole("button", { name: "WELCOME20" }).click();
  await page.getByLabel("Значение промокода").fill("25");
  await page.getByRole("button", { name: "Проверить и сохранить" }).click();
  let dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("точные before/after и срок промокода");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 717", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Закрыть" }).click();

  await page.getByRole("button", { name: "Удалить" }).click();
  dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Риск L3");
  await dialog.getByLabel("Подтверждение").fill("WELCOME20");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  const mutations = api.calls.filter((call) => call.path === "/api/admin/promos/WELCOME20");
  expect(mutations.some((call) => call.method === "PATCH" && call.headers?.["x-admin-intent-id"])).toBe(true);
  expect(mutations.some((call) => call.method === "DELETE" && call.headers?.["x-admin-intent-id"])).toBe(true);
});

test("Деньги: referral queue имеет стабильный порядок и серверное основание", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/referrals");

  const queueRows = page.getByRole("heading", { name: "Очередь решений" }).locator("xpath=ancestor::section[1]").locator("tbody tr");
  await expect(page.getByText("Готово к награде", { exact: true })).toBeVisible();
  await expect(queueRows.first()).toContainText("#301");
  await expect(queueRows.nth(1)).toContainText("#302");
  await page.getByRole("button", { name: "Проверить и обработать" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("зафиксировал очередь и основание решения");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  const process = api.calls.find((call) => call.path === "/api/admin/referrals/process" && call.method === "POST");
  expect(process?.headers?.["x-admin-intent-id"]).toBeTruthy();
  await expect(page.getByText("SYNTHETIC-RAW-REFERRAL-META", { exact: false })).toHaveCount(0);
});
