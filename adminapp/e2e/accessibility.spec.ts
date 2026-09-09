import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

const routes = [
  ["/", "Главная"],
  ["/shift", "Моя смена"],
  ["/support", "Пользователи и поддержка"],
  ["/network", "Сеть и инциденты"],
  ["/money", "Деньги и доступ"],
  ["/growth", "Рост и коммуникации"],
  ["/releases", "Релизы и клиенты"],
  ["/governance", "Управление системой"],
  ["/nodes", "Ноды"],
  ["/traffic", "Трафик"],
  ["/alerts", "Алерты"],
  ["/incidents", "Incident Room"],
  ["/provider-caps", "Лимиты провайдеров"],
  ["/emergency-network", "Экстренная сеть"],
  ["/free-tier", "Архив FREE"],
  ["/access", "Доступ"],
  ["/users", "Пользователи"],
  ["/online", "Сейчас онлайн"],
  ["/tickets", "Тикеты"],
  ["/payments", "Платежи"],
  ["/funnel", "Воронка"],
  ["/promos", "Промокоды"],
  ["/bonuses", "Бонусы"],
  ["/programs", "Программы"],
  ["/referrals", "Рефералы"],
  ["/release", "Релиз"],
  ["/broadcast", "Рассылка"],
  ["/news", "Новости"]
] as const;

for (const [path, label] of [["/users", "Список пользователей"], ["/payments", "Табличные данные"]] as const) {
  test(`длинная таблица ${path} сохраняет фокус, клавиатуру и полный режим чтения`, async ({ page }) => {
    await installAdminApiMock(page, { longTables: true, revenueScenario: "populated" });
    await page.goto(path);
    const viewport = page.getByRole("region", { name: `${label}: прокрутка`, exact: true });
    const table = viewport.getByRole("table", { name: label, exact: true });
    await expect(table).toHaveAttribute("aria-rowcount", "81");
    await expect.poll(() => table.locator("tbody tr[data-index]").count()).toBeGreaterThan(0);
    expect(await table.locator("tbody tr[data-index]").count()).toBeLessThan(40);
    const firstControl = table.getByRole("button").first();
    await firstControl.focus();
    await viewport.evaluate((element) => { element.scrollTop = element.scrollHeight; });
    await expect(firstControl).toBeFocused();
    await viewport.focus();
    await page.keyboard.press("End");
    await expect(table.locator('tr[aria-rowindex="81"]')).toBeInViewport();
    expect(await table.locator("tbody tr[data-index]").count()).toBeLessThan(40);
    await page.keyboard.press("Home");
    await expect(table.locator('tr[aria-rowindex="2"]')).toBeInViewport();
    await page.getByRole("button", { name: "Режим чтения", exact: true }).click();
    await expect(table.locator("tbody tr")).toHaveCount(80);
    await expect(table.getByRole("row")).toHaveCount(81);
    await expect(page.getByRole("button", { name: "Вернуть компактный вид" })).toHaveAttribute("aria-pressed", "true");
  });
}

test("все 28 маршрутов открываются напрямую с русскими заголовками", async ({ page }) => {
  await installAdminApiMock(page);

  for (const [path, label] of routes) {
    await page.goto(path);
    const main = page.getByRole("main");
    await expect(main).toBeVisible();
    await expect(page.getByRole("heading", { name: label, exact: true, level: 1 })).toBeVisible();
    await expect(main.locator(".ops-route-toolbar")).toHaveCount(1);
    await expect(main.getByText("Ops admin", { exact: true })).toHaveCount(0);
    await expect(main.getByText("Free tier", { exact: true })).toHaveCount(0);
    const viewport = await page.evaluate(() => ({
      documentWidth: document.documentElement.scrollWidth,
      viewportWidth: window.innerWidth
    }));
    expect(viewport.documentWidth, `общий горизонтальный скролл на ${path}`).toBeLessThanOrEqual(viewport.viewportWidth + 1);
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

  for (const width of [768, 1280, 1440]) {
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
    const clippedNavigation = await page.locator('aside nav[aria-label="Рабочие области центра управления"]').evaluate((navigation) =>
      Array.from(navigation.querySelectorAll("a"))
        .filter((link) => {
          const rect = link.getBoundingClientRect();
          return rect.left < 0 || rect.right > window.innerWidth + 1;
        })
        .map((link) => link.getAttribute("aria-label") || link.textContent?.trim() || "")
    );
    expect(clippedNavigation, `скрытые разделы при ширине ${width}`).toEqual([]);
  }
});

test("reflow при имитации 200% zoom сохраняет таблицу и клавиатурный диалог", async ({ page }) => {
  await installAdminApiMock(page, { longTables: true, revenueScenario: "populated" });
  // 1440x900 physical pixels at 200% browser zoom give a 720x450 CSS viewport.
  // This checks reflow; it is not manual browser-zoom or screen-reader evidence.
  await page.setViewportSize({ width: 720, height: 450 });
  await page.goto("/payments");
  const viewport = page.getByRole("region", { name: "Табличные данные: прокрутка", exact: true });
  await expect(viewport).toBeVisible();
  await viewport.focus();
  await page.keyboard.press("End");
  await expect(viewport.locator('tr[aria-rowindex="81"]')).toBeInViewport();
  await page.keyboard.press("Control+k");
  const dialog = page.getByRole("dialog", { name: "Палитра команд" });
  await expect(dialog.getByRole("searchbox", { name: "Глобальный поиск" })).toBeFocused();
  const geometry = await page.evaluate(() => ({ width: document.documentElement.scrollWidth, viewport: innerWidth }));
  expect(geometry.width).toBeLessThanOrEqual(geometry.viewport + 1);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(viewport).toBeFocused();
});
