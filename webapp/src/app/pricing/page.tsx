"use client";

import { getPlan, normalizePromo, PLAN_CONFIG, computePrice, parseBillingPeriod } from "@/lib/pricing";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

type PromoStatus = { kind: "ok" | "error"; text: string } | null;

export default function PricingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = (searchParams.get("from") || "").trim().toLowerCase();
  const fromLK = from === "lk";

  const initialPeriod = parseBillingPeriod(searchParams.get("period"));
  const [period, setPeriod] = useState<"monthly" | "annual">(initialPeriod);
  const [promo, setPromo] = useState((searchParams.get("promo") || "").trim().toUpperCase());
  const [promoStatus, setPromoStatus] = useState<PromoStatus>(null);

  const backHref = fromLK ? "/subscription/" : "/";
  const backLabel = fromLK ? "назад в кабинет" : "назад на сайт";

  const cards = useMemo(() => {
    return PLAN_CONFIG.map((plan) => ({
      ...plan,
      price: computePrice(plan.alias, period, promo)
    }));
  }, [period, promo]);

  const applyPromo = (): void => {
    const normalized = normalizePromo(promo);
    if (!normalized) {
      setPromoStatus({ kind: "error", text: "Введите промокод, чтобы проверить скидку." });
      return;
    }
    const percent = computePrice("pro", period, normalized).discountPercent;
    if (!percent) {
      setPromoStatus({ kind: "error", text: "Код не найден. Проверьте написание и попробуйте снова." });
      return;
    }
    setPromo(normalized);
    setPromoStatus({ kind: "ok", text: `Промокод активирован: -${percent}% на выбранный период.` });
  };

  const pickPlan = (alias: "start" | "pro" | "ultra"): void => {
    const selected = getPlan(alias);
    const result = computePrice(alias, period, promo);
    const params = new URLSearchParams({
      plan: result.planCode,
      alias: selected.alias,
      period,
      from: fromLK ? "lk" : "site"
    });
    if (result.discountPercent > 0) params.set("promo", normalizePromo(promo));
    router.push(`/subscription/checkout/?${params.toString()}`);
  };

  return (
    <main className="mx-auto max-w-6xl px-4 py-14 md:px-8">
      <div className="glass-card relative overflow-hidden p-8 md:p-10">
        <Link href={backHref} className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.16em] text-slate-500">
          <span className="material-symbols-rounded">arrow_back</span>
          {backLabel}
        </Link>
        <h1 className="mt-4 font-display text-5xl font-bold">Выберите план и удобный срок</h1>
        <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          На этой странице только актуальные суммы и реальные коды планов. После выбора вы сразу переходите к оплате
          без промежуточных экранов.
        </p>

        <div className="mt-7 inline-flex rounded-xl bg-white/70 p-1 dark:bg-slate-900/70">
          <button
            type="button"
            onClick={() => setPeriod("monthly")}
            className={`rounded-lg px-5 py-2 text-sm font-semibold transition ${
              period === "monthly" ? "bg-white shadow-sm dark:bg-slate-800" : "text-slate-500"
            }`}
          >
            Короткий срок
          </button>
          <button
            type="button"
            onClick={() => setPeriod("annual")}
            className={`rounded-lg px-5 py-2 text-sm font-semibold transition ${
              period === "annual" ? "bg-white shadow-sm dark:bg-slate-800" : "text-slate-500"
            }`}
          >
            Дольше и спокойнее
          </button>
        </div>
      </div>

      <section className="mt-8 grid gap-6 md:grid-cols-3">
        {cards.map((plan) => {
          const highlighted = plan.alias === "pro";
          return (
            <article key={plan.alias} className={`glass-card p-6 ${highlighted ? "ring-2 ring-violet-400/40" : ""}`}>
              <div className="mb-4 flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-display text-3xl font-semibold">{plan.name}</h2>
                  <p className="text-sm text-violet-700 dark:text-violet-300">{plan.subtitle}</p>
                </div>
                {highlighted ? <span className="rounded-full bg-violet-600 px-3 py-1 text-[11px] text-white">Рекомендуем</span> : null}
              </div>

              <p className="font-display text-5xl font-bold">
                {plan.price.total} <span className="text-xl font-medium text-slate-500">₽ / {plan.price.periodLabel}</span>
              </p>
              {plan.price.discountPercent ? (
                <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                  Было {plan.price.base} ₽, скидка {plan.price.discountPercent}% (-{plan.price.discountAmount} ₽)
                </p>
              ) : null}

              <ul className="mt-5 space-y-2 text-sm text-slate-600 dark:text-slate-300">
                {plan.perks.map((perk) => (
                  <li key={perk} className="flex items-center gap-2">
                    <span className="material-symbols-rounded text-base text-violet-500">verified</span>
                    {perk}
                  </li>
                ))}
              </ul>

              <p className="mt-5 text-xs text-slate-500">{plan.promise}</p>
              <p className="mt-2 text-xs text-slate-500">{plan.objection}</p>

              <button
                className={`mt-6 w-full rounded-xl py-3 text-sm font-bold uppercase tracking-[0.14em] ${
                  plan.alias === "start" ? "outline-btn" : "btn-primary"
                }`}
                type="button"
                onClick={() => pickPlan(plan.alias)}
              >
                Открыть оплату
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
