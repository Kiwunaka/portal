"use client";

import { adminNetworkRolloutConfig, adminNetworkRolloutConfigUpdate, type AdminNetworkRolloutConfig } from "@/lib/api";
import { Loader2, RefreshCw, Route, Save } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

function stringifyConfig(config: AdminNetworkRolloutConfig | null): string {
  return config ? JSON.stringify(config, null, 2) : "";
}

function countEntries(value?: Record<string, unknown> | null): number {
  return value ? Object.keys(value).length : 0;
}

function listText(value?: string[] | null): string {
  const items = (value || []).filter((item) => String(item || "").trim().length > 0);
  if (!items.length) return "—";
  return items.join(" · ");
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
    return {
      version: config.version,
      defaults: config.defaults,
      carrierOverrides: countEntries(config.carrier_overrides),
      cohortOverrides: countEntries(config.cohort_overrides),
      operatorLabEnabled: Boolean(config.operator_lab?.enabled),
      operatorLabExpiry: config.operator_lab?.expires_at || "—",
      operatorLabInstallIds: (config.operator_lab?.allowlist_install_ids || []).length,
      operatorLabTgIds: (config.operator_lab?.allowlist_tg_ids || []).length,
      operatorLabNodes: (config.operator_lab?.allowlist_node_codes || []).length,
      packageFeed: config.package_catalog_feed || "—",
      routingFeed: config.routing_rules_feed || "—",
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
      setNotice("Network rollout config сохранён.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить network rollout config."));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="space-y-5">
      <article className="stat-card p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="stat-icon stat-icon-violet">
            <Route size={22} />
          </div>
          <div className="min-w-0">
            <h2 className="font-display text-xl font-bold">Сеть и rollout</h2>
            <p className="text-xs text-slate-500">
              Здесь редактируется `network_rollout_config`, который управляет default transport profile, cohort/carrier overrides и operator lab allowlist.
            </p>
          </div>
        </div>
      </article>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr),minmax(300px,0.72fr)]">
        <article className="glass-card space-y-4 p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-display text-lg font-bold">JSON-конфиг</h3>
              <p className="text-xs text-slate-500">Редактируйте объект целиком. Сохранение идёт через тот же admin API, что и остальные operator configs.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void load()} disabled={loading || busy}>
                {loading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                Обновить
              </button>
              <button className="btn-primary inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void save()} disabled={busy || loading}>
                {busy ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                Сохранить
              </button>
            </div>
          </div>

          {loading ? <p className="text-sm text-slate-500">Загружаем rollout config...</p> : null}
          {error ? <p className="text-sm text-rose-500">{error}</p> : null}
          {notice ? <p className="text-sm text-emerald-500">{notice}</p> : null}

          <textarea
            className="min-h-[520px] w-full resize-y rounded-2xl border border-white/15 bg-white/70 p-4 font-mono text-[12px] leading-5 outline-none dark:border-white/10 dark:bg-white/[0.04]"
            value={jsonText}
            onChange={(event) => setJsonText(event.target.value)}
            spellCheck={false}
          />
        </article>

        <aside className="space-y-4">
          <article className="glass-card p-5">
            <h3 className="font-display text-lg font-bold">Сводка</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Version</p>
                <p className="mt-1 text-lg font-bold">{summary?.version ?? "—"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Defaults transport</p>
                <p className="mt-1 text-sm font-semibold">{summary?.defaults.transport_profile ?? "—"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Routing / DNS</p>
                <p className="mt-1 text-sm font-semibold">{summary ? `${summary.defaults.routing_mode_default} / ${summary.defaults.dns_policy}` : "—"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Overrides</p>
                <p className="mt-1 text-sm font-semibold">{summary ? `${summary.carrierOverrides} carrier · ${summary.cohortOverrides} cohort` : "—"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Operator lab</p>
                <p className="mt-1 text-sm font-semibold">{summary?.operatorLabEnabled ? "enabled" : "disabled"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Expiry</p>
                <p className="mt-1 text-sm font-semibold">{summary?.operatorLabExpiry ?? "—"}</p>
              </div>
            </div>
          </article>

          <article className="glass-card space-y-3 p-5">
            <h3 className="font-display text-lg font-bold">Allowlist и feeds</h3>
            <div className="space-y-2 text-sm">
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                install ids: <strong>{summary?.operatorLabInstallIds ?? "—"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                tg ids: <strong>{summary?.operatorLabTgIds ?? "—"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                node codes: <strong>{summary?.operatorLabNodes ?? "—"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                package feed: <strong className="break-all">{summary?.packageFeed ?? "—"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                routing feed: <strong className="break-all">{summary?.routingFeed ?? "—"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                support recovery: <strong className="break-all">{summary?.recoveryOrder ?? "—"}</strong>
              </p>
            </div>
          </article>
        </aside>
      </div>
    </section>
  );
}
