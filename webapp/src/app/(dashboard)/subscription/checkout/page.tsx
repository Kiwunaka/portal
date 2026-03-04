"use client";

import { createRubCheckoutOrder, fetchPublicPlans, type PlanCatalogRow } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type Breakdown = {
  base: number;
  discountPct: number;
  final: number;
};

type ComparisonRow = {
  metric: string;
  start: string;
  pro: string;
  ultra: string;
};

const COMPARISON_ROWS: ComparisonRow[] = [
  { metric: "Устройства", start: "1", pro: "До 5", ultra: "До 5" },
  { metric: "Страны", start: "NL", pro: "Польша, Нидерланды, США, Италия", ultra: "Полный пул + приоритет" },
  { metric: "Маршрутизация", start: "Базовый защищенный маршрут", pro: "Полный маршрут ежедневно", ultra: "Маршрут + приоритет" },
  { metric: "Скоростной профиль", start: "Базовый", pro: "Высокий", ultra: "Максимальный" },
  { metric: "Поддержка", start: "Стандартная", pro: "Быстрый Telegram-ответ", ultra: "Приоритет 24/7" },
];

function planColumn(planCode: string | null | undefined): "start" | "pro" | "ultra" {
  const code = String(planCode || "").trim().toLowerCase();
  if (code === "start_99") return "start";
  if (code === "1_month" || code === "3_months") return "pro";
  return "ultra";
}

function normalizePlans(rows: PlanCatalogRow[]): PlanCatalogRow[] {
  return rows
    .filter((row) => Boolean(row.is_active) && Number(row.amount_rub || 0) > 0)
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
}

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const { user } = usePortalSession();

  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
  const [selectedCode, setSelectedCode] = useState("start_99");
  const [busy, setBusy] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [breakdown, setBreakdown] = useState<Breakdown | null>(null);

  const queryCampaign = (searchParams.get("campaign") || "").trim();
  const queryPromo = (searchParams.get("promo") || "").trim().toUpperCase();
  const queryTgId = (searchParams.get("tg_id") || "").trim();

  useEffect(() => {
    const plan = (searchParams.get("plan") || "").trim().toLowerCase();
    if (plan) setSelectedCode(plan);
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await fetchPublicPlans();
        const rows = normalizePlans(payload.plans || []);
        if (!cancelled && rows.length) {
          setPlans(rows);
          if (!rows.some((row) => row.code === selectedCode)) {
            setSelectedCode(rows[0].code);
          }
        }
      } catch {
        if (!cancelled) {
          setPlans([
            { code: "start_99", label: "Start 30 дней", amount_rub: 99, amount_stars: 0, days: 30, device_limit: 1, node_policy: "nl_only", badge: "Вход", is_active: true, sort_order: 1 },
            { code: "1_month", label: "Pro 1 месяц", amount_rub: 249, amount_stars: 249, days: 30, device_limit: 5, node_policy: "paid_pool", badge: "Популярный", is_active: true, sort_order: 2 },
            { code: "12_months", label: "Ultra 12 месяцев", amount_rub: 1499, amount_stars: 1499, days: 365, device_limit: 5, node_policy: "paid_pool", badge: "Выгода", is_active: true, sort_order: 3 },
          ] as PlanCatalogRow[]);
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, [selectedCode]);

  const activePlan = useMemo(() => {
    return plans.find((plan) => plan.code === selectedCode) || plans[0] || null;
  }, [plans, selectedCode]);

  const activeColumn = planColumn(activePlan?.code || "");

  const botFallback = useMemo(() => {
    const bot = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/net4ebur_bot";
    return bot;
  }, []);

  const onCreateOrder = async (): Promise<void> => {
    if (!activePlan || !user) return;
    setBusy(true);
    setStatusText("");
    setBreakdown(null);
    try {
      const order = await createRubCheckoutOrder({
        plan_code: activePlan.code,
        source: "site",
        tg_id: user.tg_id,
        campaign: queryCampaign || undefined,
        promo_code: queryPromo || undefined,
        currency: "RUB",
      });
      const base = Number(order.base_amount_rub ?? order.amount_rub ?? activePlan.amount_rub);
      const final = Number(order.amount_rub ?? activePlan.amount_rub);
      const discountPct = Number(order.discount_pct ?? 0);
      setBreakdown({ base, final, discountPct });
      setStatusText("Заказ создан. Переводим на страницу оплаты...");
      if (order.payment_url) {
        window.location.href = order.payment_url;
        return;
      }
      setStatusText("Платежная ссылка не получена. Используйте fallback в бота.");
    } catch (error) {
      setStatusText(String((error as { message?: string })?.message || error || "Ошибка создания заказа"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-violet-600 dark:text-violet-300">[safe checkout flow]</p>
        <h1 className="mt-2 font-display text-4xl font-bold">PORTAL RUB Checkout</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Заказ создаётся на backend, затем открывается страница провайдера. Видна разбивка база/скидка/итог и контекст кампании.
        </p>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.25fr,0.9fr]">
        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Тариф</h2>
          <div className="mt-4 space-y-2">
            {plans.map((plan) => (
              <button
                key={plan.code}
                type="button"
                onClick={() => setSelectedCode(plan.code)}
                className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                  selectedCode === plan.code
                    ? "border-violet-500 bg-violet-500/10"
                    : "border-white/45 bg-white/55 hover:border-violet-300 dark:border-white/10 dark:bg-white/5"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="font-semibold">{plan.label}</span>
                  <span className="font-mono text-sm">{Number(plan.amount_rub || 0)} ₽</span>
                </div>
                <p className="mt-1 text-xs text-slate-500">{plan.days} дней • до {plan.device_limit} устройств</p>
              </button>
            ))}
          </div>

          <div className="mt-4 rounded-xl border border-white/45 bg-white/65 p-4 text-sm dark:border-white/10 dark:bg-white/5">
            <p>Контекст:</p>
            <p className="mt-1 text-xs text-slate-500">
              campaign={queryCampaign || "—"} • promo={queryPromo || "—"} • tg_id={queryTgId || String(user?.tg_id || "—")}
            </p>
            {breakdown ? (
              <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-300">
                База: {breakdown.base.toFixed(0)} ₽ • Скидка: {breakdown.discountPct}% • Итог: {breakdown.final.toFixed(0)} ₽
              </p>
            ) : null}
          </div>

          <div className="mt-4 overflow-x-auto rounded-xl border border-white/45 dark:border-white/10">
            <table className="w-full min-w-[640px] text-left text-xs">
              <thead className="bg-white/55 dark:bg-white/5">
                <tr>
                  <th className="px-3 py-2">Параметр</th>
                  <th className={`px-3 py-2 ${activeColumn === "start" ? "text-violet-600 dark:text-violet-300" : ""}`}>Start</th>
                  <th className={`px-3 py-2 ${activeColumn === "pro" ? "text-violet-600 dark:text-violet-300" : ""}`}>Pro</th>
                  <th className={`px-3 py-2 ${activeColumn === "ultra" ? "text-violet-600 dark:text-violet-300" : ""}`}>Ultra</th>
                </tr>
              </thead>
              <tbody>
                {COMPARISON_ROWS.map((row) => (
                  <tr key={row.metric} className="border-t border-white/40 dark:border-white/10">
                    <td className="px-3 py-2 font-semibold">{row.metric}</td>
                    <td className={`px-3 py-2 ${activeColumn === "start" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.start}</td>
                    <td className={`px-3 py-2 ${activeColumn === "pro" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.pro}</td>
                    <td className={`px-3 py-2 ${activeColumn === "ultra" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.ultra}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="mt-3 text-xs text-slate-500">
            Почему часть медиасервисов может идти напрямую: это может снижать задержку в отдельных сценариях. Защищенный
            канал для основного трафика сохраняется по вашей тарифной политике.
          </p>
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Оплата</h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            Основной путь — RUB checkout. Если заказ не создаётся, используйте fallback через бота.
          </p>

          <button
            type="button"
            onClick={() => void onCreateOrder()}
            disabled={!activePlan || busy}
            className="btn-primary mt-5 w-full rounded-xl py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
          >
            {busy ? "Создаём заказ..." : "Открыть оплату"}
          </button>

          <Link
            href={botFallback}
            target="_blank"
            className="outline-btn mt-3 block rounded-xl py-3 text-center text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Перейти в бота (fallback)
          </Link>

          {statusText ? (
            <div className="mt-4 rounded-xl border border-white/45 bg-white/65 px-4 py-3 text-xs text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
              {statusText}
            </div>
          ) : null}
        </article>
      </section>
    </main>
  );
}
