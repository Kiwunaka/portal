"use client";

import {
  adminMetricsStatus,
  adminNodeDisable,
  adminNodeDrain,
  adminNodeEnable,
  adminNodeResync,
  adminNodesDrift,
  adminNodesHealth,
  adminNodesRuntime,
  adminNodesSync,
  adminNodesTraffic,
  type AdminMetricsStatus,
  type AdminNodeDriftReport,
  type AdminNodeHealthRow,
  type AdminNodeRuntimeRow,
  type AdminNodeTrafficRow,
} from "@/lib/api";
import { Activity, Loader2, RefreshCw, Server, Wifi } from "lucide-react";
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
  if (normalized === "stale") return "Нужно проверить данные";
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
  if (value == null || Number.isNaN(Number(value))) return "метрики не поступили";
  return `${Number(value).toFixed(digits)}%`;
}

function formatMbPair(used?: number | null, total?: number | null): string {
  if (used == null || total == null) return "метрики не поступили";
  const usedGb = Number((Number(used || 0) / 1024).toFixed(1));
  const totalGb = Number((Number(total || 0) / 1024).toFixed(1));
  return `${usedGb} / ${totalGb} ГБ`;
}

function formatGbPair(used?: number | null, total?: number | null): string {
  if (used == null || total == null) return "метрики не поступили";
  return `${Number(used || 0).toFixed(1)} / ${Number(total || 0).toFixed(1)} ГБ`;
}

function formatDiskFree(value?: number | null): string {
  if (value == null || Number.isNaN(Number(value))) return "метрики не поступили";
  return `${Number(value).toFixed(1)} ГБ`;
}

function formatMbps(value?: number | null, digits = 1): string {
  if (value == null || Number.isNaN(Number(value))) return "нет данных";
  return `${Number(value).toFixed(digits)} Mbps`;
}

function formatBytesPerSec(value?: number | null): string {
  if (value == null || Number.isNaN(Number(value))) return "нет данных";
  const mbps = (Number(value) * 8) / 1_000_000;
  return `${mbps.toFixed(1)} Mbps`;
}

function scoreTone(score: number): { dotClass: string; badgeClass: string } {
  if (score >= 8) return { dotClass: "status-dot-online", badgeClass: "badge-success" };
  if (score >= 5) return { dotClass: "status-dot-warning", badgeClass: "badge-warning" };
  return { dotClass: "status-dot-offline", badgeClass: "badge-danger" };
}

function alertKindLabel(kind: string): string {
  const value = String(kind || "").toLowerCase();
  if (value === "cpu_high") return "CPU";
  if (value === "memory_high") return "RAM";
  if (value === "disk_high") return "Диск";
  if (value === "latency_high") return "Задержка";
  if (value === "error_rate_high") return "Ошибки";
  if (value === "active_clients_high" || value === "client_density_high") return "Клиенты";
  if (value === "observer_push_stale") return "Данные пользователей устарели";
  if (value === "network_high") return "Ethernet";
  return kind;
}

function nodeCodeKey(value: string): string {
  return String(value || "").trim().toLowerCase();
}

function transportHealthLabel(value?: unknown): { label: string; detail?: string } {
  if (value == null) return { label: "нет данных" };
  if (typeof value === "string") return { label: transportHealthValueText(value) };
  if (Array.isArray(value)) return { label: `список: ${value.length}` };
  if (typeof value === "object") {
    const data = value as Record<string, unknown>;
    const panelState = String(data.panel_state || "").trim();
    const dataplaneState = String(data.dataplane_state || "").trim();
    if (panelState || dataplaneState) {
      let label = "есть проблемы";
      if (panelState === "healthy" && dataplaneState === "healthy") {
        label = "норма";
      } else if (panelState !== "healthy" && dataplaneState === "healthy") {
        label = "панель требует проверки";
      } else if (panelState === "healthy" && dataplaneState !== "healthy") {
        label = "подключение требует проверки";
      }
      const detail =
        data.root_cause_summary != null
          ? String(data.root_cause_summary)
          : data.root_cause_detail != null
            ? String(data.root_cause_detail)
            : undefined;
      return { label, detail };
    }
    const primary = data.status ?? data.state ?? data.kind ?? data.label ?? data.transport_profile;
    const label = primary != null ? String(primary) : `${Object.keys(data).length} полей`;
    const detail =
      data.message != null
        ? String(data.message)
        : data.detail != null
          ? String(data.detail)
          : data.enabled === false
            ? "выключено"
            : undefined;
    return { label, detail };
  }
  return { label: String(value) };
}

function transportHealthRecord(value?: unknown): Record<string, unknown> | null {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : null;
}

function transportHealthValueText(value: unknown): string {
  if (value == null) return "нет данных";
  if (typeof value === "string") {
    const normalized = value.toLowerCase();
    if (normalized === "healthy" || normalized === "ok") return "норма";
    if (normalized === "degraded" || normalized === "warning") return "есть проблемы";
    if (normalized === "failed" || normalized === "fail" || normalized === "error") return "ошибка";
    if (normalized === "unknown") return "неизвестно";
    return value || "нет данных";
  }
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function transportProfileLabel(profile: {
  name?: string | null;
  kind?: string | null;
  enabled?: boolean | null;
  inbound_id?: number | null;
  host?: string | null;
  port?: number | null;
  tls_server_name?: string | null;
}): string {
  const parts = [profile.name, profile.kind, profile.port != null ? `:${profile.port}` : null].filter(Boolean);
  const prefix = profile.enabled === false ? "выкл" : "вкл";
  const suffix = [profile.inbound_id != null ? `#${profile.inbound_id}` : null, profile.tls_server_name ? profile.tls_server_name : null]
    .filter(Boolean)
    .join(" · ");
  const hostPart = profile.host ? ` @ ${profile.host}` : "";
  return `${prefix} ${parts.join(" / ") || "профиль"}${suffix ? ` · ${suffix}` : ""}${hostPart}`;
}

function probeFailureCopy(kind?: string | null, stage?: string | null, message?: string | null): { title: string; detail?: string; raw?: string } | null {
  const rawKind = String(kind || "").trim();
  const rawMessage = String(message || "").trim();
  if (!rawKind && !rawMessage) return null;
  if (rawKind === "reality_target_mismatch") {
    return {
      title: `REALITY target mismatch${stage ? ` на этапе ${stage}` : ""}`,
      detail: "Ожидаемое имя REALITY target не совпало с сертификатом или SNI, который вернул узел.",
      raw: rawKind,
    };
  }
  return {
    title: `Сбой проверки${stage ? ` на этапе ${stage}` : ""}`,
    detail: rawMessage || undefined,
    raw: rawKind || undefined,
  };
}

export default function AdminNodesPage() {
  const [nodes, setNodes] = useState<AdminNodeHealthRow[]>([]);
  const [runtime, setRuntime] = useState<AdminNodeRuntimeRow[]>([]);
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
            observerLastPushAt: row.observer_last_push_at ?? null,
            observerIsStale: Boolean(row.observer_is_stale),
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
      adminNodesRuntime()
        .then(setRuntime)
        .catch(() => setRuntime([]));
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
        setNodeActionNote(`Нода ${node.code.toUpperCase()} больше не принимает новые назначения.`);
      } else if (action === "enable") {
        await adminNodeEnable(node.code);
        setNodeActionNote(`Нода ${node.code.toUpperCase()} снова участвует в выдаче.`);
      } else if (action === "disable") {
        await adminNodeDisable(node.code, {});
        setNodeActionNote(`Нода ${node.code.toUpperCase()} выключена из выдачи.`);
      } else {
        const result = await adminNodeResync(node.code, { limit: 200 });
        setNodeActionNote(`Обновление ${node.code.toUpperCase()}: перенесено ${result.migrated}, пропущено ${result.skipped}, ошибок ${result.failed}.`);
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
      setNodeActionNote(`Сегмент ${segment} пересобран и синхронизирован.`);
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
              <h2 className="font-display text-xl font-bold">Серверы и состояние инфраструктуры</h2>
              <p className="mt-0.5 text-xs text-[color:var(--atlas-text-soft)]">
                <strong>{formatFreshness(status?.status)}</strong>. Последний срез: {formatIso(status?.last_sample_at)}.
              </p>
              <p className="mt-0.5 text-xs text-[color:var(--atlas-text-soft)]">
                Отклик и dataplane-check здесь идут с control plane `brain`; внешний RU probe живёт отдельно.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {[
              { code: "active", label: "Пересобрать активных" },
              { code: "paid", label: "Пересобрать paid" },
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
            <button className="btn-primary inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold" type="button" onClick={() => void load()}>
              <Activity size={14} />
              Обновить
            </button>
          </div>
        </div>
        {error ? <p className="mt-3 text-sm text-[color:var(--atlas-status-danger-text)]">{error}</p> : null}
        {nodeActionNote ? <p className="mt-2 text-sm text-[color:var(--atlas-status-success-text)]">{nodeActionNote}</p> : null}
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

      <div className="glass-card p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-display text-xl font-bold">Живой снимок панелей</h3>
            <p className="text-xs text-[color:var(--atlas-text-soft)]">3x-ui показывает рабочее состояние: доступ к панели, отклик, онлайн и входящее правило. Тарифы и права доступа остаются в POKROV.</p>
          </div>
          <span className="badge badge-info">{runtime.length ? `нод: ${runtime.length}` : "ожидаем данные"}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.1em] text-[color:var(--atlas-text-soft)]">
                <th className="px-3 py-2.5">Нода</th>
                <th className="px-3 py-2.5">Панель</th>
                <th className="px-3 py-2.5">Отклик</th>
                <th className="px-3 py-2.5">Онлайн</th>
                <th className="px-3 py-2.5">Правило</th>
                <th className="px-3 py-2.5">Система</th>
                <th className="px-3 py-2.5">Ошибка</th>
              </tr>
            </thead>
            <tbody>
              {runtime.map((row, index) => {
                const inbound = row.inbound;
                const system = row.system || {};
                return (
                  <tr key={row.node_code} className={`border-t border-white/20 dark:border-white/5 ${index % 2 === 0 ? "bg-[color:var(--atlas-surface)] dark:bg-white/[0.02]" : ""}`}>
                    <td className="px-3 py-3 font-semibold">{String(row.node_code || "").toUpperCase()}</td>
                    <td className="px-3 py-3">
                      <span className={`badge ${row.panel_auth_ok ? "badge-success" : "badge-danger"}`}>{row.panel_auth_ok ? "доступ есть" : "нет доступа"}</span>
                      <div className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{row.api_token_mode ? "токен API" : row.csrf_mode ? "CSRF" : "cookie"}</div>
                    </td>
                    <td className="px-3 py-3">{row.panel_latency_ms != null ? `${row.panel_latency_ms} ms` : "нет данных"}</td>
                    <td className="px-3 py-3">
                      <div>{Number(row.online?.online_keys_now || 0)} ключей</div>
                      <div className="text-xs text-[color:var(--atlas-text-soft)]">{Number(row.online?.online_connections_now || 0)} подключений</div>
                    </td>
                    <td className="px-3 py-3">
                      {inbound ? (
                        <div>
                          <div className="font-medium">
                            #{inbound.inbound_id ?? row.expected_inbound_id ?? "?"} · {inbound.protocol || "протокол?"} · {inbound.port || "порт?"}
                          </div>
                          <div className="text-xs text-[color:var(--atlas-text-soft)]">
                            {inbound.network || "сеть?"} / {inbound.security || "защита?"}
                            {inbound.server_names?.length ? ` · SNI ${inbound.server_names.slice(0, 2).join(", ")}` : ""}
                          </div>
                        </div>
                      ) : (
                        <span className="text-[color:var(--atlas-text-soft)]">не найден</span>
                      )}
                    </td>
                    <td className="px-3 py-3">
                      <div>CPU {formatPercent(system.cpu_percent, 0)}</div>
                      <div className="text-xs text-[color:var(--atlas-text-soft)]">
                        ↓ {formatBytesPerSec(system.network_rx_bytes_per_sec)} · ↑ {formatBytesPerSec(system.network_tx_bytes_per_sec)}
                      </div>
                    </td>
                    <td className="px-3 py-3 text-xs text-[color:var(--atlas-status-danger-text)]">{row.error || "—"}</td>
                  </tr>
                );
              })}
              {runtime.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-sm text-[color:var(--atlas-text-soft)]" colSpan={7}>
                    Живые данные ещё не загрузились или панели недоступны.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      {drift ? (
        <div className="glass-card p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 className="font-display text-xl font-bold">Сверка POKROV и панели</h3>
              <p className="text-xs text-[color:var(--atlas-text-soft)]">Показывает, совпадают ли ожидания контрольной плоскости с фактической конфигурацией узлов.</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="badge badge-success">совпали: {drift.summary.ok}</span>
              <span className={`badge ${drift.summary.drift > 0 ? "badge-warning" : "badge-success"}`}>расхождения: {drift.summary.drift}</span>
            </div>
          </div>
          <div className="space-y-3">
            {drift.results.map((row) => (
              <div key={row.node_code} className="rounded-2xl border border-white/15 bg-[color:var(--atlas-surface)] p-4 dark:border-white/10 dark:bg-white/[0.03]">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <strong className="text-base">{row.node_code.toUpperCase()}</strong>
                      <span className={`badge ${row.status === "ok" ? "badge-success" : "badge-warning"}`}>
                        {row.status === "ok" ? "Совпало" : "Расхождение"}
                      </span>
                    </div>
                    <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{row.node_host || "нет данных о хосте"}</p>
                  </div>
                  <div className="text-right text-xs text-[color:var(--atlas-text-soft)]">
                    <div>Порт: <strong>{row.runtime?.port ?? "—"}</strong></div>
                    <div>Защита: <strong>{row.runtime?.security || "—"}</strong></div>
                  </div>
                </div>
                {row.mismatches.length > 0 ? (
                  <p className="mt-3 text-sm text-[color:var(--atlas-status-warning-text)]">Не совпадает: {row.mismatches.join(", ")}</p>
                ) : (
                  <p className="mt-3 text-sm text-[color:var(--atlas-status-success-text)]">Конфигурация ноды совпадает с тем, что ожидает POKROV.</p>
                )}
                {row.error ? <p className="mt-2 text-xs text-[color:var(--atlas-status-danger-text)]">Ошибка проверки: {row.error}</p> : null}
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
          const memoryPercent = node.memory_used_mb != null && node.memory_total_mb && node.memory_total_mb > 0
            ? (node.memory_used_mb / node.memory_total_mb) * 100
            : null;
          const diskPercent = node.disk_used_gb != null && node.disk_total_gb && node.disk_total_gb > 0
            ? (node.disk_used_gb / node.disk_total_gb) * 100
            : null;
          const nodeFreshness = freshnessByNode.get(nodeCodeKey(node.code));
          const probeFailure = probeFailureCopy(node.last_probe_error_kind, node.last_probe_stage, node.last_probe_error_message);
          const networkPercent = node.network_utilization_percent;
          const networkPeakPercent = node.network_peak_utilization_percent_24h;
          const transportHealth = transportHealthLabel(node.transport_health);
          const transportHealthData = transportHealthRecord(node.transport_health);
          const transportProfiles = Object.values(node.transport_profiles || {}).filter(Boolean);
          const panelState = transportHealthValueText(transportHealthData?.panel_state);
          const dataplaneState = transportHealthValueText(transportHealthData?.dataplane_state);
          const probeStage = transportHealthValueText(
            transportHealthData?.dataplane_stage ?? transportHealthData?.panel_stage ?? node.last_probe_stage,
          );
          const probeClassification = transportHealthValueText(node.probe_classification);
          const telegramAppPath = transportHealthValueText(transportHealthData?.telegram_app_path);
          const telegramWebPath = transportHealthValueText(transportHealthData?.telegram_web_path);
          const tlsHandshake = transportHealthValueText(transportHealthData?.tls_handshake);
          const realityTarget = transportHealthValueText(transportHealthData?.reality_target);
          const rootCauseSummary = transportHealthData?.root_cause_summary ? String(transportHealthData.root_cause_summary) : "";
          const rootCauseDetail = transportHealthData?.root_cause_detail ? String(transportHealthData.root_cause_detail) : "";

          return (
            <article key={node.code} className="stat-card min-w-0 p-5">
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
                  <p className="text-[10px] uppercase tracking-[0.1em] text-[color:var(--atlas-text-soft)]">оценка</p>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-2 text-center sm:grid-cols-3">
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Отклик с сервера</p>
                  <p className="text-sm font-bold">{node.panel_latency_ms ?? "нет данных"}{node.panel_latency_ms != null ? <span className="text-[10px] text-[color:var(--atlas-text-muted)]"> ms</span> : null}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Ошибки</p>
                  <p className="text-sm font-bold">{formatPercent(node.panel_error_rate * 100, 1)}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Клиенты в панели</p>
                  <p className="text-sm font-bold">{node.active_clients}</p>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-1 gap-2 text-center sm:grid-cols-4">
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Назначено в POKROV</p>
                  <p className="text-sm font-bold">{node.mapped_users}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Ключей в сети</p>
                  <p className="text-sm font-bold">{node.online_keys_now}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Подключений сейчас</p>
                  <p className="text-sm font-bold">{node.online_connections_now}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">CPU</p>
                  <p className="text-sm font-bold">{formatPercent(node.cpu_percent, 0)}</p>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-1 gap-2 text-center sm:grid-cols-1">
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2 dark:bg-white/5">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">RAM</p>
                  <p className="text-sm font-bold">{formatMbPair(node.memory_used_mb, node.memory_total_mb)}</p>
                </div>
              </div>

              <div className="mt-3 rounded-xl border border-white/15 bg-[color:var(--atlas-surface)] p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="mb-2 flex items-center justify-between gap-2 text-sm font-semibold">
                  <span>Диск</span>
                  <span>{diskPercent == null ? "нет данных" : formatPercent(diskPercent, 0)}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-[color:var(--atlas-text-soft)]">
                  <span>Занято / всего</span>
                  <span>{formatGbPair(node.disk_used_gb, node.disk_total_gb)}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-[color:var(--atlas-text-soft)]">
                  <span>Свободно</span>
                  <span>{formatDiskFree(node.disk_free_gb)}</span>
                </div>
              </div>

              <div className="mt-3 rounded-xl border border-white/15 bg-[color:var(--atlas-surface)] p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="mb-2 flex items-center justify-between gap-2 text-sm font-semibold">
                  <span>Ethernet</span>
                  <span>{networkPercent == null ? "нет данных" : formatPercent(networkPercent, 0)}</span>
                </div>
                <div className="flex items-center justify-between text-xs text-[color:var(--atlas-text-soft)]">
                  <span>Сейчас RX / TX</span>
                  <span>{formatMbps(node.network_rx_mbps)} / {formatMbps(node.network_tx_mbps)}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-[color:var(--atlas-text-soft)]">
                  <span>Суммарно сейчас</span>
                  <span>{formatMbps(node.network_total_mbps)}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-[color:var(--atlas-text-soft)]">
                  <span>Пик за 24 часа</span>
                  <span>{formatMbps(node.network_peak_mbps_24h)}{networkPeakPercent == null ? "" : ` (${formatPercent(networkPeakPercent, 0)})`}</span>
                </div>
                <div className="mt-1 flex items-center justify-between text-xs text-[color:var(--atlas-text-soft)]">
                  <span>Лимит порта</span>
                  <span>{formatMbps(node.network_port_capacity_mbps, 0)}</span>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                <span className={`badge ${node.enabled ? "badge-success" : "badge-danger"}`}>{node.enabled ? "В выдаче" : "Выключена"}</span>
                <span className={`badge ${node.accepting_new_clients ? "badge-info" : "badge-warning"}`}>{node.accepting_new_clients ? "Принимает новых" : "Только текущие"}</span>
                {node.is_draining ? <span className="badge badge-warning">В процессе разгрузки</span> : null}
                {nodeFreshness ? <span className={`badge ${nodeFreshness.freshness === "fresh" ? "badge-success" : "badge-warning"}`}>{formatFreshness(nodeFreshness.freshness)}</span> : null}
                {node.probe_classification ? <span className="badge badge-info">проверка: {node.probe_classification}</span> : null}
                {node.ipv4_health ? <span className="badge badge-violet">ipv4: {node.ipv4_health}</span> : null}
                {node.ipv6_health ? <span className="badge badge-violet">ipv6: {node.ipv6_health}</span> : null}
                {(nodeFreshness?.alertKinds || []).map((kind) => (
                  <span key={`${node.code}-${kind}`} className="badge badge-warning">
                    {alertKindLabel(kind)}
                  </span>
                ))}
              </div>

              {(node.hoster_family || node.hoster_asn || node.subnet) ? (
                <div className="mt-3 rounded-xl border border-white/15 bg-[color:var(--atlas-surface)] p-3 dark:border-white/10 dark:bg-white/[0.04]">
                  <div className="mb-2 text-sm font-semibold">Хостинг</div>
                  <div className="grid gap-2 text-xs sm:grid-cols-3">
                    <p>Провайдер: <strong>{node.hoster_family || "нет данных"}</strong></p>
                    <p>ASN: <strong>{node.hoster_asn || "нет данных"}</strong></p>
                    <p>Подсеть: <strong>{node.subnet || "нет данных"}</strong></p>
                  </div>
                </div>
              ) : null}

              <div className="mt-3 rounded-xl border border-white/15 bg-[color:var(--atlas-surface)] p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="mb-2 flex items-center justify-between gap-2 text-sm font-semibold">
                  <span>Подключение</span>
                  <span className={`badge ${transportHealth.label === "ok" || transportHealth.label === "healthy" ? "badge-success" : "badge-info"}`}>
                    {transportHealth.label}
                  </span>
                </div>
                {transportHealth.detail ? <p className="text-xs text-[color:var(--atlas-text-soft)]">{transportHealth.detail}</p> : null}
                {rootCauseSummary ? <p className="mt-2 text-xs text-[color:var(--atlas-text-soft)] dark:text-slate-300">{rootCauseSummary}</p> : null}
                {rootCauseDetail ? <p className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{rootCauseDetail}</p> : null}
                <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                  <p>Панель: <strong>{panelState}</strong></p>
                  <p>Проверка подключения: <strong>{dataplaneState}</strong></p>
                  <p>Шаг проверки: <strong>{probeStage}</strong></p>
                  <p>Итог проверки: <strong>{probeClassification}</strong></p>
                  <p>Путь Telegram App: <strong>{telegramAppPath}</strong></p>
                  <p>Путь Telegram Web: <strong>{telegramWebPath}</strong></p>
                  <p>TLS: <strong>{tlsHandshake}</strong></p>
                  <p>REALITY: <strong>{realityTarget}</strong></p>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {transportProfiles.length ? (
                    transportProfiles.map((profile, index) => (
                      <span key={`${node.code}-transport-${index}`} className={`badge ${profile.enabled === false ? "badge-warning" : "badge-success"}`}>
                        {transportProfileLabel(profile)}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-[color:var(--atlas-text-soft)]">Список профилей подключения не пришёл, показываем базовый вид.</span>
                  )}
                </div>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                {node.enabled && !node.is_draining ? (
                  <button type="button" className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" disabled={!!nodeActionBusy} onClick={() => void runNodeAction(node, "drain")}>
                    {nodeActionBusy === `drain:${node.code}` ? "..." : "Остановить новые"}
                  </button>
                ) : (
                  <button type="button" className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" disabled={!!nodeActionBusy} onClick={() => void runNodeAction(node, "enable")}>
                    {nodeActionBusy === `enable:${node.code}` ? "..." : "Вернуть в выдачу"}
                  </button>
                )}
                <button type="button" className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" disabled={!!nodeActionBusy || !node.enabled} onClick={() => void runNodeAction(node, "resync")}>
                  {nodeActionBusy === `resync:${node.code}` ? "..." : "Пересобрать назначения"}
                </button>
                <button type="button" className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold sm:col-span-2" disabled={!!nodeActionBusy || !node.enabled} onClick={() => void runNodeAction(node, "disable")}>
                  {nodeActionBusy === `disable:${node.code}` ? "..." : "Выключить ноду"}
                </button>
              </div>

              {probeFailure ? (
                <div className="mt-3 rounded-xl border border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] p-3 text-xs text-[color:var(--atlas-status-danger-text)] dark:border-rose-500/20 dark:bg-rose-500/10">
                  <div className="font-semibold">{probeFailure.title}</div>
                  {probeFailure.detail ? <div className="mt-1 text-[color:var(--atlas-text-soft)] dark:text-slate-300">{probeFailure.detail}</div> : null}
                  {probeFailure.raw ? <div className="mt-1 text-[color:var(--atlas-text-soft)]">код ошибки: {probeFailure.raw}</div> : null}
                </div>
              ) : null}

              <div className="mt-3 rounded-xl border border-white/15 bg-[color:var(--atlas-surface)] p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="mb-2 flex items-center justify-between gap-2 text-sm font-semibold">
                  <span>Сбор данных по пользователям</span>
                  <span className={`badge ${node.observer_is_stale || nodeFreshness?.observerIsStale ? "badge-warning" : "badge-success"}`}>
                    {node.observer_is_stale || nodeFreshness?.observerIsStale ? "устарело" : "свежо"}
                  </span>
                </div>
                <div className="grid gap-2 text-xs sm:grid-cols-2">
                  <p>последнее обновление: <strong>{formatIso(node.observer_last_push_at || nodeFreshness?.observerLastPushAt || null)}</strong></p>
                  <p>ошибки разбора: <strong>{node.observer_parse_error_count}</strong></p>
                  <p>без совпадения: <strong>{node.observer_unmatched_count}</strong></p>
                  <p>сбор: <strong>{node.observer_is_stale || nodeFreshness?.observerIsStale ? "проверить" : "норма"}</strong></p>
                </div>
              </div>

              <p className="mt-3 text-[11px] text-[color:var(--atlas-text-soft)]">
                Последняя проверка: {formatIso(node.last_health_at)}.
                {nodeFreshness?.lastSampleAt ? ` Срез метрик: ${formatIso(nodeFreshness.lastSampleAt)}.` : ""}
                {memoryPercent != null ? ` RAM: ${formatPercent(memoryPercent, 0)}.` : " RAM: нет данных."}
              </p>
            </article>
          );
        })}
        {nodes.length === 0 ? (
          <div className="empty-state col-span-full">
            <Server size={36} />
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
            <p className="text-xs text-[color:var(--atlas-text-soft)]">Сколько устройств и трафика пришло на каждую ноду за последние 7 дней.</p>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.1em] text-[color:var(--atlas-text-soft)]">
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
                  <tr key={`${row.date}:${row.node_code}`} className={`border-t border-white/20 dark:border-white/5 ${index % 2 === 0 ? "bg-[color:var(--atlas-surface)] dark:bg-white/[0.02]" : ""}`}>
                    <td className="px-3 py-2.5 font-medium">{row.date}</td>
                    <td className="px-3 py-2.5">
                      <span className="mr-2">{flag}</span>
                      {row.node_code.toUpperCase()}
                    </td>
                    <td className="px-3 py-2.5">{row.devices}</td>
                    <td className="px-3 py-2.5">{row.traffic_gb.toFixed(2)}</td>
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
