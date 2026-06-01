"use client";

import { adminButtonClass, adminPanelClass } from "@/components/admin/admin-shell";
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
      throw new Error(`Некорректная строка веса: ${line}`);
    }
    return { days: Math.floor(days), weight: Math.floor(weight) };
  });
  if (parsed.length === 0) throw new Error("Добавьте хотя бы одну строку с весом.");
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
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить бонусы."));
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
      setResult("Настройки колеса сохранены.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить настройки колеса."));
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
            throw new Error(`Некорректная строка уровня лояльности: ${line}`);
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
      setResult("Настройки лояльности сохранены.");
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось сохранить лояльность."));
    } finally {
      setBusy(false);
    }
  };

  const grantLoyalty = async (): Promise<void> => {
    const tgId = Number(loyaltyGrantUser || 0);
    const tierDays = Number(loyaltyGrantTier || 0);
    if (!Number.isFinite(tgId) || tgId <= 0 || !Number.isFinite(tierDays) || tierDays <= 0) {
      setError("Укажите Telegram ID пользователя и длину уровня.");
      return;
    }
    setBusy(true);
    setError("");
    setResult("");
    try {
      const out = await adminUserLoyaltyGrant(tgId, tierDays);
      setResult(`Лояльность выдана: ${out.tier_days} дней пользователю ${tgId} (${out.sync_ok ? "синхронизация успешна" : "есть рассинхрон"}).`);
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось выдать бонус."));
    } finally {
      setBusy(false);
    }
  };

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
    { value: "balanced", label: "Сбалансированный" },
    { value: "generous", label: "Щедрый" },
    { value: "conservative", label: "Осторожный" },
    { value: "jackpot", label: "Джекпот" },
  ];

  return (
    <section className="space-y-5">
      <article className={adminPanelClass("neutral")}>
        <div className="mb-1 flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="stat-icon stat-icon-amber">
            <Dices size={22} />
          </div>
          <div className="min-w-0">
            <h2 className="font-display text-xl font-bold">Бонусы и лояльность</h2>
            <p className="text-xs text-slate-500">Колесо бонусов, ручная выдача уровней и настройка цепочек удержания.</p>
          </div>
        </div>
        <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
          Используйте этот раздел, чтобы управлять вероятностями, паузой между попытками и правилами начисления лояльности.
        </p>
      </article>

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr),minmax(280px,0.6fr)]">
        <article className={`${adminPanelClass("neutral")} space-y-4`}>
          {!config ? (
            <p className="text-sm text-slate-500">Загружаем настройки...</p>
          ) : (
            <>
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Пресет</label>
                  <div className="flex flex-wrap gap-1.5">
                    {PRESET_OPTIONS.map((preset) => (
                      <button
                        key={preset.value}
                        type="button"
                        className={`haptic-tap ${config.preset === preset.value ? adminButtonClass("primary", "xs") : adminButtonClass("ghost", "xs")} transition-all`}
                        onClick={() => setConfig((prev) => (prev ? { ...prev, preset: preset.value } : prev))}
                      >
                        {preset.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="mb-1.5 flex items-center gap-1 text-[10px] uppercase tracking-[0.1em] text-slate-500">
                    <Timer size={10} /> Охлаждение (часы)
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
                  <p className="mt-1 text-[10px] text-slate-400">{Math.round((config.cooldown_hours || 168) / 24)} дней до следующего запуска</p>
                </div>
              </div>

              <div>
                <label className="mb-1.5 block text-[10px] uppercase tracking-[0.1em] text-slate-500">Весы колеса (days:weight, по одной строке)</label>
                <p className="mb-2 text-xs text-slate-500">Чем выше weight, тем чаще выпадает бонус с указанной длительностью. Формат строки: <code className="rounded bg-white/70 px-1 py-0.5 dark:bg-white/10">дни:вес</code>.</p>
                <textarea
                  rows={7}
                  value={weightsText}
                  onChange={(event) => setWeightsText(event.target.value)}
                  className="w-full resize-none rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 font-mono text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                  placeholder={"1:45\n3:35\n7:15\n30:5"}
                />
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                <button className={adminButtonClass("primary")} type="button" onClick={() => void save()} disabled={busy}>
                  {busy ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                  {busy ? "Сохраняем..." : "Сохранить"}
                </button>
                <button className={adminButtonClass("secondary")} type="button" onClick={() => void load()}>
                  <RefreshCw size={13} /> Перезагрузить
                </button>
              </div>
            </>
          )}

          {result ? (
            <div className="flex items-center gap-2 rounded-xl bg-emerald-500/10 p-3">
              <span className="status-dot status-dot-online" />
              <p className="text-sm font-medium text-emerald-600 dark:text-emerald-300">{result}</p>
            </div>
          ) : null}
          {error ? (
            <div className="flex items-center gap-2 rounded-xl bg-rose-500/10 p-3">
              <span className="status-dot status-dot-offline" />
              <p className="text-sm font-medium text-rose-500">{error}</p>
            </div>
          ) : null}
        </article>

      <article className={adminPanelClass("neutral")}>
          <h3 className="mb-3 font-display text-lg font-bold">Распределение веса</h3>
          <p className="mb-3 text-xs text-slate-500">Сводка показывает, насколько часто выпадает каждый вариант в текущем наборе весов.</p>
          {weightBars.length === 0 ? (
            <div className="empty-state py-6">
              <Dices size={24} />
              <p className="text-xs">Сначала задайте весы колеса</p>
            </div>
          ) : (
            <div className="space-y-3">
              {weightBars.map((bar, idx) => {
                const colors = ["progress-fill-emerald", "progress-fill", "progress-fill-amber", "progress-fill-rose"];
                const fillClass = colors[idx % colors.length];
                return (
                  <div key={`${bar.days}-${idx}`}>
                    <div className="mb-1 flex items-center justify-between text-xs">
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

      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr),minmax(320px,0.8fr)]">
        <article className="glass-card space-y-4 p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="font-display text-lg font-bold">Настройки лояльности</h3>
            <label className="inline-flex items-center gap-2 text-xs">
              <input
                type="checkbox"
                checked={Boolean(loyaltyConfig?.enabled)}
                onChange={(event) => setLoyaltyConfig((prev) => (prev ? { ...prev, enabled: event.target.checked } : prev))}
              />
              Включено
            </label>
          </div>
          <p className="text-xs text-slate-500">Формат строки: <code className="rounded bg-white/70 px-1 py-0.5 dark:bg-white/10">days:bonus_days:perk</code>. Один уровень на строку.</p>
          <textarea
            rows={6}
            value={loyaltyText}
            onChange={(event) => setLoyaltyText(event.target.value)}
            className="w-full resize-none rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 font-mono text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            placeholder={"30:1:priority_support\n90:3:fast_resync\n180:7:vip_queue"}
          />
            <button className={adminButtonClass("secondary")} type="button" onClick={() => void saveLoyalty()} disabled={busy}>
            Сохранить лояльность
          </button>
        </article>

        <article className="glass-card space-y-3 p-5">
          <h3 className="font-display text-lg font-bold">Выдать уровень вручную</h3>
          <p className="text-xs text-slate-500">Быстрая ручная выдача бонуса по Telegram ID.</p>
          <input
            value={loyaltyGrantUser}
            onChange={(event) => setLoyaltyGrantUser(event.target.value)}
            placeholder="Telegram ID пользователя"
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <input
            value={loyaltyGrantTier}
            onChange={(event) => setLoyaltyGrantTier(event.target.value)}
            placeholder="Дни уровня, например 30 / 90 / 180"
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
            <button className={adminButtonClass("secondary")} type="button" onClick={() => void grantLoyalty()} disabled={busy}>
            Выдать бонус
          </button>
        </article>
      </div>
    </section>
  );
}
