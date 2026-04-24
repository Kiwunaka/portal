"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  AdminBadge,
  AdminEmptyState,
  AdminMetricStrip,
  AdminPanelHeader,
  AdminSurfaceHeader,
  adminButtonClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTableShellClass,
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
import { useCallback, useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

function lastDaysRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - Math.max(1, days - 1));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function formatRub(value?: number | null): string {
  if (value == null || Number.isNaN(Number(value))) return "0 RUB";
  return `${new Intl.NumberFormat("ru-RU").format(Math.round(Number(value)))} RUB`;
}

function formatShortAge(seconds?: number | null): string {
  if (seconds == null || Number.isNaN(Number(seconds))) return "no data";
  const total = Math.max(0, Math.round(Number(seconds)));
  if (total < 60) return `${total}s`;
  if (total < 3600) return `${Math.round(total / 60)}m`;
  if (total < 86400) return `${Math.round(total / 3600)}h`;
  return `${Math.round(total / 86400)}d`;
}

function metricsLabel(metrics: AdminMetricsStatus | null): string {
  if (!metrics) return "no data";
  if (metrics.status === "fresh") return `fresh · ${formatShortAge(metrics.age_seconds)}`;
  if (metrics.status === "stale") return `stale · ${formatShortAge(metrics.age_seconds)}`;
  return "missing sample";
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

function actionHref(title: string): string {
  const value = title.toLowerCase();
  if (value.includes("node") || value.includes("узл") || value.includes("metrics")) return "/admin/nodes";
  if (value.includes("payment")) return "/admin/promos";
  if (value.includes("support")) return "/admin/tickets";
  if (value.includes("recovery") || value.includes("восстанов")) return "/admin/users";
  return "/admin/dashboard";
}

function MiniBars({ values, tone = "emerald" }: { values: number[]; tone?: "emerald" | "rose" | "slate" }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const color = tone === "rose" ? "bg-rose-400" : tone === "slate" ? "bg-slate-400" : "bg-emerald-300";
  return (
    <div className="flex h-9 items-end gap-[4px]">
      {values.map((value, index) => (
        <div key={index} className={`w-[7px] rounded-sm ${color}`} style={{ height: `${Math.max(10, (Number(value || 0) / max) * 100)}%` }} />
      ))}
    </div>
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
      setError(String((err as { message?: string })?.message || err || "Could not load admin overview."));
    } finally {
      setLoading(false);
    }
  }, [sessionLoading, user?.is_admin, webLoginRequired]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const totals = useMemo(() => (series || []).reduce(
    (acc, point) => {
      acc.registrations += Number(point.registrations || 0);
      acc.churn += Number(point.churn || 0);
      acc.revenueRub += Number(point.revenue_rub || 0);
      return acc;
    },
    { registrations: 0, churn: 0, revenueRub: 0 },
  ), [series]);

  const alerts = useMemo(() => {
    if (!summary) return [];
    const next = [
      summary.errors.stale_metrics ? { title: "Metrics are stale", body: `Last sample: ${fmtRuDate(metrics?.last_sample_at)} · age ${formatShortAge(metrics?.age_seconds)}.`, tone: "warning" as const } : null,
      Number(summary.errors.unhealthy_nodes || 0) > 0 ? { title: "Риск по узлам", body: `${summary.errors.unhealthy_nodes} узл. требуют проверки.`, tone: "danger" as const } : null,
      Number(summary.errors.payment_callback_failures_24h || 0) > 0 ? { title: "Payment callback failures", body: `${summary.errors.payment_callback_failures_24h} failure(s) in 24h.`, tone: "warning" as const } : null,
      Number(summary.errors.subscription_numeric_fallbacks_24h || 0) > 0 ? { title: "Проверки восстановления", body: `${summary.errors.subscription_numeric_fallbacks_24h} проверок восстановления за 24 часа.`, tone: "warning" as const } : null,
      summary.resilience.single_point_risk ? { title: "Single point risk", body: "Review node reserve and control-plane resilience before release work.", tone: "danger" as const } : null,
      Number(summary.tickets.open || 0) > 0 ? { title: "Support queue is not empty", body: `${summary.tickets.open} open ticket(s) need operator attention.`, tone: "accent" as const } : null,
    ].filter(Boolean) as Array<{ title: string; body: string; tone: "warning" | "danger" | "accent" }>;
    return next.length ? next : [{ title: "No critical signals", body: "Scan users, tickets, and nodes without fire-drill mode.", tone: "accent" as const }];
  }, [metrics, summary]);

  if (loading) {
    return (
      <section className="space-y-4" aria-busy="true">
        <div className="h-28 animate-pulse rounded-[1rem] bg-[#f8fffc]" />
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => <div key={index} className="h-24 animate-pulse rounded-[1rem] bg-[#f8fffc]" />)}
        </div>
      </section>
    );
  }

  if (error) {
    return (
      <section className={adminPanelClass("danger")}>
        <AdminSurfaceHeader
          title="Could not load overview"
          description={error}
          actions={<button type="button" onClick={() => void refresh()} className={adminButtonClass("primary")}>Retry</button>}
        />
      </section>
    );
  }

  if (!summary) return null;

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminSurfaceHeader
          title="Операторская сводка"
          description="Старт смены: свежесть метрик, очереди, здоровье узлов, последние пользователи и нагрузка поддержки."
          actions={
            <>
              <button type="button" onClick={() => void refresh()} className={adminButtonClass("secondary", "sm")}>Обновить</button>
              <AppRouteLink href="/admin/users" className={adminButtonClass("secondary", "sm")}>Пользователи</AppRouteLink>
              <AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "sm")}>Обращения</AppRouteLink>
            </>
          }
          meta={
            <>
              <AdminBadge tone={metrics?.status === "fresh" ? "success" : metrics?.status === "stale" ? "warning" : "danger"}>Метрики: {metricsLabel(metrics)}</AdminBadge>
              <AdminBadge tone={summary.nodes.healthy === summary.nodes.total ? "success" : "warning"}>Узлы: {summary.nodes.healthy} / {summary.nodes.total}</AdminBadge>
              <AdminBadge tone={summary.tickets.open > 0 ? "warning" : "success"}>Открытые обращения: {summary.tickets.open}</AdminBadge>
            </>
          }
        />
      </article>

      <AdminMetricStrip
        items={[
          { label: "пользователи", value: `${summary.users.active} / ${summary.users.total}`, hint: `Платные ${summary.users.paid} · бесплатные ${summary.users.free}` },
          { label: "обращения", value: summary.tickets.open, hint: "Открытые кейсы поддержки.", tone: summary.tickets.open ? "warning" : "success" },
          { label: "здоровые узлы", value: `${summary.nodes.healthy} / ${summary.nodes.total}`, hint: metricsLabel(metrics), tone: summary.errors.unhealthy_nodes ? "warning" : "success" },
          { label: "доход 7 дней", value: formatRub(totals.revenueRub), hint: `Регистрации ${totals.registrations} · отток ${totals.churn}` },
        ]}
      />

      <div className="grid gap-4 xl:grid-cols-[1fr,1.1fr,0.9fr]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="как читать" title="Как читать эту страницу" />
          <div className="space-y-2 text-sm text-slate-400">
            <div className={adminInsetPanelClass}>Сначала проверьте свежесть метрик и ошибки.</div>
            <div className={adminInsetPanelClass}>Затем разберите пользователей, обращения и узлы с риском.</div>
            <div className={adminInsetPanelClass}>Ручные действия запускайте только после оценки затронутых пользователей.</div>
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="риски" title="Сводка ошибок и рисков" />
          <div className="space-y-3">
            {alerts.map((item) => (
              <div key={item.title} className={adminInsetPanelClass}>
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-100">{item.title}</p>
                  <AdminBadge tone={item.tone}>{item.tone}</AdminBadge>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{item.body}</p>
              </div>
            ))}
          </div>
        </article>

        <article className={adminPanelClass("accent")}>
          <AdminPanelHeader eyebrow="action queue" title="Очередь действий смены" />
          <div className="space-y-2">
            {alerts.map((item, index) => (
              <div key={`${item.title}-${index}`} className={adminInsetPanelClass}>
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-100">{item.title}</p>
                    <p className="mt-1 text-xs leading-5 text-slate-400">{item.body}</p>
                  </div>
                  <AdminBadge tone={item.tone}>{index + 1}</AdminBadge>
                </div>
                <AppRouteLink href={actionHref(item.title)} className={`${adminButtonClass("secondary", "xs")} mt-2`}>
                  Открыть рабочий раздел
                </AppRouteLink>
              </div>
            ))}
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="people" title="Пользователи на проверке" actions={<AppRouteLink href="/admin/users" className={adminButtonClass("secondary", "xs")}>Открыть список</AppRouteLink>} />
          <div className={adminTableShellClass}>
            <div className="overflow-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr className="border-b border-[#c6e6db] bg-[#f8fffc] text-left uppercase tracking-[0.14em] text-slate-500">
                    <th className="px-3 py-3">Пользователь</th>
                    <th className="px-3 py-3">Status</th>
                    <th className="px-3 py-3">Observer</th>
                    <th className="px-3 py-3">Expiry</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((row) => (
                    <tr key={row.tg_id} className="border-t border-[#c6e6db]">
                      <td className="px-3 py-3">
                        <p className="font-semibold text-slate-100">{row.display_name || row.username || `ID ${row.tg_id}`}</p>
                        <p className="mt-1 text-slate-500">{row.username ? `@${row.username}` : `ID ${row.tg_id}`} · {row.origin}</p>
                      </td>
                      <td className="px-3 py-3"><AdminBadge tone={userStatusTone(row)}>{row.status}</AdminBadge></td>
                      <td className="px-3 py-3"><AdminBadge tone={observerTone(row.observer_state)}>{row.observer_state}</AdminBadge></td>
                      <td className="px-3 py-3 text-slate-400">{fmtRuDate(row.expiry_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!users.length ? <AdminEmptyState title="No users returned" /> : null}
            </div>
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="support" title="Очередь обращений" actions={<AppRouteLink href="/admin/tickets" className={adminButtonClass("secondary", "xs")}>Открыть обращения</AppRouteLink>} />
          <div className="space-y-3">
            {tickets.map((ticket) => (
              <div key={ticket.id} className={adminInsetPanelClass}>
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-100">{ticket.subject || `Ticket #${ticket.id}`}</p>
                  <AdminBadge>{ticket.status_title}</AdminBadge>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{ticket.last_message_preview || "No preview."}</p>
                <p className="mt-2 text-[11px] uppercase tracking-[0.14em] text-slate-500">Updated {fmtRuDate(ticket.updated_at)}</p>
              </div>
            ))}
            {!tickets.length ? <AdminEmptyState title="No tickets returned" /> : null}
          </div>
        </article>
      </div>

      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader eyebrow="observer" title="Observer-lite counters" />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone={summary.observer.watch_users > 0 ? "warning" : "neutral"}>Observer watch</AdminBadge>
          <AdminBadge tone={summary.observer.suspicious_users > 0 ? "danger" : "neutral"}>Observer suspicious</AdminBadge>
        </div>
      </article>

      <div className="grid gap-4 xl:grid-cols-[0.9fr,1.1fr]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="7 day movement" title="Registrations, churn, revenue" />
          <div className="grid gap-3 md:grid-cols-3">
            <div className={adminInsetPanelClass}><p className="text-xs text-slate-500">Registrations</p><p className="mt-2 text-xl font-semibold">{totals.registrations}</p><MiniBars values={series.map((p) => Number(p.registrations || 0))} /></div>
            <div className={adminInsetPanelClass}><p className="text-xs text-slate-500">Churn</p><p className="mt-2 text-xl font-semibold">{totals.churn}</p><MiniBars values={series.map((p) => Number(p.churn || 0))} tone="rose" /></div>
            <div className={adminInsetPanelClass}><p className="text-xs text-slate-500">Revenue</p><p className="mt-2 text-xl font-semibold">{formatRub(totals.revenueRub)}</p><MiniBars values={series.map((p) => Number(p.revenue_rub || 0))} tone="slate" /></div>
          </div>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="сеть" title="Ключевые узлы" actions={<AppRouteLink href="/admin/nodes" className={adminButtonClass("secondary", "xs")}>Открыть узлы</AppRouteLink>} />
          <div className="grid gap-3 md:grid-cols-2">
            {summary.top_nodes.map((node) => (
              <div key={node.code} className={adminInsetPanelClass}>
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-slate-100">{node.code}</p>
                  <AdminBadge tone={nodeScoreTone(node.health_score)}>score {node.health_score}</AdminBadge>
                </div>
                <p className="mt-2 text-xs text-slate-400">Clients {node.active_clients} · latency {node.panel_latency_ms ?? "-"} ms</p>
                <p className="mt-1 text-[11px] uppercase tracking-[0.14em] text-slate-500">Last health {fmtRuDate(node.last_health_at)}</p>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  );
}
