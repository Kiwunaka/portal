"use client";

import { adminMetricsStatus, adminMetricsTimeseries, adminSummary, type AdminMetricsPoint, type AdminMetricsStatus, type AdminSummaryPayload } from "@/lib/api";
import { useEffect, useMemo, useState } from "react";
import { fmtRuDate } from "../nav";

function lastDaysRange(days: number): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - Math.max(1, days - 1));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
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

  return (
    <section className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <article className="glass-card p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Пользователи</p>
          <p className="mt-2 text-2xl font-bold">{summary?.users.total ?? "—"}</p>
          <p className="text-xs text-slate-500">Активные: {summary?.users.active ?? "—"}</p>
        </article>
        <article className="glass-card p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Тикеты</p>
          <p className="mt-2 text-2xl font-bold">{summary?.tickets.open ?? "—"}</p>
          <p className="text-xs text-slate-500">Открытых обращений</p>
        </article>
        <article className="glass-card p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Ноды</p>
          <p className="mt-2 text-2xl font-bold">{summary?.nodes.healthy ?? "—"} / {summary?.nodes.total ?? "—"}</p>
          <p className={`text-xs ${metrics?.status === "fresh" ? "text-emerald-500" : "text-amber-500"}`}>
            Метрики: {metrics?.status === "fresh" ? "fresh" : "stale"}
          </p>
        </article>
        <article className="glass-card p-4">
          <p className="text-xs uppercase tracking-[0.12em] text-slate-500">Выручка (7д)</p>
          <p className="mt-2 text-2xl font-bold">{Math.round(totals.revenueRub)} ₽</p>
          <p className="text-xs text-slate-500">{totals.revenueStars} ⭐</p>
        </article>
      </div>

      <div className="glass-card p-4">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-2xl font-semibold">Дневные метрики (7 дней)</h2>
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void refresh()}>
            Обновить
          </button>
        </div>
        {loading ? <p className="text-sm text-slate-500">Загрузка...</p> : null}
        {error ? <p className="text-sm text-rose-500">{error}</p> : null}
        {!loading && !error ? (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="px-2 py-2">Дата</th>
                  <th className="px-2 py-2">Регистрации</th>
                  <th className="px-2 py-2">Отток</th>
                  <th className="px-2 py-2">RUB</th>
                  <th className="px-2 py-2">Stars</th>
                </tr>
              </thead>
              <tbody>
                {series.map((point) => (
                  <tr key={point.date} className="border-t border-white/30 dark:border-white/10">
                    <td className="px-2 py-2">{fmtRuDate(point.date)}</td>
                    <td className="px-2 py-2">{point.registrations}</td>
                    <td className="px-2 py-2">{point.churn}</td>
                    <td className="px-2 py-2">{Math.round(point.revenue_rub || 0)} ₽</td>
                    <td className="px-2 py-2">{point.revenue_stars}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      <div className="glass-card p-4">
        <h2 className="font-display text-2xl font-semibold">Топ нод</h2>
        <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {(summary?.top_nodes || []).map((node) => (
            <article key={node.code} className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
              <div className="flex items-center justify-between">
                <strong>{node.code.toUpperCase()}</strong>
                <span className="text-xs text-slate-500">{node.health_score.toFixed(1)}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">Latency: {node.panel_latency_ms ?? "—"} ms</p>
              <p className="text-xs text-slate-500">Clients: {node.active_clients}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="glass-card p-4 text-sm text-slate-500">
        Итого за 7 дней: регистрации {totals.registrations}, отток {totals.churn}, выручка {Math.round(totals.revenueRub)} ₽ и {totals.revenueStars} ⭐.
      </div>
    </section>
  );
}
