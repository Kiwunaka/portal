"use client";

import { fetchPublicPlans, type PlanCatalogRow } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type ComparisonRow = {
  metric: string;
  start: string;
  pro: string;
  ultra: string;
};

const COMPARISON_ROWS: ComparisonRow[] = [
  { metric: "Устройства", start: "1", pro: "До 5", ultra: "До 5" },
  { metric: "Страны", start: "NL", pro: "Польша, Нидерланды, США, Италия", ultra: "Полный пул + приоритет" },
  { metric: "Маршрутизация", start: "VPN для базовых задач", pro: "Полный VPN-маршрут ежедневно", ultra: "VPN + приоритет" },
  { metric: "Скоростной профиль", start: "Базовый", pro: "Высокий", ultra: "Максимальный" },
  { metric: "Поддержка", start: "Стандартная", pro: "Быстрый Telegram-ответ", ultra: "Приоритет 24/7" },
];

function planColumn(planCode: string | null | undefined): "start" | "pro" | "ultra" {
  const code = String(planCode || "").trim().toLowerCase();
  if (code === "start_99") return "start";
  if (code === "1_month" || code === "3_months") return "pro";
  return "ultra";
}

export default function SubscriptionPage() {
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await fetchPublicPlans();
        if (!cancelled) {
          const rows = (payload.plans || [])
            .filter((plan) => Boolean(plan.is_active))
            .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
          setPlans(rows);
          setError("");
        }
      } catch (error) {
        if (!cancelled) {
          setError(String((error as { message?: string })?.message || error));
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeColumn = planColumn(dash?.current_plan_code || dash?.sub_type || "");

  const planCards = useMemo(() => {
    if (plans.length > 0) return plans;
    return [
      { code: "start_99", label: "Start", amount_rub: 99, amount_stars: 0, days: 30, device_limit: 1, node_policy: "nl_only", badge: "Вход", is_active: true, sort_order: 1 },
      { code: "1_month", label: "Pro 1 месяц", amount_rub: 249, amount_stars: 249, days: 30, device_limit: 5, node_policy: "paid_pool", badge: "Популярный", is_active: true, sort_order: 2 },
      { code: "12_months", label: "Ultra 12 месяцев", amount_rub: 1499, amount_stars: 1499, days: 365, device_limit: 5, node_policy: "paid_pool", badge: "Выгода", is_active: true, sort_order: 3 },
    ] as PlanCatalogRow[];
  }, [plans]);

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">subscription</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Управление подпиской</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          RUB-оплата на сайте — основной путь. Telegram Stars остаются как резервный вариант.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <Link href="/subscription/checkout/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть оплату
          </Link>
          <Link href="https://t.me/portal_service_bot" target="_blank" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Оплатить через бота
          </Link>
        </div>
        <p className="mt-4 text-xs text-slate-500">Пользователь: {user?.username ? `@${user.username}` : `ID ${user?.tg_id}`}</p>
      </section>

      <section className="grid gap-5 md:grid-cols-3">
        {planCards.map((plan) => (
          <article key={plan.code} className="glass-card p-6">
            <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">{plan.badge || "Тариф"}</p>
            <h2 className="mt-2 font-display text-3xl font-bold">{plan.label}</h2>
            <p className="mt-3 text-2xl font-semibold">{Number(plan.amount_rub || 0)} ₽</p>
            <p className="mt-1 text-xs text-slate-500">{plan.days} дней • до {plan.device_limit} устройств</p>
            <Link href={`/subscription/checkout/?plan=${encodeURIComponent(plan.code)}`} className="btn-primary mt-5 inline-flex rounded-xl px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.12em]">
              Выбрать
            </Link>
          </article>
        ))}
      </section>

      <section className="glass-card p-7">
        <div className="mb-4">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Сравнение тарифов VPN</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Прозрачные параметры</h2>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/45 dark:border-white/10">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="bg-white/55 dark:bg-white/5">
              <tr>
                <th className="px-4 py-3">Параметр</th>
                <th className={`px-4 py-3 ${activeColumn === "start" ? "text-violet-600 dark:text-violet-300" : ""}`}>Start</th>
                <th className={`px-4 py-3 ${activeColumn === "pro" ? "text-violet-600 dark:text-violet-300" : ""}`}>Pro</th>
                <th className={`px-4 py-3 ${activeColumn === "ultra" ? "text-violet-600 dark:text-violet-300" : ""}`}>Ultra</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.metric} className="border-t border-white/40 dark:border-white/10">
                  <td className="px-4 py-3 font-semibold">{row.metric}</td>
                  <td className={`px-4 py-3 ${activeColumn === "start" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.start}</td>
                  <td className={`px-4 py-3 ${activeColumn === "pro" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.pro}</td>
                  <td className={`px-4 py-3 ${activeColumn === "ultra" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.ultra}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">
          Почему часть медиасервисов может идти напрямую: в некоторых сценариях это снижает задержку и делает воспроизведение
          стабильнее. VPN-маршрут для основного трафика сохраняется по тарифной политике.
        </p>
        {error ? <p className="mt-3 text-xs text-rose-500">{error}</p> : null}
      </section>
    </main>
  );
}
