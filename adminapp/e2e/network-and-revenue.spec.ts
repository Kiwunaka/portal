import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

test("Сеть: трафик держит общие range/node-фильтры и честный разрыв данных", async ({ page }) => {
  const api = await installAdminApiMock(page, { networkScenario: "populated" });
  await page.goto("/traffic?range=30d&node=nl");

  await expect(page.getByRole("heading", { name: "Трафик", level: 1 })).toBeVisible();
  await expect(page.getByLabel("График трафика")).toBeVisible();
  await expect(page.getByText("Разрыв линии означает «Нет данных»; отсутствующее измерение не заменено нулём.", { exact: true })).toBeVisible();
  await expect(page.getByText("paid_pool", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("free_pool", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Нет данных", { exact: true }).first()).toBeVisible();
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/traffic/summary?from=") && call.path.includes("&to="))).toBe(true);

  await page.getByLabel("Нода трафика").selectOption("nl-free");
  await expect(page).toHaveURL(/node=nl-free/);
  await expect(page.getByText("free_pool", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("paid_pool", { exact: true })).toHaveCount(0);
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
