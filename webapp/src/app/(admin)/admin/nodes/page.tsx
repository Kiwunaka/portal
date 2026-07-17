"use client";

import {
  adminKeyRotate,
  adminKeysPressure,
  adminMetricsStatus,
  adminNodesDrift,
  adminNodesCapacity,
  adminNodesHealth,
  adminNodesRuntime,
  adminNodesSync,
  adminNodesTraffic,
  adminSubscriptionPreview,
  type AdminKeyPressureRow,
  type AdminMetricsStatus,
  type AdminNodeCapacityRow,
  type AdminNodeDriftReport,
  type AdminNodeHealthRow,
  type AdminNodeRuntimeRow,
  type AdminNodeTrafficRow,
  type AdminSubscriptionPreviewPayload,
} from "@/lib/api";
import { Activity, KeyRound, Loader2, RefreshCw, RotateCcw, Search, Server, ShieldAlert, Wifi } from "lucide-react";
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

function capacityBadgeClass(state?: string | null): string {
  const value = String(state || "").toLowerCase();
  if (value === "healthy") return "badge-success";
  if (value === "warm" || value === "drain") return "badge-warning";
  if (value === "hard_reject") return "badge-danger";
  return "badge-info";
}

function pressureBadgeClass(state?: string | null): string {
  const value = String(state || "").toLowerCase();
  if (value === "ok") return "badge-success";
  if (value === "warm" || value === "heavy") return "badge-warning";
  if (value === "suspected_shared" || value === "fair_use") return "badge-danger";
  return "badge-info";
}

function formatNumber(value?: number | null, digits = 0): string {
  if (value == null || Number.isNaN(Number(value))) return "n/a";
  return Number(value).toFixed(digits);
}

function compactReasons(reasons?: string[] | null): string {
  const values = Array.isArray(reasons) ? reasons.filter(Boolean) : [];
  return values.length ? values.slice(0, 3).join(", ") : "no pressure reasons";
}

function formatRatioPercent(value?: number | null): string {
  if (value == null || Number.isNaN(Number(value))) return "нет данных";
  return `${(Number(value) * 100).toFixed(0)}%`;
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
  const [capacity, setCapacity] = useState<AdminNodeCapacityRow[]>([]);
  const [runtime, setRuntime] = useState<AdminNodeRuntimeRow[]>([]);
  const [traffic, setTraffic] = useState<AdminNodeTrafficRow[]>([]);
  const [keyPressure, setKeyPressure] = useState<AdminKeyPressureRow[]>([]);
  const [keyPressureFilter, setKeyPressureFilter] = useState("");
  const [keyPressureBusy, setKeyPressureBusy] = useState(false);
  const [keyActionBusy, setKeyActionBusy] = useState("");
  const [subscriptionPreviewTgId, setSubscriptionPreviewTgId] = useState("");
  const [subscriptionPreviewFormat, setSubscriptionPreviewFormat] = useState("auto");
  const [subscriptionPreview, setSubscriptionPreview] = useState<AdminSubscriptionPreviewPayload | null>(null);
  const [subscriptionPreviewBusy, setSubscriptionPreviewBusy] = useState(false);
  const [status, setStatus] = useState<AdminMetricsStatus | null>(null);
  const [drift, setDrift] = useState<AdminNodeDriftReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [syncTarget, setSyncTarget] = useState("");
  const [driftBusy, setDriftBusy] = useState(false);
  const [operatorToolNote, setOperatorToolNote] = useState("");
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
  const capacityByNode = useMemo(() => new Map(capacity.map((row) => [nodeCodeKey(row.code), row])), [capacity]);

  const load = async (): Promise<void> => {
    setError("");
    try {
      const range = range7d();
      const [healthRows, capacityRows, metricsStatus, trafficRows] = await Promise.all([
        adminNodesHealth(),
        adminNodesCapacity(),
        adminMetricsStatus(),
        adminNodesTraffic(range),
      ]);
      setNodes(healthRows);
      setCapacity(capacityRows);
      setStatus(metricsStatus);
      setTraffic(trafficRows);
      adminNodesRuntime()
        .then(setRuntime)
        .catch(() => setRuntime([]));
      adminKeysPressure({ limit: 50 })
        .then(setKeyPressure)
        .catch(() => setKeyPressure([]));
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

  const loadKeyPressure = async (state = keyPressureFilter): Promise<void> => {
    setKeyPressureBusy(true);
    setError("");
    try {
      const rows = await adminKeysPressure({ state: state || undefined, limit: 50 });
      setKeyPressure(rows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Failed to load key pressure rows."));
    } finally {
      setKeyPressureBusy(false);
    }
  };

  const runKeyRotate = async (row: AdminKeyPressureRow): Promise<void> => {
    setKeyActionBusy(`rotate:${row.key_id}`);
    setOperatorToolNote("");
    setError("");
    try {
      const result = await adminKeyRotate(row.key_id, { reason: "key_pressure_dashboard" });
      setOperatorToolNote(`Rotate job queued for key ${row.key_id}${result.job_id ? `, job ${result.job_id}` : ""}.`);
      await loadKeyPressure();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Failed to queue key rotate."));
    } finally {
      setKeyActionBusy("");
    }
  };

  const runSubscriptionPreview = async (): Promise<void> => {
    const tgId = Number(subscriptionPreviewTgId.trim());
    if (!Number.isFinite(tgId) || tgId <= 0) {
      setError("Enter a positive Telegram user id for subscription preview.");
      return;
    }
    setSubscriptionPreviewBusy(true);
    setSubscriptionPreview(null);
    setError("");
    try {
      const payload = await adminSubscriptionPreview({
        tgId,
        format: subscriptionPreviewFormat === "auto" ? undefined : subscriptionPreviewFormat,
      });
      setSubscriptionPreview(payload);
      setOperatorToolNote(`Subscription preview built for tg_id ${tgId}.`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Failed to build subscription preview."));
    } finally {
      setSubscriptionPreviewBusy(false);
    }
  };

  const runSync = async (segment: string): Promise<void> => {
    setBusy(true);
    setSyncTarget(segment);
    setError("");
    try {
      await adminNodesSync({ segment, limit: 200 });
      await load();
      setOperatorToolNote(`Сегмент ${segment} пересобран и синхронизирован.`);
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
        {operatorToolNote ? <p className="mt-2 text-sm text-[color:var(--atlas-status-success-text)]">{operatorToolNote}</p> : null}
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
            <h3 className="font-display text-xl font-bold">Capacity steering</h3>
            <p className="text-xs text-[color:var(--atlas-text-soft)]">
              Smart-connect использует эти сигналы для порядка маршрутов. Число клиентов в панели показано как provisioned, не как онлайн.
            </p>
          </div>
          <span className="badge badge-info">{capacity.length ? `nodes: ${capacity.length}` : "нет данных"}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.1em] text-[color:var(--atlas-text-soft)]">
                <th className="px-3 py-2.5">Нода</th>
                <th className="px-3 py-2.5">State</th>
                <th className="px-3 py-2.5">TX</th>
                <th className="px-3 py-2.5">CPU</th>
                <th className="px-3 py-2.5">Dataplane</th>
                <th className="px-3 py-2.5">Keys</th>
                <th className="px-3 py-2.5">Reason</th>
              </tr>
            </thead>
            <tbody>
              {capacity.map((row, index) => (
                <tr key={row.code} className={`border-t border-[color:var(--atlas-border)] ${index % 2 === 0 ? "bg-[color:var(--atlas-surface)]" : ""}`}>
                  <td className="px-3 py-3 font-semibold">{row.code.toUpperCase()}</td>
                  <td className="px-3 py-3">
                    <span className={`badge ${capacityBadgeClass(row.capacity_state)}`}>{row.capacity_state}</span>
                    <div className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">score {row.capacity_score.toFixed(1)}</div>
                  </td>
                  <td className="px-3 py-3">
                    <div>{formatMbps(row.tx_mbps)}</div>
                    <div className="text-xs text-[color:var(--atlas-text-soft)]">{formatRatioPercent(row.tx_ratio)} of {formatMbps(row.capacity_mbps, 0)}</div>
                  </td>
                  <td className="px-3 py-3">{formatPercent(row.cpu_percent, 0)}</td>
                  <td className="px-3 py-3">
                    <span className={`badge ${row.dataplane_ok === false ? "badge-danger" : "badge-success"}`}>{row.dataplane_ok === false ? "down" : "ok"}</span>
                    <div className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">{row.dataplane_rtt_ms != null ? `${row.dataplane_rtt_ms} ms` : "rtt n/a"}</div>
                  </td>
                  <td className="px-3 py-3">
                    <div>provisioned {row.provisioned_clients_count}</div>
                    <div className="text-xs text-[color:var(--atlas-text-soft)]">online hint {row.online_connections_hint} · pressure {row.pressure_keys}</div>
                  </td>
                  <td className="px-3 py-3 text-xs text-[color:var(--atlas-text-soft)]">{row.reject_reason || "—"}</td>
                </tr>
              ))}
              {capacity.length === 0 ? (
                <tr>
                  <td className="px-3 py-4 text-sm text-[color:var(--atlas-text-soft)]" colSpan={7}>
                    Capacity данные еще не поступили.
                  </td>
                </tr>
              ) : null}
            </tbody>
          </table>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(360px,0.85fr)]">
        <div className="glass-card p-5">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="stat-icon stat-icon-amber">
                <ShieldAlert size={20} />
              </div>
              <div>
                <h3 className="font-display text-xl font-bold">Key pressure</h3>
                <p className="text-xs text-[color:var(--atlas-text-soft)]">
                  Traffic pressure is advisory: families are not blocked by IP churn alone.
                </p>
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <select
                className="rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-2 text-xs text-[color:var(--atlas-text)]"
                value={keyPressureFilter}
                onChange={(event) => setKeyPressureFilter(event.target.value)}
              >
                <option value="">all states</option>
                <option value="warm">warm</option>
                <option value="heavy">heavy</option>
                <option value="suspected_shared">suspected_shared</option>
                <option value="fair_use">fair_use</option>
              </select>
              <button
                type="button"
                className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
                disabled={keyPressureBusy}
                onClick={() => void loadKeyPressure()}
              >
                {keyPressureBusy ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                Refresh
              </button>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.1em] text-[color:var(--atlas-text-soft)]">
                  <th className="px-3 py-2.5">Key</th>
                  <th className="px-3 py-2.5">Pressure</th>
                  <th className="px-3 py-2.5">Usage</th>
                  <th className="px-3 py-2.5">Signals</th>
                  <th className="px-3 py-2.5">Action</th>
                </tr>
              </thead>
              <tbody>
                {keyPressure.map((row, index) => (
                  <tr key={row.key_id} className={`border-t border-[color:var(--atlas-border)] ${index % 2 === 0 ? "bg-[color:var(--atlas-surface)]" : ""}`}>
                    <td className="px-3 py-3">
                      <div className="font-semibold">#{row.key_id}</div>
                      <div className="text-xs text-[color:var(--atlas-text-soft)]">tg {row.tg_id ?? "n/a"} · {row.panel_email || "email n/a"}</div>
                      <div className="text-xs text-[color:var(--atlas-text-soft)]">node {row.node_code || "n/a"}</div>
                    </td>
                    <td className="px-3 py-3">
                      <span className={`badge ${pressureBadgeClass(row.state)}`}>{row.state}</span>
                      <div className="mt-1 text-xs text-[color:var(--atlas-text-soft)]">score {formatNumber(row.pressure_score, 1)}</div>
                      {row.manual_review_required ? <div className="mt-1"><span className="badge badge-warning">manual review</span></div> : null}
                    </td>
                    <td className="px-3 py-3">
                      <div>{formatNumber(row.traffic_gb_24h, 1)} GB / 24h</div>
                      <div className="text-xs text-[color:var(--atlas-text-soft)]">{row.node_count_24h} nodes / 24h</div>
                    </td>
                    <td className="px-3 py-3 text-xs text-[color:var(--atlas-text-soft)]">
                      <div>IPs: {row.distinct_source_ips_1h} / 1h, {row.distinct_source_ips_24h} / 24h</div>
                      <div className="mt-1 max-w-[280px] truncate" title={compactReasons(row.reasons)}>{compactReasons(row.reasons)}</div>
                      <div className="mt-1">updated {formatIso(row.updated_at)}</div>
                    </td>
                    <td className="px-3 py-3">
                      <button
                        type="button"
                        className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold"
                        disabled={!!keyActionBusy}
                        onClick={() => void runKeyRotate(row)}
                      >
                        {keyActionBusy === `rotate:${row.key_id}` ? <Loader2 size={12} className="animate-spin" /> : <RotateCcw size={12} />}
                        Rotate
                      </button>
                    </td>
                  </tr>
                ))}
                {keyPressure.length === 0 ? (
                  <tr>
                    <td className="px-3 py-4 text-sm text-[color:var(--atlas-text-soft)]" colSpan={5}>
                      No key pressure rows for this filter.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <KeyRound size={20} />
            </div>
            <div>
              <h3 className="font-display text-xl font-bold">Subscription debug</h3>
              <p className="text-xs text-[color:var(--atlas-text-soft)]">Preview node order and exclusion reasons without exposing raw tokens.</p>
            </div>
          </div>
          <div className="grid gap-3">
            <label className="grid gap-1 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--atlas-text-soft)]">
              Telegram ID
              <input
                className="rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-2 text-sm font-normal tracking-normal text-[color:var(--atlas-text)]"
                inputMode="numeric"
                value={subscriptionPreviewTgId}
                onChange={(event) => setSubscriptionPreviewTgId(event.target.value)}
                placeholder="1001"
              />
            </label>
            <label className="grid gap-1 text-xs font-semibold uppercase tracking-[0.12em] text-[color:var(--atlas-text-soft)]">
              Format
              <select
                className="rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 py-2 text-sm font-normal tracking-normal text-[color:var(--atlas-text)]"
                value={subscriptionPreviewFormat}
                onChange={(event) => setSubscriptionPreviewFormat(event.target.value)}
              >
                <option value="auto">auto</option>
                <option value="vless">vless</option>
                <option value="singbox">singbox</option>
                <option value="clash">clash</option>
              </select>
            </label>
            <button
              type="button"
              className="btn-primary inline-flex items-center justify-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold"
              disabled={subscriptionPreviewBusy}
              onClick={() => void runSubscriptionPreview()}
            >
              {subscriptionPreviewBusy ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
              Preview subscription
            </button>
          </div>
          {subscriptionPreview ? (
            <div className="mt-4 space-y-3 rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-4 text-sm">
              <div className="flex flex-wrap gap-2">
                <span className="badge badge-info">tg {subscriptionPreview.tg_id}</span>
                <span className="badge badge-info">{subscriptionPreview.client_format}</span>
                <span className={`badge ${subscriptionPreview.dynamic_ordering ? "badge-success" : "badge-warning"}`}>dynamic {subscriptionPreview.dynamic_ordering ? "on" : "off"}</span>
                <span className={`badge ${subscriptionPreview.hard_exclusion ? "badge-success" : "badge-warning"}`}>hard exclusion {subscriptionPreview.hard_exclusion ? "on" : "off"}</span>
              </div>
              <div>
                <div className="mb-1 text-xs uppercase tracking-[0.12em] text-[color:var(--atlas-text-soft)]">Node order</div>
                <div className="flex flex-wrap gap-2">
                  {subscriptionPreview.node_order.length ? subscriptionPreview.node_order.map((code) => <span key={code} className="badge badge-success">{code.toUpperCase()}</span>) : <span className="text-xs text-[color:var(--atlas-text-soft)]">No eligible nodes.</span>}
                </div>
              </div>
              <div>
                <div className="mb-1 text-xs uppercase tracking-[0.12em] text-[color:var(--atlas-text-soft)]">Excluded</div>
                <div className="max-h-40 overflow-auto rounded-lg bg-[color:var(--atlas-canvas-alt)] p-2 text-xs text-[color:var(--atlas-text-soft)]">
                  {subscriptionPreview.excluded_nodes.length ? (
                    subscriptionPreview.excluded_nodes.map((item, index) => <div key={index}>{JSON.stringify(item)}</div>)
                  ) : (
                    <div>No exclusions.</div>
                  )}
                </div>
              </div>
              <div className="text-xs text-[color:var(--atlas-text-soft)]">
                token fp: {subscriptionPreview.token_fp || "n/a"} · subscription URL: {subscriptionPreview.subscription_url_available ? "available" : "missing"}
              </div>
            </div>
          ) : null}
        </div>
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
                  <tr key={row.node_code} className={`border-t border-[color:var(--atlas-border)] ${index % 2 === 0 ? "bg-[color:var(--atlas-surface)]" : ""}`}>
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
              <div key={row.node_code} className="rounded-2xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-4">
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
          const nodeCapacity = capacityByNode.get(nodeCodeKey(node.code));
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
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Отклик с сервера</p>
                  <p className="text-sm font-bold">{node.panel_latency_ms ?? "нет данных"}{node.panel_latency_ms != null ? <span className="text-[10px] text-[color:var(--atlas-text-muted)]"> ms</span> : null}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Ошибки</p>
                  <p className="text-sm font-bold">{formatPercent(node.panel_error_rate * 100, 1)}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Provisioned</p>
                  <p className="text-sm font-bold">{node.provisioned_clients_count ?? node.active_clients}</p>
                </div>
              </div>

              <div className="mt-3 rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-3">
                <div className="mb-2 flex items-center justify-between gap-2 text-sm font-semibold">
                  <span>Capacity</span>
                  <span className={`badge ${capacityBadgeClass(nodeCapacity?.capacity_state || node.capacity_state)}`}>
                    {nodeCapacity?.capacity_state || node.capacity_state || "unknown"}
                  </span>
                </div>
                <div className="grid gap-2 text-xs sm:grid-cols-2">
                  <p>TX: <strong>{formatMbps(nodeCapacity?.tx_mbps ?? node.capacity_tx_mbps)}</strong></p>
                  <p>Utilization: <strong>{formatRatioPercent(nodeCapacity?.tx_ratio ?? node.capacity_tx_ratio)}</strong></p>
                  <p>Online hint: <strong>{nodeCapacity?.online_connections_hint ?? node.online_connections_hint ?? 0}</strong></p>
                  <p>Pressure keys: <strong>{nodeCapacity?.pressure_keys ?? 0}</strong></p>
                </div>
                {(nodeCapacity?.reject_reason || node.capacity_reject_reason) ? (
                  <p className="mt-2 text-xs text-[color:var(--atlas-status-warning-text)]">{nodeCapacity?.reject_reason || node.capacity_reject_reason}</p>
                ) : null}
              </div>

              <div className="mt-3 grid grid-cols-1 gap-2 text-center sm:grid-cols-4">
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Назначено в POKROV</p>
                  <p className="text-sm font-bold">{node.mapped_users}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Ключей в сети</p>
                  <p className="text-sm font-bold">{node.online_keys_now}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">Подключений сейчас</p>
                  <p className="text-sm font-bold">{node.online_connections_now}</p>
                </div>
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">CPU</p>
                  <p className="text-sm font-bold">{formatPercent(node.cpu_percent, 0)}</p>
                </div>
              </div>

              <div className="mt-3 grid grid-cols-1 gap-2 text-center sm:grid-cols-1">
                <div className="rounded-lg bg-[color:var(--atlas-surface)] p-2">
                  <p className="text-xs text-[color:var(--atlas-text-soft)]">RAM</p>
                  <p className="text-sm font-bold">{formatMbPair(node.memory_used_mb, node.memory_total_mb)}</p>
                </div>
              </div>

              <div className="mt-3 rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-3">
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

              <div className="mt-3 rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-3">
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
                <div className="mt-3 rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-3">
                  <div className="mb-2 text-sm font-semibold">Хостинг</div>
                  <div className="grid gap-2 text-xs sm:grid-cols-3">
                    <p>Провайдер: <strong>{node.hoster_family || "нет данных"}</strong></p>
                    <p>ASN: <strong>{node.hoster_asn || "нет данных"}</strong></p>
                    <p>Подсеть: <strong>{node.subnet || "нет данных"}</strong></p>
                  </div>
                </div>
              ) : null}

              <div className="mt-3 rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-3">
                <div className="mb-2 flex items-center justify-between gap-2 text-sm font-semibold">
                  <span>Подключение</span>
                  <span className={`badge ${transportHealth.label === "ok" || transportHealth.label === "healthy" ? "badge-success" : "badge-info"}`}>
                    {transportHealth.label}
                  </span>
                </div>
                {transportHealth.detail ? <p className="text-xs text-[color:var(--atlas-text-soft)]">{transportHealth.detail}</p> : null}
                {rootCauseSummary ? <p className="mt-2 text-xs text-[color:var(--atlas-text-soft)]">{rootCauseSummary}</p> : null}
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

              <div className="mt-4 rounded-xl border border-[color:var(--atlas-status-warning-line)] bg-[color:var(--atlas-status-warning-bg)] p-3">
                <div className="text-sm font-semibold">Команды доступны в операционном центре</div>
                <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">
                  Изменение состояния ноды и перенос клиентов требуют серверного предпросмотра и записи в аудит.
                </p>
                <a
                  href={`https://admin.pokrov.space/nodes?selected=${encodeURIComponent(node.code)}`}
                  target="_blank"
                  rel="noreferrer"
                  className="btn-primary mt-3 inline-flex rounded-xl px-3 py-2 text-xs font-semibold"
                >
                  Открыть безопасные действия
                </a>
              </div>

              {probeFailure ? (
                <div className="mt-3 rounded-xl border border-[color:var(--atlas-status-danger-line)] bg-[color:var(--atlas-status-danger-bg)] p-3 text-xs text-[color:var(--atlas-status-danger-text)]">
                  <div className="font-semibold">{probeFailure.title}</div>
                  {probeFailure.detail ? <div className="mt-1 text-[color:var(--atlas-text-soft)]">{probeFailure.detail}</div> : null}
                  {probeFailure.raw ? <div className="mt-1 text-[color:var(--atlas-text-soft)]">код ошибки: {probeFailure.raw}</div> : null}
                </div>
              ) : null}

              <div className="mt-3 rounded-xl border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-3">
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
                  <tr key={`${row.date}:${row.node_code}`} className={`border-t border-[color:var(--atlas-border)] ${index % 2 === 0 ? "bg-[color:var(--atlas-surface)]" : ""}`}>
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
