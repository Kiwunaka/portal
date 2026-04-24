"use client";

import {
  AdminConfirmDialog,
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

type ConfirmState = { kind: "wheel" | "loyalty" | "grant"; reason: string } | null;

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

function parseLoyaltyRows(input: string): Array<{ days: number; bonus_days: number; perk: string }> {
  return input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [daysRaw, bonusRaw, ...perkRaw] = line.split(":");
      return {
        days: Number(daysRaw || 0),
        bonus_days: Number(bonusRaw || 0),
        perk: perkRaw.join(":").trim(),
      };
    });
}

function loyaltyRowsToText(rows: Array<{ days: number; bonus_days: number; perk: string }>): string {
  return rows.map((row) => `${row.days}:${row.bonus_days}:${row.perk}`).join("\n");
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
  const [confirm, setConfirm] = useState<ConfirmState>(null);

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

  const saveWheel = async (operatorReason: string): Promise<void> => {
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
      const out = await adminWheelConfigUpdate(payload, operatorReason.trim());
      setConfig(out.wheel_config);
      setWeightsText(weightsToText(out.wheel_config.weights || []));
      setResult(`Колесо бонусов сохранено. Причина: ${operatorReason.trim()}`);
      setConfirm(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save wheel settings."));
    } finally {
      setBusy(false);
    }
  };

  const saveLoyalty = async (operatorReason: string): Promise<void> => {
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
      const out = await adminLoyaltyConfigUpdate({ enabled: loyaltyConfig.enabled, tiers }, operatorReason.trim());
      setLoyaltyConfig(out.loyalty_config);
      setLoyaltyText((out.loyalty_config.tiers || []).map((row) => `${row.days}:${row.bonus_days}:${row.perk}`).join("\n"));
      setResult(`Настройки лояльности сохранены. Причина: ${operatorReason.trim()}`);
      setConfirm(null);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Could not save loyalty settings."));
    } finally {
      setBusy(false);
    }
  };

  const grantLoyalty = async (operatorReason: string): Promise<void> => {
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
      const out = await adminUserLoyaltyGrant(tgId, tierDays, operatorReason.trim());
      setResult(`Бонус выдан: ${out.tier_days} дн. для ${tgId} (${out.sync_ok ? "панель синхронизирована" : "синхронизация ожидает"}).`);
      setConfirm(null);
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

  const loyaltyRows = useMemo(() => parseLoyaltyRows(loyaltyText), [loyaltyText]);
  const updateWeightRow = (index: number, patch: Partial<{ days: number; weight: number }>) => {
    const rows = weightBars.length ? weightBars.map(({ days, weight }) => ({ days, weight })) : [{ days: 1, weight: 1 }];
    rows[index] = { ...rows[index], ...patch };
    setWeightsText(weightsToText(rows));
  };
  const updateLoyaltyRow = (index: number, patch: Partial<{ days: number; bonus_days: number; perk: string }>) => {
    const rows = loyaltyRows.length ? [...loyaltyRows] : [{ days: 30, bonus_days: 1, perk: "priority_support" }];
    rows[index] = { ...rows[index], ...patch };
    setLoyaltyText(loyaltyRowsToText(rows));
  };

  return (
    <section className="space-y-4">
      <article className={adminPanelClass("neutral")}>
        <AdminPanelHeader
          eyebrow="access"
          title="Bonuses and loyalty"
          description="Control bonus wheel probabilities, loyalty tiers, and scoped manual grants from one auditable operator surface."
          actions={
            <button className={adminButtonClass("secondary", "sm")} type="button" onClick={() => void load()} disabled={busy}>
              Обновить
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
              <div className="space-y-2">
                <div className="grid grid-cols-[0.7fr,0.7fr,auto] gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                  <span>Дней</span>
                  <span>Вес</span>
                  <span />
                </div>
                {(weightBars.length ? weightBars : [{ days: 1, weight: 1, pct: 100 }]).map((row, index) => (
                  <div key={`${row.days}:${index}`} className="grid grid-cols-[0.7fr,0.7fr,auto] gap-2">
                    <input type="number" min={1} value={row.days} onChange={(event) => updateWeightRow(index, { days: Number(event.target.value || 1) })} className={adminFieldClass} />
                    <input type="number" min={1} value={row.weight} onChange={(event) => updateWeightRow(index, { weight: Number(event.target.value || 1) })} className={adminFieldClass} />
                    <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => setWeightsText(weightsToText(weightBars.filter((_, itemIndex) => itemIndex !== index)))} disabled={weightBars.length <= 1}>
                      Убрать
                    </button>
                  </div>
                ))}
                <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => setWeightsText(weightsToText([...(weightBars.length ? weightBars : []), { days: 14, weight: 10 }]))}>
                  Добавить строку
                </button>
              </div>
              <details className="rounded-xl border border-[#c6e6db] bg-[#f8fffc] p-3">
                <summary className="cursor-pointer text-xs font-semibold text-slate-600">Исходные строки wheel</summary>
                <textarea rows={5} value={weightsText} onChange={(event) => setWeightsText(event.target.value)} className={`mt-2 font-mono text-xs ${adminTextAreaClass}`} placeholder={"1:45\n3:35\n7:15\n30:5"} />
              </details>
              <button className={adminButtonClass("primary")} type="button" onClick={() => setConfirm({ kind: "wheel", reason: "" })} disabled={busy}>
                Сохранить колесо
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
          <div className="space-y-2">
            <div className="grid grid-cols-[0.6fr,0.6fr,minmax(0,1fr),auto] gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-500">
              <span>Дней</span>
              <span>Бонус</span>
              <span>Перк</span>
              <span />
            </div>
            {(loyaltyRows.length ? loyaltyRows : [{ days: 30, bonus_days: 1, perk: "priority_support" }]).map((row, index) => (
              <div key={`${row.days}:${index}`} className="grid grid-cols-[0.6fr,0.6fr,minmax(0,1fr),auto] gap-2">
                <input type="number" min={1} value={row.days} onChange={(event) => updateLoyaltyRow(index, { days: Number(event.target.value || 1) })} className={adminFieldClass} />
                <input type="number" min={0} value={row.bonus_days} onChange={(event) => updateLoyaltyRow(index, { bonus_days: Number(event.target.value || 0) })} className={adminFieldClass} />
                <input value={row.perk} onChange={(event) => updateLoyaltyRow(index, { perk: event.target.value })} className={adminFieldClass} />
                <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => setLoyaltyText(loyaltyRowsToText(loyaltyRows.filter((_, itemIndex) => itemIndex !== index)))} disabled={loyaltyRows.length <= 1}>
                  Убрать
                </button>
              </div>
            ))}
            <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => setLoyaltyText(loyaltyRowsToText([...(loyaltyRows.length ? loyaltyRows : []), { days: 180, bonus_days: 7, perk: "vip_queue" }]))}>
              Добавить уровень
            </button>
          </div>
          <details className="mt-3 rounded-xl border border-[#c6e6db] bg-[#f8fffc] p-3">
            <summary className="cursor-pointer text-xs font-semibold text-slate-600">Исходные строки loyalty</summary>
            <textarea rows={5} value={loyaltyText} onChange={(event) => setLoyaltyText(event.target.value)} className={`mt-2 font-mono text-xs ${adminTextAreaClass}`} placeholder={"30:1:priority_support\n90:3:fast_resync\n180:7:vip_queue"} />
          </details>
          <button className={`${adminButtonClass("secondary")} mt-3`} type="button" onClick={() => setConfirm({ kind: "loyalty", reason: "" })} disabled={busy}>
            Сохранить лояльность
          </button>
        </article>

        <article className={adminPanelClass("neutral")}>
          <AdminPanelHeader eyebrow="manual grant" title="Grant loyalty tier" description="Use only for a specific operator-reviewed case." />
          <div className="space-y-3">
            <input value={loyaltyGrantUser} onChange={(event) => setLoyaltyGrantUser(event.target.value)} placeholder="Telegram ID" className={adminFieldClass} />
            <input value={loyaltyGrantTier} onChange={(event) => setLoyaltyGrantTier(event.target.value)} placeholder="Tier days, for example 30" className={adminFieldClass} />
            <button className={adminButtonClass("secondary")} type="button" onClick={() => setConfirm({ kind: "grant", reason: "" })} disabled={busy}>
              Выдать бонус
            </button>
          </div>
        </article>
      </div>
      <AdminConfirmDialog
        open={Boolean(confirm)}
        title={confirm?.kind === "grant" ? "Подтвердить выдачу бонуса" : "Подтвердить сохранение бонусов"}
        description="Действие влияет на правила бонусов или живой доступ. Укажите причину для журнала аудита."
        reason={confirm?.reason || ""}
        onReasonChange={(reason) => setConfirm((current) => (current ? { ...current, reason } : current))}
        onCancel={() => setConfirm(null)}
        onConfirm={() => {
          if (!confirm) return;
          if (confirm.kind === "wheel") void saveWheel(confirm.reason);
          else if (confirm.kind === "loyalty") void saveLoyalty(confirm.reason);
          else void grantLoyalty(confirm.reason);
        }}
        busy={busy}
      />
    </section>
  );
}
