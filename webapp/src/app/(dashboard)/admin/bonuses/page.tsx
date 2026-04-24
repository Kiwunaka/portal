"use client";

import {
  AdminBadge,
  AdminMetricStrip,
  AdminPanelHeader,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
  adminTextAreaClass,
} from "@/components/admin/admin-shell";
import {
  adminLoyaltyConfig,
  adminLoyaltyConfigUpdate,
  adminUserLoyaltyGrant,
  adminWheelConfig,
  adminWheelConfigUpdate,
  type AdminLoyaltyConfig,
  type AdminWheelConfig,
} from "@/lib/api";
import { useEffect, useMemo, useState } from "react";

function parseWeights(input: string): Array<{ days: number; weight: number }> {
  const parsed = input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [daysRaw, weightRaw] = line.replace(/\s+/g, "").split(":");
      const days = Number(daysRaw || 0);
      const weight = Number(weightRaw || 0);
      if (!Number.isFinite(days) || !Number.isFinite(weight) || days <= 0 || weight <= 0) {
        throw new Error(`Invalid wheel row: ${line}`);
      }
      return { days: Math.floor(days), weight: Math.floor(weight) };
    });
  if (!parsed.length) throw new Error("Add at least one days:weight row.");
  return parsed;
}

function weightsToText(weights: Array<{ days: number; weight: number }>): string {
  return (weights || []).map((row) => `${row.days}:${row.weight}`).join("\n");
}

export default function AdminBonusesPage() {
  const [config, setConfig] = useState<AdminWheelConfig | null>(null);
  const [loyaltyConfig, setLoyaltyConfig] = useState<AdminLoyaltyConfig | null>(null);
  const [loyaltyText, setLoyaltyText] = useState("");
  const [loyaltyGrantUser, setLoyaltyGrantUser] = useState("");
  const [loyaltyGrantTier, setLoyaltyGrantTier] = useState("30");
  const [weightsText, setWeightsText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState("");

  const load = async (): Promise<void> => {
    setError("");
    setResult("");
    try {
      const [cfg, loyalty] = await Promise.all([adminWheelConfig(), adminLoyaltyConfig()]);
      setConfig(cfg);
      setWeightsText(weightsToText(cfg.weights || []));
      setLoyaltyConfig(loyalty.loyalty_config);
      setLoyaltyText((loyalty.loyalty_config.tiers || []).map((row) => `${row.days}:${row.bonus_days}:${row.perk}`).join("\n"));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not load bonus settings."));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const saveWheel = async (): Promise<void> => {
    if (!config) return;
    setBusy(true);
    setError("");
    setResult("");
    try {
      const payload: AdminWheelConfig = {
        preset: String(config.preset || "balanced").trim() || "balanced",
        cooldown_hours: Math.max(1, Math.min(2160, Number(config.cooldown_hours || 168))),
        weights: parseWeights(weightsText),
      };
      const out = await adminWheelConfigUpdate(payload);
      setConfig(out.wheel_config);
      setWeightsText(weightsToText(out.wheel_config.weights || []));
      setResult("Wheel settings saved.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save wheel settings."));
    } finally {
      setBusy(false);
    }
  };

  const saveLoyalty = async (): Promise<void> => {
    if (!loyaltyConfig) return;
    setBusy(true);
    setError("");
    setResult("");
    try {
      const tiers = loyaltyText
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => {
          const [daysRaw, bonusRaw, ...perkRaw] = line.split(":");
          const days = Number(daysRaw || 0);
          const bonusDays = Number(bonusRaw || 0);
          const perk = perkRaw.join(":").trim();
          if (!Number.isFinite(days) || !Number.isFinite(bonusDays) || days <= 0 || bonusDays < 0 || !perk) {
            throw new Error(`Invalid loyalty row: ${line}`);
          }
          return { days: Math.floor(days), bonus_days: Math.floor(bonusDays), perk };
        });
      const out = await adminLoyaltyConfigUpdate({ enabled: loyaltyConfig.enabled, tiers });
      setLoyaltyConfig(out.loyalty_config);
      setLoyaltyText((out.loyalty_config.tiers || []).map((row) => `${row.days}:${row.bonus_days}:${row.perk}`).join("\n"));
      setResult("Loyalty settings saved.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save loyalty settings."));
    } finally {
      setBusy(false);
    }
  };

  const grantLoyalty = async (): Promise<void> => {
    const tgId = Number(loyaltyGrantUser || 0);
    const tierDays = Number(loyaltyGrantTier || 0);
    if (!Number.isFinite(tgId) || tgId <= 0 || !Number.isFinite(tierDays) || tierDays <= 0) {
      setError("Enter Telegram ID and tier days.");
      return;
    }
    setBusy(true);
    setError("");
    setResult("");
    try {
      const out = await adminUserLoyaltyGrant(tgId, tierDays);
      setResult(`Loyalty granted: ${out.tier_days} days for ${tgId} (${out.sync_ok ? "panel synced" : "sync pending"}).`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not grant loyalty bonus."));
    } finally {
      setBusy(false);
    }
  };

  const weightBars = useMemo(() => {
    try {
      const parsed = parseWeights(weightsText);
      const totalWeight = parsed.reduce((sum, row) => sum + row.weight, 0);
      return parsed.map((row) => ({ ...row, pct: Math.round((row.weight / totalWeight) * 100) }));
    } catch {
      return [];
    }
  }, [weightsText]);

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="access"
          title="Bonuses and loyalty"
          description="Control bonus wheel probabilities, loyalty tiers, and scoped manual grants from one auditable operator surface."
          actions={
            <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => void load()} disabled={busy}>
              Reload
            </button>
          }
        />
        <div className="flex flex-wrap gap-2">
          <AdminBadge tone="accent">wheel</AdminBadge>
          <AdminBadge tone="accent">loyalty</AdminBadge>
          <AdminBadge tone="warning">ручные начисления требуют Telegram ID</AdminBadge>
        </div>
      </article>

      <AdminMetricStrip
        items={[
          { label: "preset", value: config?.preset || "-", hint: "Active wheel preset." },
          { label: "cooldown", value: `${config?.cooldown_hours ?? "-"}h`, hint: "Minimum pause between wheel runs." },
          { label: "weights", value: weightBars.length, hint: "Configured wheel outcomes.", tone: "accent" },
          { label: "loyalty", value: loyaltyConfig?.enabled ? "on" : "off", hint: "Retention tier automation.", tone: loyaltyConfig?.enabled ? "success" : "warning" },
        ]}
      />

      {result ? <div className={adminPanelClass("success")}>{result}</div> : null}
      {error ? <div className={adminPanelClass("danger")}>{error}</div> : null}

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(300px,0.7fr)]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="wheel" title="Bonus wheel configuration" />
          {!config ? (
            <p className="text-sm text-slate-400">Loading settings...</p>
          ) : (
            <div className="space-y-3">
              <div className="grid gap-3 md:grid-cols-2">
                <label className="text-xs text-slate-400">
                  Preset
                  <input value={config.preset || ""} onChange={(event) => setConfig((prev) => (prev ? { ...prev, preset: event.target.value } : prev))} className={`mt-1 ${adminFieldClass}`} />
                </label>
                <label className="text-xs text-slate-400">
                  Cooldown hours
                  <input
                    type="number"
                    value={config.cooldown_hours}
                    onChange={(event) => setConfig((prev) => (prev ? { ...prev, cooldown_hours: Math.max(1, Math.min(2160, Number(event.target.value || 1))) } : prev))}
                    className={`mt-1 ${adminFieldClass}`}
                  />
                </label>
              </div>
              <label className="block text-xs text-slate-400">
                Weights (days:weight)
                <textarea rows={7} value={weightsText} onChange={(event) => setWeightsText(event.target.value)} className={`mt-1 font-mono text-xs ${adminTextAreaClass}`} placeholder={"1:45\n3:35\n7:15\n30:5"} />
              </label>
              <button className={adminButtonClass("primary")} type="button" onClick={() => void saveWheel()} disabled={busy}>
                Save wheel
              </button>
            </div>
          )}
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="distribution" title="Weight preview" />
          <div className="space-y-3">
            {weightBars.map((bar) => (
              <div key={`${bar.days}:${bar.weight}`}>
                <div className="mb-1 flex justify-between text-xs">
                  <span>{bar.days} days · weight {bar.weight}</span>
                  <strong>{bar.pct}%</strong>
                </div>
                <div className="h-2 rounded-full bg-[#ffffff]">
                  <div className="h-full rounded-full bg-emerald-300" style={{ width: `${bar.pct}%` }} />
                </div>
              </div>
            ))}
            {!weightBars.length ? <p className="text-xs text-slate-500">Enter valid rows to preview probability.</p> : null}
          </div>
        </article>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr),minmax(300px,0.7fr)]">
        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="loyalty" title="Loyalty tiers" />
          <label className="mb-3 inline-flex items-center gap-2 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={Boolean(loyaltyConfig?.enabled)}
              onChange={(event) => setLoyaltyConfig((prev) => (prev ? { ...prev, enabled: event.target.checked } : prev))}
            />
            Enabled
          </label>
          <p className="mb-2 text-xs text-slate-500">Format: days:bonus_days:perk</p>
          <textarea rows={7} value={loyaltyText} onChange={(event) => setLoyaltyText(event.target.value)} className={`font-mono text-xs ${adminTextAreaClass}`} placeholder={"30:1:priority_support\n90:3:fast_resync\n180:7:vip_queue"} />
          <button className={`${adminButtonClass("secondary")} mt-3`} type="button" onClick={() => void saveLoyalty()} disabled={busy}>
            Save loyalty
          </button>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="manual grant" title="Grant loyalty tier" description="Use only for a specific operator-reviewed case." />
          <div className="space-y-3">
            <input value={loyaltyGrantUser} onChange={(event) => setLoyaltyGrantUser(event.target.value)} placeholder="Telegram ID" className={adminFieldClass} />
            <input value={loyaltyGrantTier} onChange={(event) => setLoyaltyGrantTier(event.target.value)} placeholder="Tier days, for example 30" className={adminFieldClass} />
            <button className={adminButtonClass("secondary")} type="button" onClick={() => void grantLoyalty()} disabled={busy}>
              Grant bonus
            </button>
          </div>
        </article>
      </div>
    </section>
  );
}
