"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { computePlanPrice, normalizePromo, PRICING_PLANS } from "@/lib/pricing";

type PromoStatus = { kind: "ok" | "error"; text: string } | null;

export default function PricingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = (searchParams.get("from") || "").trim().toLowerCase();
  const fromLK = from === "lk";
  const [promo, setPromo] = useState((searchParams.get("promo") || "").trim().toUpperCase());
  const [promoStatus, setPromoStatus] = useState<PromoStatus>(null);

  const backHref = fromLK ? "/subscription/" : "/";
  const backLabel = fromLK ? "Назад в кабинет" : "Назад ко входу";

  const cards = useMemo(
    () =>
      PRICING_PLANS.map((plan) => ({
        ...plan,
        pricing: computePlanPrice(plan.code, promo),
      })),
    [promo],
  );

  const applyPromo = (): void => {
    const normalized = normalizePromo(promo);
    if (!normalized) {
      setPromoStatus({ kind: "error", text: "Введите промокод, чтобы проверить скидку." });
      return;
    }
    const matched = cards.some((plan) => plan.pricing.discountPercent > 0);
    if (!matched) {
      setPromoStatus({ kind: "error", text: "Код не найден. Проверьте написание и попробуйте снова." });
      return;
    }
    setPromo(normalized);
    setPromoStatus({ kind: "ok", text: "Промокод применён. Итоговая сумма уже показана на карточках." });
  };

  const pickPlan = (planCode: string): void => {
    const params = new URLSearchParams({
      plan: planCode,
      from: fromLK ? "lk" : "site",
    });
    if (normalizePromo(promo)) {
      params.set("promo", normalizePromo(promo));
    }
    router.push(`/subscription/checkout/?${params.toString()}`);
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-14 md:px-8">
      <div className="glass-card relative overflow-hidden p-8 md:p-10">
        <Link href={backHref} className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-500">
          <span className="material-symbols-rounded">arrow_back</span>
          {backLabel}
        </Link>
        <h1 className="mt-4 font-display text-5xl font-bold">Выберите тариф и срок, который вам удобен</h1>
        <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          Здесь показаны реальные тарифы без внутренних названий. Приветственный тариф за 99 ₽ доступен один раз,
          дальше остаются обычные сроки на 1, 3, 6, 9 или 12 месяцев.
        </p>
      </div>

      <section className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((plan) => {
          const highlighted = plan.code === "6_months";
          return (
            <article key={plan.code} className={`glass-card p-6 ${highlighted ? "ring-2 ring-violet-400/40" : ""}`}>
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{plan.badge || "Тариф"}</p>
                  <h2 className="mt-2 font-display text-3xl font-semibold">{plan.label}</h2>
                </div>
                {highlighted ? <span className="rounded-full bg-violet-600 px-3 py-1 text-[11px] text-white">Рекомендуем</span> : null}
              </div>

              <p className="font-display text-5xl font-bold">
                {plan.pricing.total} <span className="text-xl font-medium text-slate-500">₽</span>
              </p>
              {plan.pricing.discountPercent ? (
                <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                  Было {plan.pricing.base} ₽, скидка {plan.pricing.discountPercent}% (-{plan.pricing.discountAmount} ₽)
                </p>
              ) : null}

              <ul className="mt-5 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                <li className="flex items-center gap-2">
                  <span className="material-symbols-rounded text-base text-violet-500">verified</span>
                  {plan.days} дней доступа
                </li>
                <li className="flex items-center gap-2">
                  <span className="material-symbols-rounded text-base text-violet-500">devices</span>
                  До {plan.deviceLimit} устройств
                </li>
                <li className="flex items-center gap-2">
                  <span className="material-symbols-rounded text-base text-violet-500">info</span>
                  {plan.note}
                </li>
              </ul>

              <button
                className={`mt-6 w-full rounded-xl py-3 text-sm font-bold uppercase tracking-[0.14em] ${
                  plan.code === "start_99" ? "outline-btn" : "btn-primary"
                }`}
                type="button"
                onClick={() => pickPlan(plan.code)}
              >
                Выбрать тариф
              </button>
            </article>
          );
        })}
      </section>

      <div className="glass-card mt-7 p-5">
        <label className="mb-2 block text-xs uppercase tracking-[0.16em] text-slate-500">Промокод</label>
        <div className="flex flex-col gap-3 md:flex-row">
          <input
            value={promo}
            onChange={(event) => {
              setPromo(event.target.value);
              if (promoStatus) setPromoStatus(null);
            }}
            placeholder="Например: PORTAL10"
            className="w-full rounded-xl border border-violet-200/60 bg-white/80 px-4 py-3 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <button
            type="button"
            onClick={applyPromo}
            className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Применить
          </button>
        </div>
        {promoStatus ? (
          <p className={`mt-3 text-xs ${promoStatus.kind === "ok" ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
            {promoStatus.text}
          </p>
        ) : null}
      </div>
    </main>
  );
}
