import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

test("оболочка группирует 15 разделов и открывает палитру с клавиатуры", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  for (const group of ["Команда", "Сеть", "Клиенты", "Деньги и рост", "Управление"]) {
    await expect(page.getByRole("navigation").getByText(group, { exact: true })).toBeVisible();
  }
  await expect(page.getByRole("link")).toHaveCount(15);
  await page.keyboard.press("Control+k");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeHidden();
});

test("поиск начинается с двух символов и ведёт по безопасному canonical href", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/nodes?keep=1");

  const commandsButton = page.getByRole("button", { name: "Команды" });
  await commandsButton.click();
  const search = page.getByRole("searchbox", { name: "Глобальный поиск" });
  await search.fill(" n ");
  await page.waitForTimeout(300);
  expect(api.calls.filter((call) => call.path.startsWith("/api/admin/search?")).length).toBe(0);

  await search.fill(" nl ");
  await expect.poll(() => api.calls.filter((call) => call.path === "/api/admin/search?q=nl").length).toBe(1);
  await page.getByRole("button", { name: /Нода NL/ }).click();

  await expect(page).toHaveURL(/\/nodes\?selected=nl$/);
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeHidden();
  await expect(commandsButton).toBeFocused();
  expect(api.calls.filter((call) => call.path.startsWith("/api/admin/search?")).every((call) => call.method === "GET")).toBe(true);
});

test("поиск 404 оставляет палитру и текущий маршрут рабочими", async ({ page }) => {
  await installAdminApiMock(page, { searchStatus: 404 });
  await page.goto("/nodes?selected=de");
  await page.getByRole("button", { name: "Команды" }).click();
  await page.getByRole("searchbox", { name: "Глобальный поиск" }).fill("de");

  await expect(page.getByText("Поиск пока недоступен", { exact: true })).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeVisible();
  await expect(page).toHaveURL(/\/nodes\?selected=de$/);
  await page.getByRole("button", { name: "Главная" }).click();
  await expect(page).toHaveURL(/\/$/);
});

test("назад и вперёд восстанавливают маршрут вместе с чужими query-параметрами", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/nodes?selected=nl&keep=yes");

  await page.getByRole("link", { name: "Пользователи", exact: true }).click();
  await expect(page).toHaveURL(/\/users$/);
  await page.goBack();
  await expect(page).toHaveURL(/\/nodes\?selected=nl&keep=yes$/);
  await expect(page.getByRole("heading", { name: "Ноды", exact: true })).toBeVisible();
  await page.goForward();
  await expect(page).toHaveURL(/\/users$/);
});

test("на узком экране навигация открывается диалогом", async ({ page }) => {
  await page.setViewportSize({ width: 768, height: 900 });
  await installAdminApiMock(page);
  await page.goto("/");

  await page.getByRole("button", { name: "Открыть навигацию" }).click();
  const drawer = page.getByRole("dialog", { name: "Навигация по разделам" });
  await expect(drawer).toBeVisible();
  await drawer.getByRole("link", { name: "Ноды", exact: true }).click();
  await expect(drawer).toBeHidden();
  await expect(page).toHaveURL(/\/nodes$/);
});
