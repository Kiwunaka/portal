"use client";

import { useCallback, useEffect, useMemo } from "react";
import { RefreshCw } from "lucide-react";

import { adminApiErrorText, RouteBoundary } from "@/components/ops/route-boundary";
import type { OpsShellStatus } from "@/components/ops/shell-status";
import { Badge, Button, Card, SectionTitle, type Tone } from "@/components/ui";
import { ErrorState, EmptyState } from "@/components/ui/states";
import { SourceRow } from "@/components/ui/source-row";
import { AdminApiError } from "@/lib/admin-api/client";
import { fetchAlerts, fetchOpsOverview, fetchRuLatest, type RuLatestStatus } from "@/lib/admin-api/overview";
import type { OpsAlert, OpsOverview } from "@/lib/admin-api/types";
import type { OpsStatusCode } from "@/lib/ops-status/types";
import { useRouteResource } from "@/lib/use-route-resource";

import { ActionQueue } from "./action-queue";

const OVERVIEW_POLL_MS = 60_000;

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatCount(value: unknown): string {
  const number = finiteNumber(value);
  return number === null ? "Нет данных" : new Intl.NumberFormat("ru-RU").format(number);
}

function formatPercent(value: unknown): string {
  const number = finiteNumber(value);
  return number === null ? "Нет данных" : `${number.toFixed(1)}%`;
}

function formatPair(left: unknown, right: unknown): string {
  const first = finiteNumber(left);
  const second = finiteNumber(right);
  if (first === null || second === null) return "Нет данных";
  return `${formatCount(first)} / ${formatCount(second)}`;
}

function isAccessDenied(error: AdminApiError | null): boolean {
  return Boolean(error && (error.status === 401 || error.status === 403));
}

function metricsStatus(status: unknown): OpsStatusCode {
  const value = String(status || "").toLowerCase();
  if (["fresh", "ok", "healthy"].includes(value)) return "ok";
  if (["stale", "old"].includes(value)) return "stale";
  if (["failed", "error", "critical"].includes(value)) return "failed";
  if (["degraded", "warning"].includes(value)) return "degraded";
  if (["unavailable", "unavailable_probe_host"].includes(value)) return "unavailable";
  if (value === "blocked_by_access") return "BLOCKED_BY_ACCESS";
  return "missing";
}

function toneForState(status: unknown): Tone {
  const value = String(status || "").toLowerCase();
  if (["critical", "failed", "offline", "hard_reject"].includes(value)) return "danger";
  if (["warning", "degraded", "stale", "draining"].includes(value)) return "warning";
  if (["ok", "healthy", "fresh", "active"].includes(value)) return "success";
  return "neutral";
}

function CompactKpi({ label, value, detail, tone = "neutral" }: { label: string; value: string; detail: string; tone?: Tone }) {
  return (
    <Card className="min-h-32">
      <div className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">{label}</div>
      <div className="mt-3 text-2xl font-semibold tracking-tight text-[color:var(--atlas-text)]">{value}</div>
      <div className="mt-2"><Badge tone={tone}>{detail}</Badge></div>
    </Card>
  );
}

function NodeContour({ overview }: { overview: OpsOverview }) {
  const nodes = Array.isArray(overview.capacity?.nodes) ? overview.capacity.nodes : [];
  return (
    <Card>
      <SectionTitle title="Контур нод" description="Короткий health/capacity-срез из overview; подробная диагностика остаётся в разделе нод." />
      {nodes.length ? (
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {nodes.map((rawNode, index) => {
            const node = rawNode && typeof rawNode === "object" ? rawNode as Record<string, unknown> : {};
            const code = String(node.node_code || node.code || `node-${index + 1}`);
            const state = node.capacity_state || node.state || node.health_status;
            return (
              <article key={code} className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="truncate text-sm font-semibold">{code}</h3>
                  <Badge tone={toneForState(state)}>{state ? String(state) : "Нет данных"}</Badge>
                </div>
                <dl className="mt-3 grid grid-cols-2 gap-2 text-xs text-[color:var(--atlas-text-soft)]">
                  <div><dt>Здоровье</dt><dd className="font-semibold text-[color:var(--atlas-text)]">{formatCount(node.health_score)}</dd></div>
                  <div><dt>Ёмкость</dt><dd className="font-semibold text-[color:var(--atlas-text)]">{formatCount(node.capacity_score)}</dd></div>
                  <div><dt>Онлайн-ключи</dt><dd className="font-semibold text-[color:var(--atlas-text)]">{formatCount(node.online_keys_now)}</dd></div>
                  <div><dt>Свежесть, сек</dt><dd className="font-semibold text-[color:var(--atlas-text)]">{formatCount(node.freshness_age_seconds)}</dd></div>
                </dl>
              </article>
            );
          })}
        </div>
      ) : (
        <EmptyState description="Overview пока не вернул ноды. Откройте раздел «Ноды» для проверки источников." />
      )}
    </Card>
  );
}

function formatThreshold(seconds: number | null): string {
  if (seconds === null) return "Порог не получен от backend";
  if (seconds % 3600 === 0) return `Порог свежести: ${seconds / 3600} ч`;
  if (seconds % 60 === 0) return `Порог свежести: ${seconds / 60} мин`;
  return `Порог свежести: ${seconds} сек`;
}

const RU_REASON_TEXT: Record<string, string> = {
  current_ru_run: "Текущий пригодный запуск",
  eligible_run_stale: "Последний пригодный запуск устарел",
  eligible_run_missing: "Пригодный запуск ещё не получен",
  google_unavailable: "Среда RU-пробы недоступна",
  release_failed: "Обязательная RU-проверка завершилась сбоем",
  release_incomplete: "Последняя RU-проверка неполная",
  blocked_by_access: "Проверка заблокирована подтверждённым отсутствием доступа"
};

function ruReason(reasonCode: unknown): string {
  const code = String(reasonCode || "").trim();
  return RU_REASON_TEXT[code] || (code ? `Причина: ${code}` : "Причина не указана");
}

function FreshnessRows({
  overview,
  ruLatest,
  ruLoading,
  ruError
}: {
  overview: OpsOverview;
  ruLatest: RuLatestStatus | null;
  ruLoading: boolean;
  ruError: AdminApiError | null;
}) {
  const brainAge = finiteNumber(overview.metrics?.age_seconds);
  const metrics = overview.metrics as OpsOverview["metrics"] & {
    last_sample_at?: string | null;
    stale_after_seconds?: number | null;
  };
  const brainThreshold = finiteNumber(metrics.stale_after_seconds);
  const ruThreshold = finiteNumber(ruLatest?.threshold_seconds);
  const ruSampledAt = ruLatest?.sampled_at || ruLatest?.latest_eligible_run?.finished_at || null;
  const ruStatus: OpsStatusCode = ruError
    ? "unavailable"
    : ruLatest
      ? metricsStatus(ruLatest.status)
      : "missing";
  const ruDetail = ruError
    ? "Источник RU-origin не ответил"
    : ruLatest
      ? ruReason(ruLatest.reason_code)
      : ruLoading
        ? "Запрашиваем отдельный RU-снимок"
        : "Пригодный RU-снимок ещё не получен";
  return (
    <Card>
      <SectionTitle title="Свежесть контуров" description="Brain и RU-origin показаны раздельно: один источник не подтверждает другой." />
      <div className="overflow-hidden rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]">
        <SourceRow
          source="Brain-origin"
          status={metricsStatus(overview.metrics?.status)}
          sampledAt={metrics.last_sample_at || overview.generated_at || null}
          detail={brainAge === null ? null : `Возраст метрик: ${formatCount(brainAge)} сек`}
          threshold={formatThreshold(brainThreshold)}
        />
        <SourceRow
          source="RU-origin"
          status={ruStatus}
          sampledAt={ruSampledAt}
          detail={ruDetail}
          threshold={formatThreshold(ruThreshold)}
        />
      </div>
      <p className="mt-3 text-xs text-[color:var(--atlas-text-soft)]">
        Brain-origin показывает измерения control plane. RU-origin подтверждается только отдельной внешней пробой из РФ.
      </p>
    </Card>
  );
}

function RecentAdminEvents({ overview }: { overview: OpsOverview }) {
  const events = Array.isArray(overview.recent_admin_events) ? overview.recent_admin_events : [];
  return (
    <Card>
      <SectionTitle title="Недавние действия администраторов" description="Только события, пришедшие в текущем overview-снимке." />
      {events.length ? (
        <div className="divide-y divide-[color:var(--atlas-border)]">
          {events.slice(0, 8).map((event, index) => {
            const id = String(event.id || event.event_id || `event-${index + 1}`);
            const timestamp = typeof event.created_at === "string" ? event.created_at : typeof event.timestamp === "string" ? event.timestamp : null;
            return (
              <article key={id} className="grid gap-1 py-3 md:grid-cols-[180px_1fr_180px] md:items-center">
                <div className="text-xs text-[color:var(--atlas-text-muted)]">{timestamp ? <time dateTime={timestamp}>{new Date(timestamp).toLocaleString("ru-RU")}</time> : "Нет данных"}</div>
                <div className="text-sm font-semibold">{String(event.action || event.title || "Действие без названия")}</div>
                <div className="text-xs text-[color:var(--atlas-text-soft)] md:text-right">{event.actor ? String(event.actor) : "Автор не указан"}</div>
              </article>
            );
          })}
        </div>
      ) : (
        <EmptyState description="События ещё не получены в overview. Это не означает, что действий не было." />
      )}
    </Card>
  );
}

export function OverviewPage({ onShellStatus }: { onShellStatus?: (status: OpsShellStatus) => void }) {
  const loadOverview = useCallback((signal: AbortSignal) => fetchOpsOverview({ signal }), []);
  const loadAlerts = useCallback((signal: AbortSignal) => fetchAlerts("active", { signal }), []);
  const loadRuLatest = useCallback((signal: AbortSignal) => fetchRuLatest({ signal }), []);
  const overview = useRouteResource("overview", loadOverview, { pollMs: OVERVIEW_POLL_MS, enabled: true });
  const alerts = useRouteResource("overview-alerts", loadAlerts, { pollMs: OVERVIEW_POLL_MS, enabled: true });
  const ruLatest = useRouteResource("overview-ru-latest", loadRuLatest, { pollMs: OVERVIEW_POLL_MS, enabled: true });

  useEffect(() => {
    const successCount = Number(overview.data !== null) + Number(alerts.data !== null) + Number(ruLatest.data !== null);
    const errors = [overview.error, alerts.error, ruLatest.error].filter((error): error is AdminApiError => error !== null);
    const loading = overview.loading || alerts.loading || ruLatest.loading;
    const api = errors.length
      ? successCount > 0 ? "degraded" : "failed"
      : loading && successCount < 3 ? "missing" : "ok";
    const session = errors.some(isAccessDenied)
      ? "failed"
      : successCount > 0 ? "ok" : errors.length ? "unavailable" : "missing";
    const requiredSourceTimes = [
      overview.data?.generated_at,
      ruLatest.data?.sampled_at,
      ruLatest.data?.latest_eligible_run?.finished_at
    ].filter((value): value is string => Boolean(value)).sort();
    onShellStatus?.({
      api,
      session,
      oldestRequiredSourceAt: requiredSourceTimes.at(0) || null
    });
  }, [
    alerts.data,
    alerts.error,
    alerts.loading,
    onShellStatus,
    overview.data,
    overview.error,
    overview.loading,
    ruLatest.data,
    ruLatest.error,
    ruLatest.loading
  ]);

  const activeAlerts = useMemo<OpsAlert[]>(() => alerts.data ?? overview.data?.alerts?.active ?? [], [alerts.data, overview.data]);
  const overviewRefreshing = overview.refreshing;
  const alertsRefreshing = alerts.refreshing;
  const ruRefreshing = ruLatest.refreshing;
  const refreshing = overviewRefreshing || alertsRefreshing || ruRefreshing;
  const lastUpdated = [overview.updatedAt, alerts.updatedAt, ruLatest.updatedAt].filter((value): value is string => Boolean(value)).sort().at(0) || null;
  const hasSourceError = Boolean(overview.error || alerts.error || ruLatest.error);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs text-[color:var(--atlas-text-soft)]">
          <Badge tone={hasSourceError ? "warning" : "success"}>{hasSourceError ? "Есть сбой источника" : "Источники отвечают"}</Badge>
          <span>{lastUpdated ? `Обновлено ${new Date(lastUpdated).toLocaleString("ru-RU")}` : "Данные ещё не получены"}</span>
          {refreshing ? <Badge tone="info">Обновляем</Badge> : null}
        </div>
        <Button
          tone="secondary"
          disabled={overview.loading || alerts.loading || ruLatest.loading || refreshing}
          onClick={() => {
            overview.reload();
            alerts.reload();
            ruLatest.reload();
          }}
        >
          <RefreshCw size={15} className={refreshing ? "animate-spin" : ""} /> Обновить
        </Button>
      </div>

      <ActionQueue alerts={activeAlerts} loading={alerts.loading} refreshing={alertsRefreshing} />

      {alerts.error ? (
        <ErrorState
          title="Алерты не загрузились"
          description={`${adminApiErrorText(alerts.error, "Повторите запрос алертов.")} Остальные блоки overview сохранены.`}
          action={<Button tone="secondary" onClick={alerts.reload}>Повторить загрузку алертов</Button>}
          className="min-h-0"
        />
      ) : null}

      {ruLatest.error ? (
        <ErrorState
          title="RU-origin не загрузился"
          description={`${adminApiErrorText(ruLatest.error, "Повторите запрос RU-origin.")} Остальные блоки обзора сохранены.`}
          action={<Button tone="secondary" onClick={ruLatest.reload}>Повторить загрузку RU-origin</Button>}
          className="min-h-0"
        />
      ) : null}

      <RouteBoundary
        loading={overview.loading}
        refreshing={overviewRefreshing}
        error={overview.error}
        hasData={overview.data !== null}
        retryLabel="Повторить загрузку overview"
        onRetry={overview.reload}
      >
        {overview.data ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
              <CompactKpi label="Активные пользователи" value={formatCount(overview.data.summary?.users?.active)} detail="Текущий overview" tone="info" />
              <CompactKpi label="Открытые тикеты" value={formatCount(overview.data.summary?.tickets?.open)} detail="Требуют разбора" tone={finiteNumber(overview.data.summary?.tickets?.open) ? "warning" : "success"} />
              <CompactKpi label="Здоровые ноды" value={formatPair(overview.data.summary?.nodes?.healthy, overview.data.summary?.nodes?.total)} detail="Здоровые / всего" tone="success" />
              <CompactKpi label="Активные алерты" value={alerts.data === null ? formatCount(overview.data.alerts?.active_count) : formatCount(alerts.data.length)} detail="Отдельный источник" tone={activeAlerts.length ? "warning" : "success"} />
              <CompactKpi label="Бесплатный контур" value={formatPercent(overview.data.free_tier?.used_pct)} detail="Использовано лимита" tone={finiteNumber(overview.data.free_tier?.used_pct) !== null && Number(overview.data.free_tier.used_pct) >= 80 ? "warning" : "info"} />
              <CompactKpi label="Метрики Brain" value={finiteNumber(overview.data.metrics?.age_seconds) === null ? "Нет данных" : `${formatCount(overview.data.metrics.age_seconds)} сек`} detail="Возраст снимка" tone={toneForState(overview.data.metrics?.status)} />
            </div>
            <NodeContour overview={overview.data} />
            <FreshnessRows
              overview={overview.data}
              ruLatest={ruLatest.data}
              ruLoading={ruLatest.loading}
              ruError={ruLatest.error}
            />
            <RecentAdminEvents overview={overview.data} />
          </>
        ) : null}
      </RouteBoundary>
    </div>
  );
}
