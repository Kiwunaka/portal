import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

test("прямая ссылка на пользователя загружает карточку, а IP — только расследование", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/users?selected=1001&tab=overview");

  await expect(page.getByRole("heading", { name: "Пользователь 1001" })).toBeVisible();
  await expect(page.getByText("Снимок панели неполный", { exact: true })).toBeVisible();
  await expect(page.getByText("Нет данных", { exact: true }).first()).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/users/1001")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/support/users/1001")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/users/1001/investigation")).toBe(false);
  await expect(page.getByText("203.0.113.44", { exact: true })).toHaveCount(0);

  await page.getByRole("tab", { name: "События приложения" }).click();
  await expect(page).toHaveURL(/selected=1001.*tab=events/);
  await expect(page.getByText("Core не запустился", { exact: true })).toBeVisible();
  await expect(page.getByText(/desktop_tun_start_failed/)).toBeVisible();
  await expect(page.getByText("windows · v1.1.5+28", { exact: true })).toBeVisible();
  await expect(page.getByText("Сгруппированные попытки", { exact: true })).toBeVisible();
  await expect(page.getByText("Исходная сеть устройства", { exact: true })).toBeVisible();
  await expect(page.getByText("203.0.113.77", { exact: true })).toBeVisible();
  await expect(page.getByText("RU · Fixture region", { exact: true })).toBeVisible();
  const offlineNetwork = page.getByRole("row").filter({ hasText: "Offline carrier" });
  await expect(offlineNetwork.getByRole("cell", { name: "Неизвестен", exact: true })).toHaveCount(2);
  await expect(page.getByText("attempt_11111111111111111111", { exact: true })).toBeVisible();
  await expect(page.getByText("raw-session-secret", { exact: true })).toHaveCount(0);

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
  expect(api.calls.some((call) => call.path === "/api/admin/v2/support/online?limit=200")).toBe(true);
  expect(api.calls.some((call) => call.path.includes("investigation"))).toBe(false);
});

test("прямая ссылка на тикет лениво загружает полную переписку", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/tickets?status=open&priority=high&selected=501");

  await expect(page.getByRole("heading", { name: "Тикет #501" })).toBeVisible();
  await expect(page.getByText("Уточните платформу", { exact: true })).toBeVisible();
  await expect(page.getByText("Проверить Windows TUN", { exact: true })).toBeVisible();
  await expect(page.getByText("SLA: под риском", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Скачать вложение" })).toBeVisible();
  await expect(page.getByRole("list", { name: "Timeline обращения" })).toBeVisible();
  for (const fact of ["Разрешения", "Core", "TUN", "DNS", "Egress"]) {
    await expect(page.getByText(fact, { exact: true })).toBeVisible();
  }
  await expect(page.getByText("Core не запускается после обновления", { exact: true })).toBeVisible();
  expect(api.calls.some((call) => call.path === "/api/admin/v2/support/tickets?status=open&priority=high&limit=100")).toBe(true);
  expect(api.calls.some((call) => call.path === "/api/admin/v2/support/tickets/501")).toBe(true);
  expect(api.calls.some((call) => call.path.startsWith("/api/admin/v2/support/attempts?ticket_id=501"))).toBe(true);
});

test("L1 видит явную редактированную область вместо ложного пустого состояния", async ({ page }) => {
  await installAdminApiMock(page, {
    operatorPermissions: ["system.meta.read", "session.self.read", "support.read", "support.write"],
    redactUserFields: true,
  });
  await page.goto("/users?selected=1001&tab=overview");

  await expect(page.getByText("Привязанный Telegram, установка и устройство не показаны текущей роли.")).toBeVisible();
  await expect(page.getByText("Устаревшие команды карточки недоступны этой роли; профильные операции выполняются через рабочее место тикетов.")).toBeVisible();
  await expect(page.getByText("Сбросить trial")).toHaveCount(0);

  await page.getByRole("tab", { name: "События приложения" }).click();
  await expect(page.getByText("Установки, сессии, попытки и события приложения относятся к чувствительной диагностике.")).toBeVisible();
  await expect(page.getByText("203.0.113.77", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Событий приложения нет.")).toHaveCount(0);

  await page.getByRole("tab", { name: "Платежи" }).click();
  await expect(page.getByText("Платёжные заказы пользователя недоступны текущей роли.")).toBeVisible();
  await expect(page.getByText("Платежей пользователя нет.")).toHaveCount(0);

  await page.getByRole("tab", { name: "Аудит" }).click();
  await expect(page.getByText("История действий администраторов скрыта текущей роли.")).toBeVisible();
});

test("сводка обращения не подменяет отсутствующую связанную попытку", async ({ page }) => {
  await installAdminApiMock(page, { supportScenario: "missing_linked_attempt" });
  await page.goto("/tickets?selected=501");

  await expect(page.getByRole("heading", { name: "Тикет #501" })).toBeVisible();
  await expect(page.getByText("Связанная попытка отсутствует в доступных данных.", { exact: true })).toBeVisible();
  await expect(page.getByText("Сводка выбранной попытки", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Сводка связанной попытки", { exact: true })).toHaveCount(0);
  await expect(page.getByText("attempt_11111111111111111111", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Связать с тикетом", exact: true })).toBeVisible();
});

test("обновление сборки пакета пересверяет known issue без смены кода ошибки", async ({ page }) => {
  const api = await installAdminApiMock(page, { supportScenario: "bundle_build_changes" });
  await page.goto("/tickets?selected=501");
  await expect(page.getByText("Core не запускается после обновления", { exact: true })).toBeVisible();

  await page.getByRole("main").getByRole("button", { name: "Обновить", exact: true }).click();
  await expect(page.getByText("windows · 1.2.0 · 43", { exact: true }).last()).toBeVisible();
  await expect.poll(() => api.calls.some((call) => call.path.startsWith("/api/admin/v2/support/known-issues?") && call.path.includes("build_number=43"))).toBe(true);
  await expect(page.getByText("Core не запускается после обновления", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Для текущего кода и версии известная проблема не зарегистрирована.", { exact: true })).toBeVisible();
  await expect(page.getByText("windows · 1.2.0 · 42", { exact: true })).toBeVisible();
});

test("L2 скачивает только шифротекст через обоснованный одноразовый grant", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/tickets?selected=501");
  await expect(page.getByRole("heading", { name: "Тикет #501" })).toBeVisible();

  await page.getByLabel("Причина доступа к bundle_22222222222222222222").selectOption("incident_review");
  await page.getByRole("button", { name: "Скачать шифротекст" }).click();

  await expect.poll(() => api.calls.filter((call) => call.path.endsWith("/access-grants")).length).toBe(1);
  await expect.poll(() => api.calls.filter((call) => call.path.endsWith("/content")).length).toBe(1);
  const grant = api.calls.find((call) => call.path.endsWith("/access-grants"));
  const content = api.calls.find((call) => call.path.endsWith("/content"));
  expect(grant?.body).toEqual({ reason_code: "incident_review" });
  expect(content?.headers?.["x-pokrov-support-grant"]).toBe("grant_333333333333333333333333333333333333");
});

test("L1 видит безопасную сводку пакета без download-контрола", async ({ page }) => {
  await installAdminApiMock(page, {
    operatorPermissions: ["system.meta.read", "session.self.read", "support.read", "support.write"]
  });
  await page.goto("/tickets?selected=501");

  await expect(page.getByText("bundle_22222222222222222222", { exact: true })).toBeVisible();
  await expect(page.getByText(/L1 видит только безопасную сводку/)).toBeVisible();
  await expect(page.getByRole("button", { name: "Скачать шифротекст" })).toHaveCount(0);
});

test("Support Inbox claim и внутренняя заметка используют guarded intent и optimistic version", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/tickets?selected=501");
  await expect(page.getByRole("heading", { name: "Тикет #501" })).toBeVisible();

  await page.getByRole("button", { name: "Взять в работу" }).click();
  let dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("Действие выполнено", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Закрыть", exact: true }).click();

  await page.getByPlaceholder("Зафиксируйте ход разбора без секретов и сырых сетевых данных").fill("Проверить корреляцию CORE-001");
  await page.getByRole("button", { name: "Добавить заметку" }).click();
  dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("Действие выполнено", { exact: true })).toBeVisible();

  expect(api.calls.some((call) => call.path === "/api/admin/v2/support/action-intents")).toBe(true);
  expect(api.calls.some((call) => /^\/api\/admin\/v2\/support\/action-intents\/[0-9a-f-]{36}\/execute$/.test(call.path))).toBe(true);
  const note = api.calls.find((call) => call.path.endsWith("/execute") && (call.body as { action?: string })?.action === "ticket.note");
  expect(note?.path).toMatch(/^\/api\/admin\/v2\/support\/action-intents\/[0-9a-f-]{36}\/execute$/);
  expect(note?.body).toMatchObject({ payload: { expected_version: 3 } });
  expect(api.calls.some((call) => call.path === "/api/admin/tickets/501/note")).toBe(false);
});

test("пакет связывается с выбранной попыткой через support intent", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/tickets?selected=501");
  const save = page.getByRole("button", { name: "Сохранить связь", exact: true });
  await expect(save).toBeDisabled();
  await page.getByLabel("Попытка для bundle_22222222222222222222").selectOption("attempt_11111111111111111111");
  await save.click();
  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("ПОДТВЕРДИТЬ");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("Действие выполнено", { exact: true })).toBeVisible();
  const command = api.calls.find((call) => call.path.endsWith("/execute"));
  expect(command?.path).toMatch(/^\/api\/admin\/v2\/support\/action-intents\/[0-9a-f-]{36}\/execute$/);
  expect(command?.body).toMatchObject({ action: "ticket.update", payload: {
    expected_version: 3, bundle_ref: "bundle_22222222222222222222", attempt_ref: "attempt_11111111111111111111",
  } });
});

test("блокировка и ответ проходят через намерение, а неясный ответ сохраняет черновик", async ({ page }) => {
  const api = await installAdminApiMock(page, { ticketReplyOutcomes: ["uncertain"] });
  await page.goto("/users?selected=1001");

  await page.getByRole("button", { name: "Заблокировать" }).click();
  let dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await dialog.getByLabel("Подтверждение").fill("1001");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("Действие выполнено", { exact: true })).toBeVisible();
  await dialog.getByRole("button", { name: "Закрыть", exact: true }).click();

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
