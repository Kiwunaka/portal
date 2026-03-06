"use client";

import { createRubCheckoutOrder, fetchPublicPlans, type PlanCatalogRow } from "@/lib/api";
import { getCopyText, getPortalPublicConfig, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

function normalizePlans(rows: PlanCatalogRow[]): PlanCatalogRow[] {
  return rows
    .filter((row) => Boolean(row.is_active) && Number(row.amount_rub || 0) > 0)
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
}

function fallbackPlans(): PlanCatalogRow[] {
  return [
    { code: "start_99", label: "Start 30 дней", amount_rub: 99, amount_stars: 0, days: 30, device_limit: 1, node_policy: "nl_only", badge: "Вход", is_active: true, sort_order: 1 },
    { code: "1_month", label: "Pro 1 месяц", amount_rub: 249, amount_stars: 249, days: 30, device_limit: 5, node_policy: "paid_pool", badge: "Популярный", is_active: true, sort_order: 2 },
    { code: "12_months", label: "Ultra 12 месяцев", amount_rub: 1499, amount_stars: 1499, days: 365, device_limit: 5, node_policy: "paid_pool", badge: "Выгода", is_active: true, sort_order: 3 }
  ];
}

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const { user } = usePortalSession();
  const [plans, setPlans] = useState<PlanCatalogRow[]>([]);
  const [selectedCode, setSelectedCode] = useState("1_month");
  const [busy, setBusy] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [breakdown, setBreakdown] = useState<{ base: number; discountPct: number; final: number } | null>(null);

  const queryCampaign = (searchParams.get("campaign") || "").trim();
  const queryPromo = (searchParams.get("promo") || "").trim().toUpperCase();

  useEffect(() => {
    const planCode = normalizePlanCode(searchParams.get("plan"), "1_month");
    setSelectedCode(planCode);
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const payload = await fetchPublicPlans();
        const rows = normalizePlans(payload.plans || []);
        if (!cancelled) {
          const nextPlans = rows.length ? rows : fallbackPlans();
          setPlans(nextPlans);
          if (!nextPlans.some((row) => row.code === selectedCode)) {
            setSelectedCode(nextPlans[0].code);
          }
        }
      } catch {
        if (!cancelled) {
          const nextPlans = fallbackPlans();
          setPlans(nextPlans);
          if (!nextPlans.some((row) => row.code === selectedCode)) {
            setSelectedCode(nextPlans[0].code);
          }
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
        currency: "RUB"
      });
      const base = Number(order.base_amount_rub ?? order.amount_rub ?? activePlan.amount_rub);
      const final = Number(order.amount_rub ?? activePlan.amount_rub);
      const discountPct = Number(order.discount_pct ?? 0);
      setBreakdown({ base, final, discountPct });
      if (order.payment_url) {
        setStatusText("Ссылка готова. Переводим на страницу оплаты...");
        window.location.href = order.payment_url;
        return;
      }
      setStatusText("Не удалось получить ссылку на оплату. Попробуйте ещё раз или откройте поддержку.");
    } catch (error) {
      setStatusText(String((error as { message?: string })?.message || error || "Ошибка создания заказа"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-violet-600 dark:text-violet-300">checkout</p>
        <h1 className="mt-2 font-display text-4xl font-bold">{getCopyText("webapp.checkout.title", "Оплата и продление")}</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          {getCopyText(
            "webapp.checkout.subtitle",
            "Сумма и скидка видны до перехода на страницу оплаты. Если вход не привязан, можно быстро продолжить через Telegram.",
          )}
        </p>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.25fr,0.9fr]">
        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Выберите план</h2>
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
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Итог</h2>
          {activePlan ? (
            <div className="mt-3 space-y-2 text-sm text-slate-600 dark:text-slate-300">
              <p>План: <span className="font-semibold text-slate-900 dark:text-white">{activePlan.label}</span></p>
              <p>Срок: {activePlan.days} дней</p>
              <p>Лимит устройств: до {activePlan.device_limit}</p>
              {queryPromo ? <p>Промокод: {queryPromo}</p> : null}
              {breakdown ? (
                <div className="rounded-xl border border-white/45 bg-white/65 p-4 text-xs dark:border-white/10 dark:bg-white/5">
                  <p>База: {breakdown.base.toFixed(0)} ₽</p>
                  <p>Скидка: {breakdown.discountPct}%</p>
                  <p className="font-semibold text-slate-900 dark:text-white">Итог: {breakdown.final.toFixed(0)} ₽</p>
                </div>
              ) : null}
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-500">Планы загружаются...</p>
          )}

          <button
            type="button"
            onClick={() => void onCreateOrder()}
            disabled={!activePlan || busy || !user}
            className="btn-primary mt-5 w-full rounded-xl py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
          >
            {busy ? "Создаём заказ..." : "Открыть оплату"}
          </button>

          <div className="mt-3 grid gap-3">
            <Link
              href={config.botUrl}
              target="_blank"
              className="outline-btn block rounded-xl py-3 text-center text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Открыть Telegram
            </Link>
            <Link
              href={config.supportTelegramUrl}
              target="_blank"
              className="outline-btn block rounded-xl py-3 text-center text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Поддержка
            </Link>
          </div>

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
