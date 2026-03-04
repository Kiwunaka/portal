"use client";

import { adminMetricsStatus, adminNodesHealth, adminNodesSync, adminNodesTraffic, type AdminMetricsStatus, type AdminNodeHealthRow, type AdminNodeTrafficRow } from "@/lib/api";
import { useEffect, useState } from "react";

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
    setError("");
    try {
      await adminNodesSync({ segment, limit: 200 });
      await load();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка sync"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-4">
      <div className="glass-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl font-semibold">Node Health & Metrics</h2>
            <p className={`text-sm ${status?.status === "fresh" ? "text-emerald-500" : "text-amber-500"}`}>
              Timer status: {status?.status || "—"} • last sample: {status?.last_sample_at || "—"}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void runSync("active")} disabled={busy}>
              Sync active
            </button>
            <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void runSync("free")} disabled={busy}>
              Sync free
            </button>
            <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void runSync("paid")} disabled={busy}>
              Sync paid
            </button>
            <button className="btn-primary rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void load()}>
              Обновить
            </button>
          </div>
        </div>
        {error ? <p className="mt-2 text-sm text-rose-500">{error}</p> : null}
      </div>

      <div className="glass-card p-4 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="px-2 py-2">Node</th>
              <th className="px-2 py-2">Healthy</th>
              <th className="px-2 py-2">Score</th>
              <th className="px-2 py-2">Latency</th>
              <th className="px-2 py-2">Error</th>
              <th className="px-2 py-2">Clients</th>
              <th className="px-2 py-2">Last Health</th>
            </tr>
          </thead>
          <tbody>
            {nodes.map((node) => (
              <tr key={node.code} className="border-t border-white/30 dark:border-white/10">
                <td className="px-2 py-2 font-medium">{node.code.toUpperCase()}</td>
                <td className="px-2 py-2">{node.is_healthy ? "yes" : "no"}</td>
                <td className="px-2 py-2">{node.health_score.toFixed(1)}</td>
                <td className="px-2 py-2">{node.panel_latency_ms ?? "—"} ms</td>
                <td className="px-2 py-2">{(node.panel_error_rate * 100).toFixed(1)}%</td>
                <td className="px-2 py-2">{node.active_clients}</td>
                <td className="px-2 py-2 text-xs">{node.last_health_at || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="glass-card p-4 overflow-x-auto">
        <h3 className="mb-2 font-display text-xl font-semibold">Traffic GB/day (7 дней)</h3>
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="px-2 py-2">Дата</th>
              <th className="px-2 py-2">Node</th>
              <th className="px-2 py-2">Devices</th>
              <th className="px-2 py-2">Traffic GB</th>
            </tr>
          </thead>
          <tbody>
            {traffic.map((row) => (
              <tr key={`${row.date}:${row.node_code}`} className="border-t border-white/30 dark:border-white/10">
                <td className="px-2 py-2">{row.date}</td>
                <td className="px-2 py-2">{row.node_code.toUpperCase()}</td>
                <td className="px-2 py-2">{row.devices}</td>
                <td className="px-2 py-2">{row.traffic_gb.toFixed(3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
