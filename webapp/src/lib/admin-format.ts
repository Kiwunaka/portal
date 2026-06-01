export function formatRub(value?: number | null): string {
  if (value == null || Number.isNaN(Number(value))) return "0 ₽";
  return `${new Intl.NumberFormat("ru-RU").format(Math.round(Number(value)))} ₽`;
}

export function formatRuDateTime(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

export function formatShortAge(seconds?: number | null): string {
  if (seconds == null || Number.isNaN(Number(seconds))) return "нет данных";
  const total = Math.max(0, Math.round(Number(seconds)));
  if (total < 60) return `${total} с`;
  if (total < 3600) return `${Math.round(total / 60)} мин`;
  if (total < 86400) return `${Math.round(total / 3600)} ч`;
  return `${Math.round(total / 86400)} д`;
}
