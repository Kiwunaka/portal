import { Badge, Card, SectionTitle, type Tone } from "@/components/ui";
import type { OpsAlert } from "@/lib/admin-api/types";

export type ActionQueueItem = {
  id: string;
  title: string;
  detail: string | null;
  severity: string;
  affectedCount: number | null;
  sourceTimestamp: string | null;
  source: string | null;
};

const severityRank: Record<string, number> = {
  critical: 3,
  warning: 2,
  info: 1
};

function finiteCount(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function validTimestamp(value: unknown): string | null {
  if (typeof value !== "string" || !value.trim() || Number.isNaN(Date.parse(value))) return null;
  return value;
}

function compareOptionalNumberDescending(left: number | null, right: number | null): number {
  if (left === null && right === null) return 0;
  if (left === null) return 1;
  if (right === null) return -1;
  return right - left;
}

function compareOptionalTimestampAscending(left: string | null, right: string | null): number {
  if (left === null && right === null) return 0;
  if (left === null) return 1;
  if (right === null) return -1;
  return Date.parse(left) - Date.parse(right);
}

export function sortActionQueue(items: readonly ActionQueueItem[]): ActionQueueItem[] {
  return [...items].sort((left, right) => {
    const severity = (severityRank[right.severity.toLowerCase()] ?? 0) - (severityRank[left.severity.toLowerCase()] ?? 0);
    if (severity !== 0) return severity;
    const affected = compareOptionalNumberDescending(left.affectedCount, right.affectedCount);
    if (affected !== 0) return affected;
    const timestamp = compareOptionalTimestampAscending(left.sourceTimestamp, right.sourceTimestamp);
    if (timestamp !== 0) return timestamp;
    if (left.id === right.id) return 0;
    return left.id < right.id ? -1 : 1;
  });
}

export function actionQueueFromAlerts(alerts: readonly OpsAlert[]): ActionQueueItem[] {
  return sortActionQueue(alerts.map((alert) => ({
    id: String(alert.fingerprint || `alert-${alert.id}`),
    title: alert.title,
    detail: typeof alert.body === "string" && alert.body.trim() ? alert.body : null,
    severity: String(alert.severity || "info"),
    affectedCount: finiteCount(alert.affected_count),
    sourceTimestamp: validTimestamp(alert.last_seen_at) || validTimestamp(alert.first_seen_at),
    source: typeof alert.source === "string" && alert.source.trim() ? alert.source : null
  })));
}

function toneForSeverity(severity: string): Tone {
  if (severity.toLowerCase() === "critical") return "danger";
  if (severity.toLowerCase() === "warning") return "warning";
  return "info";
}

function severityLabel(severity: string): string {
  if (severity.toLowerCase() === "critical") return "Критично";
  if (severity.toLowerCase() === "warning") return "Внимание";
  return "Информация";
}

export function ActionQueue({ alerts, loading, refreshing }: { alerts: readonly OpsAlert[]; loading: boolean; refreshing: boolean }) {
  const items = actionQueueFromAlerts(alerts);

  return (
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <SectionTitle
          title="Требует реакции"
          description="Сначала критичные сигналы с наибольшим подтверждённым охватом; при равенстве — более ранний источник."
        />
        {refreshing ? <Badge tone="info">Обновляем</Badge> : null}
      </div>
      {loading && !items.length ? (
        <div role="status" className="text-sm text-[color:var(--atlas-text-soft)]">Загружаем активные сигналы…</div>
      ) : items.length ? (
        <div className="divide-y divide-[color:var(--atlas-border)]">
          {items.map((item) => (
            <article
              key={item.id}
              data-action-id={item.id}
              className="grid gap-2 py-3 md:grid-cols-[112px_minmax(0,1fr)_220px] md:items-center"
            >
              <Badge tone={toneForSeverity(item.severity)}>{severityLabel(item.severity)}</Badge>
              <div className="min-w-0">
                <h3 className="truncate text-sm font-semibold text-[color:var(--atlas-text)]">{item.title}</h3>
                <p className="truncate text-xs text-[color:var(--atlas-text-soft)]">{item.detail || "Описание не получено"}</p>
              </div>
              <div className="text-xs text-[color:var(--atlas-text-muted)] md:text-right">
                <div>Охват: {item.affectedCount === null ? "Нет данных" : new Intl.NumberFormat("ru-RU").format(item.affectedCount)}</div>
                <div>
                  {item.source || "Источник не указан"} · {item.sourceTimestamp ? <time dateTime={item.sourceTimestamp}>{new Date(item.sourceTimestamp).toLocaleString("ru-RU")}</time> : "Нет данных"}
                </div>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <div role="status" className="rounded-[var(--pokrov-radius-card)] border border-dashed border-[color:var(--atlas-border)] px-4 py-5 text-sm text-[color:var(--atlas-text-soft)]">
          Активных сигналов нет.
        </div>
      )}
    </Card>
  );
}
