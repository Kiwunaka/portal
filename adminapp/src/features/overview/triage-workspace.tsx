"use client";

import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  CheckCircle2,
  RefreshCw,
  Server,
  ShieldCheck,
  Ticket,
  Users,
  type LucideIcon
} from "lucide-react";

import { Badge, Button, Card, EmptyState, Progress, type Tone } from "@/components/ui";
import { SourceRow } from "@/components/ui/source-row";
import { AdminApiError } from "@/lib/admin-api/client";
import type { RuLatestStatus } from "@/lib/admin-api/overview";
import type { OpsAlert, OpsOverview } from "@/lib/admin-api/types";
import type { OpsStatusCode } from "@/lib/ops-status/types";

import { ActionQueue } from "./action-queue";

const SOURCE_LABELS: Record<string, string> = {
  node_metrics: "Метрики ноды",
  node_capacity: "Ёмкость ноды",
  provider_quota: "Лимит провайдера",
  free_tier: "Бесплатный контур",
  security: "Безопасность",
  ru_probe: "RU-origin"
};

const RU_REASON_TEXT: Record<string, string> = {
  current_ru_run: "Текущий пригодный запуск",
  eligible_run_stale: "Последний пригодный запуск устарел",
  eligible_run_missing: "Пригодный запуск ещё не получен",
  google_unavailable: "Среда RU-пробы недоступна",
  release_failed: "Обязательная RU-проверка завершилась сбоем",
  release_incomplete: "Последняя RU-проверка неполная",
  blocked_by_access: "Проверка заблокирована подтверждённым отсутствием доступа",
  superseded_manifest: "Конфигурация RU-проверки изменилась: нужен новый запуск",
  current_target_missing: "В последнем запуске нет обязательной текущей цели",
  required_target_failed: "Обязательная цель RU-проверки завершилась сбоем",
  required_target_incomplete: "Обязательная цель RU-проверки проверена не полностью"
};

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function formatCount(value: unknown): string {
  const number = finiteNumber(value);
  return number === null ? "Нет данных" : new Intl.NumberFormat("ru-RU").format(number);
}

function formatPair(left: unknown, right: unknown): string {
  const first = finiteNumber(left);
  const second = finiteNumber(right);
  if (first === null || second === null) return "Нет данных";
  return `${formatCount(first)} / ${formatCount(second)}`;
}

function validTimestamp(value: unknown): value is string {
  return typeof value === "string" && Boolean(value.trim()) && !Number.isNaN(Date.parse(value));
}

function dateTimeText(value: unknown): string {
  if (!validTimestamp(value)) return "Нет данных";
  return new Date(value).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
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
  if (["warning", "degraded", "stale", "draining", "soft_limit"].includes(value)) return "warning";
  if (["ok", "healthy", "fresh", "active", "available"].includes(value)) return "success";
  return "neutral";
}

function severityLabel(severity: unknown): string {
  const value = String(severity || "").toLowerCase();
  if (value === "critical") return "Критично";
  if (value === "warning") return "Внимание";
  if (value === "info") return "Информация";
  return value || "Нет данных";
}

function sourceLabel(source: unknown): string {
  const value = String(source || "").trim();
  return SOURCE_LABELS[value] || value || "Источник не указан";
}

function formatThreshold(seconds: number | null): string {
  if (seconds === null) return "Порог не получен от backend";
  if (seconds % 3600 === 0) return `Порог свежести: ${seconds / 3600} ч`;
  if (seconds % 60 === 0) return `Порог свежести: ${seconds / 60} мин`;
  return `Порог свежести: ${seconds} сек`;
}

function ruReason(reasonCode: unknown): string {
  const code = String(reasonCode || "").trim();
  return RU_REASON_TEXT[code] || (code ? `Причина: ${code}` : "Причина не указана");
}

function SnapshotMetric({
  icon: Icon,
  label,
  value,
  detail,
  tone = "neutral"
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
  tone?: Tone;
}) {
  return (
    <div className="flex min-w-0 items-center gap-3 px-4 py-3">
      <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-[var(--pokrov-radius-card)] border ${
        tone === "danger"
          ? "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]"
          : tone === "warning"
            ? "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)]"
            : "border-[color:var(--atlas-border-strong)] bg-[color:var(--pokrov-status-success-bg)] text-[color:var(--atlas-primary)]"
      }`}>
        <Icon aria-hidden="true" size={18} strokeWidth={1.8} />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-medium text-[color:var(--atlas-text-soft)]">{label}</div>
        <div className="mt-0.5 flex items-baseline justify-between gap-2">
          <span className="truncate text-xl font-semibold tracking-tight text-[color:var(--atlas-text)]">{value}</span>
          <span className="hidden truncate text-[10px] text-[color:var(--atlas-text-muted)] 2xl:inline">{detail}</span>
        </div>
      </div>
    </div>
  );
}

function SnapshotStrip({ overview }: { overview: OpsOverview }) {
  const activeAlerts = Number(overview.alerts?.active_count || 0);
  const openTickets = finiteNumber(overview.summary?.tickets?.open);
  return (
    <section
      aria-label="Ключевые показатели"
      className="grid overflow-hidden rounded-[var(--pokrov-radius-panel)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] shadow-[var(--atlas-shadow-soft)] sm:grid-cols-2 xl:grid-cols-4 xl:divide-x xl:divide-[color:var(--atlas-border)]"
    >
      <SnapshotMetric icon={Users} label="Активные пользователи" value={formatCount(overview.summary?.users?.active)} detail="Текущий overview" />
      <SnapshotMetric icon={Server} label="Здоровые ноды" value={formatPair(overview.summary?.nodes?.healthy, overview.summary?.nodes?.total)} detail="Здоровые / всего" />
      <SnapshotMetric icon={AlertTriangle} label="Активные алерты" value={formatCount(activeAlerts)} detail="Durable alert store" tone={activeAlerts ? "warning" : "success"} />
      <SnapshotMetric icon={Ticket} label="Открытые тикеты" value={formatCount(openTickets)} detail="Требуют разбора" tone={openTickets ? "warning" : "success"} />
    </section>
  );
}

function SourceFreshness({
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
  const metrics = overview.metrics as OpsOverview["metrics"] & {
    last_sample_at?: string | null;
    stale_after_seconds?: number | null;
  };
  const brainAge = finiteNumber(metrics.age_seconds);
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
    <section className="border-t border-[color:var(--atlas-border)] px-5 py-4">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-[color:var(--atlas-text)]">Свежесть доказательств</h3>
        <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Brain и RU-origin остаются разными источниками.</p>
      </div>
      <div className="overflow-hidden rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]">
        <SourceRow
          source="Brain-origin"
          status={metricsStatus(metrics.status)}
          sampledAt={metrics.last_sample_at || null}
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
    </section>
  );
}

function nodeRecord(raw: unknown): Record<string, unknown> {
  return raw && typeof raw === "object" ? raw as Record<string, unknown> : {};
}

function nodeCode(node: Record<string, unknown>, index: number): string {
  return String(node.node_code || node.code || `node-${index + 1}`).trim().toLowerCase();
}

function NodeEvidenceTable({ overview, alert }: { overview: OpsOverview; alert: OpsAlert | null }) {
  const allNodes = Array.isArray(overview.capacity?.nodes)
    ? overview.capacity.nodes.map(nodeRecord)
    : [];
  const selectedCode = String(alert?.node_code || "").trim().toLowerCase();
  const matchingNodes = selectedCode
    ? allNodes.filter((node, index) => nodeCode(node, index) === selectedCode)
    : allNodes;
  const nodes = matchingNodes.slice(0, 8);

  return (
    <section className="border-t border-[color:var(--atlas-border)] px-5 py-4">
      <div className="mb-3 flex flex-wrap items-end justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-[color:var(--atlas-text)]">{selectedCode ? "Затронутая нода" : "Контур нод"}</h3>
          <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">Ёмкость и health из того же overview-снимка.</p>
        </div>
        <Badge tone={nodes.some((node) => toneForState(node.capacity_state) === "danger") ? "danger" : "neutral"}>{nodes.length}</Badge>
      </div>
      {nodes.length ? (
        <div className="ops-scrollbar overflow-x-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]">
          <table className="w-full min-w-[590px] border-collapse text-left text-xs">
            <thead className="bg-[color:var(--pokrov-table-header-bg)] text-[10px] uppercase tracking-[0.06em] text-[color:var(--atlas-text-muted)]">
              <tr>
                <th className="px-3 py-2 font-semibold">Нода</th>
                <th className="px-3 py-2 font-semibold">Состояние</th>
                <th className="px-3 py-2 font-semibold">CPU</th>
                <th className="px-3 py-2 font-semibold">Онлайн</th>
                <th className="px-3 py-2 font-semibold">Последний health</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[color:var(--pokrov-table-divider)]">
              {nodes.map((node, index) => {
                const code = nodeCode(node, index);
                const state = String(node.capacity_state || "unknown");
                return (
                  <tr key={code} data-node-code={code} className="hover:bg-[color:var(--pokrov-table-row-hover-bg)]">
                    <td className="px-3 py-2.5">
                      <div className="font-mono text-xs font-semibold uppercase text-[color:var(--atlas-text)]">{code}</div>
                      {node.name ? <div className="mt-0.5 max-w-40 truncate text-[10px] text-[color:var(--atlas-text-muted)]">{String(node.name)}</div> : null}
                    </td>
                    <td className="px-3 py-2.5"><Badge tone={toneForState(state)}>{state}</Badge></td>
                    <td className="px-3 py-2.5 font-semibold">{finiteNumber(node.cpu_percent) === null ? "Нет данных" : `${formatCount(node.cpu_percent)}%`}</td>
                    <td className="px-3 py-2.5 font-semibold">{formatCount(node.online_connections_hint)}</td>
                    <td className="px-3 py-2.5 text-[color:var(--atlas-text-soft)]">
                      {validTimestamp(node.last_health_at)
                        ? <time dateTime={node.last_health_at}>{dateTimeText(node.last_health_at)}</time>
                        : "Нет данных"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState
          title={selectedCode ? `Нода ${selectedCode.toUpperCase()} не найдена в overview` : "Ноды не получены"}
          description="Откройте раздел нод: его источник загружается отдельно и не замедляет главную."
          className="min-h-24"
        />
      )}
    </section>
  );
}

function IncidentEvidence({
  overview,
  alert,
  ruLatest,
  ruLoading,
  ruError
}: {
  overview: OpsOverview;
  alert: OpsAlert | null;
  ruLatest: RuLatestStatus | null;
  ruLoading: boolean;
  ruError: AdminApiError | null;
}) {
  return (
    <Card className="min-w-0 overflow-hidden p-0 shadow-none">
      <header className="px-5 py-4">
        {alert ? (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone={toneForState(alert.severity)}>{severityLabel(alert.severity)}</Badge>
              <span className="font-mono text-[10px] uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">{sourceLabel(alert.source)}</span>
            </div>
            <h2 className="mt-3 text-xl font-semibold tracking-tight text-[color:var(--atlas-text)]">{alert.title}</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-[color:var(--atlas-text-soft)]">{alert.body || "Описание не получено от alert source."}</p>
            <dl className="mt-4 grid gap-3 border-t border-[color:var(--atlas-border)] pt-4 sm:grid-cols-3">
              <div>
                <dt className="text-[10px] uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">Обнаружено</dt>
                <dd className="mt-1 text-xs font-semibold">{dateTimeText(alert.first_seen_at)}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">Последний сигнал</dt>
                <dd className="mt-1 text-xs font-semibold">{dateTimeText(alert.last_seen_at)}</dd>
              </div>
              <div>
                <dt className="text-[10px] uppercase tracking-[0.08em] text-[color:var(--atlas-text-muted)]">Контур</dt>
                <dd className="mt-1 font-mono text-xs font-semibold uppercase">{alert.node_code || "Общий"}</dd>
              </div>
            </dl>
          </>
        ) : (
          <div className="flex items-start gap-3 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] p-4">
            <ShieldCheck aria-hidden="true" className="mt-0.5 shrink-0 text-[color:var(--atlas-status-success-text)]" size={21} strokeWidth={1.8} />
            <div>
              <h2 className="text-lg font-semibold text-[color:var(--atlas-status-success-text)]">Система под контролем</h2>
              <p className="mt-1 text-sm leading-6 text-[color:var(--atlas-text-soft)]">В текущем durable alert store нет активных сигналов. Ниже остаются независимые health-источники.</p>
            </div>
          </div>
        )}
      </header>

      {alert ? (
        <section className="border-t border-[color:var(--atlas-border)] px-5 py-4">
          <h3 className="text-sm font-semibold text-[color:var(--atlas-text)]">Лента доказательств</h3>
          <div className="mt-4 space-y-0">
            <div className="grid grid-cols-[20px_86px_minmax(0,1fr)] gap-3">
              <div className="relative flex justify-center">
                <span className="relative z-10 mt-1.5 h-2.5 w-2.5 rounded-full border-2 border-[color:var(--atlas-status-danger-text)] bg-[color:var(--atlas-surface)]" />
                <span className="absolute inset-y-3 w-px bg-[color:var(--atlas-border-strong)]" />
              </div>
              <time className="pt-0.5 text-[11px] text-[color:var(--atlas-text-muted)]" dateTime={validTimestamp(alert.first_seen_at) ? alert.first_seen_at : undefined}>{dateTimeText(alert.first_seen_at)}</time>
              <div className="pb-5">
                <div className="text-xs font-semibold">Сигнал зарегистрирован</div>
                <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{sourceLabel(alert.source)} создал активную запись в очереди.</p>
              </div>
            </div>
            <div className="grid grid-cols-[20px_86px_minmax(0,1fr)] gap-3">
              <div className="relative flex justify-center">
                <span className="relative z-10 mt-1.5 h-2.5 w-2.5 rounded-full border-2 border-[color:var(--atlas-primary)] bg-[color:var(--atlas-surface)]" />
              </div>
              <time className="pt-0.5 text-[11px] text-[color:var(--atlas-text-muted)]" dateTime={validTimestamp(alert.last_seen_at) ? alert.last_seen_at : undefined}>{dateTimeText(alert.last_seen_at)}</time>
              <div>
                <div className="text-xs font-semibold">Последнее наблюдение</div>
                <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Сигнал всё ещё присутствует в последнем overview-снимке.</p>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      <NodeEvidenceTable overview={overview} alert={alert} />
      <SourceFreshness overview={overview} ruLatest={ruLatest} ruLoading={ruLoading} ruError={ruError} />
    </Card>
  );
}

function NextStepPanel({
  alert,
  overview,
  ruLatest,
  onNavigate,
  onRefresh
}: {
  alert: OpsAlert | null;
  overview: OpsOverview;
  ruLatest: RuLatestStatus | null;
  onNavigate?: (href: string) => void;
  onRefresh: () => void;
}) {
  const metrics = overview.metrics as OpsOverview["metrics"] & { last_sample_at?: string | null };
  const evidence = alert
    ? [
        validTimestamp(alert.first_seen_at),
        validTimestamp(alert.last_seen_at),
        Boolean(String(alert.source || "").trim()),
        validTimestamp(metrics.last_sample_at),
        validTimestamp(ruLatest?.sampled_at || ruLatest?.latest_eligible_run?.finished_at)
      ]
    : [];
  const completeness = evidence.length ? Math.round((evidence.filter(Boolean).length / evidence.length) * 100) : 100;
  const navigate = (href: string) => {
    if (onNavigate) onNavigate(href);
    else window.location.assign(href);
  };

  return (
    <aside aria-label="Следующий шаг" className="min-w-0">
      <Card className="overflow-hidden p-0 shadow-none xl:sticky xl:top-[7.75rem]">
        <div className="border-b border-[color:var(--atlas-border)] px-4 py-4">
          <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-[color:var(--atlas-text-muted)]">Рабочий контекст</div>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">Следующий шаг</h2>
        </div>
        {alert ? (
          <div className="px-4 py-4">
            <div className="flex items-start gap-3">
              <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-[var(--pokrov-radius-card)] border ${
                alert.severity.toLowerCase() === "critical"
                  ? "border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] text-[color:var(--atlas-status-danger-text)]"
                  : "border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] text-[color:var(--atlas-status-warning-text)]"
              }`}>
                <AlertTriangle aria-hidden="true" size={17} strokeWidth={1.8} />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold">{severityLabel(alert.severity)}</div>
                <p className="mt-1 line-clamp-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">{alert.title}</p>
              </div>
            </div>

            <dl className="mt-4 divide-y divide-[color:var(--atlas-border)] text-xs">
              <div className="flex justify-between gap-3 py-2.5"><dt className="text-[color:var(--atlas-text-soft)]">Владелец</dt><dd className="text-right font-semibold">Не назначен в overview</dd></div>
              <div className="flex justify-between gap-3 py-2.5"><dt className="text-[color:var(--atlas-text-soft)]">Источник</dt><dd className="text-right font-semibold">{sourceLabel(alert.source)}</dd></div>
              <div className="flex justify-between gap-3 py-2.5"><dt className="text-[color:var(--atlas-text-soft)]">Нода</dt><dd className="font-mono font-semibold uppercase">{alert.node_code || "Общий контур"}</dd></div>
              <div className="flex justify-between gap-3 py-2.5"><dt className="text-[color:var(--atlas-text-soft)]">Охват</dt><dd className="font-semibold">{formatCount(alert.affected_count)}</dd></div>
            </dl>

            <div className="mt-4">
              <div className="mb-2 flex items-center justify-between gap-3 text-xs">
                <span className="font-semibold">Полнота данных</span>
                <span className="font-mono">{completeness}%</span>
              </div>
              <Progress value={completeness} tone={completeness >= 80 ? "success" : "warning"} label="Полнота данных по сигналу" />
              <p className="mt-2 text-[10px] leading-4 text-[color:var(--atlas-text-muted)]">Показывает наличие timestamps и независимых источников, а не вероятность причины.</p>
            </div>

            <div className="mt-5 grid gap-2">
              <Button variant="primary" className="w-full" onClick={() => navigate(`/alerts?selected=${encodeURIComponent(String(alert.id))}`)}>
                Открыть разбор
                <ArrowUpRight aria-hidden="true" size={15} strokeWidth={1.8} />
              </Button>
              {alert.node_code ? (
                <Button variant="secondary" className="w-full" onClick={() => navigate(`/nodes?selected=${encodeURIComponent(alert.node_code || "")}`)}>
                  <Server aria-hidden="true" size={15} strokeWidth={1.8} />
                  Открыть ноду {alert.node_code.toUpperCase()}
                </Button>
              ) : null}
              <Button variant="ghost" className="w-full" onClick={onRefresh}>
                <RefreshCw aria-hidden="true" size={15} strokeWidth={1.8} />
                Обновить снимок
              </Button>
            </div>
          </div>
        ) : (
          <div className="px-4 py-5">
            <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-status-success-line)] bg-[color:var(--atlas-status-success-bg)] p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-[color:var(--atlas-status-success-text)]">
                <CheckCircle2 aria-hidden="true" size={18} strokeWidth={1.8} />
                Разбор не требуется
              </div>
              <p className="mt-2 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Активных алертов нет. Продолжайте наблюдение за свежестью источников.</p>
            </div>
            <div className="mt-4 grid gap-2">
              <Button variant="secondary" className="w-full" onClick={() => navigate("/nodes")}>
                <Server aria-hidden="true" size={15} strokeWidth={1.8} />
                Открыть ноды
              </Button>
              <Button variant="ghost" className="w-full" onClick={onRefresh}>
                <RefreshCw aria-hidden="true" size={15} strokeWidth={1.8} />
                Обновить снимок
              </Button>
            </div>
          </div>
        )}
      </Card>
    </aside>
  );
}

function FleetDock({ overview }: { overview: OpsOverview }) {
  const nodes = Array.isArray(overview.capacity?.nodes)
    ? overview.capacity.nodes.map(nodeRecord)
    : [];
  return (
    <Card className="overflow-hidden p-0 shadow-none">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[color:var(--atlas-border)] px-4 py-3">
        <div className="flex items-center gap-2">
          <Activity aria-hidden="true" size={16} strokeWidth={1.8} className="text-[color:var(--atlas-primary)]" />
          <h2 className="text-sm font-semibold">Флот нод</h2>
        </div>
        <span className="text-[10px] text-[color:var(--atlas-text-muted)]">Один overview-снимок · без дополнительного запроса</span>
      </div>
      {nodes.length ? (
        <div className="ops-scrollbar flex overflow-x-auto">
          {nodes.map((node, index) => {
            const code = nodeCode(node, index);
            const state = String(node.capacity_state || "unknown");
            const tone = toneForState(state);
            return (
              <div key={code} className="flex min-w-40 flex-1 items-center justify-between gap-3 border-r border-[color:var(--atlas-border)] px-4 py-3 last:border-r-0">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`h-2 w-2 shrink-0 rounded-full ${
                      tone === "danger" ? "bg-red-500" : tone === "warning" ? "bg-amber-500" : tone === "success" ? "bg-emerald-600" : "bg-slate-400"
                    }`} />
                    <span className="font-mono text-xs font-semibold uppercase">{code}</span>
                  </div>
                  <div className="mt-1 truncate text-[10px] text-[color:var(--atlas-text-muted)]">{state}</div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-[color:var(--atlas-text-muted)]">CPU</div>
                  <div className="font-mono text-xs font-semibold">{finiteNumber(node.cpu_percent) === null ? "—" : `${formatCount(node.cpu_percent)}%`}</div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="px-4 py-4 text-xs text-[color:var(--atlas-text-soft)]">Ноды не вошли в compact overview. Всего по summary: {formatCount(overview.summary?.nodes?.total)}.</div>
      )}
    </Card>
  );
}

function RecentAdminEvents({ overview }: { overview: OpsOverview }) {
  const events = Array.isArray(overview.recent_admin_events) ? overview.recent_admin_events : [];
  return (
    <Card className="p-0 shadow-none">
      <details>
        <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-sm font-semibold outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[color:var(--atlas-focus)]">
          <span>Недавние действия администраторов</span>
          <Badge tone="neutral">{events.length}</Badge>
        </summary>
        <div className="border-t border-[color:var(--atlas-border)] px-4">
          {events.length ? (
            <div className="divide-y divide-[color:var(--atlas-border)]">
              {events.slice(0, 8).map((event, index) => {
                const id = String(event.id || event.event_id || `event-${index + 1}`);
                const timestamp = typeof event.created_at === "string" ? event.created_at : typeof event.timestamp === "string" ? event.timestamp : null;
                return (
                  <article key={id} className="grid gap-1 py-3 md:grid-cols-[180px_1fr_180px] md:items-center">
                    <div className="text-xs text-[color:var(--atlas-text-muted)]">{timestamp ? <time dateTime={timestamp}>{dateTimeText(timestamp)}</time> : "Нет данных"}</div>
                    <div className="text-sm font-semibold">{String(event.action || event.title || "Действие без названия")}</div>
                    <div className="text-xs text-[color:var(--atlas-text-soft)] md:text-right">{event.actor ? String(event.actor) : "Автор не указан"}</div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="py-4 text-xs text-[color:var(--atlas-text-soft)]">События не вошли в текущий overview. Это не доказывает отсутствие действий.</p>
          )}
        </div>
      </details>
    </Card>
  );
}

export function TriageWorkspace({
  overview,
  alerts,
  selectedAlert,
  selectedActionId,
  loading,
  refreshing,
  ruLatest,
  ruLoading,
  ruError,
  onSelect,
  onNavigate,
  onRefresh
}: {
  overview: OpsOverview;
  alerts: readonly OpsAlert[];
  selectedAlert: OpsAlert | null;
  selectedActionId: string | null;
  loading: boolean;
  refreshing: boolean;
  ruLatest: RuLatestStatus | null;
  ruLoading: boolean;
  ruError: AdminApiError | null;
  onSelect: (id: string) => void;
  onNavigate?: (href: string) => void;
  onRefresh: () => void;
}) {
  return (
    <div className="space-y-3">
      <SnapshotStrip overview={overview} />
      <div className="ops-command-layout">
        <ActionQueue
          alerts={alerts}
          loading={loading}
          refreshing={refreshing}
          selectedId={selectedActionId}
          onSelect={onSelect}
        />
        <IncidentEvidence
          overview={overview}
          alert={selectedAlert}
          ruLatest={ruLatest}
          ruLoading={ruLoading}
          ruError={ruError}
        />
        <NextStepPanel
          alert={selectedAlert}
          overview={overview}
          ruLatest={ruLatest}
          onNavigate={onNavigate}
          onRefresh={onRefresh}
        />
      </div>
      <FleetDock overview={overview} />
      <RecentAdminEvents overview={overview} />
    </div>
  );
}
