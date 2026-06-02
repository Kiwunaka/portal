"use client";

import { adminFunnelSummary, type AdminFunnelSummary } from "@/lib/api";
import { ArrowDownRight, BarChart3, Loader2, MousePointerClick, RefreshCw, Route, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type RangePreset = "7" | "14" | "30";

function buildRange(days: RangePreset): { from: string; to: string } {
  const to = new Date();
  const from = new Date(to);
  from.setDate(to.getDate() - (Number(days) - 1));
  return { from: from.toISOString().slice(0, 10), to: to.toISOString().slice(0, 10) };
}

function formatNumber(value?: number | null): string {
  return new Intl.NumberFormat("ru-RU").format(Number(value || 0));
}

function formatDateTime(value?: string | null): string {
  if (!value) return "нет времени";
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function sourceLabel(value: string): string {
  const source = String(value || "unknown").toLowerCase();
  if (source === "site") return "Сайт";
  if (source === "webapp") return "Кабинет";
  if (source === "bot") return "Бот";
  if (source === "offer") return "Оффер";
  if (source === "unknown") return "Без источника";
  return value;
}

function stageLabel(value?: string | null): string {
  const stage = String(value || "").toLowerCase();
  if (stage === "site_visit") return "Сайт";
  if (stage === "install_intent") return "Установка";
  if (stage === "cabinet_intent") return "Кабинет";
  if (stage === "bot_intent") return "Бот";
  if (stage === "checkout_view") return "Оплата";
  if (stage === "checkout_start") return "Оплата начата";
  return value || "Пользовательское событие";
}

export default function AdminFunnelPage() {
  const [range, setRange] = useState<RangePreset>("7");
  const [data, setData] = useState<AdminFunnelSummary | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  const period = useMemo(() => buildRange(range), [range]);

  const load = async (): Promise<void> => {
    setBusy(true);
    setError("");
    try {
      setData(await adminFunnelSummary(period));
    } catch (err) {
      setError(String((err as { message?: string })?.message || err || "Не удалось загрузить воронку."));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    void load();
  }, [period.from, period.to]);

  const totals = data?.totals || { visitors: 0, app_opens: 0, checkouts: 0, paid: 0, connected: 0 };

  return (
    <section className="space-y-5">
      <div className="glass-card p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="stat-icon stat-icon-blue">
              <Route size={20} />
            </div>
            <div>
              <h2 className="font-display text-xl font-bold">Воронка входа</h2>
              <p className="mt-0.5 text-xs text-slate-500">
                Сайт, кабинет, бот и оплата за период {data?.period.from || period.from} — {data?.period.to || period.to}.
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {(["7", "14", "30"] as RangePreset[]).map((item) => (
              <button
                key={item}
                className={`outline-btn rounded-xl px-3 py-2 text-xs font-semibold ${range === item ? "border-emerald-300 bg-emerald-50 text-emerald-700" : ""}`}
                type="button"
                onClick={() => setRange(item)}
              >
                {item} дней
              </button>
            ))}
            <button className="btn-primary inline-flex items-center gap-1.5 rounded-xl px-4 py-2 text-xs font-semibold" type="button" onClick={() => void load()} disabled={busy}>
              {busy ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              Обновить
            </button>
          </div>
        </div>
        {error ? <p className="mt-3 text-sm text-rose-500">{error}</p> : null}
      </div>

      <div className="grid gap-3 md:grid-cols-5">
        {[
          { label: "Посетители", value: totals.visitors, icon: Users, tone: "stat-icon-blue" },
          { label: "Кабинет/бот", value: totals.app_opens, icon: MousePointerClick, tone: "stat-icon-emerald" },
          { label: "Начали оплату", value: totals.checkouts, icon: BarChart3, tone: "stat-icon-amber" },
          { label: "Оплатили", value: totals.paid, icon: BarChart3, tone: "stat-icon-emerald" },
          { label: "Подключились", value: totals.connected, icon: Route, tone: "stat-icon-violet" },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="stat-card p-4">
              <div className={`stat-icon ${item.tone}`}>
                <Icon size={18} />
              </div>
              <p className="mt-3 text-xs text-slate-500">{item.label}</p>
              <p className="mt-1 text-2xl font-bold">{formatNumber(item.value)}</p>
            </div>
          );
        })}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_0.85fr]">
        <div className="glass-card p-5">
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h3 className="font-display text-xl font-bold">Где люди останавливаются</h3>
              <p className="text-xs text-slate-500">Каждый этап показывает, сколько дошло до следующего шага.</p>
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-3 py-2.5">Этап</th>
                  <th className="px-3 py-2.5">Вошли</th>
                  <th className="px-3 py-2.5">Дошли дальше</th>
                  <th className="px-3 py-2.5">Остановились</th>
                  <th className="px-3 py-2.5">Переход</th>
                </tr>
              </thead>
              <tbody>
                {(data?.stages || []).map((row, index) => (
                  <tr key={row.key} className={`border-t border-white/20 dark:border-white/5 ${index % 2 === 0 ? "bg-white/30 dark:bg-white/[0.02]" : ""}`}>
                    <td className="px-3 py-3 font-semibold">{row.label}</td>
                    <td className="px-3 py-3">{formatNumber(row.entered)}</td>
                    <td className="px-3 py-3">{formatNumber(row.reached_next)}</td>
                    <td className="px-3 py-3">
                      <span className={row.dropped > 0 ? "text-amber-600" : "text-emerald-600"}>{formatNumber(row.dropped)}</span>
                    </td>
                    <td className="px-3 py-3">
                      <span className={`badge ${row.conversion_pct >= 70 ? "badge-success" : row.conversion_pct >= 30 ? "badge-warning" : "badge-danger"}`}>
                        {row.conversion_pct.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card p-5">
          <div className="mb-4 flex items-center gap-3">
            <div className="stat-icon stat-icon-amber">
              <ArrowDownRight size={18} />
            </div>
            <div>
              <h3 className="font-display text-xl font-bold">Отвалы</h3>
              <p className="text-xs text-slate-500">Куда смотреть оператору в первую очередь.</p>
            </div>
          </div>
          <div className="space-y-3">
            {(data?.drop_reasons || []).map((row) => (
              <div key={row.reason} className="rounded-xl border border-white/15 bg-white/35 p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold">{row.reason}</p>
                  <span className={`badge ${row.count > 0 ? "badge-warning" : "badge-success"}`}>{formatNumber(row.count)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <div className="glass-card p-5">
          <h3 className="font-display text-xl font-bold">Источники</h3>
          <p className="mt-1 text-xs text-slate-500">Сайт считается по session id, кабинет и бот — по известным событиям пользователей.</p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-[0.1em] text-slate-500">
                  <th className="px-3 py-2.5">Источник</th>
                  <th className="px-3 py-2.5">Входы</th>
                  <th className="px-3 py-2.5">Кабинет/бот</th>
                  <th className="px-3 py-2.5">Оплата</th>
                  <th className="px-3 py-2.5">Успех</th>
                </tr>
              </thead>
              <tbody>
                {(data?.by_source || []).map((row, index) => (
                  <tr key={row.source} className={`border-t border-white/20 dark:border-white/5 ${index % 2 === 0 ? "bg-white/30 dark:bg-white/[0.02]" : ""}`}>
                    <td className="px-3 py-2.5 font-semibold">{sourceLabel(row.source)}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.visitors)}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.app_opens)}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.checkouts)}</td>
                    <td className="px-3 py-2.5">{formatNumber(row.paid || row.connected)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-card p-5">
          <h3 className="font-display text-xl font-bold">Последние входы и действия</h3>
          <p className="mt-1 text-xs text-slate-500">Известные пользователи показываются по Telegram ID, сайт — по короткому session id.</p>
          <div className="mt-4 space-y-2">
            {(data?.recent || []).map((row, index) => (
              <div key={`${row.kind}:${row.created_at}:${row.event_name}:${index}`} className="rounded-xl border border-white/15 bg-white/35 p-3 dark:border-white/10 dark:bg-white/[0.04]">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`badge ${row.kind === "site" ? "badge-info" : "badge-success"}`}>{row.kind === "site" ? "сайт" : "пользователь"}</span>
                      <strong className="text-sm">{stageLabel(row.stage)}</strong>
                      <span className="text-xs text-slate-500">{row.event_name}</span>
                    </div>
                    <p className="mt-1 text-xs text-slate-500">
                      {row.tg_id ? `tg_id ${row.tg_id}` : `session ${String(row.session_id || "").slice(0, 12) || "нет"}`} · {sourceLabel(row.source)}
                      {row.path ? ` · ${row.path}` : ""}
                    </p>
                  </div>
                  <span className="text-xs text-slate-500">{formatDateTime(row.created_at)}</span>
                </div>
              </div>
            ))}
            {!busy && (data?.recent || []).length === 0 ? <p className="text-sm text-slate-500">За период событий не найдено.</p> : null}
          </div>
        </div>
      </div>

      {data?.notes?.length ? (
        <div className="glass-card p-4">
          <div className="flex flex-wrap gap-2">
            {data.notes.map((note) => (
              <span key={note} className="badge badge-info">
                {note}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}
