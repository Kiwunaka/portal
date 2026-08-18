"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, BellOff, Check, CircleCheck, ExternalLink, RefreshCw, ShieldAlert } from "lucide-react";

import { MISSING_DATA_TEXT, MissingData } from "@/components/ops/missing-data";
import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, EmptyState, ErrorState, MetricCell, MetricStrip, SectionTitle, type Tone } from "@/components/ui";
import { AdminApiError } from "@/lib/admin-api/client";
import { acknowledgeAlert, fetchNetworkAlerts, silenceAlert, type NetworkAlert } from "@/lib/admin-api/network";
import { useRouteResource } from "@/lib/use-route-resource";
import { pushUrlState, readUrlState, replaceUrlState, subscribeToUrlState, urlCodecs } from "@/lib/url-state";

type AlertStatus = "active" | "all" | "resolved";
type AlertsUrlState = { status: AlertStatus; selected: number | null };

const ALERTS_URL_CODECS = {
  status: urlCodecs.enum(["active", "all", "resolved"] as const, "active"),
  selected: urlCodecs.number(null),
};

const SOURCE_LABELS: Record<string, string> = {
  node_metrics: "Метрики ноды",
  node_capacity: "Ёмкость ноды",
  provider_quota: "Лимит провайдера",
  free_tier: "Архив FREE",
  security: "Безопасность",
  ru_probe: "RU-origin",
};

function tone(value: string): Tone {
  const normalized = value.toLowerCase();
  if (normalized === "critical") return "danger";
  if (normalized === "warning" || normalized === "silenced") return "warning";
  if (normalized === "resolved") return "success";
  return "neutral";
}

function severityLabel(value: string): string {
  const normalized = value.toLowerCase();
  if (normalized === "critical") return "Критично";
  if (normalized === "warning") return "Внимание";
  if (normalized === "info") return "Информация";
  return value || MISSING_DATA_TEXT;
}

function statusLabel(value: string): string {
  return { active: "Активен", silenced: "Приглушён", resolved: "Закрыт" }[value.toLowerCase()] || value || MISSING_DATA_TEXT;
}

function dateText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return "—";
  return new Date(value).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function ageText(value: string | null): string {
  if (!value || Number.isNaN(Date.parse(value))) return MISSING_DATA_TEXT;
  const seconds = Math.max(0, Math.floor((Date.now() - Date.parse(value)) / 1000));
  if (seconds < 60) return "только что";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} мин назад`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} ч назад`;
  return `${Math.floor(seconds / 86400)} дн назад`;
}

function durationText(first: string | null, last: string | null): string {
  if (!first || !last || Number.isNaN(Date.parse(first)) || Number.isNaN(Date.parse(last))) return MISSING_DATA_TEXT;
  const minutes = Math.max(0, Math.floor((Date.parse(last) - Date.parse(first)) / 60_000));
  if (minutes < 60) return `${minutes} мин`;
  const hours = Math.floor(minutes / 60);
  return hours < 24 ? `${hours} ч ${minutes % 60} мин` : `${Math.floor(hours / 24)} дн ${hours % 24} ч`;
}

function entityHref(alert: NetworkAlert): { href: string; label: string } | null {
  if (alert.tg_id !== null) return { href: `/users?selected=${encodeURIComponent(String(alert.tg_id))}`, label: `Открыть пользователя ${alert.tg_id}` };
  if (alert.source === "provider_quota" && alert.node_code) return { href: `/provider-caps?selected=${encodeURIComponent(alert.node_code)}`, label: `Открыть лимит ${alert.node_code.toUpperCase()}` };
  if (alert.node_code) return { href: `/nodes?selected=${encodeURIComponent(alert.node_code)}`, label: `Открыть ноду ${alert.node_code.toUpperCase()}` };
  if (alert.source === "free_tier") return { href: "/free-tier", label: "Открыть архив FREE" };
  return null;
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

export function AlertsPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const [urlState, setUrlState] = useState<AlertsUrlState>(() => readUrlState(ALERTS_URL_CODECS));
  const [actionId, setActionId] = useState<number | null>(null);
  const [actionError, setActionError] = useState("");
  useEffect(() => subscribeToUrlState<AlertsUrlState>(ALERTS_URL_CODECS, setUrlState), []);

  const load = useCallback((signal: AbortSignal) => fetchNetworkAlerts(urlState.status, { signal }), [urlState.status]);
  const resource = useRouteResource(`alerts:${urlState.status}`, load, { enabled: true, pollMs: 60_000 });
  const alerts = useMemo(() => [...(resource.data?.alerts || [])].sort((left, right) => {
    const rank = (value: string) => value.toLowerCase() === "critical" ? 2 : value.toLowerCase() === "warning" ? 1 : 0;
    return rank(right.severity) - rank(left.severity) || Date.parse(left.first_seen_at || "9999-12-31") - Date.parse(right.first_seen_at || "9999-12-31");
  }), [resource.data]);
  const selected = alerts.find((alert) => alert.id === urlState.selected) || null;

  useEffect(() => {
    onShellStatus?.({
      api: resource.error ? resource.data ? "degraded" : "failed" : resource.loading ? "missing" : "ok",
      session: isAccessDenied(resource.error) ? "failed" : resource.data ? "ok" : resource.error ? "unavailable" : "missing",
      oldestRequiredSourceAt: alerts.map((alert) => alert.last_seen_at).filter((value): value is string => Boolean(value)).sort().at(0) || resource.data?.generated_at || null,
    });
  }, [alerts, onShellStatus, resource.data, resource.error, resource.loading]);

  const runAction = useCallback(async (alert: NetworkAlert, action: "ack" | "silence") => {
    setActionId(alert.id);
    setActionError("");
    try {
      if (action === "ack") await acknowledgeAlert(alert.id);
      else await silenceAlert(alert.id, 60);
      resource.reload();
    } catch (error) {
      setActionError(error instanceof AdminApiError
        ? adminApiErrorText(error, "Действие с алертом не выполнено.")
        : "Действие с алертом не выполнено.");
    } finally {
      setActionId(null);
    }
  }, [resource]);

  return (
    <div className="ops-page space-y-3">
      <div className="ops-route-toolbar">
        <div className="flex flex-wrap items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={resource.error ? "warning" : resource.data === null ? "neutral" : alerts.some((alert) => alert.severity === "critical") ? "danger" : "success"}>{resource.data === null ? resource.error ? "Данные алертов недоступны" : "Данные алертов ещё не получены" : alerts.length ? `В очереди: ${alerts.length}` : "Очередь пуста"}</Badge>
          <span>{resource.data?.generated_at ? `Снимок ${dateText(resource.data.generated_at)}` : "Снимок ещё не получен"}</span>
        </div>
        <div className="flex items-center gap-2">
          <select aria-label="Статус алертов" value={urlState.status} onChange={(event) => replaceUrlState<AlertsUrlState>({ status: event.target.value as AlertStatus, selected: null }, ALERTS_URL_CODECS)} className="min-h-10 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] px-3 text-xs outline-none focus:border-[color:var(--atlas-focus)]">
            <option value="active">Активные</option><option value="resolved">Закрытые</option><option value="all">Все</option>
          </select>
          <Button tone="secondary" disabled={resource.loading || resource.refreshing} onClick={resource.reload}><RefreshCw size={15} className={resource.refreshing ? "animate-spin" : ""} /> Обновить</Button>
        </div>
      </div>

      {actionError ? <ErrorState title="Действие не выполнено" description={actionError} className="min-h-0" /> : null}

      {resource.data ? (
        <MetricStrip label="Сводка очереди алертов">
          <MetricCell icon={<ShieldAlert aria-hidden="true" size={17} />} label="В текущем представлении" value={alerts.length} detail={urlState.status === "active" ? "Активные и приглушённые" : urlState.status === "resolved" ? "Закрытые" : "Все состояния"} tone={alerts.length ? "warning" : "success"} />
          <MetricCell icon={<AlertTriangle aria-hidden="true" size={17} />} label="Критичные" value={alerts.filter((alert) => alert.severity.toLowerCase() === "critical").length} detail="Сортируются первыми" tone={alerts.some((alert) => alert.severity.toLowerCase() === "critical") ? "danger" : "success"} />
          <MetricCell icon={<BellOff aria-hidden="true" size={17} />} label="Приглушённые" value={alerts.filter((alert) => alert.status.toLowerCase() === "silenced").length} detail="Не удалены из истории" tone="warning" />
          <MetricCell icon={<CircleCheck aria-hidden="true" size={17} />} label="Закрытые" value={alerts.filter((alert) => alert.status.toLowerCase() === "resolved").length} detail="В выбранном фильтре" tone="success" />
        </MetricStrip>
      ) : null}

      <div className="ops-workspace lg:grid-cols-[minmax(22rem,0.82fr)_minmax(20rem,1.18fr)]">
        <Card>
          <SectionTitle title="Очередь реакции" description="Критичные сигналы идут первыми. Подтверждение и приглушение — L1-действия с обычным аудитом, без action intent." />
          <RouteBoundary loading={resource.loading} refreshing={resource.refreshing} error={resource.error} hasData={resource.data !== null} retryLabel="Повторить загрузку алертов" onRetry={resource.reload}>
            {alerts.length ? <div className="divide-y divide-[color:var(--atlas-border)]">{alerts.map((alert) => (
              <article key={alert.id} className={`py-3 ${selected?.id === alert.id ? "bg-[color:var(--command-surface-raised)]" : ""}`}>
                <button aria-label={`Открыть алерт ${alert.id}`} className="w-full rounded-[var(--pokrov-radius-control)] p-1 text-left outline-none transition hover:bg-[color:var(--command-surface-raised)] focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)] active:translate-y-px" onClick={() => pushUrlState<AlertsUrlState>({ selected: alert.id }, ALERTS_URL_CODECS)}>
                  <div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2"><Badge tone={tone(alert.severity)}>{severityLabel(alert.severity)}</Badge><h3 className="text-sm font-semibold">{alert.title}</h3></div><Badge tone={tone(alert.status)}>{statusLabel(alert.status)}</Badge></div>
                  <p className="mt-2 line-clamp-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{alert.body || MISSING_DATA_TEXT}</p>
                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[11px] text-[color:var(--atlas-text-muted)]"><span>{SOURCE_LABELS[alert.source] || alert.source || MISSING_DATA_TEXT}</span><span>{ageText(alert.last_seen_at)}</span><span>Длительность: {durationText(alert.first_seen_at, alert.last_seen_at)}</span></div>
                </button>
              </article>
            ))}</div> : resource.data ? <EmptyState description="Активных алертов нет. Это состояние текущей серверной очереди." /> : null}
          </RouteBoundary>
        </Card>

        <aside aria-label="Детали алерта">
          <Card className="lg:sticky lg:top-20 xl:top-[7.75rem]">
            {!selected ? <EmptyState title="Выберите алерт" description="Детали, источник, возраст и действия откроются здесь." /> : (
              <div>
                <div className="flex flex-wrap items-center gap-2"><Badge tone={tone(selected.severity)}>{severityLabel(selected.severity)}</Badge><Badge tone={tone(selected.status)}>{statusLabel(selected.status)}</Badge></div>
                <h2 className="mt-3 text-lg font-semibold tracking-tight">{selected.title}</h2>
                <p className="mt-2 text-sm leading-6 text-[color:var(--atlas-text-soft)]">{selected.body || MISSING_DATA_TEXT}</p>
                <dl className="mt-4 divide-y divide-[color:var(--atlas-border)] text-xs">
                  <div className="flex justify-between gap-3 py-2"><dt>Источник</dt><dd className="font-semibold">{SOURCE_LABELS[selected.source] || selected.source || <MissingData inline />}</dd></div>
                  <div className="flex justify-between gap-3 py-2"><dt>Первый сигнал</dt><dd className="text-right font-semibold">{dateText(selected.first_seen_at)}<span className="block font-normal text-[color:var(--atlas-text-muted)]">{selected.first_seen_at ? ageText(selected.first_seen_at) : "Нет данных"}</span></dd></div>
                  <div className="flex justify-between gap-3 py-2"><dt>Последний сигнал</dt><dd className="text-right font-semibold">{dateText(selected.last_seen_at)}<span className="block font-normal text-[color:var(--atlas-text-muted)]">{selected.last_seen_at ? ageText(selected.last_seen_at) : "Нет данных"}</span></dd></div>
                  <div className="flex justify-between gap-3 py-2"><dt>Длительность</dt><dd className="font-semibold">{durationText(selected.first_seen_at, selected.last_seen_at)}</dd></div>
                </dl>
                {entityHref(selected) ? <a href={entityHref(selected)!.href} className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-[var(--pokrov-radius-control)] text-xs font-semibold text-[color:var(--atlas-primary)] outline-none hover:underline focus-visible:ring-2 focus-visible:ring-[color:var(--atlas-focus)]"><ExternalLink size={14} /> {entityHref(selected)!.label}</a> : <p className="mt-4 text-xs text-[color:var(--atlas-text-muted)]">Связанная сущность: — · Нет данных</p>}
                {selected.status !== "resolved" ? <div className="mt-4 flex flex-wrap gap-2"><Button tone="primary" disabled={actionId === selected.id} onClick={() => void runAction(selected, "ack")}><Check size={14} /> Подтвердить</Button><Button tone="secondary" disabled={actionId === selected.id} onClick={() => void runAction(selected, "silence")}><BellOff size={14} /> Приглушить на 1 час</Button></div> : null}
              </div>
            )}
          </Card>
        </aside>
      </div>
      {resource.error && resource.data ? <p className="text-xs text-[color:var(--atlas-text-soft)]">{adminApiErrorText(resource.error, "Повторите загрузку.")}</p> : null}
    </div>
  );
}
