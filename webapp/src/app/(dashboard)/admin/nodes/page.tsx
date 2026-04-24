"use client";

import {
  AdminConfirmDialog,
  AdminBadge,
  AdminEmptyState,
  AdminInlineNote,
  AdminKpiCard,
  AdminPanelHeader,
  AdminSurfaceHeader,
  adminButtonClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTableShellClass,
} from "@/components/admin/admin-shell";
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
import { Activity, GitCompare, Loader2, RefreshCw, Server } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type PendingAction =
  | { kind: "drain" | "enable" | "disable" | "resync"; node: AdminNodeHealthRow; label: string; tone: "warning" | "danger" | "accent" }
  | { kind: "segment"; segment: string; label: string; tone: "warning" };

function range7d(): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - 6);
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function fmtIso(value?: string | null): string {
  if (!value) return "no data";
  try {
    return new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
  } catch {
    return value;
  }
}

function fmtPct(value?: number | null, digits = 0): string {
  return value == null || Number.isNaN(Number(value)) ? "missing" : `${Number(value).toFixed(digits)}%`;
}

function fmtGb(value?: number | null, digits = 1): string {
  return value == null || Number.isNaN(Number(value)) ? "missing" : `${Number(value).toFixed(digits)} GB`;
}

function fmtMbps(value?: number | null, digits = 1): string {
  return value == null || Number.isNaN(Number(value)) ? "missing" : `${Number(value).toFixed(digits)} Mbps`;
}

function nodeKey(value: string): string {
  return String(value || "").trim().toLowerCase();
}

function freshnessLabel(value?: string | null): string {
  if (value === "fresh") return "Метрики свежие";
  if (value === "stale") return "Нужно проверить данные";
  if (value === "missing") return "Нет данных по метрикам";
  return "Freshness unknown";
}

function freshnessTone(value?: string | null): "success" | "warning" | "danger" | "neutral" {
  if (value === "fresh") return "success";
  if (value === "stale") return "warning";
  if (value === "missing") return "danger";
  return "neutral";
}

function alertKindLabel(kind: string): string {
  const value = String(kind || "").toLowerCase();
  if (value === "cpu_high") return "CPU";
  if (value === "memory_high") return "RAM";
  if (value === "disk_high") return "Disk";
  if (value === "latency_high") return "Latency";
  if (value === "error_rate_high") return "Errors";
  if (value === "active_clients_high" || value === "client_density_high") return "Клиенты";
  if (value === "observer_push_stale") return "Observer";
  if (value === "network_high") return "Ethernet";
  return kind;
}

function healthTone(node: AdminNodeHealthRow): "success" | "warning" | "danger" {
  if (!node.enabled || !node.is_healthy || node.health_score < 5) return "danger";
  if (node.is_draining || node.health_score < 8) return "warning";
  return "success";
}

function transportRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function textValue(value: unknown): string {
  if (value == null || value === "") return "missing";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") return String(value);
  return JSON.stringify(value);
}

function profileLabel(profile: Record<string, unknown>): string {
  const kind = textValue(profile.kind);
  const port = profile.port == null ? "" : `:${profile.port}`;
  const inbound = profile.inbound_id == null ? "" : ` #${profile.inbound_id}`;
  const host = profile.host == null ? "" : ` @ ${profile.host}`;
  const sni = profile.tls_server_name == null ? "" : ` / ${profile.tls_server_name}`;
  return `${profile.enabled === false ? "off" : "on"} ${kind}${port}${inbound}${host}${sni}`;
}

function trafficForNode(rows: AdminNodeTrafficRow[], code: string): number {
  return rows.filter((row) => nodeKey(row.node_code) === nodeKey(code)).reduce((sum, row) => sum + Number(row.traffic_gb || 0), 0);
}

function probeFailure(node: AdminNodeHealthRow): { title: string; detail: string } | null {
  const kind = String(node.last_probe_error_kind || "").trim();
  const message = String(node.last_probe_error_message || "").trim();
  if (!kind && !message) return null;
  if (kind === "reality_target_mismatch") {
    return {
      title: `REALITY target mismatch${node.last_probe_stage ? ` at ${node.last_probe_stage}` : ""}`,
      detail: message || "Certificate names do not match expected reality target.",
    };
  }
  return {
    title: `Сбой проверки${node.last_probe_stage ? ` на этапе ${node.last_probe_stage}` : ""}`,
    detail: message || kind,
  };
}

export default function AdminNodesPage() {
  const [nodes, setNodes] = useState<AdminNodeHealthRow[]>([]);
  const [traffic, setTraffic] = useState<AdminNodeTrafficRow[]>([]);
  const [status, setStatus] = useState<AdminMetricsStatus | null>(null);
  const [drift, setDrift] = useState<AdminNodeDriftReport | null>(null);
  const [busy, setBusy] = useState(false);
  const [driftBusy, setDriftBusy] = useState(false);
  const [pending, setPending] = useState<PendingAction | null>(null);
  const [reason, setReason] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const metricsByNode = useMemo(
    () =>
      new Map(
        (status?.nodes || []).map((row) => [
          nodeKey(row.node_code),
          {
            freshness: row.status,
            lastSampleAt: row.last_sample_at,
            observerLastPushAt: row.observer_last_push_at ?? null,
            observerIsStale: Boolean(row.observer_is_stale),
            alertKinds: row.alert_kinds || [],
          },
        ]),
      ),
    [status?.nodes],
  );

  const totals = useMemo(() => {
    const healthy = nodes.filter((node) => node.enabled && node.is_healthy).length;
    const online = nodes.reduce((sum, node) => sum + Number(node.online_connections_now || 0), 0);
    const clients = nodes.reduce((sum, node) => sum + Number(node.active_clients || 0), 0);
    const traffic7d = traffic.reduce((sum, row) => sum + Number(row.traffic_gb || 0), 0);
    return { healthy, online, clients, traffic7d };
  }, [nodes, traffic]);

  const load = async (): Promise<void> => {
    setError("");
    try {
      const range = range7d();
      const [healthRows, metricsStatus, trafficRows] = await Promise.all([adminNodesHealth(), adminMetricsStatus(), adminNodesTraffic(range)]);
      setNodes(healthRows);
      setStatus(metricsStatus);
      setTraffic(trafficRows);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not load node telemetry."));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const loadDrift = async (): Promise<void> => {
    setDriftBusy(true);
    setError("");
    try {
      setDrift(await adminNodesDrift());
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not load drift report."));
    } finally {
      setDriftBusy(false);
    }
  };

  const runPending = async (): Promise<void> => {
    if (!pending) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      if (pending.kind === "segment") {
        await adminNodesSync({ segment: pending.segment, limit: 200 });
        setNotice(`Сегмент ${pending.segment} синхронизирован. Причина: ${reason.trim()}`);
      } else if (pending.kind === "drain") {
        await adminNodeDrain(pending.node.code, reason.trim());
        setNotice(`${pending.node.code.toUpperCase()} переведен в drain. Причина: ${reason.trim()}`);
      } else if (pending.kind === "enable") {
        await adminNodeEnable(pending.node.code, reason.trim());
        setNotice(`${pending.node.code.toUpperCase()} включен. Причина: ${reason.trim()}`);
      } else if (pending.kind === "disable") {
        await adminNodeDisable(pending.node.code, { operator_reason: reason.trim() });
        setNotice(`${pending.node.code.toUpperCase()} выключен. Причина: ${reason.trim()}`);
      } else {
        const result = await adminNodeResync(pending.node.code, { limit: 200, operator_reason: reason.trim() });
        setNotice(`${pending.node.code.toUpperCase()} resync: перенесено ${result.migrated}, пропущено ${result.skipped}, ошибок ${result.failed}. Причина: ${reason.trim()}`);
      }
      setPending(null);
      setReason("");
      await load();
      if (drift) await loadDrift();
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Node action failed."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <AdminSurfaceHeader
        title="Узлы и состояние узлов"
        description="Операторская консоль сети: свежесть, риск маршрутизации, предупреждения и безопасные действия с узлами."
        meta={
          <>
            <AdminBadge tone={freshnessTone(status?.status)} className="badge">{freshnessLabel(status?.status)}</AdminBadge>
            <AdminBadge tone="neutral">last sample {fmtIso(status?.last_sample_at)}</AdminBadge>
          </>
        }
        actions={
          <>
            <button type="button" className={adminButtonClass("secondary", "sm")} onClick={load} disabled={busy}>
              <RefreshCw size={14} /> Обновить
            </button>
            <button type="button" className={adminButtonClass("secondary", "sm")} onClick={loadDrift} disabled={driftBusy || busy}>
              {driftBusy ? <Loader2 className="animate-spin" size={14} /> : <GitCompare size={14} />} Проверить расхождения
            </button>
          </>
        }
      />

      {error ? <AdminInlineNote tone="danger">{error}</AdminInlineNote> : null}
      {notice ? <AdminInlineNote tone="success">{notice}</AdminInlineNote> : null}

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <AdminKpiCard label="Здоровые узлы" value={`${totals.healthy}/${nodes.length}`} hint="Включены и проходят последнюю проверку." tone={totals.healthy === nodes.length ? "success" : "warning"} />
        <AdminKpiCard label="Онлайн-сессии" value={totals.online} hint={`${totals.clients} активных клиентов по отчетам узлов.`} />
        <AdminKpiCard label="Трафик 7д" value={fmtGb(totals.traffic7d)} hint="По текущему диапазону API трафика узлов." />
        <AdminKpiCard label="Активные алерты" value={status?.active_alerts?.length || 0} hint="Синтетические realtime-данные здесь не создаются." tone={status?.active_alerts?.length ? "danger" : "success"} />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader
            eyebrow="флот"
            title="Таблица узлов"
            description="Плотная таблица здоровья, свежести, runtime, емкости, пути подключения и observer-состояния."
            actions={
              <>
                <button type="button" className={adminButtonClass("ghost", "xs")} onClick={() => setPending({ kind: "segment", segment: "free", label: "Синхронизировать free-сегмент", tone: "warning" })}>
                  Resync free
                </button>
                <button type="button" className={adminButtonClass("ghost", "xs")} onClick={() => setPending({ kind: "segment", segment: "premium", label: "Синхронизировать premium-сегмент", tone: "warning" })}>
                  Resync premium
                </button>
              </>
            }
          />
          {nodes.length ? (
            <div className={adminTableShellClass}>
              <div className="overflow-x-auto">
                <table className="min-w-[960px] w-full text-left text-xs">
                  <thead className="border-b border-[#c6e6db] bg-[#f8fffc] text-[10px] uppercase tracking-[0.16em] text-slate-500">
                    <tr>
                      <th className="px-3 py-3">Узел</th>
                      <th className="px-3 py-3">Здоровье</th>
                      <th className="px-3 py-3">Свежесть</th>
                      <th className="px-3 py-3">Runtime</th>
                      <th className="px-3 py-3">Емкость</th>
                      <th className="px-3 py-3">Путь</th>
                      <th className="px-3 py-3">Observer</th>
                      <th className="px-3 py-3 text-right">Действия</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#c6e6db]">
                    {nodes.map((node) => {
                      const metric = metricsByNode.get(nodeKey(node.code));
                      const probe = probeFailure(node);
                      return (
                        <tr key={node.code} className="align-top">
                          <td className="px-3 py-3">
                            <div className="flex items-center gap-2">
                              <Server size={14} className="text-emerald-200" />
                              <div>
                                <p className="font-semibold text-slate-100">{node.code.toUpperCase()}</p>
                                <p className="text-[11px] text-slate-500">{node.name}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-3 py-3">
                            <AdminBadge tone={healthTone(node)}>{node.enabled ? (node.is_draining ? "draining" : "enabled") : "disabled"}</AdminBadge>
                            <p className="mt-1 text-[11px] text-slate-500">score {node.health_score}</p>
                          </td>
                          <td className="px-3 py-3">
                            <AdminBadge tone={freshnessTone(metric?.freshness)} className="badge">{freshnessLabel(metric?.freshness)}</AdminBadge>
                            <p className="mt-1 text-[11px] text-slate-500">{fmtIso(metric?.lastSampleAt || node.last_health_at)}</p>
                          </td>
                          <td className="px-3 py-3 text-slate-300">
                            <p><Activity className="mr-1 inline" size={12} /> {node.online_connections_now} conn</p>
                            <p className="text-[11px] text-slate-500">{node.mapped_users} mapped · {node.active_clients} active</p>
                          </td>
                          <td className="px-3 py-3 text-slate-300">
                            <p>CPU {fmtPct(node.cpu_percent)} · RAM {node.memory_total_mb ? fmtPct((Number(node.memory_used_mb || 0) / Number(node.memory_total_mb)) * 100) : "missing"}</p>
                            <p className="text-[11px] text-slate-500">disk {fmtGb(node.disk_free_gb)} free · eth {fmtMbps(node.network_total_mbps)}</p>
                            <p className="text-[11px] text-slate-500">7d {fmtGb(trafficForNode(traffic, node.code))}</p>
                          </td>
                          <td className="px-3 py-3 text-slate-300">
                            <p>{textValue(transportRecord(node.transport_health).panel_state || transportRecord(node.transport_health).status || node.probe_classification)}</p>
                            {probe ? <p className="mt-1 text-[11px] text-amber-200">probe detail in context</p> : null}
                          </td>
                          <td className="px-3 py-3 text-slate-300">
                            <p>Observer collector</p>
                            <p className="text-[11px] text-slate-500">parse: {node.observer_parse_error_count} · unmatched: {node.observer_unmatched_count}</p>
                          </td>
                          <td className="px-3 py-3">
                            <div className="flex flex-wrap justify-end gap-1.5">
                              <button type="button" className={adminButtonClass("ghost", "xs")} onClick={() => setPending({ kind: "resync", node, label: `Resync ${node.code.toUpperCase()}`, tone: "accent" })}>Resync</button>
                              <button type="button" className={adminButtonClass("ghost", "xs")} onClick={() => setPending({ kind: "drain", node, label: `Drain ${node.code.toUpperCase()}`, tone: "warning" })}>Drain</button>
                              {node.enabled ? (
                                <button type="button" className={adminButtonClass("danger", "xs")} onClick={() => setPending({ kind: "disable", node, label: `Disable ${node.code.toUpperCase()}`, tone: "danger" })}>Disable</button>
                              ) : (
                                <button type="button" className={adminButtonClass("secondary", "xs")} onClick={() => setPending({ kind: "enable", node, label: `Enable ${node.code.toUpperCase()}`, tone: "accent" })}>Enable</button>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <AdminEmptyState title="Узлы не загружены" description="Health API вернул пустой список узлов." />
          )}
        </article>

        <div className="space-y-4">
          <article className={adminPanelClass(status?.active_alerts?.length ? "danger" : "success")}>
            <AdminPanelHeader eyebrow="алерты" title="Активные алерты" description="Свежесть метрик и метки алертов по узлам." />
            {status?.active_alerts?.length ? (
              <div className="space-y-2">
                {status.active_alerts.map((alert, index) => (
                  <div key={`${alert.node_code}-${alert.kind}-${index}`} className={adminInsetPanelClass}>
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <AdminBadge tone="danger">{alert.node_code.toUpperCase()}: {alertKindLabel(alert.kind)}</AdminBadge>
                      <span className="text-[11px] text-slate-500">{freshnessLabel(alert.status)}</span>
                    </div>
                    <p className="mt-2 text-xs text-slate-400">последний срез {fmtIso(alert.last_sample_at)} · возраст {alert.age_seconds ?? "unknown"}s</p>
                  </div>
                ))}
              </div>
            ) : (
              <AdminEmptyState title="Активных алертов нет" description="Metrics status сейчас не показывает активных алертов узлов." />
            )}
          </article>

          {drift ? (
            <article className={adminPanelClass(drift.summary.drift ? "warning" : "success")}>
              <AdminPanelHeader eyebrow="drift" title="Drift runtime-конфига" description={`${drift.summary.ok}/${drift.summary.total} узл. совпадают с ожидаемым inbound-состоянием.`} />
              <div className="space-y-2">
                {drift.results.map((row) => (
                  <div key={row.node_code} className={adminInsetPanelClass}>
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold text-slate-100">{row.node_code.toUpperCase()}</p>
                      <AdminBadge tone={row.status === "ok" ? "success" : "warning"}>{row.status}</AdminBadge>
                    </div>
                    {row.mismatches.length ? <p className="mt-2 text-xs text-amber-100">{row.mismatches.join(", ")}</p> : null}
                    {row.error ? <p className="mt-2 text-xs text-rose-100">{row.error}</p> : null}
                  </div>
                ))}
              </div>
            </article>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {nodes.map((node) => {
          const record = transportRecord(node.transport_health);
          const probe = probeFailure(node);
          const profiles = Object.entries(node.transport_profiles || {});
          return (
            <article key={`context-${node.code}`} className={adminPanelClass("neutral")}>
              <AdminPanelHeader eyebrow="инспектор узла" title={`${node.code.toUpperCase()} контекст хостинга`} description="Расширенные детали панели, client-path probe и transport-профилей для сетевых инцидентов." />
              <div className="grid gap-3 text-xs leading-5 text-slate-300 sm:grid-cols-2">
                <div className={adminInsetPanelClass}><strong>Hoster:</strong> {node.hoster_family || "missing"} · {node.hoster_asn || "missing"}</div>
                <div className={adminInsetPanelClass}><strong>Subnet:</strong> {node.subnet || "missing"}</div>
                <div className={adminInsetPanelClass}><strong>Panel / control plane:</strong> {textValue(record.panel_state || record.panel_stage)}</div>
                <div className={adminInsetPanelClass}><strong>Client-path probe:</strong> {textValue(record.dataplane_state || record.dataplane_stage)}</div>
                <div className={adminInsetPanelClass}><strong>Probe stage:</strong> {node.last_probe_stage || textValue(record.dataplane_stage)}</div>
                <div className={adminInsetPanelClass}><strong>Probe classification:</strong> {node.probe_classification || "missing"}</div>
                <div className={adminInsetPanelClass}><strong>Telegram app path:</strong> {textValue(record.telegram_app_path)}</div>
                <div className={adminInsetPanelClass}><strong>Telegram web path:</strong> {textValue(record.telegram_web_path)}</div>
                <div className={adminInsetPanelClass}><strong>TLS handshake:</strong> {textValue(record.tls_handshake)}</div>
                <div className={adminInsetPanelClass}><strong>REALITY target:</strong> {textValue(record.reality_target)}</div>
              </div>
              {record.root_cause_summary || record.root_cause_detail || probe ? (
                <div className="mt-3 rounded-xl border border-amber-900/60 bg-amber-950/35 p-3 text-xs leading-5 text-amber-100">
                  <p className="font-semibold">{textValue(record.root_cause_summary || probe?.title)}</p>
                  <p className="mt-1">{textValue(record.root_cause_detail || probe?.detail)}</p>
                </div>
              ) : null}
              {profiles.length ? (
                <div className="mt-3 grid gap-2">
                  {profiles.map(([name, profile]) => (
                    <div key={name} className={adminInsetPanelClass}>
                      <p className="font-semibold text-slate-100">{name}</p>
                      <p className="mt-1 text-xs text-slate-400">{profileLabel(profile as Record<string, unknown>)}</p>
                    </div>
                  ))}
                </div>
              ) : null}
            </article>
          );
        })}
      </div>

      <AdminConfirmDialog
        open={Boolean(pending)}
        title={pending?.label || "Подтвердить действие с узлом"}
        description="Действие меняет live-назначения или состояние узла. Укажите причину для аудита перед выполнением."
        reason={reason}
        onReasonChange={setReason}
        onCancel={() => {
          setPending(null);
          setReason("");
        }}
        onConfirm={() => void runPending()}
        confirmLabel={busy ? <><Loader2 className="animate-spin" size={14} /> Выполняется</> : "Подтвердить"}
        danger={pending?.tone === "danger"}
        busy={busy}
      />
    </section>
  );
}
