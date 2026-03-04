"use client";

import { adminWheelConfig, adminWheelConfigUpdate, type AdminWheelConfig } from "@/lib/api";
import { useEffect, useState } from "react";

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
  const [weightsText, setWeightsText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState("");

  const load = async (): Promise<void> => {
    setError("");
    setResult("");
    try {
      const cfg = await adminWheelConfig();
      setConfig(cfg);
      setWeightsText(weightsToText(cfg.weights || []));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Ошибка загрузки wheel config"));
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

  return (
    <section className="space-y-4">
      <article className="glass-card p-4">
        <h2 className="font-display text-2xl font-semibold">Bonuses / Рулетка</h2>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Настройка cooldown и весов выдачи дней бонуса.</p>
      </article>

      <article className="glass-card p-4 space-y-3">
        {!config ? (
          <p className="text-sm text-slate-500">Загрузка конфигурации...</p>
        ) : (
          <>
            <div className="grid gap-3 md:grid-cols-2">
              <label className="text-sm">
                <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">Preset</span>
                <input
                  value={config.preset}
                  onChange={(event) => setConfig((prev) => (prev ? { ...prev, preset: event.target.value } : prev))}
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
              </label>
              <label className="text-sm">
                <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">Cooldown hours</span>
                <input
                  type="number"
                  value={config.cooldown_hours}
                  onChange={(event) =>
                    setConfig((prev) =>
                      prev ? { ...prev, cooldown_hours: Math.max(1, Math.min(2160, Number(event.target.value || 1))) } : prev,
                    )
                  }
                  className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
              </label>
            </div>

            <label className="block text-sm">
              <span className="mb-1 block text-xs uppercase tracking-[0.12em] text-slate-500">Weights (days:weight, по строкам)</span>
              <textarea
                rows={7}
                value={weightsText}
                onChange={(event) => setWeightsText(event.target.value)}
                className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 font-mono text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                placeholder={"1:45\n3:35\n7:15\n30:5"}
              />
            </label>

            <div className="flex flex-wrap gap-2">
              <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em]" type="button" onClick={() => void save()} disabled={busy}>
                {busy ? "Сохранение..." : "Сохранить"}
              </button>
              <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={() => void load()}>
                Перезагрузить
              </button>
            </div>
          </>
        )}

        {result ? <p className="text-sm text-emerald-500">{result}</p> : null}
        {error ? <p className="text-sm text-rose-500">{error}</p> : null}
      </article>
    </section>
  );
}
