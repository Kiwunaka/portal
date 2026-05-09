import { expect, test } from "@playwright/test";

import { finishTelegramOidcLogin } from "../src/lib/api";
import {
  isTelegramAuthRefreshRequired,
  isTelegramWebLoginRefreshError,
  shouldRefreshTelegramWebLoginPayload,
  telegramAuthRefreshMessage,
} from "../src/lib/telegram-login-refresh";

test("flags stale Telegram widget payloads before the backend rejects them", () => {
  const now = 1_800_000;

  expect(
    shouldRefreshTelegramWebLoginPayload(
      {
        id: 1001,
        first_name: "Alice",
        username: "alice",
        auth_date: now - 86_400,
        hash: "redacted",
      },
      now,
    ),
  ).toBe(true);
});

test("keeps fresh Telegram widget payloads on the direct widget login path", () => {
  const now = 1_800_000;

  expect(
    shouldRefreshTelegramWebLoginPayload(
      {
        id: 1001,
        first_name: "Alice",
        username: "alice",
        auth_date: now - 300,
        hash: "redacted",
      },
      now,
    ),
  ).toBe(false);
});

test("treats expired or deprecated Telegram widget errors as refreshable auth", () => {
  expect(isTelegramWebLoginRefreshError("Сессия Telegram устарела. Нажмите вход через Telegram еще раз.")).toBe(true);
  expect(isTelegramWebLoginRefreshError("telegram login token is deprecated")).toBe(true);
  expect(isTelegramWebLoginRefreshError("Telegram login token has been deprecated")).toBe(true);
  expect(isTelegramWebLoginRefreshError("telegram_login_invalid")).toBe(true);
  expect(isTelegramWebLoginRefreshError("Invalid password")).toBe(false);
});

test("treats deprecated Telegram session API errors as reauth instead of a generic cabinet error", () => {
  expect(isTelegramAuthRefreshRequired("telegram_login_deprecated")).toBe(true);
  expect(isTelegramAuthRefreshRequired("Telegram init data is deprecated")).toBe(true);
  expect(isTelegramAuthRefreshRequired("Telegram auth required: repeat login")).toBe(true);
  expect(isTelegramAuthRefreshRequired("Network timeout")).toBe(false);
});

test("maps raw Telegram deprecated errors to a human reauth CTA", () => {
  expect(telegramAuthRefreshMessage("telegram_login_deprecated")).toBe(
    "Вход устарел. Нажмите вход через Telegram еще раз, и мы вернем вас в кабинет.",
  );
  expect(telegramAuthRefreshMessage("telegram_init_invalid")).toBe(
    "Вход устарел. Нажмите вход через Telegram еще раз, и мы вернем вас в кабинет.",
  );
  expect(telegramAuthRefreshMessage("web_session_expired")).toBe(
    "Вход устарел. Нажмите вход через Telegram еще раз, и мы вернем вас в кабинет.",
  );
  expect(telegramAuthRefreshMessage("Сессия Telegram устарела. Нажмите вход через Telegram еще раз.")).toBe(
    "Сессия Telegram устарела. Нажмите вход через Telegram еще раз.",
  );
});

test("keeps Telegram OIDC auth error codes from API headers for refresh handling", async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (async () =>
    new Response(JSON.stringify({ detail: "Invalid Telegram OAuth state" }), {
      status: 401,
      headers: {
        "content-type": "application/json",
        "x-pokrov-auth-error": "telegram_oidc_state_expired",
      },
    })) as typeof fetch;

  try {
    await expect(finishTelegramOidcLogin({ code: "old-code", state: "old-state" })).rejects.toThrow(
      /telegram_oidc_state_expired/,
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
