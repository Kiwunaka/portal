"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";

import { getPortalPublicConfig } from "@/lib/portal";
import { computePlanPrice, normalizePromo, PRICING_PLANS } from "@/lib/pricing";

type PromoStatus = { kind: "ok" | "error"; text: string } | null;

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

const VALUE_POINTS = [
  {
    icon: "verified_user",
    title: "Сначала пробуете сервис",
    text: "5 дней премиум-доступа дают время спокойно проверить скорость, маршруты и повседневные сценарии.",
  },
  {
    icon: "workspace_premium",
    title: "Платный доступ без суеты",
    text: "Когда тест уже убедил, выбираете срок и продолжаете пользоваться тем же кабинетом без повторной настройки.",
  },
  {
    icon: "loyalty",
    title: "Бонусы остаются понятными",
    text: "Промокод сразу пересчитывает итог, а за Telegram-канал можно получить еще +10 дней после привязки.",
  },
] as const;

const PLAN_PROMISES = [
  { label: "Премиум-тест", value: "5 дней" },
  { label: "Платный доступ", value: "до 5 устройств" },
  { label: "Telegram-бонус", value: "+10 дней" },
] as const;

function formatMonthlyApprox(total: number, days: number): string {
  const value = Math.round(total / Math.max(days / 30, 1));
  return `≈ ${value} ₽ / 30 дней`;
}

function getPlanButtonLabel(planCode: string): string {
  if (planCode === "start_99") return "Открыть приветственный план";
  return "Продолжить с этим планом";
}

function getPlanTone(planCode: string) {
  if (planCode === "6_months") {
    return {
      badge: "разумный баланс",
      ring: "border-emerald-900/20 bg-[linear-gradient(180deg,rgba(255,255,255,0.92),rgba(242,247,244,0.92))] shadow-[0_28px_60px_-40px_rgba(18,48,36,0.5)] dark:border-emerald-200/10 dark:bg-[linear-gradient(180deg,rgba(21,32,27,0.88),rgba(14,22,18,0.92))]",
    };
  }

  if (planCode === "start_99") {
    return {
      badge: "мягкий вход",
      ring: "border-emerald-900/10 dark:border-emerald-200/10",
    };
  }

  return {
    badge: null,
    ring: "border-white/70 dark:border-white/10",
  };
}

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
      PRICING_PLANS.map((plan) => {
        const pricing = computePlanPrice(plan.code, promo);
        return {
          ...plan,
          pricing,
          monthlyApprox: formatMonthlyApprox(pricing.total, plan.days),
        };
      }),
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
      setPromoStatus({ kind: "error", text: "Код не найден. Проверьте написание и попробуйте еще раз." });
      return;
    }
    setPromo(normalized);
    setPromoStatus({ kind: "ok", text: "Промокод применен. Итоговая сумма уже обновилась в карточках и уйдет с вами в checkout." });
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
    <main className="mx-auto max-w-[1240px] px-4 py-10 md:px-8 lg:py-12">
      <section className="glass-card relative overflow-hidden border border-white/70 p-6 dark:border-[#243129]/80 sm:p-8 lg:p-10">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-emerald-700/45 to-transparent dark:via-emerald-300/30" />

        <Link
          href={backHref}
          className="inline-flex items-center gap-2 rounded-full border border-emerald-900/10 bg-white/75 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-600 transition hover:bg-white dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-300"
        >
          <span className="material-symbols-rounded text-base">arrow_back</span>
          {backLabel}
        </Link>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.08fr_0.92fr] lg:items-start">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-900/10 bg-emerald-900/5 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-900/70 dark:border-emerald-100/10 dark:bg-emerald-100/5 dark:text-emerald-100/70">
              pricing without pressure
            </div>

            <div className="space-y-4">
              <h1 className="font-display text-4xl font-semibold leading-[0.96] text-slate-900 dark:text-slate-50 sm:text-5xl lg:text-[3.5rem]">
                Планы POKROV без витрины и суеты
              </h1>
              <p className="max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300 sm:text-[15px]">
                Сначала проверяете сервис в спокойном режиме, потом выбираете срок, который удобно живет вместе с вашим ритмом. Продление продолжается в том же кабинете, без повторной настройки и лишней беготни.
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              {PLAN_PROMISES.map((item) => (
                <article
                  key={item.label}
                  className="rounded-[24px] border border-white/70 bg-white/68 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]"
                >
                  <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{item.label}</p>
                  <p className="mt-2 font-display text-[1.7rem] font-semibold leading-none text-slate-900 dark:text-slate-50">
                    {item.value}
                  </p>
                </article>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              <Link
                href="/subscription/"
                className="outline-btn rounded-2xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em] text-emerald-950 dark:text-emerald-100"
              >
                Открыть кабинет
              </Link>
              <a
                href={config.botUrl}
                target="_blank"
                rel="noreferrer"
                className="btn-primary rounded-2xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
              >
                Запустить 5 дней бесплатно
              </a>
            </div>
          </div>

          <div className="rounded-[30px] border border-white/70 bg-white/80 p-5 shadow-[0_30px_60px_-42px_rgba(18,48,36,0.42)] dark:border-white/10 dark:bg-white/[0.04] sm:p-6">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
              Выбор без сюрпризов
            </p>
            <div className="mt-4 grid gap-3">
              {VALUE_POINTS.map((item) => (
                <div
                  key={item.title}
                  className="flex items-start gap-3 rounded-[24px] border border-emerald-900/8 bg-[#f8f5ef]/88 px-4 py-4 dark:border-emerald-200/10 dark:bg-[#0f1714]"
                >
                  <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-900/8 text-emerald-800 dark:bg-emerald-200/10 dark:text-emerald-200">
                    <span className="material-symbols-rounded text-[22px]">{item.icon}</span>
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">{item.title}</p>
                    <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mt-8 grid gap-4 md:grid-cols-3">
        {VALUE_POINTS.map((item) => (
          <article
            key={item.title}
            className="glass-card border border-white/70 p-5 dark:border-[#243129]/80"
          >
            <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-900/8 text-emerald-800 dark:bg-emerald-200/10 dark:text-emerald-200">
              <span className="material-symbols-rounded text-[22px]">{item.icon}</span>
            </span>
            <h2 className="mt-4 font-display text-[1.9rem] font-semibold leading-[0.96] text-slate-900 dark:text-slate-50">
              {item.title}
            </h2>
            <p className="mt-3 text-sm leading-7 text-slate-600 dark:text-slate-300">{item.text}</p>
          </article>
        ))}
      </section>

      <section className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {cards.map((plan) => {
          const highlighted = plan.code === "6_months";
          const tone = getPlanTone(plan.code);

          return (
            <article
              key={plan.code}
              className={`glass-card flex h-full flex-col border p-6 ${tone.ring}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                    {plan.badge || "план"}
                  </p>
                  <h2 className="mt-2 font-display text-[2rem] font-semibold leading-[0.98] text-slate-900 dark:text-slate-50">
                    {plan.label}
                  </h2>
                </div>
                {tone.badge ? (
                  <span className="rounded-full bg-emerald-900 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-white dark:bg-emerald-700">
                    {tone.badge}
                  </span>
                ) : null}
              </div>

              <div className="mt-5">
                <p className="font-display text-[3.4rem] font-semibold leading-none text-slate-900 dark:text-slate-50">
                  {plan.pricing.total}
                  <span className="ml-2 text-xl font-medium text-slate-500 dark:text-slate-400">₽</span>
                </p>
                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{plan.monthlyApprox}</p>
                {plan.pricing.discountPercent ? (
                  <p className="mt-2 text-sm text-emerald-700 dark:text-emerald-300">
                    Было {plan.pricing.base} ₽, скидка {plan.pricing.discountPercent}% (-{plan.pricing.discountAmount} ₽)
                  </p>
                ) : null}
              </div>

              <div className="mt-5 rounded-[24px] border border-emerald-900/8 bg-white/72 p-4 dark:border-emerald-200/10 dark:bg-white/[0.03]">
                <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                  Почему этот срок
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-700 dark:text-slate-200">{plan.note}</p>
              </div>

              <ul className="mt-5 space-y-3 text-sm text-slate-600 dark:text-slate-300">
                <li className="flex items-start gap-3">
                  <span className="material-symbols-rounded text-[20px] text-emerald-700 dark:text-emerald-300">calendar_month</span>
                  <span>{plan.days} дней доступа без повторной настройки.</span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="material-symbols-rounded text-[20px] text-emerald-700 dark:text-emerald-300">devices</span>
                  <span>
                    {plan.code === "start_99"
                      ? `До ${plan.deviceLimit} устройства на аккуратный старт.`
                      : `До ${plan.deviceLimit} устройств на платном доступе.`}
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <span className="material-symbols-rounded text-[20px] text-amber-600 dark:text-amber-300">payments</span>
                  <span>
                    {highlighted
                      ? "Хороший баланс общей суммы и спокойного длинного горизонта."
                      : plan.code === "start_99"
                        ? "Мягкий вход, если хотите сначала пожить с сервисом чуть дольше теста."
                        : "Выбор для тех, кто хочет реже возвращаться к продлению."}
                  </span>
                </li>
              </ul>

              <div className="mt-6 flex flex-1 items-end">
                <button
                  className={`w-full rounded-2xl py-3 text-sm font-semibold uppercase tracking-[0.12em] ${
                    plan.code === "start_99"
                      ? "outline-btn text-emerald-950 dark:text-emerald-100"
                      : "btn-primary"
                  }`}
                  type="button"
                  onClick={() => pickPlan(plan.code)}
                >
                  {getPlanButtonLabel(plan.code)}
                </button>
              </div>
            </article>
          );
        })}
      </section>

      <section className="mt-8 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="glass-card border border-white/70 p-5 dark:border-[#243129]/80 sm:p-6">
          <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            Промокод
          </label>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-slate-600 dark:text-slate-300">
            Если у вас есть код, примените его здесь. Скидка сразу отразится в карточках выше и автоматически сохранится в checkout.
          </p>

          <div className="mt-4 flex flex-col gap-3 md:flex-row">
            <input
              value={promo}
              onChange={(event) => {
                setPromo(event.target.value);
                if (promoStatus) setPromoStatus(null);
              }}
              placeholder="Например: POKROV10"
              className="w-full rounded-2xl border border-emerald-900/12 bg-white/85 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-emerald-700 focus:ring-2 focus:ring-emerald-700/10 dark:border-emerald-200/10 dark:bg-[#111916] dark:text-slate-50"
            />
            <button
              type="button"
              onClick={applyPromo}
              className="btn-primary rounded-2xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]"
            >
              Применить
            </button>
          </div>

          {promoStatus ? (
            <p
              className={`mt-3 text-sm ${
                promoStatus.kind === "ok" ? "text-emerald-700 dark:text-emerald-300" : "text-rose-600 dark:text-rose-300"
              }`}
            >
              {promoStatus.text}
            </p>
          ) : null}
        </div>

        <div className="glass-card border border-white/70 p-5 dark:border-[#243129]/80 sm:p-6">
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            Перед оплатой
          </p>
          <div className="mt-4 space-y-3">
            <div className="rounded-[22px] border border-white/70 bg-white/68 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">Checkout продолжится из кабинета</p>
              <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                После выбора плана мы переносим вас в ваш личный маршрут оплаты, а не в абстрактную витрину.
              </p>
            </div>
            <div className="rounded-[22px] border border-white/70 bg-white/68 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]">
              <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">Настройка не сбрасывается</p>
              <p className="mt-1 text-sm leading-6 text-slate-600 dark:text-slate-300">
                Скорость продолжается через тот же кабинет и тот же надежный маршрут оптимизации.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
