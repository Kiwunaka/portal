"use client";

import { adminMetricsStatus, adminNodesHealth, adminNodesSync, adminNodesTraffic, type AdminMetricsStatus, type AdminNodeHealthRow, type AdminNodeTrafficRow } from "@/lib/api";
import { Activity, Globe, Loader2, RefreshCw, Server, Wifi } from "lucide-react";
import { useEffect, useState } from "react";

const COUNTRY_FLAGS: Record<string, string> = {
  us: "🇺🇸", pl: "🇵🇱", it: "🇮🇹", nl: "🇳🇱", de: "🇩🇪", free: "🆓", brain: "🧠",
};

function range7d(): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - 6);
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

export default function AdminNodesPage() {
  const [nodes, setNodes] = useState<AdminNodeHealthRow[]>([]);
  const [traffic, setTraffic] = useState<AdminNodeTrafficRow[]>([]);
  const [status, setStatus] = useState<AdminMetricsStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [syncTarget, setSyncTarget] = useState("");
  const [error, setError] = useState("");

  const load = async (): Promise<void> => {
    setError("");
    try {
      const r = range7d();
      const [healthRows, metricsStatus, trafficRows] = await Promise.all([
        adminNodesHealth(),
        adminMetricsStatus(),
        adminNodesTraffic(r),
      ]);
      setNodes(healthRows);
      setStatus(metricsStatus);
      setTraffic(trafficRows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки"));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const runSync = async (segment: string): Promise<void> => {
    setBusy(true);
    setSyncTarget(segment);
    setError("");
    try {
      await adminNodesSync({ segment, limit: 200 });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка sync"));
    } finally {
      setBusy(false);
      setSyncTarget("");
    }
  };

  return (
    <section className="space-y-5">
      {/* ── Header ───────────────────────────────────── */}
      <div className="glass-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`stat-icon ${status?.status === "fresh" ? "stat-icon-emerald" : "stat-icon-amber"}`}>
              <Server size={20} />
            </div>
            <div>
              <h2 className="font-display text-xl font-bold">Node Health & Metrics</h2>
              <div className="mt-0.5 flex items-center gap-2">
                <span className={`status-dot ${status?.status === "fresh" ? "status-dot-online" : "status-dot-warning"}`} />
                <p className="text-xs text-slate-500">
                  Timer: <strong>{status?.status || "—"}</strong> • Last sample: {status?.last_sample_at || "—"}
                </p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {["active", "free", "paid"].map((seg) => (
              <button
                key={seg}
                className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold uppercase tracking-[0.08em] inline-flex items-center gap-1.5"
                type="button"
                onClick={() => void runSync(seg)}
                disabled={busy}
              >
                {busy && syncTarget === seg ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                Sync {seg}
              </button>
            ))}
            <button className="btn-primary rounded-xl px-4 py-2 text-xs font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void load()}>
              <Activity size={14} />
              Обновить
            </button>
          </div>
        </div>
        {error ? <p className="mt-3 text-sm text-rose-500">{error}</p> : null}
      </div>

      {/* ── Node cards ────────────────────────────────── */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {nodes.map((node) => {
          const score = Number(node.health_score || 0);
          const healthPct = Math.min(100, Math.max(0, score * 10));
          const fillClass = score >= 8 ? "progress-fill-emerald" : score >= 5 ? "progress-fill-amber" : "progress-fill-rose";
          const flag = COUNTRY_FLAGS[node.code.toLowerCase()] || "🌐";

          return (
            <article key={node.code} className="stat-card p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{flag}</span>
                  <div>
                    <p className="text-lg font-bold">{node.code.toUpperCase()}</p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className={`status-dot ${node.is_healthy ? "status-dot-online" : "status-dot-offline"}`} />
                      <span className={`badge ${node.is_healthy ? "badge-success" : "badge-danger"}`}>
                        {node.is_healthy ? "healthy" : "unhealthy"}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold gradient-text">{score.toFixed(1)}</p>
                  <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">score</p>
                </div>
              </div>

              <div className="mt-4">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1.5">
                  <span>Health</span>
                  <span>{Math.round(healthPct)}%</span>
                </div>
                <div className="progress-track">
                  <div className={`progress-fill ${fillClass}`} style={{ width: `${healthPct}%` }} />
                </div>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">Latency</p>
                  <p className="text-sm font-bold">{node.panel_latency_ms ?? "—"}<span className="text-[10px] text-slate-400"> ms</span></p>
                </div>
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">Error</p>
                  <p className="text-sm font-bold">{(node.panel_error_rate * 100).toFixed(1)}<span className="text-[10px] text-slate-400">%</span></p>
                </div>
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">Clients</p>
                  <p className="text-sm font-bold">{node.active_clients}</p>
                </div>
              </div>

              {node.last_health_at ? (
                <p className="mt-3 text-[10px] text-slate-400 text-right">Last check: {node.last_health_at}</p>
              ) : null}
            </article>
          );
        })}
        {nodes.length === 0 ? (
          <div className="empty-state col-span-full">
            <Globe size={36} />
            <p className="text-sm">Нет данных о нодах</p>
          </div>
        ) : null}
      </div>

      {/* ── Traffic table ─────────────────────────────── */}
      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-blue">
            <Wifi size={20} />
          </div>
          <div>
            <h3 className="font-display text-xl font-bold">Traffic GB/day</h3>
            <p className="text-xs text-slate-500">Детализация за последние 7 дней</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                <th className="px-3 py-2.5">Дата</th>
                <th className="px-3 py-2.5">Node</th>
                <th className="px-3 py-2.5">Devices</th>
                <th className="px-3 py-2.5">Traffic GB</th>
              </tr>
            </thead>
            <tbody>
              {traffic.map((row, idx) => {
                const flag = COUNTRY_FLAGS[row.node_code.toLowerCase()] || "🌐";
                return (
                  <tr key={`${row.date}:${row.node_code}`} className={`border-t border-white/20 dark:border-white/5 ${idx % 2 === 0 ? "bg-white/30 dark:bg-white/[0.02]" : ""}`}>
                    <td className="px-3 py-2.5 font-medium">{row.date}</td>
                    <td className="px-3 py-2.5">
                      <span className="inline-flex items-center gap-1.5">
                        <span>{flag}</span>
                        <strong>{row.node_code.toUpperCase()}</strong>
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <span className="badge badge-info">{row.devices}</span>
                    </td>
                    <td className="px-3 py-2.5 font-mono font-medium">{row.traffic_gb.toFixed(3)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
