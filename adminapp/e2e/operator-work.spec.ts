import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

test("Моя смена: серверные очереди и task transition используют optimistic action intent", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/shift");

  await expect(page.getByRole("heading", { name: "Моя смена", level: 1 })).toBeVisible();
  await expect(page.getByText("Проверить callback заказа", { exact: true })).toBeVisible();
  await expect(page.getByText("Назначить владельца сетевого сигнала", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Сбойные команды" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Платёжная проверка" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Блокеры релиза" })).toBeVisible();

  await page.getByRole("button", { name: "Начать" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Сервер связал preview с текущей версией.");
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 721", { exact: true })).toBeVisible();

  const prepare = api.calls.find((call) => call.path === "/api/admin/v2/shift/action-intents");
  expect(prepare?.body).toMatchObject({ action: "operator_task.update", payload: { expected_version: 2, status: "in_progress" } });
  const execute = api.calls.find((call) => call.path.includes("/api/admin/v2/shift/action-intents/") && call.path.endsWith("/execute"));
  expect(execute?.headers?.["x-admin-intent-id"]).toBeTruthy();
  expect(execute?.headers?.["x-admin-idempotency-key"]).toBeTruthy();
  expect(execute?.headers?.["x-admin-confirmation-sha256"]).toMatch(/^[0-9a-f]{64}$/);
});

test("Incident Room: detail, timeline, links, alerts и lifecycle читаются из единого incident authority", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/incidents");

  await expect(page.getByRole("heading", { name: "Incident Room", level: 1 })).toBeVisible();
  await page.getByRole("button", { name: /Деградация лимита NL/ }).click();
  await expect(page.getByRole("heading", { name: "Деградация лимита NL", level: 2 })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Timeline" })).toBeVisible();
  await expect(page.getByText("Создан из сигнала квоты.", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Связанные сущности" })).toBeVisible();
  await expect(page.getByText("NL provider", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Алерты" })).toBeVisible();

  await page.getByRole("button", { name: "Перевести в наблюдение" }).click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 721", { exact: true })).toBeVisible();

  const prepare = api.calls.find((call) => call.path === "/api/admin/v2/incidents/action-intents");
  expect(prepare?.body).toMatchObject({ action: "incident.update", payload: { expected_version: 4, workflow_status: "monitoring" } });
  expect(api.calls.some((call) => call.path === `/api/admin/v2/incidents/${"00000000-0000-4000-8000-000000000301"}`)).toBe(true);
});
