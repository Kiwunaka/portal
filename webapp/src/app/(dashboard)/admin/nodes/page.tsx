"use client";

import {
  adminMetricsStatus,
  adminNodeDisable,
  adminNodeDrain,
  adminNodeEnable,
  adminNodeResync,
  adminNodesDrift,
  adminNodesHealth,
  adminNodesSync,
  adminNodesTraffic,
  type AdminMetricsStatus,
  type AdminNodeDriftReport,
  type AdminNodeHealthRow,
  type AdminNodeTrafficRow,
} from "@/lib/api";
import { Activity, Gauge, HardDrive, Loader2, RefreshCw, Server, Wifi } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

const COUNTRY_FLAGS: Record<string, string> = {
  us: "🇺🇸",
  pl: "🇵🇱",
  it: "🇮🇹",
  nl: "🇳🇱",
  de: "🇩🇪",
  free: "🆓",
  brain: "🧠",
};

function range7d(): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - 6);
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function formatFreshness(value?: string | null): string {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "fresh") return "Метрики свежие";
  if (normalized === "stale") return "Метрики устарели";
  if (normalized === "missing") return "Нет данных по метрикам";
  return "Состояние метрик неизвестно";
}

function formatIso(value?: string | null): string {
  if (!value) return "нет данных";
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function formatPercent(value?: number | null, digits = 0): string {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return `${Number(value).toFixed(digits)}%`;
}

function formatMbPair(used?: number | null, total?: number | null): string {
  if (!total) return "нет данных";
  const usedGb = Number((Number(used || 0) / 1024).toFixed(1));
  const totalGb = Number((Number(total || 0) / 1024).toFixed(1));
  return `${usedGb} / ${totalGb} ГБ`;
}

function formatGbPair(used?: number | null, total?: number | null): string {
  if (!total) return "нет данных";
  return `${Number(used || 0).toFixed(1)} / ${Number(total || 0).toFixed(1)} ГБ`;
}

function scoreTone(score: number): { fillClass: string; dotClass: string; badgeClass: string; healthPct: number } {
  const healthPct = Math.min(100, Math.max(0, score * 10));
  if (score >= 8) {
    return {
      fillClass: "progress-fill-emerald",
      dotClass: "status-dot-online",
      badgeClass: "badge-success",
      healthPct,
    };
  }
  if (score >= 5) {
    return {
      fillClass: "progress-fill-amber",
      dotClass: "status-dot-warning",
      badgeClass: "badge-warning",
      healthPct,
    };
  }
  return {
    fillClass: "progress-fill-rose",
    dotClass: "status-dot-offline",
    badgeClass: "badge-danger",
    healthPct,
  };
}

function alertKindLabel(kind: string): string {
  const value = String(kind || "").toLowerCase();
  if (value === "cpu_high") return "CPU";
  if (value === "memory_high") return "RAM";
  if (value === "disk_high") return "Диск";
  if (value === "latency_high") return "Задержка";
  if (value === "error_rate_high") return "Ошибки";
  if (value === "active_clients_high" || value === "client_density_high") return "Клиенты";
  return kind;
}

function nodeCodeKey(value: string): string {
  return String(value || "").trim().toLowerCase();
}

export default function AdminNodesPage() {
  const [nodes, setNodes] = useState<AdminNodeHealthRow[]>([]);
  const [traffic, setTraffic] = useState<AdminNodeTrafficRow[]>([]);
  const [status, setStatus] = useState<AdminMetricsStatus | null>(null);
  const [drift, setDrift] = useState<AdminNodeDriftReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [syncTarget, setSyncTarget] = useState("");
  const [driftBusy, setDriftBusy] = useState(false);
  const [nodeActionBusy, setNodeActionBusy] = useState("");
  const [nodeActionNote, setNodeActionNote] = useState("");
  const [error, setError] = useState("");

  const freshnessByNode = useMemo(
    () =>
      new Map(
        (status?.nodes || []).map((row) => [
          nodeCodeKey(row.node_code),
          {
            freshness: row.status,
            alertKinds: row.alert_kinds || [],
            lastSampleAt: row.last_sample_at,
            ageSeconds: row.age_seconds,
          },
        ]),
      ),
    [status?.nodes],
  );

  const load = async (): Promise<void> => {
    setError("");
    try {
      const range = range7d();
      const [healthRows, metricsStatus, trafficRows] = await Promise.all([
        adminNodesHealth(),
        adminMetricsStatus(),
        adminNodesTraffic(range),
      ]);
      setNodes(healthRows);
      setStatus(metricsStatus);
      setTraffic(trafficRows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить данные по нодам."));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const loadDrift = async (): Promise<void> => {
    setDriftBusy(true);
    setError("");
    try {
      const report = await adminNodesDrift();
      setDrift(report);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось проверить расхождения."));
    } finally {
      setDriftBusy(false);
    }
  };

  const runNodeAction = async (node: AdminNodeHealthRow, action: "drain" | "enable" | "disable" | "resync"): Promise<void> => {
    setNodeActionBusy(`${action}:${node.code}`);
    setNodeActionNote("");
    setError("");
    try {
      if (action === "drain") {
        await adminNodeDrain(node.code);
        setNodeActionNote(`Нода ${node.code.toUpperCase()} больше не принимает новые назначения. Текущие клиенты не затронуты.`);
      } else if (action === "enable") {
        await adminNodeEnable(node.code);
        setNodeActionNote(`Нода ${node.code.toUpperCase()} снова участвует в выдаче новых пользователей.`);
      } else if (action === "disable") {
        await adminNodeDisable(node.code, {});
        setNodeActionNote(`Нода ${node.code.toUpperCase()} выключена из выдачи.`);
      } else {
        const result = await adminNodeResync(node.code, { limit: 200 });
        setNodeActionNote(
          `Пересборка назначений для ${node.code.toUpperCase()}: перенесено ${result.migrated}, пропущено ${result.skipped}, ошибок ${result.failed}.`,
        );
      }
      await load();
      if (drift) await loadDrift();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось выполнить действие с нодой."));
    } finally {
      setNodeActionBusy("");
    }
  };

  const runSync = async (segment: string): Promise<void> => {
    setBusy(true);
    setSyncTarget(segment);
    setError("");
    try {
      await adminNodesSync({ segment, limit: 200 });
      await load();
      if (segment === "active") {
        setNodeActionNote("Пересобраны назначения для активных пользователей.");
      } else if (segment === "free") {
        setNodeActionNote("Пересобраны назначения для free-контура.");
      } else {
        setNodeActionNote("Пересобраны назначения для платного контура.");
      }
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось пересобрать назначения."));
    } finally {
      setBusy(false);
      setSyncTarget("");
    }
  };

  return (
    <section className="space-y-5">
      <div className="glass-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`stat-icon ${status?.status === "fresh" ? "stat-icon-emerald" : "stat-icon-amber"}`}>
              <Server size={20} />
            </div>
            <div>
              <h2 className="font-display text-xl font-bold">Ноды и состояние инфраструктуры</h2>
              <p className="mt-0.5 text-xs text-slate-500">
                <strong>{formatFreshness(status?.status)}</strong>. Последний срез: {formatIso(status?.last_sample_at)}.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              { code: "active", label: "Пересобрать активных" },
              { code: "paid", label: "Пересобрать платных" },
              { code: "free", label: "Пересобрать free" },
            ].map((segment) => (
              <button
                key={segment.code}
                className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
                type="button"
                onClick={() => void runSync(segment.code)}
                disabled={busy}
              >
                {busy && syncTarget === segment.code ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                {segment.label}
              </button>
            ))}
            <button
              className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
              type="button"
              onClick={() => void loadDrift()}
              disabled={driftBusy}
            >
              {driftBusy ? <Loader2 size={12} className="animate-spin" /> : <Server size={12} />}
              Проверить расхождения
            </button>
            <button
              className="btn-primary inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold"
              type="button"
              onClick={() => void load()}
            >
              <Activity size={14} />
              Обновить
            </button>
          </div>
        </div>
        {error ? <p className="mt-3 text-sm text-rose-500">{error}</p> : null}
        {nodeActionNote ? <p className="mt-2 text-sm text-emerald-500">{nodeActionNote}</p> : null}
        {status?.active_alerts?.length ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {status.active_alerts.map((alert) => (
              <span key={`${alert.node_code}-${alert.kind}`} className="badge badge-warning">
                {alert.node_code.toUpperCase()}: {alertKindLabel(alert.kind)}
              </span>
            ))}
          </div>
        ) : null}
      </div>

      {drift ? (
        <div className="glass-card p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 className="font-display text-xl font-bold">Сверка POKROV и панели</h3>
              <p className="text-xs text-slate-500">
                Помогает понять, совпадает ли то, что записано в POKROV, с реальным inbound на ноде.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="badge badge-success">совпали: {drift.summary.ok}</span>
              <span className={`badge ${drift.summary.drift > 0 ? "badge-warning" : "badge-success"}`}>
                расхождения: {drift.summary.drift}
              </span>
            </div>
          </div>
          <div className="space-y-3">
            {drift.results.map((row) => (
              <div key={row.node_code} className="rounded-2xl border border-white/15 bg-white/30 p-4 dark:border-white/10 dark:bg-white/[0.03]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <strong className="text-base">{row.node_code.toUpperCase()}</strong>
                      <span className={`badge ${row.status === "ok" ? "badge-success" : "badge-warning"}`}>
                        {row.status === "ok" ? "Совпало" : "Расхождение"}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">{row.node_host || "нет данных о хосте"}</p>
                  </div>
                  <div className="text-right text-xs text-slate-500">
                    <div>Порт: <strong>{row.runtime?.port ?? "—"}</strong></div>
                    <div>Безопасность: <strong>{row.runtime?.security || "—"}</strong></div>
                  </div>
                </div>
                {row.mismatches.length > 0 ? (
                  <p className="mt-3 text-sm text-amber-500">Не совпадает: {row.mismatches.join(", ")}</p>
                ) : (
                  <p className="mt-3 text-sm text-emerald-500">Настройка ноды совпадает с тем, что ожидает POKROV.</p>
                )}
                {row.error ? <p className="mt-2 text-xs text-rose-500">Ошибка проверки: {row.error}</p> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {nodes.map((node) => {
          const score = Number(node.health_score || 0);
          const tone = scoreTone(score);
          const flag = COUNTRY_FLAGS[nodeCodeKey(node.code)] || "🌐";
          const memoryPercent = node.memory_total_mb > 0 ? (node.memory_used_mb / node.memory_total_mb) * 100 : null;
          const diskPercent = node.disk_total_gb > 0 ? (node.disk_used_gb / node.disk_total_gb) * 100 : null;
          const nodeFreshness = freshnessByNode.get(nodeCodeKey(node.code));

          return (
            <article key={node.code} className="stat-card p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{flag}</span>
                  <div>
                    <p className="text-lg font-bold">{node.code.toUpperCase()}</p>
                    <div className="mt-0.5 flex items-center gap-1.5">
                      <span className={`status-dot ${node.is_healthy ? tone.dotClass : "status-dot-offline"}`} />
                      <span className={`badge ${node.is_healthy ? "badge-success" : "badge-danger"}`}>
                        {node.is_healthy ? "Стабильно" : "Нужна проверка"}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold gradient-text">{score.toFixed(1)}</p>
                  <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">оценка</p>
                </div>
              </div>

              <div className="mt-4">
                <div className="mb-1.5 flex items-center justify-between text-xs text-slate-500">
                  <span>Общая устойчивость</span>
                  <span>{Math.round(tone.healthPct)}%</span>
                </div>
                <div className="progress-track">
                  <div className={`progress-fill ${tone.fillClass}`} style={{ width: `${tone.healthPct}%` }} />
                </div>
                <p className="mt-2 text-xs text-slate-500">
                  Оценка строится из отклика панели, количества ошибок и текущей нагрузки.
                </p>
              </div>

              <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">Отклик</p>
                  <p className="text-sm font-bold">
                    {node.panel_latency_ms ?? "—"}
                    <span className="text-[10px] text-slate-400"> ms</span>
                  </p>
                </div>
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">Ошибки</p>
                  <p className="text-sm font-bold">{formatPercent(node.panel_error_rate * 100, 1)}</p>
                </div>
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">Клиенты в панели</p>
                  <p className="text-sm font-bold">{node.active_clients}</p>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">Назначено в POKROV</p>
                  <p className="text-sm font-bold">{node.mapped_users}</p>
                </div>
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">CPU</p>
                  <p className="text-sm font-bold">{formatPercent(node.cpu_percent, 0)}</p>
                </div>
                <div className="rounded-lg bg-white/50 p-2 dark:bg-white/5">
                  <p className="text-xs text-slate-500">RAM</p>
                  <p className="text-sm font-bold">{formatMbPair(node.memory_used_mb, node.memory_total_mb)}</p>
                </div>
              </div>

              <div className="mt-3 rounded-xl border border-white/15 bg-white/35 p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                  <HardDrive size={15} />
                  Диск
                </div>
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>Занято / всего</span>
                  <span>{formatGbPair(node.disk_used_gb, node.disk_total_gb)}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-slate-500">
                  <span>Свободно</span>
                  <span>{node.disk_free_gb > 0 ? `${node.disk_free_gb.toFixed(1)} ГБ` : "—"}</span>
                </div>
                {diskPercent != null ? (
                  <>
                    <div className="mt-2 progress-track">
                      <div
                        className={`progress-fill ${
                          diskPercent > 90 ? "progress-fill-rose" : diskPercent > 75 ? "progress-fill-amber" : "progress-fill-emerald"
                        }`}
                        style={{ width: `${Math.min(100, Math.max(0, diskPercent))}%` }}
                      />
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500">Использовано {formatPercent(diskPercent, 0)}</p>
                  </>
                ) : null}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className={`badge ${node.enabled ? "badge-success" : "badge-danger"}`}>
                  {node.enabled ? "В выдаче" : "Выключена"}
                </span>
                <span className={`badge ${node.accepting_new_clients ? "badge-info" : "badge-warning"}`}>
                  {node.accepting_new_clients ? "Принимает новых" : "Только текущие"}
                </span>
                {node.is_draining ? <span className="badge badge-warning">Дренируется</span> : null}
                {nodeFreshness ? (
                  <span className={`badge ${nodeFreshness.freshness === "fresh" ? "badge-success" : "badge-warning"}`}>
                    {formatFreshness(nodeFreshness.freshness)}
                  </span>
                ) : null}
                {(nodeFreshness?.alertKinds || []).map((kind) => (
                  <span key={`${node.code}-${kind}`} className="badge badge-warning">
                    {alertKindLabel(kind)}
                  </span>
                ))}
              </div>

              <div className="mt-4 grid grid-cols-2 gap-2">
                {node.enabled && !node.is_draining ? (
                  <button
                    type="button"
                    className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold"
                    disabled={!!nodeActionBusy}
                    onClick={() => void runNodeAction(node, "drain")}
                  >
                    {nodeActionBusy === `drain:${node.code}` ? "..." : "Остановить новые"}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold"
                    disabled={!!nodeActionBusy}
                    onClick={() => void runNodeAction(node, "enable")}
                  >
                    {nodeActionBusy === `enable:${node.code}` ? "..." : "Вернуть в выдачу"}
                  </button>
                )}
                <button
                  type="button"
                  className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold"
                  disabled={!!nodeActionBusy || !node.enabled}
                  onClick={() => void runNodeAction(node, "resync")}
                >
                  {nodeActionBusy === `resync:${node.code}` ? "..." : "Пересобрать назначения"}
                </button>
                <button
                  type="button"
                  className="outline-btn col-span-2 rounded-xl px-3 py-2 text-xs font-semibold"
                  disabled={!!nodeActionBusy || !node.enabled}
                  onClick={() => void runNodeAction(node, "disable")}
                >
                  {nodeActionBusy === `disable:${node.code}` ? "..." : "Выключить ноду"}
                </button>
              </div>

              {node.last_probe_error_kind || node.last_probe_error_message ? (
                <div className="mt-3 rounded-xl border border-rose-200/50 bg-rose-50/70 p-3 text-xs text-rose-600 dark:border-rose-500/20 dark:bg-rose-500/10">
                  <div className="font-semibold">
                    Сбой проверки
                    {node.last_probe_stage ? ` на этапе ${node.last_probe_stage}` : ""}
                    {node.last_probe_error_kind ? `: ${node.last_probe_error_kind}` : ""}
                  </div>
                  {node.last_probe_error_message ? (
                    <div className="mt-1 text-slate-600 dark:text-slate-300">{node.last_probe_error_message}</div>
                  ) : null}
                </div>
              ) : null}

              <p className="mt-3 text-[11px] text-slate-500">
                Последняя проверка: {formatIso(node.last_health_at)}.
                {nodeFreshness?.lastSampleAt ? ` Срез метрик: ${formatIso(nodeFreshness.lastSampleAt)}.` : ""}
                {memoryPercent != null ? ` RAM: ${formatPercent(memoryPercent, 0)}.` : ""}
              </p>
            </article>
          );
        })}
        {nodes.length === 0 ? (
          <div className="empty-state col-span-full">
            <Gauge size={36} />
            <p className="text-sm">Данных по нодам пока нет</p>
          </div>
        ) : null}
      </div>

      <div className="glass-card p-5">
        <div className="mb-4 flex items-center gap-3">
          <div className="stat-icon stat-icon-blue">
            <Wifi size={20} />
          </div>
          <div>
            <h3 className="font-display text-xl font-bold">Трафик по дням</h3>
            <p className="text-xs text-slate-500">Сколько устройств и трафика пришло на каждую ноду за последние 7 дней.</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                <th className="px-3 py-2.5">Дата</th>
                <th className="px-3 py-2.5">Нода</th>
                <th className="px-3 py-2.5">Устройств</th>
                <th className="px-3 py-2.5">Трафик, ГБ</th>
              </tr>
            </thead>
            <tbody>
              {traffic.map((row, index) => {
                const flag = COUNTRY_FLAGS[nodeCodeKey(row.node_code)] || "🌐";
                return (
                  <tr
                    key={`${row.date}:${row.node_code}`}
                    className={`border-t border-white/20 dark:border-white/5 ${index % 2 === 0 ? "bg-white/30 dark:bg-white/[0.02]" : ""}`}
                  >
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
