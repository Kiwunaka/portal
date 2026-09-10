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
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/v2/network/traffic?from=") && call.path.includes("&to="))).toBe(true);

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

test("Сеть: alert ack выполняется только после version-bound server preview", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/alerts?status=active&selected=81");

  await expect(page.getByRole("heading", { name: "Алерты", level: 1 })).toBeVisible();
  const contextLink = page.getByRole("link", { name: "Открыть лимит NL" });
  await expect(contextLink).toHaveAttribute("href", "/provider-caps?selected=nl");
  await expect(page.getByText("Длительность", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Подтвердить" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Версия алерта");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 721", { exact: true })).toBeVisible();
  const prepare = api.calls.find((call) => call.path === "/api/admin/v2/incidents/action-intents");
  expect(prepare?.body).toMatchObject({ action: "alert.ack", payload: { expected_version: 3 } });
  const execute = api.calls.find((call) => call.path.endsWith("/execute") && call.path.includes("/api/admin/v2/incidents/action-intents/"));
  expect(execute?.headers?.["x-admin-intent-id"]).toBeTruthy();
  expect(api.calls.some((call) => call.path === "/api/admin/alerts/81/ack")).toBe(false);
});

test("Сеть: приглушение алерта проходит через network v2 intent", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/alerts?status=active&selected=81");

  await page.getByRole("button", { name: "Приглушить на 1 час" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Риск L2");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 721", { exact: true })).toBeVisible();

  const prepare = api.calls.find((call) => call.path === "/api/admin/v2/network/action-intents");
  expect(prepare?.body).toMatchObject({ action: "alert.silence", payload: { expected_version: 3, minutes: 60 } });
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/v2/network/action-intents/") && call.path.endsWith("/execute"))).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/alerts/81/silence")).toBe(false);
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

  const previewIndex = api.calls.findIndex((call) => call.path === "/api/admin/v2/network/action-intents");
  const executeIndex = api.calls.findIndex((call) => call.path.startsWith("/api/admin/v2/network/action-intents/") && call.path.endsWith("/execute"));
  expect(executeIndex).toBeGreaterThan(previewIndex);
  expect(api.calls[executeIndex].headers?.["x-admin-intent-id"]).toBeTruthy();
  expect(api.calls[executeIndex].headers?.["x-admin-confirmation-sha256"]).toMatch(/^[0-9a-f]{64}$/);
  expect(api.calls.some((call) => call.path === "/api/admin/provider-quotas/nl" && call.method === "PATCH")).toBe(false);
});

test("Сеть: пустой лимит не открывает intent, а обновление не стирает dirty-черновик", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/provider-caps?selected=de");

  const limit = page.getByLabel("Лимит квоты в ГиБ");
  await limit.fill("   ");
  await page.getByRole("button", { name: "Проверить и сохранить" }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Введите лимит квоты в ГиБ" })).toHaveText("Введите лимит квоты в ГиБ: пустое значение нельзя сохранить.");
  expect(api.calls.filter((call) => call.path === "/api/admin/v2/network/action-intents")).toHaveLength(0);

  await page.goto("/provider-caps?selected=nl");
  await limit.fill("123");
  await expect(page.getByText("Есть несохранённые изменения.", { exact: true })).toBeVisible();
  const initialReads = api.calls.filter((call) => call.path === "/api/admin/v2/network/providers").length;
  await page.getByRole("main").getByRole("button", { name: "Обновить" }).click();
  await expect.poll(() => api.calls.filter((call) => call.path === "/api/admin/v2/network/providers").length).toBeGreaterThan(initialReads);
  await expect(limit).toHaveValue("123");
});

test("Сеть: архив FREE показывает legacy burn rate и только raw FREE-строки", async ({ page }) => {
  await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/free-tier");

  await expect(page.getByRole("heading", { name: "Архив FREE", level: 1 })).toBeVisible();
  await expect(page.getByText("Расход в день", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /^Анна Бесплатная(?:\s|$)/ })).toBeVisible();
  await expect(page.getByRole("link", { name: /^Илья Бесплатный(?:\s|$)/ })).toBeVisible();
  await expect(page.getByText("Здесь только legacy-строки FREE; действующий доступ определяется как TRIAL, PAID или PENDING.", { exact: true })).toBeVisible();
  await expect(page.getByText("paid_pool", { exact: true })).toHaveCount(0);
});

test("Деньги: доступ читает entitlement authority и показывает выданный код только из результата L3", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/access");

  await expect(page.getByRole("heading", { name: "Доступ", level: 1 })).toBeVisible();
  await expect(page.getByText("Телеметрия не подтверждает оплату; доступ определяется grant и outbox.", { exact: true })).toBeVisible();
  await expect(page.getByText("grant_1234567890abcdefabcd", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Подготовить" }).last().click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Риск L3");
  await dialog.getByLabel("Подтверждение").fill("mini");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("GIFT-ONE-TIME-123", { exact: true })).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/v2/money/access")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/money/action-intents" && (call.body as { action?: string } | null)?.action === "gift_code.create")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/gift-codes")).toBe(false);
});

test("Рост: бонусные настройки сохраняются через version-bound growth intent", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/bonuses");

  await expect(page.getByRole("heading", { name: "Бонусы", level: 1 })).toBeVisible();
  await expect(page.getByLabel("Секторы колеса")).toContainText("days:1:70");
  await page.getByLabel("Cooldown колеса").fill("240");
  await page.getByRole("button", { name: "Проверить и сохранить" }).first().click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("текущей версией AppSetting");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  expect(api.calls.some((call) => call.path === "/api/admin/v2/growth/bonuses")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/growth/action-intents" && (call.body as { action?: string } | null)?.action === "wheel_config.update")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/wheel-config")).toBe(false);
});

test("Рост: решение по программе и reward grant проходят через единый L3 intent", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/programs");

  await expect(page.getByRole("heading", { name: "Программы", level: 1 })).toBeVisible();
  await page.getByRole("button", { name: /Переход от VPN|Исследование/ }).first().click();
  await page.getByLabel("Награда по заявке").selectOption("3");
  await page.getByRole("button", { name: "Одобрить" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Статус и entitlement reward изменятся атомарно");
  await dialog.getByLabel("Подтверждение").fill("00000000-0000-4000-8000-000000000801");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 719", { exact: true })).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/v2/growth/programs?limit=200")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/growth/action-intents" && (call.body as { action?: string } | null)?.action === "program_application.review")).toBe(true);
  expect(api.calls.some((call) => call.path.includes("/api/admin/program-applications/"))).toBe(false);
});

test("Деньги: платежи разделяют order status и callback, держат периоды и guarded reconcile", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/payments?period=today");

  await expect(page.getByRole("heading", { name: "Платежи", level: 1 })).toBeVisible();
  await expect(page.getByText("Зависшие", { exact: true })).toBeVisible();
  const metrics = page.getByLabel("Показатели платежей");
  const browserCohort = metrics.locator(".ops-metric-cell").filter({ hasText: "Сессии сайта без оплаты" });
  const productCohort = metrics.locator(".ops-metric-cell").filter({ hasText: "Пользователи без оплаты" });
  await expect(browserCohort.getByText("8", { exact: true })).toBeVisible();
  await expect(browserCohort).toContainText("Начали оплату: 12");
  await expect(productCohort.getByText("4", { exact: true })).toBeVisible();
  await expect(productCohort).toContainText("Начали оплату: 8");
  await expect(metrics.getByText("Checkout без оплаты", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("columnheader", { name: "Состояние callback", exact: true }).first()).toBeVisible();
  await page.getByLabel("Период платежей").selectOption("7d");
  await expect(page).toHaveURL(/period=7d/);
  await page.getByLabel("Период платежей").selectOption("30d");
  await expect(page).toHaveURL(/period=30d/);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/money/payments/summary?period=today")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/money/payments/summary?period=7d")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/money/payments/summary?period=30d")).toBe(true);

  await page.getByRole("button", { name: /order-review-901/ }).first().click();
  await expect.poll(() => api.calls.some((call) => call.path === "/api/admin/v2/money/payments/orders/freekassa/order-review-901")).toBe(true);
  const orderCard = page.getByRole("complementary", { name: "Карточка платёжного заказа" });
  const quote = orderCard.getByRole("region", { name: "Сохранённый расчёт заказа" });
  await expect(quote).toContainText("сумма: 99.00 RUB");
  await expect(quote).toContainText("До скидки: 149 RUB");
  await expect(quote).toContainText("Кампания: winback-fixture · ревизия 3");
  await expect(quote).toContainText("Оферта: terms-fixture");
  await expect(orderCard.getByText("Callback не обработан", { exact: true })).toBeVisible();
  await expect(orderCard.getByText("Начисление доступа требует ручной проверки", { exact: true })).toBeVisible();
  const delivery = orderCard.getByRole("region", { name: "Начисление и доставка доступа" });
  await expect(delivery).toContainText("Начисление: manual_review");
  await expect(delivery).toContainText("Право доступа: active");
  await expect(delivery).toContainText("Доставка: pending");
  await expect(delivery).toContainText("Попыток: 3");
  await expect(delivery).toContainText("delivery_deferred");
  await expect(delivery).toContainText("Следующая попытка:");
  await expect(orderCard.getByRole("region", { name: "История команд заказа" })).toContainText("intent_review_901");
  await page.getByLabel("Примечание сверки").fill("Проверено в кабинете провайдера, callback не изменяем.");
  await page.getByRole("button", { name: "Проверить и сверить" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Провайдер, номер заказа, статус и версия callback зафиксированы сервером.");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 717", { exact: true })).toBeVisible();
  const reconcile = api.calls.find((call) => call.path === "/api/admin/v2/money/action-intents");
  expect(reconcile?.body).toMatchObject({ action: "payment.reconcile" });
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/v2/money/action-intents/") && call.path.endsWith("/execute"))).toBe(true);
  expect(api.calls.some((call) => call.path.endsWith("/reconcile"))).toBe(false);
  await expect(page.getByText(/payload_json|provider_payload|raw callback/i)).toHaveCount(0);
  await dialog.getByRole("button", { name: "Закрыть", exact: true }).click();
  await page.getByRole("button", { name: /order-paid-902/ }).click();
  await expect(orderCard.getByText("Команд по заказу нет.", { exact: true })).toBeVisible();
  await expect(delivery).toContainText("Доставка: Запись отсутствует");
  await expect(orderCard.getByText("delivery_deferred", { exact: true })).toHaveCount(0);
  await expect(quote).toContainText("Сохранённый расчёт недоступен.");
});

test("Кампании: юридические условия и ёмкость видны до решения о запуске", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated", winbackScenario: "blocked" });
  await page.goto("/promos");
  const policy = page.getByRole("region", { name: "Условия запуска кампании" });
  await expect(policy).toContainText("Юридический профиль: owner_approved · оферта: terms-fixture");
  await expect(policy).toContainText("Ёмкость: 950 / 1 000 · зона: red");
  await expect(policy).toContainText("Привлечение по ёмкости: приостановлено");
  await expect(policy).toContainText("legal_launch_blocked");
  await expect(page.getByText("4 / 20", { exact: true })).toBeVisible();
  const growth = page.getByRole("region", { name: "Ограничитель роста" });
  await expect(growth).toContainText("Соединения по данным узлов: 37 · Одновременные устройства: не измерены");
  await expect(growth).toContainText("Поддержка: 5 открытых · 1 срочных · 2 просроченных ответов");
  await expect(growth).toContainText("CPU 20% · 15 Мбит/с · потери 0%");
  await expect(growth).toContainText("Рост остановлен");
  expect(api.calls.filter((call) => call.method === "POST")).toHaveLength(0);
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("Деньги: сбой реестра заказов не скрывает KPI и очередь внимания", async ({ page }) => {
  await installAdminApiMock(page, { revenueScenario: "populated", paymentOrdersStatus: 503 });
  await page.goto("/payments?period=7d");

  await expect(page.getByText("Часть источников недоступна", { exact: true })).toBeVisible();
  await expect(page.getByText("3 885 RUB", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /^order-review-901\b/ })).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "payment_orders_unavailable" })).toBeVisible();
});

test("Деньги: рекламная и продуктовая воронки не смешивают cohort и пользователей", async ({ page }) => {
  await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/funnel?range=30d");

  await expect(page.getByRole("heading", { name: "Воронка", level: 1 })).toBeVisible();
  const chart = page.getByLabel("График воронки");
  await expect(chart).toHaveAttribute("data-view", "acquisition");
  await expect(chart).toHaveAttribute("data-source", "all");
  await page.getByLabel("Источник воронки").selectOption("site");
  await page.getByLabel("Стадия воронки").selectOption("checkout_to_paid");
  await expect(page).toHaveURL(/source=site/);
  await expect(page).toHaveURL(/stage=checkout_to_paid/);
  await expect(chart).toHaveAttribute("data-source", "site");
  await expect(chart).toHaveAttribute("data-stage", "checkout_to_paid");
  await expect(page.getByRole("cell", { name: "site", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "bot", exact: true })).toHaveCount(0);
  await expect(page.getByRole("columnheader", { name: "Оплатили" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Первый визит" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Начали оплату → оплатили", exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Продукт", exact: true }).click();
  await expect(page).toHaveURL(/view=product/);
  await expect(chart).toHaveAttribute("data-view", "product");
  await expect(page.getByLabel("Источник воронки")).toHaveCount(0);
  await expect(page.getByRole("cell", { name: "Открыли продукт → начали оплату", exact: true })).toBeVisible();
  await expect(page.getByText("151", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Ошибки клиента" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "provider_timeout", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "android · 1.1.1", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Как считается продукт" })).toBeVisible();
  await expect(page.getByText(/\{.*\}|payload_json|raw json/i)).toHaveCount(0);
});

test("Деньги: promo edit и delete проходят через L2/L3 server intent", async ({ page }) => {
  const api = await installAdminApiMock(page, { revenueScenario: "populated" });
  await page.goto("/promos");

  await page.getByRole("button", { name: "WELCOME20" }).click();
  await page.getByLabel("Значение промокода").fill("25");
  await page.getByLabel("Редактор промокода").getByRole("button", { name: "Проверить и сохранить" }).click();
  let dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Код, тип, значение, остаток использований и срок зафиксированы сервером.");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 717", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Закрыть", exact: true }).click();

  await page.getByRole("button", { name: "Удалить" }).click();
  dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Риск L3");
  await dialog.getByLabel("Подтверждение").fill("WELCOME20");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  const prepares = api.calls.filter((call) => call.path === "/api/admin/v2/money/action-intents");
  expect(prepares.some((call) => (call.body as { action?: string } | null)?.action === "promo.update")).toBe(true);
  expect(prepares.some((call) => (call.body as { action?: string } | null)?.action === "promo.delete")).toBe(true);
  expect(api.calls.filter((call) => call.path.startsWith("/api/admin/v2/money/action-intents/") && call.path.endsWith("/execute"))).toHaveLength(2);
  expect(api.calls.some((call) => call.path === "/api/admin/promos/WELCOME20")).toBe(false);
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
  const prepare = api.calls.find((call) => call.path === "/api/admin/v2/growth/action-intents" && call.method === "POST" && (call.body as { action?: string } | null)?.action === "referral.process");
  expect(prepare?.body).toMatchObject({ action: "referral.process", target: { type: "referral_queue", id: "ready" } });
  const execute = api.calls.find((call) => call.path.startsWith("/api/admin/v2/growth/action-intents/") && call.path.endsWith("/execute"));
  expect(execute?.headers?.["x-admin-intent-id"]).toBeTruthy();
  await expect(page.getByText("SYNTHETIC-RAW-REFERRAL-META", { exact: false })).toHaveCount(0);
});
