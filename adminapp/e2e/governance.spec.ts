import { expect, test } from "@playwright/test";

import { installAdminApiMock } from "./fixtures/admin-api";

test("Governance: роли, audit, sensitive log и retention читаются из v2 authority", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/governance");

  await expect(page.getByRole("heading", { name: "Управление системой", level: 1 })).toBeVisible();
  await expect(page.getByText("owner", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("superadmin", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("Без токенов и CSRF в read model", { exact: true })).toBeVisible();

  await page.getByRole("tab", { name: "Аудит и команды" }).click();
  await expect(page.getByText("session.bootstrap", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "CSV до 1000 строк" })).toBeVisible();

  await page.getByRole("tab", { name: "Чувствительный доступ" }).click();
  await expect(page.getByRole("heading", { name: "Sensitive-access log" })).toBeVisible();
  await expect(page.getByText("Доступов не было", { exact: true })).toBeVisible();

  await page.getByRole("tab", { name: "Privacy и retention" }).click();
  await expect(page.getByText("90 дней", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Deletion / anonymization" })).toBeVisible();
  await expect(page.getByText("72 ч", { exact: true })).toBeVisible();
  await expect(page.getByText("Cleanup backlog", { exact: true })).toBeVisible();
  await expect(page.getByText("Не выдаём: token · token_hash · csrf", { exact: true })).toBeVisible();

  const calls = api.calls.map((call) => call.path);
  expect(calls).toContain("/api/admin/v2/governance/roles");
  expect(calls).toContain("/api/admin/v2/governance/operators?limit=200");
  expect(calls).toContain("/api/admin/v2/governance/audit?limit=100");
  expect(calls).toContain("/api/admin/v2/governance/privacy");
  expect(calls).toContain("/api/admin/v2/governance/sensitive-access?limit=100");
  expect(calls).not.toContain("/api/admin/v2/auth/sessions");
});

test("Governance: выдача роли использует только guarded action-intent", async ({ page }) => {
  const api = await installAdminApiMock(page);
  await page.goto("/governance");

  await page.getByLabel("Тип выдачи").selectOption("jit");
  await page.getByLabel("Срок, минут").fill("30");
  await page.getByRole("button", { name: "Подготовить выдачу" }).click();

  const dialog = page.getByRole("dialog", { name: "Проверка действия" });
  await expect(dialog).toContainText("Сервер связал изменение с operator/role/session snapshot.");
  await dialog.getByLabel("Подтверждение").fill("00000000-0000-4000-8000-000000000999");
  await dialog.getByRole("button", { name: "Выполнить" }).click();
  await expect(dialog.getByText("ID аудита: 721", { exact: true })).toBeVisible();

  const prepared = api.calls.find((call) => call.path === "/api/admin/v2/governance/action-intents");
  expect(prepared?.body).toMatchObject({
    action: "operator.role.grant",
    target: { type: "operator", id: "00000000-0000-4000-8000-000000000999" },
    payload: { role_code: "readonly", grant_kind: "jit" },
  });
  const executed = api.calls.find((call) => call.path.startsWith("/api/admin/v2/governance/action-intents/") && call.path.endsWith("/execute"));
  expect(executed?.headers?.["x-admin-idempotency-key"]).toBeTruthy();
  expect(executed?.headers?.["x-admin-confirmation-sha256"]).toMatch(/^[0-9a-f]{64}$/);
});
