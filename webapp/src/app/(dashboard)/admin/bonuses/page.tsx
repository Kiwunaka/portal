"use client";

import { adminLoyaltyConfig, adminLoyaltyConfigUpdate, adminUserLoyaltyGrant, adminWheelConfig, adminWheelConfigUpdate, type AdminLoyaltyConfig, type AdminWheelConfig } from "@/lib/api";
import { Dices, Loader2, RefreshCw, Save, Timer } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

function parseWeights(input: string): Array<{ days: number; weight: number }> {
  const rows = input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => line.replace(/\s+/g, ""));
  const parsed = rows.map((line) => {
    const [daysRaw, weightRaw] = line.split(":");
    const days = Number(daysRaw || 0);
    const weight = Number(weightRaw || 0);
    if (!Number.isFinite(days) || !Number.isFinite(weight) || days <= 0 || weight <= 0) {
      throw new Error(`Некорректная строка весов: ${line}`);
    }
    return { days: Math.floor(days), weight: Math.floor(weight) };
  });
  if (parsed.length === 0) throw new Error("Укажите хотя бы одну строку весов");
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
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки конфигурации рулетки"));
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async (): Promise<void> => {
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
      setResult("Конфигурация рулетки сохранена.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка сохранения"));
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
            throw new Error(`Некорректная строка уровней лояльности: ${line}`);
          }
          return { days: Math.floor(days), bonus_days: Math.floor(bonusDays), perk };
        });
      const payload: AdminLoyaltyConfig = {
        enabled: loyaltyConfig.enabled,
        tiers,
      };
      const out = await adminLoyaltyConfigUpdate(payload);
      setLoyaltyConfig(out.loyalty_config);
      setLoyaltyText((out.loyalty_config.tiers || []).map((row) => `${row.days}:${row.bonus_days}:${row.perk}`).join("\n"));
      setResult("Конфигурация лояльности сохранена.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка сохранения конфигурации лояльности"));
    } finally {
      setBusy(false);
    }
  };

  const grantLoyalty = async (): Promise<void> => {
    const tgId = Number(loyaltyGrantUser || 0);
    const tierDays = Number(loyaltyGrantTier || 0);
    if (!Number.isFinite(tgId) || tgId <= 0 || !Number.isFinite(tierDays) || tierDays <= 0) {
      setError("Укажите корректные tg_id и дни уровня");
      return;
    }
    setBusy(true);
    setError("");
    setResult("");
    try {
      const out = await adminUserLoyaltyGrant(tgId, tierDays);
      setResult(`Награда лояльности выдана: ${out.tier_days} дней для ${tgId} (синхронизация: ${out.sync_ok ? "ok" : "предупреждение"})`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось выдать награду лояльности"));
    } finally {
      setBusy(false);
    }
  };

  // Visual weight distribution
  const weightBars = useMemo(() => {
    try {
      const parsed = parseWeights(weightsText);
      const totalWeight = parsed.reduce((sum, w) => sum + w.weight, 0);
      return parsed.map((w) => ({ ...w, pct: Math.round((w.weight / totalWeight) * 100) }));
    } catch {
      return [];
    }
  }, [weightsText]);

  const PRESET_OPTIONS = [
    { value: "balanced", label: "сбалансированный" },
    { value: "generous", label: "щедрый" },
    { value: "conservative", label: "консервативный" },
    { value: "jackpot", label: "джекпот" },
  ];

  return (
    <section className="space-y-5">
      <article className="stat-card p-6">
        <div className="flex items-center gap-3 mb-1">
          <div className="stat-icon stat-icon-amber"><Dices size={22} /></div>
          <div>
            <h2 className="font-display text-xl font-bold">Бонусы и рулетка</h2>
            <p className="text-xs text-slate-500">Настройка cooldown и весов выдачи дней бонуса</p>
          </div>
        </div>
      </article>

      <div className="grid gap-5 xl:grid-cols-[1fr,0.6fr]">
        {/* ── Config form ──────────────────────────────── */}
        <article className="glass-card p-5 space-y-4">
          {!config ? (
            <p className="text-sm text-slate-500">Загрузка конфигурации...</p>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1.5">Профиль</label>
                  <div className="flex flex-wrap gap-1.5">
                    {PRESET_OPTIONS.map((preset) => (
                      <button
                        key={preset.value}
                        type="button"
                        className={`haptic-tap rounded-xl px-3 py-1.5 text-xs font-semibold transition-all ${config.preset === preset.value
                            ? "bg-violet-600 text-white shadow-md shadow-violet-600/20"
                            : "outline-btn"
                          }`}
                        onClick={() => setConfig((prev) => (prev ? { ...prev, preset: preset.value } : prev))}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1.5 flex items-center gap-1">
                    <Timer size={10} /> Cooldown (часы)
                  </label>
                  <input
                    type="number"
                    value={config.cooldown_hours}
                    onChange={(event) =>
                      setConfig((prev) =>
                        prev ? { ...prev, cooldown_hours: Math.max(1, Math.min(2160, Number(event.target.value || 1))) } : prev,
                      )
                    }
                    className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  />
                  <p className="mt-1 text-[10px] text-slate-400">{Math.round((config.cooldown_hours || 168) / 24)} дней между спинами</p>
                </div>
              </div>

              <div>
                <label className="block text-[10px] uppercase tracking-[0.1em] text-slate-500 mb-1.5">Веса (days:weight, по строкам)</label>
                <textarea
                  rows={7}
                  value={weightsText}
                  onChange={(event) => setWeightsText(event.target.value)}
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 font-mono text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70 resize-none"
                  placeholder={"1:45\n3:35\n7:15\n30:5"}
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <button className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em] inline-flex items-center gap-2" type="button" onClick={() => void save()} disabled={busy}>
                  {busy ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                  {busy ? "Сохранение..." : "Сохранить"}
                </button>
                <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold inline-flex items-center gap-1.5" type="button" onClick={() => void load()}>
                  <RefreshCw size={13} /> Перезагрузить
                </button>
              </div>
            </>
          )}

          {result ? (
            <div className="rounded-xl bg-emerald-500/10 p-3 flex items-center gap-2">
              <span className="status-dot status-dot-online" />
              <p className="text-sm text-emerald-600 dark:text-emerald-300 font-medium">{result}</p>
            </div>
          ) : null}
          {error ? (
            <div className="rounded-xl bg-rose-500/10 p-3 flex items-center gap-2">
              <span className="status-dot status-dot-offline" />
              <p className="text-sm text-rose-500 font-medium">{error}</p>
            </div>
          ) : null}
        </article>

        {/* ── Weight distribution visual ───────────────── */}
        <article className="glass-card p-5">
          <h3 className="font-display text-lg font-bold mb-3">Распределение весов</h3>
          {weightBars.length === 0 ? (
            <div className="empty-state py-6">
              <Dices size={24} />
              <p className="text-xs">Введите корректные веса</p>
            </div>
          ) : (
            <div className="space-y-3">
              {weightBars.map((bar, idx) => {
                const colors = ["progress-fill-emerald", "progress-fill", "progress-fill-amber", "progress-fill-rose"];
                const fillClass = colors[idx % colors.length];
                return (
                  <div key={`${bar.days}-${idx}`}>
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="flex items-center gap-1.5">
                        <span className="badge badge-violet">{bar.days}d</span>
                        <span className="text-slate-500">weight: {bar.weight}</span>
                      </span>
                      <strong className="gradient-text">{bar.pct}%</strong>
                    </div>
                    <div className="progress-track">
                      <div className={`progress-fill ${fillClass}`} style={{ width: `${bar.pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </article>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr,0.8fr]">
        <article className="glass-card p-5 space-y-4">
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-display text-lg font-bold">Лояльность без оттока</h3>
            <label className="inline-flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={Boolean(loyaltyConfig?.enabled)}
                onChange={(event) => setLoyaltyConfig((prev) => (prev ? { ...prev, enabled: event.target.checked } : prev))}
              />
              включено
            </label>
          </div>
          <p className="text-xs text-slate-500">Формат строк: `days:bonus_days:perk`</p>
          <textarea
            rows={6}
            value={loyaltyText}
            onChange={(event) => setLoyaltyText(event.target.value)}
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 font-mono text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70 resize-none"
            placeholder={"30:1:priority_support\n90:3:fast_resync\n180:7:vip_queue"}
          />
            <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void saveLoyalty()} disabled={busy}>
            Сохранить лояльность
          </button>
        </article>

        <article className="glass-card p-5 space-y-3">
          <h3 className="font-display text-lg font-bold">Ручная выдача tier</h3>
          <input
            value={loyaltyGrantUser}
            onChange={(event) => setLoyaltyGrantUser(event.target.value)}
            placeholder="tg_id пользователя"
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <input
            value={loyaltyGrantTier}
            onChange={(event) => setLoyaltyGrantTier(event.target.value)}
            placeholder="дни уровня (30/90/180)"
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void grantLoyalty()} disabled={busy}>
            Выдать уровень
          </button>
        </article>
      </div>
    </section>
  );
}
