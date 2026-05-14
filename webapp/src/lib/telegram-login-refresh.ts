import type { TelegramWebLoginPayload } from "./api";

const DEFAULT_REFRESH_AGE_SECONDS = 23 * 60 * 60;
const DEFAULT_REAUTH_MESSAGE = "Вход устарел. Нажмите вход через Telegram еще раз, и мы вернем вас в кабинет.";

function refreshAgeSeconds(): number {
  const raw = Number(
    process.env.NEXT_PUBLIC_TELEGRAM_WEB_LOGIN_REFRESH_AGE_SECONDS ||
      process.env.VITE_TELEGRAM_WEB_LOGIN_REFRESH_AGE_SECONDS ||
      DEFAULT_REFRESH_AGE_SECONDS,
  );
  if (!Number.isFinite(raw) || raw <= 60) return DEFAULT_REFRESH_AGE_SECONDS;
  return Math.floor(raw);
}

export function shouldRefreshTelegramWebLoginPayload(
  payload: Pick<TelegramWebLoginPayload, "auth_date"> | null | undefined,
  nowSeconds = Math.floor(Date.now() / 1000),
): boolean {
  const authDate = Number(payload?.auth_date || 0);
  if (!Number.isFinite(authDate) || authDate <= 0) return true;
  return nowSeconds - authDate >= refreshAgeSeconds();
}

export function isTelegramWebLoginRefreshError(error: unknown): boolean {
  const message = String(error instanceof Error ? error.message : error || "").toLowerCase();
  return (
    message.includes("telegram_login_expired") ||
    message.includes("telegram login expired") ||
    message.includes("telegram_login_deprecated") ||
    message.includes("telegram_login_invalid") ||
    message.includes("telegram token is deprecated") ||
    message.includes("token is deprecated") ||
    message.includes("deprecated token") ||
    message.includes("сессия telegram устарела") ||
    (message.includes("telegram") &&
      (message.includes("deprecated") ||
        message.includes("expired") ||
        message.includes("устарел") ||
        message.includes("повторите вход")))
  );
}

export function isTelegramAuthRefreshRequired(error: unknown): boolean {
  const message = String(error instanceof Error ? error.message : error || "").toLowerCase();
  if (isTelegramWebLoginRefreshError(message)) return true;
  return (
    message.includes("telegram auth required") ||
    message.includes("invalid telegram signature") ||
    message.includes("telegram_init_invalid") ||
    message.includes("telegram_login_invalid") ||
    message.includes("telegram_oidc_state_expired") ||
    message.includes("telegram_oidc_invalid") ||
    message.includes("web_session_expired") ||
    message.includes("web_session_invalid") ||
    message.includes("повторите вход") ||
    message.includes("обновите вход") ||
    (message.includes("telegram") &&
      (message.includes("deprecated") || message.includes("expired") || message.includes("устарел")))
  );
}

export function telegramAuthRefreshMessage(error: unknown): string {
  const message = String(error instanceof Error ? error.message : error || "").trim();
  if (!message) return DEFAULT_REAUTH_MESSAGE;
  if (isTelegramAuthRefreshRequired(message)) {
    const technicalRemainder = message.replace(/\b(Telegram|POKROV|email)\b/gi, "");
    const looksHumanRussian = /[А-Яа-яЁё]/.test(message) && !/[a-z_]{3,}/i.test(technicalRemainder);
    return looksHumanRussian ? message : DEFAULT_REAUTH_MESSAGE;
  }
  return message;
}
