"use client";

export type TelegramOidcCallbackParams = {
  code?: string;
  state?: string;
  error?: string;
  errorDescription?: string;
};

const CALLBACK_KEYS = ["code", "state", "error", "error_description"] as const;

export function readTelegramOidcCallback(): TelegramOidcCallbackParams | null {
  if (typeof window === "undefined") return null;
  try {
    const current = new URL(window.location.href);
    const code = String(current.searchParams.get("code") || "").trim();
    const state = String(current.searchParams.get("state") || "").trim();
    const error = String(current.searchParams.get("error") || "").trim();
    const errorDescription = String(current.searchParams.get("error_description") || "").trim();
    if (!code && !state && !error && !errorDescription) return null;
    return {
      code: code || undefined,
      state: state || undefined,
      error: error || undefined,
      errorDescription: errorDescription || undefined,
    };
  } catch {
    return null;
  }
}

export function clearTelegramOidcCallback(): void {
  if (typeof window === "undefined") return;
  try {
    const current = new URL(window.location.href);
    for (const key of CALLBACK_KEYS) {
      current.searchParams.delete(key);
    }
    const next = `${current.pathname}${current.search}${current.hash}`;
    window.history.replaceState({}, "", next || "/");
  } catch {
    // ignore malformed URL state
  }
}

export function describeTelegramOidcError(params: TelegramOidcCallbackParams): string {
  const code = String(params.error || "").trim();
  const description = String(params.errorDescription || "").trim();
  if (description) return description;
  if (code === "access_denied") {
    return "Вход через Telegram был отменён.";
  }
  if (code) {
    return `Telegram вернул ошибку авторизации: ${code}`;
  }
  return "Не удалось завершить вход через Telegram.";
}
