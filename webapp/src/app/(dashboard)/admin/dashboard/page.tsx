"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminBadge,
  AdminEmptyState,
  AdminMetricStrip,
  AdminSurfaceHeader,
  adminButtonClass,
  adminPanelClass,
} from "@/components/admin/admin-shell";
import {
  adminMetricsStatus,
  adminMetricsTimeseries,
  adminSummary,
  adminTickets,
  adminUsers,
  type AdminMetricsPoint,
  type AdminMetricsStatus,
  type AdminSummaryPayload,
  type AdminUserRow,
  type TicketInfo,
} from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { fmtRuDate } from "../nav";

function lastDaysRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - Math.max(1, days - 1));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function MiniBars({ values, tone = "emerald" }: { values: number[]; tone?: "emerald" | "slate" | "rose" }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const colorClass = tone === "rose" ? "bg-rose-500" : tone === "slate" ? "bg-slate-400" : "bg-emerald-500";
  return (
    <div className="flex h-9 items-end gap-[4px]">
      {values.map((value, index) => (
        <div
          key={index}
          className={`w-[7px] rounded-sm ${colorClass}`}
          style={{ height: `${Math.max(10, (Number(value || 0) / max) * 100)}%`, opacity: 0.38 + (Number(value || 0) / max) * 0.62 }}
        />
      ))}
    </div>
  );
}

function formatRub(value?: number | null): string {
  if (value == null || Number.isNaN(Number(value))) return "0 ₽";
  return `${new Intl.NumberFormat("ru-RU").format(Math.round(Number(value)))} ₽`;
}

function formatShortDate(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
  }).format(parsed);
}

function formatShortAge(seconds?: number | null): string {
  if (seconds == null || Number.isNaN(Number(seconds))) return "нет данных";
  const total = Math.max(0, Math.round(Number(seconds)));
  if (total < 60) return `${total}с`;
  if (total < 3600) return `${Math.round(total / 60)}м`;
  if (total < 86400) return `${Math.round(total / 3600)}ч`;
  return `${Math.round(total / 86400)}д`;
}

function metricsLabel(metrics: AdminMetricsStatus | null): string {
  if (!metrics) return "нет данных";
  if (metrics.status === "fresh") return `свежо · ${formatShortAge(metrics.age_seconds)}`;
  if (metrics.status === "stale") return `устарело · ${formatShortAge(metrics.age_seconds)}`;
  return "нет среза";
}

function userStatusLabel(status: AdminUserRow["status"]): string {
  if (status === "active") return "Активен";
  if (status === "expired") return "Истёк";
  if (status === "blocked") return "Ограничен";
  return "Проверка";
}

function observerLabel(state: AdminUserRow["observer_state"]): string {
  if (state === "suspicious") return "Риск";
  if (state === "watch") return "Наблюдение";
  return "Ок";
}

function userStatusTone(row: AdminUserRow): "success" | "warning" | "danger" | "neutral" {
  if (row.status === "active") return "success";
  if (row.status === "expired") return "warning";
  if (row.status === "blocked") return "danger";
  return "neutral";
}

function observerTone(state: AdminUserRow["observer_state"]): "success" | "warning" | "danger" {
  if (state === "suspicious") return "danger";
  if (state === "watch") return "warning";
  return "success";
}

function nodeScoreTone(score: number): "success" | "warning" | "danger" {
  if (score >= 8) return "success";
  if (score >= 5) return "warning";
  return "danger";
}

function nodeScoreLabel(score: number): string {
  if (score >= 8) return "стабильно";
  if (score >= 5) return "проверить";
  return "риск";
}

function DashboardCell({
  title,
  subtitle,
  actions,
  children,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
}) {
  return (
    <article className={adminPanelClass("neutral")}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-slate-50">{title}</h2>
          {subtitle ? <p className="mt-1 text-sm leading-6 text-slate-400">{subtitle}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2">{actions}</div> : null}
      </div>
      <div className="mt-4">{children}</div>
    </article>
  );
}

function AdminDashboardSkeleton() {
  return (
    <section className="space-y-4" aria-busy="true" aria-live="polite">
      <div className="h-28 animate-pulse rounded-[1rem] bg-slate-200/80" />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-24 animate-pulse rounded-[1rem] bg-slate-200/80" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="h-72 animate-pulse rounded-[1rem] bg-slate-200/80" />
        ))}
      </div>
    </section>
  );
}

export default function AdminDashboardPage() {
  const { loading: sessionLoading, user, webLoginRequired } = usePortalSession();
  const [summary, setSummary] = useState<AdminSummaryPayload | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsStatus | null>(null);
  const [series, setSeries] = useState<AdminMetricsPoint[]>([]);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [tickets, setTickets] = useState<TicketInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async (): Promise<void> => {
    if (sessionLoading || webLoginRequired || !user?.is_admin) return;
    setLoading(true);
    setError("");
    try {
      const range = lastDaysRange(7);
      const [summaryPayload, metricsPayload, seriesPayload, usersPayload, ticketsPayload] = await Promise.all([
        adminSummary(),
        adminMetricsStatus(),
        adminMetricsTimeseries(range),
        adminUsers({ page_size: 7 }),
        adminTickets("", 6),
      ]);

      setSummary(summaryPayload);
      setMetrics(metricsPayload);
      setSeries(seriesPayload.points || []);
      setUsers(usersPayload.users || []);
      setTickets(ticketsPayload || []);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить административную сводку."));
    } finally {
      setLoading(false);
    }
  }, [sessionLoading, user?.is_admin, webLoginRequired]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const totals = useMemo(
    () =>
      (series || []).reduce(
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

  const alertItems = useMemo(() => {
    if (!summary) return [];

    const items = [
      summary.errors.stale_metrics
        ? {
            title: "Срез по метрикам устарел",
            body: metrics?.last_sample_at
              ? `Последний срез: ${fmtRuDate(metrics.last_sample_at)}. Возраст: ${formatShortAge(metrics.age_seconds)}.`
              : "Нужно проверить сборщик метрик и таймер.",
            tone: "warning" as const,
          }
        : null,
      Number(summary.errors.unhealthy_nodes || 0) > 0
        ? {
            title: "Есть ноды с риском",
            body: `${summary.errors.unhealthy_nodes} нод требуют внимания по health score или свежести телеметрии.`,
            tone: "danger" as const,
          }
        : null,
      Number(summary.errors.payment_callback_failures_24h || 0) > 0
        ? {
            title: "Проблемы с платёжными callback",
            body: `${summary.errors.payment_callback_failures_24h} сбоев за 24 часа.`,
            tone: "warning" as const,
          }
        : null,
      Number(summary.errors.subscription_numeric_fallbacks_24h || 0) > 0
        ? {
            title: "Срабатывал резервный lookup подписок",
            body: `${summary.errors.subscription_numeric_fallbacks_24h} случаев за 24 часа. Проверьте миграцию на токены.`,
            tone: "warning" as const,
          }
        : null,
      summary.resilience.single_point_risk
        ? {
            title: "Есть риск единой точки отказа",
            body: "Перед релизом проверьте резерв по нодам и устойчивость управляющей панели.",
            tone: "danger" as const,
          }
        : null,
      Number(summary.tickets.open || 0) > 0
        ? {
            title: "Очередь поддержки не пустая",
            body: `${summary.tickets.open} открытых кейсов ждут реакции оператора.`,
            tone: "accent" as const,
          }
        : null,
    ].filter(Boolean) as Array<{ title: string; body: string; tone: "warning" | "danger" | "accent" }>;

    if (!items.length) {
      return [
        {
          title: "Критичных сигналов сейчас нет",
          body: "Можно спокойно пройтись по пользователям, нодам и очередям без пожарного режима.",
          tone: "success" as const,
        },
      ];
    }

    return items.slice(0, 5);
  }, [metrics, summary]);

  const registrationsSeries = useMemo(() => series.map((point) => Number(point.registrations || 0)), [series]);
  const churnSeries = useMemo(() => series.map((point) => Number(point.churn || 0)), [series]);
  const revenueSeries = useMemo(() => series.map((point) => Number(point.revenue_rub || 0)), [series]);

  if (loading) {
    return <AdminDashboardSkeleton />;
  }

  if (error) {
    return (
      <section className={adminPanelClass("danger")}>
        <AdminSurfaceHeader
          title="Не получилось собрать административную сводку"
          description={error}
          actions={
            <button type="button" onClick={() => void refresh()} className={adminButtonClass("primary")}>
              Повторить
            </button>
          }
        />
      </section>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminSurfaceHeader
          title="Сводка"
          description="Основной экран смены: очереди, риски, свежесть данных и ближайшие действия по пользователям и сети."
          actions={
            <>
              <button type="button" onClick={() => void refresh()} className={adminButtonClass("secondary", "sm")}>
                Обновить
              </button>
              <AppRouteLink href="/admin/users" className={adminButtonClass("secondary", "sm")}>
                Пользователи
              </AppRouteLink>
              <AppRouteLink href="/admin/nodes" className={adminButtonClass("secondary", "sm")}>
                Ноды
              </AppRouteLink>
              <AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "sm")}>
                Обращения
              </AppRouteLink>
            </>
          }
          meta={
            <>
              <AdminBadge tone={metrics?.status === "fresh" ? "success" : metrics?.status === "stale" ? "warning" : "danger"}>
                Метрики: {metricsLabel(metrics)}
              </AdminBadge>
              <AdminBadge tone={summary.nodes.healthy === summary.nodes.total ? "success" : "warning"}>
                Ноды: {summary.nodes.healthy} / {summary.nodes.total}
              </AdminBadge>
              <AdminBadge tone={summary.tickets.open > 0 ? "warning" : "success"}>Открытые тикеты: {summary.tickets.open}</AdminBadge>
            </>
          }
        />
      </article>

      <AdminMetricStrip
        items={[
          {
            label: "Пользователи",
            value: `${summary.users.active} / ${summary.users.total}`,
            hint: `Платные: ${summary.users.paid} · Базовый режим: ${summary.users.free}`,
          },
          {
            label: "Открытые тикеты",
            value: String(summary.tickets.open),
            hint: "Очередь, которую лучше не оставлять без ответа.",
            tone: summary.tickets.open > 0 ? "warning" : "success",
          },
          {
            label: "Ноды готовы",
            value: `${summary.nodes.healthy} / ${summary.nodes.total}`,
            hint: `Метрики: ${metricsLabel(metrics)}`,
            tone: summary.errors.unhealthy_nodes > 0 ? "warning" : "success",
          },
          {
            label: "Выручка за 7 дней",
            value: formatRub(totals.revenueRub),
            hint: `Регистрации: ${totals.registrations} · Отток: ${totals.churn}`,
          },
        ]}
      />

      <div className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr_0.92fr]">
        <DashboardCell
          title="Как читать эту страницу"
          subtitle="Сначала оцените свежесть метрик, затем очереди и только после этого переходите в глубину."
        >
          <div className="space-y-3 text-sm text-slate-400">
            <div className="rounded-[0.9rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="font-semibold text-slate-100">1. Риски и ошибки</p>
              <p className="mt-1 text-xs leading-5">Если здесь есть danger или warning, разберите их раньше ручных задач.</p>
            </div>
            <div className="rounded-[0.9rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="font-semibold text-slate-100">2. Открытые очереди</p>
              <p className="mt-1 text-xs leading-5">Проверьте тикеты, пользователей под наблюдением и истекающие доступы.</p>
            </div>
            <div className="rounded-[0.9rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="font-semibold text-slate-100">3. Сеть и устойчивость</p>
              <p className="mt-1 text-xs leading-5">Если телеметрия свежая, идите в ноды и rollout только по конкретным сигналам.</p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            <AppRouteLink href="/admin/users" className={adminButtonClass("secondary", "xs")}>
              Пользователи
            </AppRouteLink>
            <AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "xs")}>
              Очередь поддержки
            </AppRouteLink>
            <AppRouteLink href="/admin/nodes" className={adminButtonClass("secondary", "xs")}>
              Состояние нод
            </AppRouteLink>
          </div>
        </DashboardCell>

        <DashboardCell
          title="Сводка ошибок и рисков"
          subtitle="Показывает только то, что требует решения или осознанного подтверждения."
        >
          <div className="space-y-3">
            {alertItems.map((item) => (
              <div key={item.title} className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-100">{item.title}</p>
                  <AdminBadge tone={item.tone}>{item.tone === "danger" ? "Риск" : item.tone === "warning" ? "Проверить" : item.tone === "success" ? "Норма" : "Очередь"}</AdminBadge>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.body}</p>
              </div>
            ))}
          </div>
        </DashboardCell>

        <DashboardCell
          title="Открытые очереди"
          subtitle="Срез по темам, которые обычно всплывают в начале смены."
        >
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Observer</p>
              <div className="mt-2 flex flex-wrap gap-2">
                <AdminBadge tone={summary.observer.watch_users > 0 ? "warning" : "neutral"}>Observer watch</AdminBadge>
                <AdminBadge tone={summary.observer.suspicious_users > 0 ? "danger" : "neutral"}>Observer suspicious</AdminBadge>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-400">
                Watch: {summary.observer.watch_users} · Suspicious: {summary.observer.suspicious_users}
              </p>
            </div>
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Поддержка</p>
              <p className="mt-2 text-2xl font-semibold text-slate-50">{summary.tickets.open}</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">Открытые кейсы в очереди оператора.</p>
            </div>
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Удержание</p>
              <p className="mt-2 text-lg font-semibold text-slate-50">{summary.retention.expiring_3d} / {summary.retention.expired_7d}</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">Истекают за 3 дня / истекли за 7 дней.</p>
            </div>
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Реактивация</p>
              <p className="mt-2 text-2xl font-semibold text-slate-50">{summary.retention.reactivation_candidates}</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">Кандидаты на возврат без ручного поиска.</p>
            </div>
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Бонусы за 24ч</p>
              <p className="mt-2 text-lg font-semibold text-slate-50">
                {summary.bonus_events_24h.channel_activated} / {summary.bonus_events_24h.channel_denied}
              </p>
              <p className="mt-1 text-xs leading-5 text-slate-400">Выдано / отказано по бонусу за канал.</p>
            </div>
          </div>
        </DashboardCell>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.08fr_0.92fr]">
        <DashboardCell
          title="Пользователи под разбор"
          subtitle="Быстрый срез очереди по людям без перехода в полный users view."
          actions={
            <AppRouteLink href="/admin/users" className={adminButtonClass("secondary", "xs")}>
              Открыть таблицу
            </AppRouteLink>
          }
        >
          <div className="overflow-hidden rounded-[1rem] border border-[#22303c]">
            <div className="overflow-x-auto">
              <div className="min-w-[620px]">
                <div className="sticky top-0 grid grid-cols-[minmax(0,1.35fr)_110px_120px_110px] gap-3 border-b border-[#22303c] bg-[#101821] px-3 py-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                  <span>Пользователь</span>
                  <span>Статус</span>
                  <span>Observer</span>
                  <span>Срок</span>
                </div>

                <div className="divide-y divide-[#22303c] bg-[#0b1218]">
                  {users.length ? (
                    users.map((row) => (
                      <div key={row.tg_id} className="grid grid-cols-[minmax(0,1.35fr)_110px_120px_110px] gap-3 px-3 py-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-slate-100">{row.display_name || row.username || `ID ${row.tg_id}`}</p>
                          <p className="mt-1 truncate text-xs text-slate-500">
                            {row.username ? `@${row.username}` : `ID ${row.tg_id}`} · {row.origin}
                          </p>
                        </div>
                        <div>
                          <AdminBadge tone={userStatusTone(row)}>{userStatusLabel(row.status)}</AdminBadge>
                        </div>
                        <div>
                          <AdminBadge tone={observerTone(row.observer_state)}>{observerLabel(row.observer_state)}</AdminBadge>
                        </div>
                        <div className="text-sm font-medium text-slate-300">{formatShortDate(row.expiry_at)}</div>
                      </div>
                    ))
                  ) : (
                    <AdminEmptyState className="m-3 min-h-[150px]" title="Пользователей под разбор сейчас нет." />
                  )}
                </div>
              </div>
            </div>
          </div>
        </DashboardCell>

        <DashboardCell
          title="Очередь поддержки"
          subtitle="Последние кейсы, чтобы быстро понять, что уже ждёт ответа."
          actions={
            <AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "xs")}>
              Открыть очередь
            </AppRouteLink>
          }
        >
          <div className="space-y-3">
            {tickets.length ? (
              tickets.map((ticket) => (
                <div key={ticket.id} className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-slate-100">{ticket.subject || `Тикет #${ticket.id}`}</p>
                    <AdminBadge>{ticket.status_title}</AdminBadge>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{ticket.last_message_preview || "Без превью последнего сообщения."}</p>
                  <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-slate-400">Обновлён: {fmtRuDate(ticket.updated_at)}</p>
                </div>
              ))
            ) : (
              <AdminEmptyState className="min-h-[180px]" title="Очередь поддержки пуста." />
            )}
          </div>
        </DashboardCell>
      </div>

      <div className="grid gap-4 xl:grid-cols-[0.92fr_1.08fr]">
        <DashboardCell title="Движение за 7 дней" subtitle="Компактный графический срез без перехода в отдельную аналитику.">
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Регистрации</p>
              <p className="mt-2 text-xl font-semibold text-slate-50">{totals.registrations}</p>
              <div className="mt-4">
                <MiniBars values={registrationsSeries} tone="emerald" />
              </div>
            </div>
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Отток</p>
              <p className="mt-2 text-xl font-semibold text-slate-50">{totals.churn}</p>
              <div className="mt-4">
                <MiniBars values={churnSeries} tone="rose" />
              </div>
            </div>
            <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Выручка</p>
              <p className="mt-2 text-xl font-semibold text-slate-50">{formatRub(totals.revenueRub)}</p>
              <div className="mt-4">
                <MiniBars values={revenueSeries} tone="slate" />
              </div>
            </div>
          </div>
        </DashboardCell>

        <DashboardCell title="Сеть и устойчивость" subtitle="Ноды, резерв и бонусные контуры, которые стоит проверить до ручных действий.">
          <div className="space-y-3">
            {summary.top_nodes.map((node) => (
              <div key={node.code} className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-100">{node.code}</p>
                    <p className="mt-1 text-xs text-slate-400">Клиенты: {node.active_clients} · задержка: {node.panel_latency_ms ?? "—"} мс</p>
                  </div>
                  <AdminBadge tone={nodeScoreTone(node.health_score)}>
                    {nodeScoreLabel(node.health_score)} · {node.health_score}
                  </AdminBadge>
                </div>
                <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-slate-400">Последняя проверка: {fmtRuDate(node.last_health_at)}</p>
              </div>
            ))}

            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Устойчивость</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <AdminBadge tone={summary.resilience.free_node_enabled ? "success" : "warning"}>
                    бесплатный узел {summary.resilience.free_node_enabled ? "включён" : "выключен"}
                  </AdminBadge>
                  <AdminBadge tone={summary.resilience.single_point_risk ? "danger" : "success"}>
                    {summary.resilience.single_point_risk ? "есть риск одной точки" : "резерв есть"}
                  </AdminBadge>
                </div>
              </div>
              <div className="rounded-[0.95rem] border border-[#22303c] bg-[#111922] p-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">Бонусы и промо</p>
                <p className="mt-2 text-sm text-slate-100">
                  Канал: <strong>{summary.bonus_events_24h.channel_activated}</strong> / отказов <strong>{summary.bonus_events_24h.channel_denied}</strong>
                </p>
                <p className="mt-1 text-sm text-slate-100">
                  Промо: <strong>{summary.bonus_events_24h.promo_redeemed}</strong> / отказов <strong>{summary.bonus_events_24h.promo_denied}</strong>
                </p>
              </div>
            </div>
          </div>
        </DashboardCell>
      </div>
    </section>
  );
}
