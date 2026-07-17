import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

test("прямая ссылка на пользователя загружает карточку, а IP — только расследование", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/users?selected=1001&tab=overview");

  await expect(page.getByRole("heading", { name: "Пользователь 1001" })).toBeVisible();
  await expect(page.getByText("Снимок панели неполный", { exact: true })).toBeVisible();
  await expect(page.getByText("Нет данных", { exact: true }).first()).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/users/1001")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/users/1001/investigation")).toBe(false);
  await expect(page.getByText("203.0.113.44", { exact: true })).toHaveCount(0);

  await page.getByRole("tab", { name: "Расследование" }).click();
  await expect(page).toHaveURL(/selected=1001.*tab=investigation/);
  await expect(page.getByText("203.0.113.44", { exact: true })).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/users/1001/investigation")).toBe(true);
});

test("прямая ссылка на онлайн сохраняет фильтры и не показывает исходный IP", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/online?node=nl&source=user&q=%D0%98%D0%B2%D0%B0%D0%BD");

  await expect(page.getByRole("link", { name: /Пользователь 1001/ })).toBeVisible();
  await expect(page).toHaveURL(/node=nl.*source=user.*q=/);
  await expect(page.getByText("203.0.113.44", { exact: true })).toHaveCount(0);
  expect(api.calls.some((call) => call.path === "/api/admin/online/users?limit=200")).toBe(true);
  expect(api.calls.some((call) => call.path.includes("investigation"))).toBe(false);
});

test("прямая ссылка на тикет лениво загружает полную переписку", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/tickets?status=open&priority=high&selected=501");

  await expect(page.getByRole("heading", { name: "Тикет #501" })).toBeVisible();
  await expect(page.getByText("Уточните платформу", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Скачать вложение" })).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/tickets?status=open&limit=100")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/tickets/501")).toBe(true);
});

test("блокировка и ответ проходят через намерение, а неясный ответ сохраняет черновик", async ({ page }) => {
  const api = await installAdminApiMock(page, { ticketReplyOutcomes: ["uncertain"] });
  await page.goto("/users?selected=1001");

  await page.getByRole("button", { name: "Заблокировать" }).click();
  let dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("1001");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("Действие выполнено", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Закрыть" }).click();

  await page.goto("/tickets?selected=501");
  const draft = page.getByLabel("Текст ответа");
  await draft.fill("Проверочный ответ без секретов");
  await page.getByRole("button", { name: "Подготовить ответ" }).click();
  dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("ОТПРАВИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByRole("button", { name: "Проверить текущее состояние" })).toBeVisible();
  await expect(draft).toHaveValue("Проверочный ответ без секретов");

  for (const path of ["/api/admin/users/1001/manual/block", "/api/admin/tickets/501/reply"]) {
    const call = api.calls.find((item) => item.path === path);
    expect(call?.headers?.["x-admin-intent-id"]).toBe("00000000-0000-4000-8000-000000000713");
    expect(call?.headers?.["x-admin-idempotency-key"]).toMatch(/^[0-9a-f-]{36}$/);
    expect(call?.headers?.["x-admin-confirmation-sha256"]).toMatch(/^[0-9a-f]{64}$/);
  }
});
