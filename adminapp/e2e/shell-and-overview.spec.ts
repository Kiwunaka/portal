import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

const expectedGroups = [
  { label: "Команда", links: [["Главная", "/"]] },
  {
    label: "Сеть",
    links: [
      ["Ноды", "/nodes"],
      ["Трафик", "/traffic"],
      ["Алерты", "/alerts"],
      ["Лимиты провайдеров", "/provider-caps"],
      ["Бесплатный контур", "/free-tier"]
    ]
  },
  {
    label: "Клиенты",
    links: [
      ["Пользователи", "/users"],
      ["Сейчас онлайн", "/online"],
      ["Тикеты", "/tickets"]
    ]
  },
  {
    label: "Деньги и рост",
    links: [
      ["Платежи", "/payments"],
      ["Воронка", "/funnel"],
      ["Промо", "/promos"],
      ["Рефералы", "/referrals"]
    ]
  },
  {
    label: "Управление",
    links: [
      ["Релиз", "/release"],
      ["Рассылка", "/broadcast"]
    ]
  }
] as const;

test("оболочка группирует 15 разделов и открывает палитру с клавиатуры", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  const navigation = page.getByRole("navigation", { name: "Разделы центра управления" });
  const groups = navigation.getByRole("region");
  await expect(groups).toHaveCount(expectedGroups.length);
  for (const [groupIndex, group] of expectedGroups.entries()) {
    const region = groups.nth(groupIndex);
    await expect(region).toHaveAccessibleName(group.label);
    const links = region.getByRole("link");
    await expect(links).toHaveCount(group.links.length);
    for (const [index, [label, href]] of group.links.entries()) {
      await expect(links.nth(index)).toHaveText(label);
      await expect(links.nth(index)).toHaveAttribute("href", href);
    }
  }
  await page.keyboard.press("Control+k");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeVisible();
  await expect(page.getByRole("searchbox", { name: "Глобальный поиск" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog", { name: "Палитра команд" })).toBeHidden();
});

test("верхняя панель показывает фактический статус API, сессии и timestamp источника", async ({ page }) => {
  await installAdminApiMock(page);
  await page.goto("/");

  await expect(page.getByLabel("Состояние API: Норма")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Норма")).toBeVisible();
  await expect(page.locator('time[datetime="2026-07-15T10:00:00Z"]')).toBeVisible();
  await expect(page.getByText(/Старейший источник:/)).not.toContainText("Нет данных");
});

test("401 от загрузчика не выглядит активной сессией", async ({ page }) => {
  await installAdminApiMock(page, { overviewStatus: 401 });
  await page.goto("/");

  await expect(page.getByLabel("Состояние API: Доступ заблокирован")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Доступ заблокирован")).toBeVisible();
  await expect(page.getByLabel("Состояние сессии: Норма")).toHaveCount(0);
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

test("поиск не рендерит IPv6, URL, токены и поля вне allowlist", async ({ page }) => {
  await installAdminApiMock(page, { includeUnsafeSearchResults: true });
  await page.goto("/");
  await page.getByRole("button", { name: "Команды" }).click();
  await page.getByRole("searchbox", { name: "Глобальный поиск" }).fill("safe");

  await expect(page.getByRole("button", { name: /Нода NL/ })).toBeVisible();
  for (const unsafeTitle of ["Небезопасный IPv6", "Небезопасная ссылка", "Небезопасный токен", "Лишнее поле"]) {
    await expect(page.getByText(unsafeTitle, { exact: true })).toHaveCount(0);
  }
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
