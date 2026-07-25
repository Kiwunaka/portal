import { AlertCircle, CheckCircle2, ChevronRight, Clock3 } from "lucide-react";

import { Badge, Card, type Tone } from "@/components/ui";
import type { OpsAlert } from "@/lib/admin-api/types";

export type ActionQueueItem = {
  id: string;
  title: string;
  detail: string | null;
  severity: string;
  affectedCount: number | null;
  sourceTimestamp: string | null;
  source: string | null;
  nodeCode: string | null;
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
    source: typeof alert.source === "string" && alert.source.trim() ? alert.source : null,
    nodeCode: typeof alert.node_code === "string" && alert.node_code.trim() ? alert.node_code : null
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

export function ActionQueue({
  alerts,
  loading,
  refreshing,
  selectedId,
  onSelect
}: {
  alerts: readonly OpsAlert[];
  loading: boolean;
  refreshing: boolean;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
}) {
  const items = actionQueueFromAlerts(alerts);
  const criticalCount = items.filter((item) => item.severity.toLowerCase() === "critical").length;

  return (
    <Card className="overflow-hidden p-0 shadow-none xl:sticky xl:top-[7.75rem]">
      <div className="border-b border-[color:var(--atlas-border)] px-4 py-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[color:var(--atlas-text-muted)]">Лента инцидентов</div>
            <h2 className="mt-1 text-lg font-semibold tracking-tight text-[color:var(--atlas-text)]">Требует реакции</h2>
          </div>
          {refreshing ? <Badge tone="info">Обновляем</Badge> : <Badge tone={criticalCount ? "danger" : "neutral"}>{items.length}</Badge>}
        </div>
        <div className="mt-3 flex items-center gap-3 text-[11px] text-[color:var(--atlas-text-soft)]">
          <span className="font-semibold text-[color:var(--atlas-text)]">Активные {items.length}</span>
          <span>Критичные {criticalCount}</span>
        </div>
      </div>
      {loading && !items.length ? (
        <div role="status" className="px-4 py-6 text-sm text-[color:var(--atlas-text-soft)]">Загружаем активные сигналы…</div>
      ) : items.length ? (
        <div className="ops-scrollbar max-h-[min(46rem,calc(100dvh-14rem))] divide-y divide-[color:var(--atlas-border)] overflow-y-auto">
          {items.map((item) => (
            <article
              key={item.id}
              data-action-id={item.id}
              className="relative"
            >
              <button
                type="button"
                aria-label={`Открыть сигнал: ${item.title}`}
                aria-pressed={selectedId === item.id}
                onClick={() => onSelect?.(item.id)}
                className={`group w-full px-4 py-3.5 text-left outline-none transition focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[color:var(--atlas-focus)] ${
                  selectedId === item.id
                    ? "bg-[color:var(--pokrov-status-success-bg)] before:absolute before:inset-y-0 before:left-0 before:w-0.5 before:bg-[color:var(--atlas-primary)]"
                    : "hover:bg-[color:var(--command-surface-raised)]"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-[var(--pokrov-radius-card)] border ${
                    toneForSeverity(item.severity) === "danger"
                      ? "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]"
                      : "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)]"
                  }`}>
                    <AlertCircle aria-hidden="true" size={16} strokeWidth={1.8} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="line-clamp-2 text-sm font-semibold leading-5 text-[color:var(--atlas-text)]">{item.title}</h3>
                      <ChevronRight aria-hidden="true" className="mt-0.5 shrink-0 text-[color:var(--atlas-text-muted)] transition-transform group-hover:translate-x-0.5" size={16} strokeWidth={1.8} />
                    </div>
                    <p className="mt-1 line-clamp-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{item.detail || "Описание не получено"}</p>
                    <div className="mt-2 flex flex-wrap items-center gap-x-2 gap-y-1 text-[10px] text-[color:var(--atlas-text-muted)]">
                      <Badge tone={toneForSeverity(item.severity)} className="px-1.5 py-0.5">{severityLabel(item.severity)}</Badge>
                      {item.nodeCode ? <span className="font-mono uppercase">{item.nodeCode}</span> : null}
                      <span className="inline-flex items-center gap-1">
                        <CheckCircle2 aria-hidden="true" size={11} strokeWidth={1.8} />
                        Охват: {item.affectedCount === null ? "Нет данных" : new Intl.NumberFormat("ru-RU").format(item.affectedCount)}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock3 aria-hidden="true" size={11} strokeWidth={1.8} />
                        {item.sourceTimestamp ? <time dateTime={item.sourceTimestamp}>{new Date(item.sourceTimestamp).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</time> : "Нет данных"}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            </article>
          ))}
        </div>
      ) : (
        <div role="status" className="m-4 rounded-[var(--pokrov-radius-card)] border border-dashed border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] px-4 py-5">
          <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--atlas-status-success-text)]">
            <CheckCircle2 aria-hidden="true" size={17} strokeWidth={1.8} />
            Активных сигналов нет
          </div>
          <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Очередь пуста в текущем серверном снимке.</p>
        </div>
      )}
    </Card>
  );
}
