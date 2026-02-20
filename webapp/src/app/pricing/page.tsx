"use client";

import { AnimatePresence, motion } from "framer-motion";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { computePrice, normalizePromo, PLAN_CONFIG } from "@/lib/pricing";

type PromoStatus = { kind: "ok" | "error"; text: string } | null;
type CopyVariant = "a" | "b";

function parseCopyVariant(raw: string | null): CopyVariant {
  return raw === "b" ? "b" : "a";
}

export default function PricingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const from = (searchParams.get("from") || "").trim().toLowerCase();
  const copyVariant = parseCopyVariant(searchParams.get("copy"));
  const fromLK = from === "lk";

  const [annual, setAnnual] = useState(false);
  const [promo, setPromo] = useState("");
  const [promoStatus, setPromoStatus] = useState<PromoStatus>(null);
  const [showFounderNote, setShowFounderNote] = useState(false);
  const holdTimer = useRef<number | null>(null);

  const period = annual ? "annual" : "monthly";
  const backHref = fromLK ? "/subscription" : copyVariant === "b" ? "/?copy=b" : "/";
  const backLabel = fromLK ? "назад в кабинет" : "назад на сайт";

  const cards = useMemo(() => {
    return PLAN_CONFIG.map((plan) => {
      const price = computePrice(plan.key, period, promo);
      return { ...plan, ...price };
    });
  }, [period, promo]);

  useEffect(() => {
    return () => {
      if (holdTimer.current) window.clearTimeout(holdTimer.current);
    };
  }, []);

  const startHold = (): void => {
    holdTimer.current = window.setTimeout(() => setShowFounderNote(true), 2500);
  };

  const clearHold = (): void => {
    if (holdTimer.current) window.clearTimeout(holdTimer.current);
  };

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

  const pickPlan = (planKey: "start" | "pro" | "ultra"): void => {
    const params = new URLSearchParams({
      plan: planKey,
      period,
      from: fromLK ? "lk" : "site",
    });
    if (copyVariant === "b") params.set("copy", "b");
    if (computePrice("pro", period, promo).discountPercent > 0) {
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
        <h1 className="mt-4 font-display text-5xl font-bold">
          {copyVariant === "b" ? "Выберите план и начните без задержек" : "Выберите план и зафиксируйте выгоду"}
        </h1>
        <p className="mt-4 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">
          Актуальная линейка: 99 / 249 / 699 / 1199 / 1399 / 1499 ₽. Стартуйте с удобного периода и меняйте режим,
          когда вам это нужно.
        </p>
        <div className="mt-4 inline-flex rounded-xl border border-emerald-300/40 bg-emerald-50/80 px-4 py-2 text-xs text-emerald-700 dark:border-emerald-500/30 dark:bg-emerald-900/20 dark:text-emerald-300">
          {copyVariant === "b"
            ? "Только сейчас: для новых пользователей персональная скидка до -15% на первый платеж."
            : "Для новых пользователей: персональная скидка до -15% на первый платеж до конца дня."}
        </div>

        <div className="mt-7 inline-flex rounded-xl bg-white/70 p-1 dark:bg-slate-900/70">
          <button
            type="button"
            onClick={() => setAnnual(false)}
            className={`rounded-lg px-5 py-2 text-sm font-semibold transition ${
              !annual ? "bg-white shadow-sm dark:bg-slate-800" : "text-slate-500"
            }`}
          >
            Быстрый старт
          </button>
          <button
            type="button"
            onClick={() => setAnnual(true)}
            className={`rounded-lg px-5 py-2 text-sm font-semibold transition ${
              annual ? "bg-white shadow-sm dark:bg-slate-800" : "text-slate-500"
            }`}
          >
            Максимальная выгода
          </button>
        </div>
      </div>

      <section className="mt-8 grid gap-6 md:grid-cols-3">
        {cards.map((plan) => {
          const highlighted = plan.key === "pro";
          const ultra = plan.key === "ultra";
          return (
            <motion.article
              key={plan.key}
              whileHover={{ y: -6, scale: 1.01 }}
              className={`glass-card p-6 ${highlighted ? "ring-2 ring-violet-400/40" : ""}`}
            >
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <h2 className="font-display text-3xl font-semibold">{plan.name}</h2>
                  <p className="text-sm text-violet-700 dark:text-violet-300">{plan.subtitle}</p>
                </div>
                {highlighted ? <span className="rounded-full bg-violet-600 px-3 py-1 text-[11px] text-white">Рекомендуем</span> : null}
              </div>

              <button
                type="button"
                onMouseDown={ultra ? startHold : undefined}
                onMouseUp={ultra ? clearHold : undefined}
                onMouseLeave={ultra ? clearHold : undefined}
                onTouchStart={ultra ? startHold : undefined}
                onTouchEnd={ultra ? clearHold : undefined}
                className="w-full text-left"
              >
                <p className="font-display text-5xl font-bold">
                  {plan.total} <span className="text-xl font-medium text-slate-500">₽ / {plan.periodLabel}</span>
                </p>
                {plan.discountPercent ? (
                  <p className="mt-1 text-xs text-emerald-600 dark:text-emerald-400">
                    Было {plan.base} ₽, скидка {plan.discountPercent}% (-{plan.discountAmount} ₽)
                  </p>
                ) : null}
              </button>

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

              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`mt-6 w-full rounded-xl py-3 text-sm font-bold uppercase tracking-[0.14em] ${
                  plan.key === "start" ? "outline-btn" : "btn-primary"
                }`}
                type="button"
                onClick={() => pickPlan(plan.key)}
              >
                {copyVariant === "b" ? "Забрать цену" : "Открыть оплату"}
              </motion.button>
            </motion.article>
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
        <AnimatePresence>
          {promoStatus ? (
            <motion.p
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 6 }}
              className={`mt-3 text-xs ${promoStatus.kind === "ok" ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}
            >
              {promoStatus.text}
            </motion.p>
          ) : null}
        </AnimatePresence>
        <p className="mt-3 text-xs text-slate-500">
          Нажимая «Открыть оплату», вы переходите к защищенному checkout и подтверждаете условия PORTAL.
          Оплата в Stars остается как резервный способ внутри Telegram.
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Если не уверены, начните со Start. Если нужен ежедневный режим, оптимально выбрать Pro.
        </p>
      </div>

      <AnimatePresence>
        {showFounderNote ? (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[220] grid place-items-center bg-black/60 p-4"
            onClick={() => setShowFounderNote(false)}
          >
            <motion.div
              initial={{ y: 20, opacity: 0, scale: 0.97 }}
              animate={{ y: 0, opacity: 1, scale: 1 }}
              exit={{ y: 20, opacity: 0, scale: 0.97 }}
              className="glass-card max-w-lg p-7"
              onClick={(event) => event.stopPropagation()}
            >
              <p className="font-mono text-xs uppercase tracking-[0.2em] text-violet-600 dark:text-violet-300">Easter Egg</p>
              <h3 className="mt-2 font-display text-3xl font-bold">Founder Note</h3>
              <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">
                PORTAL делали с простым принципом: минимум лишних шагов, максимум предсказуемости.
                Вы видите итоговую сумму заранее, выбираете удобный период и продолжаете задачи без пауз.
              </p>
              <button type="button" onClick={() => setShowFounderNote(false)} className="btn-primary mt-6 rounded-xl px-5 py-2.5 text-sm font-semibold">
                Закрыть
              </button>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </main>
  );
}
