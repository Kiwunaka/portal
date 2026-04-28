"use client";

import {
  AdminBadge,
  AdminEmptyState,
  AdminPanelHeader,
  adminButtonClass,
  adminCompactCardClass,
  adminIconFrameClass,
  adminPanelClass,
  adminTextAreaClass,
} from "@/components/admin/admin-shell";
import {
  adminNetworkRolloutConfig,
  adminNetworkRolloutConfigUpdate,
  type AdminNetworkRolloutConfig,
  type AdminNetworkRolloutOverride,
} from "@/lib/api";
import { Loader2, RefreshCw, Route, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

function stringifyConfig(config: AdminNetworkRolloutConfig | null): string {
  return config ? JSON.stringify(config, null, 2) : "";
}

function listText(value?: string[] | null): string {
  const items = (value || []).filter((item) => String(item || "").trim().length > 0);
  if (!items.length) return "—";
  return items.join(" · ");
}

function numberListText(value?: number[] | null): string {
  const items = (value || []).map((item) => String(item)).filter((item) => item.trim().length > 0);
  if (!items.length) return "—";
  return items.join(" · ");
}

function feedText(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "string") return value.trim() || "—";
  if (typeof value === "number" || typeof value === "boolean") return String(value);
  if (typeof value === "object") {
    const data = value as Record<string, unknown>;
    const preferred = data.version ?? data.url ?? data.feed ?? data.name ?? data.id;
    if (preferred != null) return String(preferred);
    try {
      return JSON.stringify(data);
    } catch {
      return "[object]";
    }
  }
  return String(value);
}

function overrideEntries(value?: Record<string, AdminNetworkRolloutOverride> | null): Array<[string, AdminNetworkRolloutOverride]> {
  return Object.entries(value || {});
}

export default function AdminNetworkPage() {
  const [config, setConfig] = useState<AdminNetworkRolloutConfig | null>(null);
  const [jsonText, setJsonText] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async (): Promise<void> => {
    setLoading(true);
    setError("");
    setNotice("");
    try {
      const out = await adminNetworkRolloutConfig();
      setConfig(out.network_rollout_config);
      setJsonText(stringifyConfig(out.network_rollout_config));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить network rollout config."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const summary = useMemo(() => {
    if (!config) return null;
    const carrierOverrides = overrideEntries(config.carrier_overrides);
    const cohortOverrides = overrideEntries(config.cohort_overrides);
    return {
      version: config.version,
      defaults: config.defaults,
      carrierOverrides,
      cohortOverrides,
      operatorLabEnabled: Boolean(config.operator_lab?.enabled),
      operatorLabExpiry: config.operator_lab?.expires_at || "—",
      operatorLabInstallIds: (config.operator_lab?.allowlist_install_ids || []).length,
      operatorLabTgIds: (config.operator_lab?.allowlist_tg_ids || []).length,
      operatorLabNodes: (config.operator_lab?.allowlist_node_codes || []).length,
      packageFeed: config.package_catalog_feed,
      routingFeed: config.routing_rules_feed,
      recoveryOrder: listText(config.support_recovery_order),
    };
  }, [config]);

  const save = async (): Promise<void> => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const parsed = JSON.parse(jsonText) as AdminNetworkRolloutConfig;
      const out = await adminNetworkRolloutConfigUpdate(parsed);
      setConfig(out.network_rollout_config);
      setJsonText(stringifyConfig(out.network_rollout_config));
      setNotice("Network rollout config сохранен.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить network rollout config."));
    } finally {
      setBusy(false);
    }
  };

  const selectorEntries = [...(summary?.carrierOverrides || []), ...(summary?.cohortOverrides || [])];

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className={adminIconFrameClass("accent")}>
            <Route size={22} />
          </div>
          <div className="min-w-0">
            <h2 className="text-xl font-semibold text-slate-50">Сеть и rollout</h2>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              Здесь редактируется `network_rollout_config`: default transport profile, cohort/carrier overrides и operator lab allowlist.
            </p>
          </div>
        </div>
      </article>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(320px,0.78fr)]">
        <article className={adminPanelClass("neutral")}>
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <AdminPanelHeader
              eyebrow="rollout config"
              title="JSON-конфиг"
              description="Редактируйте объект целиком. Сохранение идет через тот же admin API, что и остальные operator configs."
            />
            <div className="flex flex-wrap gap-2">
              <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => void load()} disabled={loading || busy}>
                {loading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                Обновить
              </button>
              <button aria-label="Сохранить" className={adminButtonClass("primary", "sm")} type="button" onClick={() => void save()} disabled={busy || loading}>
                {busy ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                Сохранить
              </button>
            </div>
          </div>

          {loading ? (
            <div className="mb-3 grid gap-2" aria-busy="true" aria-live="polite">
              <div className="h-3 w-44 animate-pulse rounded-full bg-slate-700" />
              <div className="h-3 w-64 animate-pulse rounded-full bg-slate-800" />
            </div>
          ) : null}
          {error ? <p className="mb-3 text-sm text-rose-300">{error}</p> : null}
          {notice ? <p className="mb-3 text-sm text-emerald-300">{notice}</p> : null}

          <textarea
            className={`${adminTextAreaClass} min-h-[520px] font-mono text-[12px] leading-5`}
            value={jsonText}
            onChange={(event) => setJsonText(event.target.value)}
            spellCheck={false}
          />
        </article>

        <aside className="space-y-4">
          <article className={adminPanelClass("neutral")}>
            <h3 className="text-lg font-semibold text-slate-50">Сводка</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className={adminCompactCardClass}>
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Version</p>
                <p className="mt-1 text-lg font-semibold text-slate-50">{summary?.version ?? "—"}</p>
              </div>
              <div className={adminCompactCardClass}>
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Defaults transport</p>
                <p className="mt-1 text-sm font-semibold text-slate-100">{summary?.defaults?.transport_profile ?? "—"}</p>
              </div>
              <div className={adminCompactCardClass}>
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Routing / DNS</p>
                <p className="mt-1 text-sm font-semibold text-slate-100">
                  {summary?.defaults ? `${summary.defaults.routing_mode_default} / ${summary.defaults.dns_policy}` : "—"}
                </p>
              </div>
              <div className={adminCompactCardClass}>
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Overrides</p>
                <p className="mt-1 text-sm font-semibold text-slate-100">
                  {summary ? `${summary.carrierOverrides.length} carrier · ${summary.cohortOverrides.length} cohort` : "—"}
                </p>
              </div>
              <div className={adminCompactCardClass}>
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Operator lab</p>
                <AdminBadge tone={summary?.operatorLabEnabled ? "warning" : "neutral"} className="mt-2">
                  {summary?.operatorLabEnabled ? "enabled" : "disabled"}
                </AdminBadge>
              </div>
              <div className={adminCompactCardClass}>
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Expiry</p>
                <p className="mt-1 text-sm font-semibold text-slate-100">{summary?.operatorLabExpiry ?? "—"}</p>
              </div>
            </div>
          </article>

          <article className={adminPanelClass("neutral")}>
            <h3 className="text-lg font-semibold text-slate-50">Allowlist и feeds</h3>
            <div className="space-y-2 text-sm">
              <p className={adminCompactCardClass}>
                install ids: <strong>{summary?.operatorLabInstallIds ?? "—"}</strong>
              </p>
              <p className={adminCompactCardClass}>
                tg ids: <strong>{summary?.operatorLabTgIds ?? "—"}</strong>
              </p>
              <p className={adminCompactCardClass}>
                node codes: <strong>{summary?.operatorLabNodes ?? "—"}</strong>
              </p>
              <p className={adminCompactCardClass}>
                package feed: <strong className="break-all">{feedText(summary?.packageFeed)}</strong>
              </p>
              <p className={adminCompactCardClass}>
                routing feed: <strong className="break-all">{feedText(summary?.routingFeed)}</strong>
              </p>
              <p className={adminCompactCardClass}>
                support recovery: <strong className="break-all">{summary?.recoveryOrder ?? "—"}</strong>
              </p>
            </div>
          </article>

          <article className={adminPanelClass("neutral")}>
            <h3 className="text-lg font-semibold text-slate-50">Targeting selectors</h3>
            <div className="space-y-3 text-sm">
              {selectorEntries.length ? (
                selectorEntries.map(([key, value]) => (
                  <div key={key} className={adminCompactCardClass}>
                    <p className="font-semibold text-slate-100">{key}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      transport: <strong>{value.transport_profile || "—"}</strong> · dns: <strong>{value.dns_policy || "—"}</strong>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      routing: <strong>{value.routing_mode_default || "—"}</strong> · ip: <strong>{value.ip_version_preference || "—"}</strong>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      install_ids: <strong className="break-all">{listText(value.install_ids)}</strong>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      tg_ids: <strong className="break-all">{numberListText(value.tg_ids)}</strong>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      linked_tg_ids: <strong className="break-all">{numberListText(value.linked_tg_ids)}</strong>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      platforms: <strong className="break-all">{listText(value.platforms)}</strong>
                    </p>
                  </div>
                ))
              ) : (
                <AdminEmptyState className="min-h-[120px]" title="Selector overrides пока не заданы." />
              )}
            </div>
          </article>
        </aside>
      </div>
    </section>
  );
}
