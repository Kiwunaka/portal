"use client";

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
  if (!items.length) return "вЂ”";
  return items.join(" В· ");
}

function numberListText(value?: number[] | null): string {
  const items = (value || []).map((item) => String(item)).filter((item) => item.trim().length > 0);
  if (!items.length) return "вЂ”";
  return items.join(" В· ");
}

function feedText(value: unknown): string {
  if (value == null) return "вЂ”";
  if (typeof value === "string") return value.trim() || "вЂ”";
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
      setError(String((err as { message?: string })?.message || err || "РќРµ СѓРґР°Р»РѕСЃСЊ Р·Р°РіСЂСѓР·РёС‚СЊ network rollout config."));
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
      operatorLabExpiry: config.operator_lab?.expires_at || "вЂ”",
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
      setNotice("Network rollout config сохранён.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "РќРµ СѓРґР°Р»РѕСЃСЊ СЃРѕС…СЂР°РЅРёС‚СЊ network rollout config."));
    } finally {
      setBusy(false);
    }
  };

  const selectorEntries = [...(summary?.carrierOverrides || []), ...(summary?.cohortOverrides || [])];

  return (
    <section className="space-y-5">
      <article className="stat-card p-5 sm:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="stat-icon stat-icon-violet">
            <Route size={22} />
          </div>
          <div className="min-w-0">
            <h2 className="font-display text-xl font-bold">РЎРµС‚СЊ Рё rollout</h2>
            <p className="text-xs text-slate-500">
              Р—РґРµСЃСЊ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ `network_rollout_config`, РєРѕС‚РѕСЂС‹Р№ СѓРїСЂР°РІР»СЏРµС‚ default transport profile, cohort/carrier overrides Рё operator lab allowlist.
            </p>
          </div>
        </div>
      </article>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr),minmax(320px,0.78fr)]">
        <article className="glass-card space-y-4 p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h3 className="font-display text-lg font-bold">JSON-РєРѕРЅС„РёРі</h3>
              <p className="text-xs text-slate-500">Р РµРґР°РєС‚РёСЂСѓР№С‚Рµ РѕР±СЉРµРєС‚ С†РµР»РёРєРѕРј. РЎРѕС…СЂР°РЅРµРЅРёРµ РёРґС‘С‚ С‡РµСЂРµР· С‚РѕС‚ Р¶Рµ admin API, С‡С‚Рѕ Рё РѕСЃС‚Р°Р»СЊРЅС‹Рµ operator configs.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button className="outline-btn inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void load()} disabled={loading || busy}>
                {loading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                РћР±РЅРѕРІРёС‚СЊ
              </button>
              <button aria-label="Сохранить" className="btn-primary inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={() => void save()} disabled={busy || loading}>
                {busy ? <Loader2 size={13} className="animate-spin" /> : <Save size={13} />}
                РЎРѕС…СЂР°РЅРёС‚СЊ
              </button>
            </div>
          </div>

          {loading ? <p className="text-sm text-slate-500">Р—Р°РіСЂСѓР¶Р°РµРј rollout config...</p> : null}
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
            <h3 className="font-display text-lg font-bold">РЎРІРѕРґРєР°</h3>
            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Version</p>
                <p className="mt-1 text-lg font-bold">{summary?.version ?? "вЂ”"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Defaults transport</p>
                <p className="mt-1 text-sm font-semibold">{summary?.defaults?.transport_profile ?? "вЂ”"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Routing / DNS</p>
                <p className="mt-1 text-sm font-semibold">
                  {summary?.defaults ? `${summary.defaults.routing_mode_default} / ${summary.defaults.dns_policy}` : "вЂ”"}
                </p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Overrides</p>
                <p className="mt-1 text-sm font-semibold">
                  {summary ? `${summary.carrierOverrides.length} carrier В· ${summary.cohortOverrides.length} cohort` : "вЂ”"}
                </p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Operator lab</p>
                <p className="mt-1 text-sm font-semibold">{summary?.operatorLabEnabled ? "enabled" : "disabled"}</p>
              </div>
              <div className="node-card">
                <p className="text-[10px] uppercase tracking-[0.1em] text-slate-500">Expiry</p>
                <p className="mt-1 text-sm font-semibold">{summary?.operatorLabExpiry ?? "вЂ”"}</p>
              </div>
            </div>
          </article>

          <article className="glass-card space-y-3 p-5">
            <h3 className="font-display text-lg font-bold">Allowlist Рё feeds</h3>
            <div className="space-y-2 text-sm">
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                install ids: <strong>{summary?.operatorLabInstallIds ?? "вЂ”"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                tg ids: <strong>{summary?.operatorLabTgIds ?? "вЂ”"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                node codes: <strong>{summary?.operatorLabNodes ?? "вЂ”"}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                package feed: <strong className="break-all">{feedText(summary?.packageFeed)}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                routing feed: <strong className="break-all">{feedText(summary?.routingFeed)}</strong>
              </p>
              <p className="rounded-xl bg-white/50 px-3 py-2 dark:bg-white/5">
                support recovery: <strong className="break-all">{summary?.recoveryOrder ?? "вЂ”"}</strong>
              </p>
            </div>
          </article>

          <article className="glass-card space-y-3 p-5">
            <h3 className="font-display text-lg font-bold">Targeting selectors</h3>
            <div className="space-y-3 text-sm">
              {selectorEntries.length ? (
                selectorEntries.map(([key, value]) => (
                  <div key={key} className="rounded-xl bg-white/50 px-3 py-3 dark:bg-white/5">
                    <p className="font-semibold">{key}</p>
                    <p className="mt-1 text-xs text-slate-500">
                      transport: <strong>{value.transport_profile || "вЂ”"}</strong> В· dns: <strong>{value.dns_policy || "вЂ”"}</strong>
                    </p>
                    <p className="mt-1 text-xs text-slate-500">
                      routing: <strong>{value.routing_mode_default || "вЂ”"}</strong> В· ip: <strong>{value.ip_version_preference || "вЂ”"}</strong>
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
                <p className="rounded-xl bg-white/50 px-3 py-2 text-sm text-slate-500 dark:bg-white/5">
                  Selector overrides РїРѕРєР° РЅРµ Р·Р°РґР°РЅС‹.
                </p>
              )}
            </div>
          </article>
        </aside>
      </div>
    </section>
  );
}
