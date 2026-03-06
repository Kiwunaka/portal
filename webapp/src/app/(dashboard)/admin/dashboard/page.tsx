"use client";

import { adminMetricsStatus, adminMetricsTimeseries, adminSummary, type AdminMetricsPoint, type AdminMetricsStatus, type AdminSummaryPayload } from "@/lib/api";
import { Activity, RefreshCw, Server, Star, TrendingUp, Users, Ticket, ArrowUp, ArrowDown, AlertTriangle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

function lastDaysRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - Math.max(1, days - 1));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function MiniBar({ values, color = "violet" }: { values: number[]; color?: string }) {
  if (!values.length) return null;
  const max = Math.max(...values, 1);
  const colorClass = color === "emerald" ? "bg-emerald-500" : color === "rose" ? "bg-rose-500" : "bg-violet-500";
  return (
    <div className="flex items-end gap-[3px] h-8">
      {values.map((value, index) => (
        <div
          key={index}
          className={`w-[5px] rounded-sm ${colorClass} transition-all duration-300`}
          style={{ height: `${Math.max(8, (value / max) * 100)}%`, opacity: 0.4 + (value / max) * 0.6 }}
        />
      ))}
    </div>
  );
}

export default function AdminDashboardPage() {
  const [summary, setSummary] = useState<AdminSummaryPayload | null>(null);
  const [metrics, setMetrics] = useState<AdminMetricsStatus | null>(null);
  const [series, setSeries] = useState<AdminMetricsPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = async (): Promise<void> => {
    setLoading(true);
    setError("");
    try {
      const range = lastDaysRange(7);
      const [sum, status, ts] = await Promise.all([
        adminSummary(),
        adminMetricsStatus(),
        adminMetricsTimeseries(range),
      ]);
      setSummary(sum);
      setMetrics(status);
      setSeries(ts.points || []);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const totals = useMemo(() => {
    return (series || []).reduce(
      (acc, point) => {
        acc.registrations += Number(point.registrations || 0);
        acc.churn += Number(point.churn || 0);
        acc.revenueRub += Number(point.revenue_rub || 0);
        acc.revenueStars += Number(point.revenue_stars || 0);
        return acc;
      },
      { registrations: 0, churn: 0, revenueRub: 0, revenueStars: 0 },
    );
  }, [series]);

  const registrationValues = useMemo(() => series.map((p) => Number(p.registrations || 0)), [series]);
  const revenueValues = useMemo(() => series.map((p) => Number(p.revenue_rub || 0)), [series]);
  const errorCards = [
    {
      label: "Метрики",
      value: summary?.errors.stale_metrics ? "stale" : "ok",
      tone: summary?.errors.stale_metrics ? "badge-warning" : "badge-success",
      detail: summary?.errors.stale_metrics ? "нужна проверка timer/collector" : "сэмплы свежие",
    },
    {
      label: "Ноды с риском",
      value: summary?.errors.unhealthy_nodes ?? "—",
      tone: Number(summary?.errors.unhealthy_nodes || 0) > 0 ? "badge-danger" : "badge-success",
      detail: "health score и panel latency",
    },
    {
      label: "Callback ошибки 24ч",
      value: summary?.errors.payment_callback_failures_24h ?? "—",
      tone: Number(summary?.errors.payment_callback_failures_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "invalid signature / processed_ok=false",
    },
    {
      label: "Fallback подписки 24ч",
      value: summary?.errors.subscription_numeric_fallbacks_24h ?? "—",
      tone: Number(summary?.errors.subscription_numeric_fallbacks_24h || 0) > 0 ? "badge-warning" : "badge-success",
      detail: "случаи lookup по tg_id",
    },
    {
      label: "Открытые тикеты",
      value: summary?.errors.open_tickets ?? "—",
      tone: Number(summary?.errors.open_tickets || 0) > 0 ? "badge-info" : "badge-success",
      detail: "очередь поддержки",
    },
  ];

  const statCards = [
    {
      label: "Пользователи",
      value: summary?.users.total ?? "—",
      sub: `Активные: ${summary?.users.active ?? "—"}`,
      icon: Users,
      iconClass: "stat-icon-violet",
      sparkline: registrationValues,
      sparkColor: "violet" as const,
    },
    {
      label: "Тикеты",
      value: summary?.tickets.open ?? "—",
      sub: "Открытых обращений",
      icon: Ticket,
      iconClass: "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "violet" as const,
    },
    {
      label: "Ноды",
      value: `${summary?.nodes.healthy ?? "—"} / ${summary?.nodes.total ?? "—"}`,
      sub: metrics?.status === "fresh" ? "Метрики актуальны" : "Метрики устарели",
      icon: Server,
      iconClass: metrics?.status === "fresh" ? "stat-icon-emerald" : "stat-icon-amber",
      sparkline: [] as number[],
      sparkColor: "emerald" as const,
    },
    {
      label: "Выручка (7д)",
      value: `${Math.round(totals.revenueRub)} ₽`,
      sub: `${totals.revenueStars} ⭐`,
      icon: TrendingUp,
      iconClass: "stat-icon-emerald",
      sparkline: revenueValues,
      sparkColor: "emerald" as const,
    },
  ];

  return (
    <section className="space-y-5">
      {/* ── Stat cards ─────────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <article key={card.label} className="stat-card p-5">
              <div className="flex items-start justify-between gap-3">
                <div className={`stat-icon ${card.iconClass}`}>
                  <Icon size={20} />
                </div>
                {card.sparkline.length > 0 ? <MiniBar values={card.sparkline} color={card.sparkColor} /> : null}
              </div>
              <p className="mt-3 text-3xl font-bold gradient-text">{card.value}</p>
              <p className="mt-1 text-xs uppercase tracking-[0.12em] text-slate-500">{card.label}</p>
              <p className="mt-0.5 text-xs text-slate-500">{card.sub}</p>
            </article>
          );
        })}
      </div>

      {/* ── Metrics table ──────────────────────────────── */}
      <div className="glass-card p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <Activity size={20} />
            </div>
            <div>
              <h2 className="font-display text-xl font-bold">Дневные метрики</h2>
              <p className="text-xs text-slate-500">Последние 7 дней</p>
            </div>
          </div>
          <button
            className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-2"
            type="button"
            onClick={() => void refresh()}
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Обновить
          </button>
        </div>
        {loading ? <p className="text-sm text-slate-500">Загрузка...</p> : null}
        {error ? <p className="text-sm text-rose-500">{error}</p> : null}
        {!loading && !error ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-3 py-2.5">Дата</th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1"><ArrowUp size={12} className="text-emerald-500" /> Регистрации</span>
                  </th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1"><ArrowDown size={12} className="text-rose-500" /> Отток</span>
                  </th>
                  <th className="px-3 py-2.5">RUB</th>
                  <th className="px-3 py-2.5">
                    <span className="inline-flex items-center gap-1"><Star size={12} className="text-amber-500" /> Stars</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {series.map((point, idx) => (
                  <tr key={point.date} className={`border-t border-white/20 dark:border-white/5 ${idx % 2 === 0 ? "bg-white/30 dark:bg-white/[0.02]" : ""}`}>
                    <td className="px-3 py-2.5 font-medium">{fmtRuDate(point.date)}</td>
                    <td className="px-3 py-2.5">
                      {Number(point.registrations) > 0 ? (
                        <span className="badge badge-success">{point.registrations}</span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      {Number(point.churn) > 0 ? (
                        <span className="badge badge-danger">{point.churn}</span>
                      ) : (
                        <span className="text-slate-400">0</span>
                      )}
                    </td>
                    <td className="px-3 py-2.5 font-medium">{Math.round(point.revenue_rub || 0)} ₽</td>
                    <td className="px-3 py-2.5">{point.revenue_stars}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {/* ── Top nodes ──────────────────────────────────── */}
      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-emerald">
            <Server size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Топ нод</h2>
            <p className="text-xs text-slate-500">Здоровье и метрики по нодам</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {(summary?.top_nodes || []).map((node) => {
            const score = Number(node.health_score || 0);
            const healthPct = Math.min(100, Math.max(0, score * 10));
            const fillClass = score >= 8 ? "progress-fill-emerald" : score >= 5 ? "progress-fill-amber" : "progress-fill-rose";
            return (
              <article key={node.code} className="node-card">
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className={`status-dot ${score >= 8 ? "status-dot-online" : score >= 5 ? "status-dot-warning" : "status-dot-offline"}`} />
                    <strong className="text-sm font-bold">{node.code.toUpperCase()}</strong>
                  </div>
                  <span className={`badge ${score >= 8 ? "badge-success" : score >= 5 ? "badge-warning" : "badge-danger"}`}>
                    {score.toFixed(1)}
                  </span>
                </div>
                <div className="mt-3">
                  <div className="progress-track">
                    <div className={`progress-fill ${fillClass}`} style={{ width: `${healthPct}%` }} />
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                  <span>Задержка: {node.panel_latency_ms ?? "—"} ms</span>
                  <span className="font-medium">{node.active_clients} клиентов</span>
                </div>
              </article>
            );
          })}
          {(summary?.top_nodes || []).length === 0 && !loading ? (
            <div className="empty-state col-span-full">
              <Server size={32} />
              <p className="text-sm">Нет данных о нодах</p>
            </div>
          ) : null}
        </div>
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-amber">
            <AlertTriangle size={20} />
          </div>
          <div>
            <h2 className="font-display text-xl font-bold">Сводка ошибок и рисков</h2>
            <p className="text-xs text-slate-500">То, что сейчас требует внимания оператора</p>
          </div>
        </div>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          {errorCards.map((card) => (
            <article key={card.label} className="node-card">
              <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">{card.label}</p>
              <div className="mt-2 flex items-center gap-2">
                <span className={`badge ${card.tone}`}>{card.value}</span>
              </div>
              <p className="mt-2 text-xs text-slate-500">{card.detail}</p>
            </article>
          ))}
        </div>
      </div>

      {/* ── Summary footer ─────────────────────────────── */}
      <div className="stat-card p-4">
        <div className="flex items-center gap-3">
          <div className="stat-icon stat-icon-violet">
            <Activity size={18} />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-300">
            Итого за 7 дней: <strong>{totals.registrations}</strong> регистраций, <strong>{totals.churn}</strong> отток, выручка <strong>{Math.round(totals.revenueRub)} ₽</strong> и <strong>{totals.revenueStars} ⭐</strong>
          </p>
        </div>
      </div>
      {summary?.errors.stale_metrics || Number(summary?.errors.unhealthy_nodes || 0) > 0 ? (
        <p className="text-xs text-amber-500">
          Проверьте `portal-node-metrics.timer`, свежесть сэмплов и проблемные ноды до релиза.
        </p>
      ) : null}
    </section>
  );
}
