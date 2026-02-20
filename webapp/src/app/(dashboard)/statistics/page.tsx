"use client";

import { motion } from "framer-motion";
import { useMemo, useState } from "react";

const WEEK = {
  points: [16, 28, 22, 31, 42, 39, 34],
  labels: ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
  table: [
    ["Сегодня 14:30", "Нидерланды", "2ч 15м", "1.2 ГБ"],
    ["Вчера 18:45", "Италия", "45м", "450 МБ"],
    ["12 окт 09:10", "США", "5ч 30м", "4.8 ГБ"],
  ],
  traffic: "42.8 ГБ",
  trend: "+12% к прошлой неделе",
};

const MONTH = {
  points: [34, 48, 40, 56, 62, 55, 44],
  labels: ["1", "5", "10", "15", "20", "25", "30"],
  table: [
    ["15 окт 21:40", "Польша", "3ч 12м", "2.4 ГБ"],
    ["13 окт 11:12", "Нидерланды", "1ч 05м", "630 МБ"],
    ["10 окт 08:22", "США", "6ч 10м", "5.6 ГБ"],
  ],
  traffic: "168.4 ГБ",
  trend: "+24% к прошлому месяцу",
};

export default function StatisticsPage() {
  const [mode, setMode] = useState<"week" | "month">("week");
  const current = useMemo(() => (mode === "week" ? WEEK : MONTH), [mode]);

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">statistics</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Статистика использования доступа</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Визуальная картина по трафику и сессиям. В один взгляд понятно, как используется ваш профиль.
        </p>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        <article className="glass-card p-5">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Всего трафика</p>
          <p className="mt-3 font-display text-4xl font-bold">{current.traffic}</p>
          <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-400">{current.trend}</p>
        </article>
        <article className="glass-card p-5">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Средняя скорость</p>
          <p className="mt-3 font-display text-4xl font-bold">{mode === "week" ? "84 Мбит/с" : "91 Мбит/с"}</p>
          <p className="mt-2 text-xs text-slate-500">Пиковая: {mode === "week" ? "120" : "132"} Мбит/с</p>
        </article>
        <article className="glass-card p-5">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Основная локация</p>
          <p className="mt-3 font-display text-4xl font-bold">{mode === "week" ? "NL" : "PL"}</p>
          <p className="mt-2 text-xs text-slate-500">{mode === "week" ? "Amsterdam-1 • 23ms" : "Warsaw-2 • 19ms"}</p>
        </article>
        <article className="glass-card p-5">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Сессии</p>
          <p className="mt-3 font-display text-4xl font-bold">{mode === "week" ? "17" : "68"}</p>
          <p className="mt-2 text-xs text-slate-500">{mode === "week" ? "за последние 7 дней" : "за последние 30 дней"}</p>
        </article>
      </section>

      <section className="glass-card p-7">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="font-display text-2xl font-semibold">Потребление по дням</h2>
          <div className="flex gap-2 text-xs uppercase tracking-[0.14em]">
            <button
              type="button"
              onClick={() => setMode("week")}
              className={`rounded-lg px-3 py-1.5 ${mode === "week" ? "bg-violet-600 text-white" : "bg-white/70 text-slate-600 dark:bg-white/10 dark:text-slate-300"}`}
            >
              Неделя
            </button>
            <button
              type="button"
              onClick={() => setMode("month")}
              className={`rounded-lg px-3 py-1.5 ${mode === "month" ? "bg-violet-600 text-white" : "bg-white/70 text-slate-600 dark:bg-white/10 dark:text-slate-300"}`}
            >
              Месяц
            </button>
          </div>
        </div>
        <div className="grid h-56 grid-cols-7 items-end gap-3">
          {current.points.map((point, idx) => (
            <motion.div
              key={`${mode}-${point}-${idx}`}
              initial={{ height: 0 }}
              animate={{ height: `${point * 3.2}px` }}
              transition={{ duration: 0.45, delay: idx * 0.05 }}
              className="rounded-t-xl bg-gradient-to-t from-violet-700 to-violet-400"
            />
          ))}
        </div>
        <div className="mt-3 grid grid-cols-7 gap-3 text-center text-xs text-slate-500">
          {current.labels.map((day) => (
            <span key={day}>{day}</span>
          ))}
        </div>
      </section>

      <section className="glass-card overflow-hidden p-0">
        <div className="border-b border-white/50 px-7 py-5 dark:border-white/10">
          <h2 className="font-display text-2xl font-semibold">История подключений</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] text-left text-sm">
            <thead className="bg-white/55 dark:bg-white/5">
              <tr>
                <th className="px-7 py-3 font-medium">Дата</th>
                <th className="px-7 py-3 font-medium">Локация</th>
                <th className="px-7 py-3 font-medium">Длительность</th>
                <th className="px-7 py-3 font-medium">Трафик</th>
              </tr>
            </thead>
            <tbody>
              {current.table.map((row) => (
                <tr key={row[0]} className="border-t border-white/40 hover:bg-white/45 dark:border-white/10 dark:hover:bg-white/5">
                  {row.map((cell) => (
                    <td key={cell} className="px-7 py-3">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
