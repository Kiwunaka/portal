"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { getPortalPublicConfig } from "@/lib/portal";
import { computePlanPrice, normalizePromo, PRICING_PLANS } from "@/lib/pricing";

type PromoStatus = { kind: "ok" | "error"; text: string } | null;

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

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
      setPromoStatus({ kind: "error", text: "Код не найден. Проверьте написание и попробуйте ещё раз." });
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
    const normalized = normalizePromo(promo);
    if (normalized) {
      params.set("promo", normalized);
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
        <h1 className="mt-4 font-display text-5xl font-bold">Выберите план POKROV VPN</h1>
        <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          Сначала проверяете сервис в спокойном режиме, потом выбираете тариф без спешки. Если вы ещё не запускали тест, начните с Telegram-бота и возьмите 5 дней, чтобы всё посмотреть своими глазами.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/subscription/"
            className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Открыть кабинет
          </Link>
          <a
            href={config.botUrl}
            target="_blank"
            rel="noreferrer"
            className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
          >
            Запустить тест в Telegram
          </a>
        </div>
      </div>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <article className="glass-card p-6">
          <p className="text-xs uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-300">trial-first</p>
          <h2 className="mt-2 font-display text-3xl font-semibold">5 дней, чтобы спокойно всё проверить</h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            Бесплатный период дан вам для комфорта: убедитесь в высокой скорости сервиса прямо сейчас!
          </p>
        </article>
        <article className="glass-card p-6">
          <p className="text-xs uppercase tracking-[0.16em] text-slate-500">что дальше</p>
          <h2 className="mt-2 font-display text-3xl font-semibold">Платный доступ без лишней суеты</h2>
          <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
            Когда тест уже показал себя нормально, выбирайте комфортный срок и пользуйтесь интернетом без повторной настройки и лишней возни.
          </p>
        </article>
      </section>

      <section className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((plan) => {
          const highlighted = plan.code === "6_months";
          return (
            <article key={plan.code} className={`glass-card p-6 ${highlighted ? "ring-2 ring-emerald-500/30" : ""}`}>
              <div className="mb-4 flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.16em] text-slate-500">{plan.badge || "План"}</p>
                  <h2 className="mt-2 font-display text-3xl font-semibold">{plan.label}</h2>
                </div>
                {highlighted ? (
                  <span className="rounded-full bg-gradient-to-r from-emerald-700 to-amber-500 px-3 py-1 text-[11px] text-white">Рекомендуем</span>
                ) : null}
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
                  <span className="material-symbols-rounded text-base text-emerald-700 dark:text-amber-200">verified</span>
                  {plan.days} дней доступа
                </li>
                <li className="flex items-center gap-2">
                  <span className="material-symbols-rounded text-base text-emerald-700 dark:text-amber-200">devices</span>
                  До {plan.deviceLimit} устройств
                </li>
                <li className="flex items-center gap-2">
                  <span className="material-symbols-rounded text-base text-emerald-700 dark:text-amber-200">info</span>
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
                {plan.code === "start_99" ? "Открыть приветственный план" : "Перейти к продлению"}
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
            placeholder="Например: POKROV10"
            className="brand-input px-4 py-3 text-sm"
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
          <p
            className={`mt-3 text-xs ${
              promoStatus.kind === "ok" ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
            }`}
          >
            {promoStatus.text}
          </p>
        ) : null}
      </div>
    </main>
  );
}
