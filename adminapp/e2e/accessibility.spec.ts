import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

const routes = [
  ["/", "Главная"],
  ["/nodes", "Ноды"],
  ["/traffic", "Трафик"],
  ["/alerts", "Алерты"],
  ["/provider-caps", "Лимиты провайдеров"],
  ["/free-tier", "Бесплатный контур"],
  ["/users", "Пользователи"],
  ["/online", "Сейчас онлайн"],
  ["/tickets", "Тикеты"],
  ["/payments", "Платежи"],
  ["/funnel", "Воронка"],
  ["/promos", "Промо"],
  ["/referrals", "Рефералы"],
  ["/release", "Релиз"],
  ["/broadcast", "Рассылка"]
] as const;

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    window.sessionStorage.setItem("pokrov_admin_session_token", "mock-admin-token");
  });
});

test("все 15 маршрутов открываются напрямую с русскими заголовками", async ({ page }) => {
  await installAdminApiMock(page);

  for (const [path, label] of routes) {
    await page.goto(path);
    const main = page.getByRole("main");
    await expect(main).toBeVisible();
    await expect(page.getByRole("heading", { name: label, exact: true, level: 1 })).toBeVisible();
    await expect(main.getByText("Ops admin", { exact: true })).toHaveCount(0);
    await expect(main.getByText("Free tier", { exact: true })).toHaveCount(0);
  }
});

test("подсказка и диалог управляются клавиатурой и возвращают фокус", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  await page.goto("/nodes");

  const tooltipTrigger = page.getByRole("button", { name: "Показать пояснение" }).first();
  await tooltipTrigger.hover();
  await expect(page.getByRole("tooltip").first()).toBeVisible();
  await tooltipTrigger.focus();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("tooltip").first()).toBeHidden();
  await expect(tooltipTrigger).toBeFocused();

  const commands = page.getByRole("button", { name: "Команды" });
  await commands.focus();
  await page.keyboard.press("Control+k");
  const dialog = page.getByRole("dialog", { name: "Палитра команд" });
  const close = dialog.getByRole("button", { name: "Закрыть диалог" });
  await expect(page.getByRole("searchbox", { name: "Глобальный поиск" })).toBeFocused();
  await dialog.getByRole("button").last().focus();
  await page.keyboard.press("Tab");
  await expect(close).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(commands).toBeFocused();

  const focusStyle = await commands.evaluate((element) => {
    const style = getComputedStyle(element);
    return {
      outline: style.outlineStyle,
      width: style.outlineWidth,
      shadow: style.boxShadow,
      transition: style.transitionDuration
    };
  });
  expect(
    (focusStyle.outline === "solid" && Number.parseFloat(focusStyle.width) > 0)
      || focusStyle.shadow !== "none"
  ).toBe(true);
  expect(Number.parseFloat(focusStyle.transition)).toBeLessThanOrEqual(0.001);
});

test("mobile master-detail и desktop layout не создают общий горизонтальный скролл", async ({ page }) => {
  await installAdminApiMock(page, { ruScenario: "fresh-pass" });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/nodes");

  const table = page.getByRole("table", { name: "Список нод" });
  await expect(table).toBeVisible();
  expect(await table.evaluate((element) => {
    const scroller = element.parentElement;
    return Boolean(scroller && scroller.scrollWidth > scroller.clientWidth);
  })).toBe(true);

  await page.getByRole("button", { name: "Открыть ноду NL" }).click();
  await expect(page.getByRole("button", { name: "Назад к нодам" })).toBeVisible();
  await expect(table).toBeHidden();
  await page.getByRole("button", { name: "Назад к нодам" }).click();
  await expect(table).toBeVisible();

  await page.getByRole("button", { name: "Открыть навигацию" }).click();
  const navigation = page.getByRole("dialog", { name: "Навигация по разделам" });
  await navigation.getByRole("link", { name: "Трафик", exact: true }).click();
  await expect(navigation).toBeHidden();
  await expect(page).toHaveURL(/\/traffic$/);

  for (const width of [1280, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/nodes");
    const layout = await page.evaluate(() => {
      const sidebar = document.querySelector("aside")?.getBoundingClientRect();
      const main = document.querySelector("main")?.getBoundingClientRect();
      return {
        sidebarRight: sidebar?.right ?? 0,
        mainLeft: main?.left ?? 0,
        mainRight: main?.right ?? 0,
        documentWidth: document.documentElement.scrollWidth,
        viewportWidth: window.innerWidth
      };
    });
    expect(layout.mainLeft).toBeGreaterThanOrEqual(layout.sidebarRight - 1);
    expect(layout.mainRight).toBeLessThanOrEqual(layout.viewportWidth + 1);
    expect(layout.documentWidth).toBeLessThanOrEqual(layout.viewportWidth + 1);
  }
});
