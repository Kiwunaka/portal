const TECHNICAL_ERROR_RE =
  /api error|http\s+\d+|failed to fetch|networkerror|received app shell|invalid api json|request timed out|request aborted|traceback|stack/i;

function rawErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String((error as { message?: unknown })?.message || error || "").trim();
}

export function userFacingErrorMessage(error: unknown, fallback: string): string {
  const message = rawErrorMessage(error);
  const lower = message.toLowerCase();

  if (lower.includes("access key already redeemed") || lower.includes("already_redeemed")) {
    return "Код уже был использован. Для восстановления лучше открыть поддержку.";
  }
  if (lower.includes("you cannot redeem your own key") || lower.includes("self_redeem")) {
    return "Этот код выпущен для передачи другому человеку. Свой код активировать не нужно.";
  }
  if (lower.includes("accept terms before redeeming") || lower.includes("tos_required")) {
    return "Сначала примите условия в кабинете, потом активируйте код.";
  }
  if (lower.includes("access key not found") || lower.includes("not_found")) {
    return "Такой код не найден. Проверьте, не потерялся ли символ.";
  }
  if (lower.includes("attachment too large") || lower.includes("file too large")) {
    return "Файл больше 20 МБ. Уменьшите вложение или отправьте его в Telegram-поддержку.";
  }
  if (lower.includes("already claimed")) {
    return "Бонус уже был добавлен раньше.";
  }
  if (lower.includes("not subscribed") || lower.includes("subscriber")) {
    return "Подписка пока не подтверждена. Откройте канал и попробуйте еще раз.";
  }
  if (lower.includes("auth") || lower.includes("unauthorized") || lower.includes("forbidden")) {
    return "Сессия устарела. Обновите вход и попробуйте еще раз.";
  }
  if (!message || !/[А-Яа-яЁё]/.test(message)) return fallback;
  if (TECHNICAL_ERROR_RE.test(message)) return fallback;
  return message;
}
