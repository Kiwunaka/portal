export function formatGb(value: number | null | undefined): string {
  const n = Number(value || 0);
  if (n >= 1024) return `${(n / 1024).toFixed(2)} TB`;
  if (n >= 10) return `${n.toFixed(1)} GB`;
  return `${n.toFixed(2)} GB`;
}

export function formatPct(value: number | null | undefined): string {
  return `${Number(value || 0).toFixed(1)}%`;
}

export function formatInt(value: number | null | undefined): string {
  return new Intl.NumberFormat("ru-RU").format(Number(value || 0));
}

export function shortDateTime(value: string | null | undefined): string {
  if (!value) return "n/a";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}
