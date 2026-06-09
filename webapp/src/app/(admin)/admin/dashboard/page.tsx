"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminDashboardSkeleton,
  CompactTableShell,
  DashboardCell,
  MiniBars,
  ShiftMetric,
  SignalRow,
  WorkQueueCard,
  adminUserQueueGridClass,
  type DashboardTone,
} from "@/components/admin/dashboard/dashboard-widgets";
import { AdminBadge, AdminEmptyState, AdminSurfaceHeader, adminButtonClass, adminPanelClass } from "@/components/admin/admin-shell";
import { formatRub, formatRuDateTime, formatShortAge } from "@/lib/admin-format";
import {
  AlertTriangle,
  ArrowRight,
  Clock3,
  CreditCard,
  LifeBuoy,
  RefreshCw,
  Server,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import {
  adminClientWarpSummary,
  adminMetricsStatus,
  adminMetricsTimeseries,
  adminSummary,
  adminTickets,
  adminUsers,
  type AdminClientWarpSummaryPayload,
  type AdminMetricsPoint,
  type AdminMetricsStatus,
  type AdminSummaryPayload,
  type AdminUserRow,
  type TicketInfo,
} from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useCallback, useEffect, useMemo, useState } from "react";

type AlertItem = { title: string; body: string; tone: Exclude<DashboardTone, "neutral"> };
type WarpMaterials = AdminClientWarpSummaryPayload["materials"];
type WarpEvents = AdminClientWarpSummaryPayload["events"];

const EMPTY_WARP_MATERIALS: WarpMaterials = {
  total: 0,
  active: 0,
  stale_active: 0,
  revoked: 0,
  rotation_requested: 0,
};

const EMPTY_WARP_EVENTS: WarpEvents = {
  active_consents: 0,
  recent_material_provisions: 0,
  recent_provisioning_failures: 0,
  recent_rotation_requests: 0,
  recent_runtime_errors: 0,
  recent_rate_limits: 0,
};

function warpMaterials(summary: AdminClientWarpSummaryPayload | null): WarpMaterials {
  return summary?.materials ?? EMPTY_WARP_MATERIALS;
}

function warpEvents(summary: AdminClientWarpSummaryPayload | null): WarpEvents {
  return summary?.events ?? EMPTY_WARP_EVENTS;
}

function hasWarpData(summary: AdminClientWarpSummaryPayload | null): boolean {
  return Boolean(summary?.materials || summary?.events || summary?.runtime);
}

function lastDaysRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - Math.max(1, days - 1));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function metricsLabel(metrics: AdminMetricsStatus | null): string {
  if (!metrics) return "нет данных";
  if (metrics.status === "fresh") return `свежие · ${formatShortAge(metrics.age_seconds)}`;
  if (metrics.status === "stale") return `устарели · ${formatShortAge(metrics.age_seconds)}`;
  return "нет среза";
}

function userStatusLabel(status: AdminUserRow["status"]): string {
  if (status === "active") return "Активен";
  if (status === "expired") return "Истёк";
  if (status === "blocked") return "Ограничен";
  return "Тест";
}

function userStatusTone(row: AdminUserRow): DashboardTone {
  if (row.status === "active") return "success";
  if (row.status === "expired") return "warning";
  if (row.status === "blocked") return "danger";
  return "neutral";
}

function nodeScoreTone(score: number): DashboardTone {
  if (score >= 8) return "success";
  if (score >= 5) return "warning";
  return "danger";
}

function nodeScoreLabel(score: number): string {
  if (score >= 8) return "стабильно";
  if (score >= 5) return "проверить";
  return "риск";
}

function warpSummaryTone(summary: AdminClientWarpSummaryPayload | null): DashboardTone {
  if (!hasWarpData(summary)) return "neutral";
  const materials = warpMaterials(summary);
  const events = warpEvents(summary);
  if (events.recent_provisioning_failures > 0 || events.recent_runtime_errors > 0) return "danger";
  if (materials.stale_active > 0 || materials.rotation_requested > 0 || events.recent_rate_limits > 0) return "warning";
  if (materials.active > 0 || events.active_consents > 0) return "success";
  return "neutral";
}

function warpRuntimeLabel(summary: AdminClientWarpSummaryPayload | null): string {
  if (!hasWarpData(summary)) return "нет данных";
  const runtime = summary?.runtime ?? { state_counts: {}, recent_events: [] };
  const state = runtime.last_state || "quiet";
  const reason = runtime.last_reason_code ? ` / ${runtime.last_reason_code}` : "";
  return `${state}${reason}`;
}

function isAlertItem(item: AlertItem | null): item is AlertItem {
  return item != null;
}

export default function AdminDashboardPage() {
  const { loading: sessionLoading, user, webLoginRequired } = usePortalSession();
  const isAdmin = Boolean(user?.is_admin);
  const [summary, setSummary] = useState<AdminSummaryPayload | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsStatus | null>(null);
  const [series, setSeries] = useState<AdminMetricsPoint[]>([]);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [warpSummary, setWarpSummary] = useState<AdminClientWarpSummaryPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastRefreshedAt, setLastRefreshedAt] = useState<Date | null>(null);

  const refresh = useCallback(async (): Promise<void> => {
    if (sessionLoading || webLoginRequired || !isAdmin) return;
    setLoading(true);
    setError("");
    try {
      const range = lastDaysRange(7);
      const [summaryPayload, metricsPayload, seriesPayload, usersPayload, ticketsPayload, warpPayload] = await Promise.all([
        adminSummary(),
        adminMetricsStatus(),
        adminMetricsTimeseries(range),
        adminUsers({ page_size: 5 }),
        adminTickets("", 5),
        adminClientWarpSummary().catch(() => null),
      ]);

      setSummary(summaryPayload);
      setMetrics(metricsPayload);
      setSeries(seriesPayload.points || []);
      setUsers(usersPayload.users || []);
      setTickets(ticketsPayload || []);
      setWarpSummary(warpPayload);
      setLastRefreshedAt(new Date());
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить административную сводку."));
    } finally {
      setLoading(false);
    }
  }, [isAdmin, sessionLoading, webLoginRequired]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const totals = useMemo(
    () =>
      series.reduce(
        (acc, point) => {
          acc.registrations += Number(point.registrations || 0);
          acc.churn += Number(point.churn || 0);
          acc.revenueRub += Number(point.revenue_rub || 0);
          return acc;
        },
        { registrations: 0, churn: 0, revenueRub: 0 },
      ),
    [series],
  );

  const alertItems = useMemo<AlertItem[]>(() => {
    if (!summary) return [];
    const errors = summary.errors ?? {};
    const resilience = summary.resilience ?? {};
    const ticketsSummary = summary.tickets ?? { open: 0 };

    const candidateItems: Array<AlertItem | null> = [
      errors.stale_metrics
        ? {
            title: "Срез по метрикам устарел",
            body: metrics?.last_sample_at
              ? `Последний срез: ${formatRuDateTime(metrics.last_sample_at)}. Возраст: ${formatShortAge(metrics.age_seconds)}.`
              : "Нужно проверить сборщик метрик и таймер.",
            tone: "warning" as const,
          }
        : null,
      Number(errors.unhealthy_nodes || 0) > 0
        ? {
            title: "Есть узлы с риском",
            body: `${Number(errors.unhealthy_nodes || 0)} узл. требуют проверки по health score или свежести телеметрии.`,
            tone: "danger" as const,
          }
        : null,
      Number(errors.payment_callback_failures_24h || 0) > 0
        ? {
            title: "Проблемы с подтверждениями оплаты",
            body: `${Number(errors.payment_callback_failures_24h || 0)} сбоев за 24 часа. Откройте платёжный журнал перед ручными действиями.`,
            tone: "warning" as const,
          }
        : null,
      Number(errors.subscription_numeric_fallbacks_24h || 0) > 0
        ? {
            title: "Срабатывала резервная обработка подписок",
            body: `${Number(errors.subscription_numeric_fallbacks_24h || 0)} случаев за 24 часа. Проверьте миграцию на токены.`,
            tone: "warning" as const,
          }
        : null,
      Boolean(resilience.single_point_risk)
        ? {
            title: "Есть риск единой точки отказа",
            body: "Перед релизом проверьте резерв по узлам и устойчивость управляющей панели.",
            tone: "danger" as const,
          }
        : null,
      Number(ticketsSummary.open || 0) > 0
        ? {
            title: "Очередь поддержки не пустая",
            body: `${Number(ticketsSummary.open || 0)} открытых кейсов ждут реакции оператора.`,
            tone: "accent" as const,
          }
        : null,
    ];
    const items = candidateItems.filter(isAlertItem);

    if (!items.length) {
      return [
        {
          title: "Критичных сигналов сейчас нет",
          body: "Метрики, узлы и очереди можно читать как обычную рабочую сводку.",
          tone: "success" as const,
        },
      ];
    }

    return items.slice(0, 5);
  }, [metrics, summary]);

  const activitySeries = useMemo(() => series.map((point) => Number(point.registrations || 0) + Number(point.churn || 0)), [series]);
  const latestPoint = series.at(-1);
  const lastRefreshedLabel = lastRefreshedAt
    ? lastRefreshedAt.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })
    : "не обновлялось";

  if (loading) return <AdminDashboardSkeleton />;

  if (error) {
    return (
      <section className={adminPanelClass("danger")}>
        <AdminSurfaceHeader
          title="Не получилось собрать административную сводку"
          description={error}
          actions={
            <button type="button" onClick={() => void refresh()} className={adminButtonClass("primary")}>
              <RefreshCw aria-hidden className="h-4 w-4" />
              Повторить
            </button>
          }
        />
      </section>
    );
  }

  if (!summary) return null;

  const usersSummary = summary.users ?? { total: 0, active: 0, free: 0, paid: 0 };
  const ticketsSummary = summary.tickets ?? { open: 0 };
  const nodesSummary = summary.nodes ?? { healthy: 0, total: 0 };
  const errorsSummary = summary.errors ?? {};
  const retentionSummary = summary.retention ?? { expiring_3d: 0, expired_7d: 0, reactivation_candidates: 0 };
  const bonusSummary = summary.bonus_events_24h ?? { channel_activated: 0, channel_denied: 0, promo_redeemed: 0, promo_denied: 0 };
  const resilienceSummary = summary.resilience ?? { free_node_enabled: false, single_point_risk: false };
  const topNodes = summary.top_nodes ?? [];
  const unhealthyNodes = Math.max(0, Number(nodesSummary.total || 0) - Number(nodesSummary.healthy || 0));
  const freshnessTone: DashboardTone = metrics?.status === "fresh" ? "success" : metrics?.status === "stale" ? "warning" : "danger";
  const nodeTone: DashboardTone = unhealthyNodes > 0 || Number(errorsSummary.unhealthy_nodes || 0) > 0 ? "warning" : "success";
  const supportTone: DashboardTone = Number(ticketsSummary.open || 0) > 0 ? "warning" : "success";
  const paymentTone: DashboardTone = Number(errorsSummary.payment_callback_failures_24h || 0) > 0 ? "warning" : "success";
  const fallbackTone: DashboardTone = Number(errorsSummary.subscription_numeric_fallbacks_24h || 0) > 0 ? "warning" : "success";
  const warpTone = warpSummaryTone(warpSummary);
  const warpHasData = hasWarpData(warpSummary);
  const warpMaterialCounts = warpMaterials(warpSummary);
  const warpEventCounts = warpEvents(warpSummary);

  return (
    <section className="space-y-4">
      <article className={`${adminPanelClass("neutral")} border-slate-200 bg-white/90`}>
        <AdminSurfaceHeader
          title="Сводка смены"
          description="Первый экран для оператора: что требует реакции, какие очереди открыты и свежие ли данные, на которых можно принимать решения."
          actions={
            <>
              <button type="button" onClick={() => void refresh()} className={adminButtonClass("primary", "sm")}>
                <RefreshCw aria-hidden className="h-3.5 w-3.5" />
                Обновить
              </button>
              <AppRouteLink href="/admin/users" className={adminButtonClass("secondary", "sm")}>
                <UsersRound aria-hidden className="h-3.5 w-3.5" />
                Люди
              </AppRouteLink>
              <AppRouteLink href="/admin/nodes" className={adminButtonClass("secondary", "sm")}>
                <Server aria-hidden className="h-3.5 w-3.5" />
                Ноды
              </AppRouteLink>
              <AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "sm")}>
                <LifeBuoy aria-hidden className="h-3.5 w-3.5" />
                Поддержка
              </AppRouteLink>
            </>
          }
          meta={
            <>
              <AdminBadge tone={freshnessTone}>
                <Clock3 aria-hidden className="h-3.5 w-3.5" />
                Метрики: {metricsLabel(metrics)}
              </AdminBadge>
              <AdminBadge tone={nodeTone}>Узлы: {nodesSummary.healthy} / {nodesSummary.total}</AdminBadge>
              <AdminBadge tone={supportTone}>Тикеты: {ticketsSummary.open}</AdminBadge>
              <AdminBadge>Обновлено в {lastRefreshedLabel}</AdminBadge>
            </>
          }
        />
      </article>

      <div className="grid gap-3 lg:grid-cols-3 2xl:grid-cols-5">
        <ShiftMetric label="WARP" value={warpHasData ? `${warpMaterialCounts.active}/${warpMaterialCounts.total}` : "нет"} hint={warpHasData ? `Runtime: ${warpRuntimeLabel(warpSummary)}` : "Сводка временно недоступна."} icon={<ShieldCheck aria-hidden className="h-4 w-4" />} tone={warpTone} />
        <ShiftMetric label="Люди" value={`${usersSummary.active}/${usersSummary.total}`} hint={`Платные ${usersSummary.paid} · бесплатные ${usersSummary.free}`} icon={<UsersRound aria-hidden className="h-4 w-4" />} />
        <ShiftMetric label="Открытые тикеты" value={ticketsSummary.open} hint={Number(ticketsSummary.open || 0) > 0 ? "Очередь поддержки ждёт ответа." : "Очередь поддержки пустая."} icon={<LifeBuoy aria-hidden className="h-4 w-4" />} tone={supportTone} />
        <ShiftMetric label="Узлов в норме" value={`${nodesSummary.healthy}/${nodesSummary.total}`} hint={unhealthyNodes > 0 ? `Проверить ${unhealthyNodes} узл.` : `Свежесть: ${metricsLabel(metrics)}`} icon={<Server aria-hidden className="h-4 w-4" />} tone={nodeTone} />
        <ShiftMetric label="Платежи 24 ч" value={Number(errorsSummary.payment_callback_failures_24h || 0)} hint={paymentTone === "success" ? "Ошибок подтверждения нет." : "Есть сбои подтверждения, проверьте журнал."} icon={<CreditCard aria-hidden className="h-4 w-4" />} tone={paymentTone} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
        <DashboardCell
          title="Тревоги"
          subtitle="Только сигналы, которые меняют порядок работы. Если здесь пусто, можно идти по очередям."
          actions={
            <AppRouteLink href="/admin/nodes" className={adminButtonClass("secondary", "xs")}>
              <AlertTriangle aria-hidden className="h-3.5 w-3.5" />
              Разобрать
            </AppRouteLink>
          }
        >
          <div className="divide-y divide-slate-200/60">
            {alertItems.map((item) => (
              <SignalRow key={item.title} title={item.title} body={item.body} tone={item.tone} />
            ))}
          </div>
        </DashboardCell>

        <DashboardCell title="В работе" subtitle="Очереди, которые оператор должен открыть после проверки тревог.">
          <div className="grid gap-3 sm:grid-cols-2">
            <WorkQueueCard title="WARP lifecycle" value={warpHasData ? warpEventCounts.recent_runtime_errors : 0} hint={warpHasData ? `Runtime: ${warpRuntimeLabel(warpSummary)} · согласия: ${warpEventCounts.active_consents}` : "Сводка временно недоступна."} href="/admin/network" tone={warpTone} />
            <WorkQueueCard title="Поддержка" value={ticketsSummary.open} hint="Открытые обращения, где пользователю нужен ответ." href="/admin/tickets" tone={supportTone} />
            <WorkQueueCard title="Истекает за 3 дня" value={retentionSummary.expiring_3d} hint={`Истекли за 7 дней: ${retentionSummary.expired_7d}`} href="/admin/users" tone={retentionSummary.expiring_3d > 0 ? "warning" : "neutral"} />
            <WorkQueueCard title="К реактивации" value={retentionSummary.reactivation_candidates} hint="Кандидаты на возврат без ручного поиска." href="/admin/users" tone={retentionSummary.reactivation_candidates > 0 ? "accent" : "neutral"} />
            <WorkQueueCard title="Бонусы 24 ч" value={`${bonusSummary.channel_activated}/${bonusSummary.channel_denied}`} hint={`Промо: ${bonusSummary.promo_redeemed}/${bonusSummary.promo_denied}`} href="/admin/bonuses" tone={bonusSummary.channel_denied > 0 || bonusSummary.promo_denied > 0 ? "warning" : "neutral"} />
          </div>
        </DashboardCell>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
        <DashboardCell title="Люди под разбор" subtitle="Пять последних записей из списка пользователей: статус, происхождение и срок доступа." actions={<AppRouteLink href="/admin/users" className={adminButtonClass("secondary", "xs")}>Все люди<ArrowRight aria-hidden className="h-3.5 w-3.5" /></AppRouteLink>}>
          <CompactTableShell>
            <div className="overflow-x-auto">
              <div className="min-w-[620px]">
                <div className={`${adminUserQueueGridClass} border-b border-slate-200/70 bg-slate-50/80 px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500`}>
                  <span>Пользователь</span>
                  <span>Статус</span>
                  <span>Вход</span>
                  <span>Срок</span>
                </div>
                <div className="divide-y divide-slate-200/70">
                  {users.length ? (
                    users.map((row) => (
                      <div key={row.tg_id} className={`${adminUserQueueGridClass} px-3 py-3`}>
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-900">{row.display_name || row.username || `ID ${row.tg_id}`}</p>
                          <p className="mt-1 truncate text-xs text-slate-500">{row.username ? `@${row.username}` : `ID ${row.tg_id}`}</p>
                        </div>
                        <div><AdminBadge tone={userStatusTone(row)}>{userStatusLabel(row.status)}</AdminBadge></div>
                        <div><AdminBadge>{row.origin}</AdminBadge></div>
                        <div className="font-mono text-sm font-medium text-slate-600">{formatRuDateTime(row.expiry_at)}</div>
                      </div>
                    ))
                  ) : (
                    <AdminEmptyState className="m-3 min-h-[150px]" title="Пользователей под разбор сейчас нет." />
                  )}
                </div>
              </div>
            </div>
          </CompactTableShell>
        </DashboardCell>

        <DashboardCell title="Очередь поддержки" subtitle="Последние кейсы: тема, статус и короткий контекст без ухода в Telegram." actions={<AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "xs")}>Все тикеты<ArrowRight aria-hidden className="h-3.5 w-3.5" /></AppRouteLink>}>
          <div className="space-y-3">
            {tickets.length ? (
              tickets.map((ticket) => (
                <div key={ticket.id} className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-slate-900">{ticket.subject || `Тикет #${ticket.id}`}</p>
                    <AdminBadge>{ticket.status_title}</AdminBadge>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{ticket.last_message_preview || "Нет превью последнего сообщения."}</p>
                  <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-slate-400">Обновлён: {formatRuDateTime(ticket.updated_at)}</p>
                </div>
              ))
            ) : (
              <AdminEmptyState className="min-h-[180px]" title="Очередь поддержки пустая." />
            )}
          </div>
        </DashboardCell>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
        <DashboardCell title="Контекст недели" subtitle="Короткая динамика без попытки выдать её за live-аналитику.">
          <div className="grid gap-3 md:grid-cols-[1fr_1.1fr]">
            <div className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">События</p>
              <p className="mt-2 font-mono text-2xl font-semibold leading-none text-slate-950">{totals.registrations + totals.churn}</p>
              <p className="mt-2 text-xs leading-5 text-slate-500">Регистрации {totals.registrations} · отток {totals.churn}</p>
              <div className="mt-4">
                <MiniBars values={activitySeries} tone="emerald" label="Сумма регистраций и оттока за семь дней" />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-3 md:grid-cols-1">
              <div className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Выручка за 7 дней</p>
                <p className="mt-2 font-mono text-xl font-semibold text-slate-950">{formatRub(totals.revenueRub)}</p>
              </div>
              <div className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Сегодня</p>
                <p className="mt-2 text-sm font-semibold text-slate-900">+{latestPoint?.registrations ?? 0} · -{latestPoint?.churn ?? 0} · {formatRub(latestPoint?.revenue_rub ?? 0)}</p>
              </div>
              <div className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Фоллбэк подписок</p>
                <div className="mt-2"><AdminBadge tone={fallbackTone}>{Number(errorsSummary.subscription_numeric_fallbacks_24h || 0)} за 24 ч</AdminBadge></div>
              </div>
            </div>
          </div>
        </DashboardCell>

        <DashboardCell title="Сеть и устойчивость" subtitle="На первом экране только агрегаты и топ-узлы. Глубокий разбор остаётся в разделе нод." actions={<AppRouteLink href="/admin/nodes" className={adminButtonClass("secondary", "xs")}>Все ноды<ArrowRight aria-hidden className="h-3.5 w-3.5" /></AppRouteLink>}>
          <div className="space-y-3">
            {topNodes.slice(0, 4).map((node) => (
              <div key={node.code} className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-sm font-semibold text-slate-900">{node.code}</p>
                    <p className="mt-1 text-xs text-slate-500">Клиенты: {node.active_clients} · задержка: {node.panel_latency_ms ?? "—"} мс</p>
                  </div>
                  <AdminBadge tone={nodeScoreTone(node.health_score)}>{nodeScoreLabel(node.health_score)} · {node.health_score}</AdminBadge>
                </div>
                <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-slate-400">Проверка: {formatRuDateTime(node.last_health_at)}</p>
              </div>
            ))}

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Устойчивость</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <AdminBadge tone={resilienceSummary.free_node_enabled ? "success" : "warning"}>NL-free {resilienceSummary.free_node_enabled ? "включён" : "выключен"}</AdminBadge>
                  <AdminBadge tone={resilienceSummary.single_point_risk ? "danger" : "success"}>{resilienceSummary.single_point_risk ? "нет резерва" : "резерв есть"}</AdminBadge>
                </div>
              </div>
              <div className="rounded-[0.95rem] border border-slate-200/70 bg-white/65 p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Активные alert</p>
                <p className="mt-2 font-mono text-xl font-semibold text-slate-950">{metrics?.active_alerts?.length ?? 0}</p>
                <p className="mt-1 text-xs leading-5 text-slate-500">Показаны в деталях раздела «Ноды».</p>
              </div>
            </div>
          </div>
        </DashboardCell>
      </div>
    </section>
  );
}
