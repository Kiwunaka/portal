"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import AppRouteLink from "@/components/app-route-link";
import { getAccessState, resolvePlanLabel } from "@/lib/access-policy";
import { fetchPublicCatalog } from "@/lib/api";
import {
  getAccessMatrix,
  getPortalPublicConfig,
  getPricingPreviewDiscountPercent,
  getTariffPlans,
  normalizePlanCode,
} from "@/lib/portal";
import { usePortalSession } from "@/lib/session";

type DisplayPlan = {
  code: string;
  label: string;
  badge?: string;
  days: number;
  amountRub: number;
  deviceLimit: number;
  note: string;
};

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const ACCESS_MATRIX = getAccessMatrix();
const SHARED_PLANS: DisplayPlan[] = getTariffPlans()
  .slice()
  .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
  .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
  .map((plan) => ({
    code: plan.code,
    label: plan.label,
    badge: plan.badge || undefined,
    days: Number(plan.duration_days || 0),
    amountRub: Number(plan.amount_rub || 0),
    deviceLimit: Number(plan.device_limit || 1),
    note: plan.cabinet_note || plan.marketing_note || plan.label,
  }));

function normalizePromo(raw: string): string {
  return String(raw || "").trim().toUpperCase();
}

function buildHostedCheckoutHref(planCode: string, promoCode?: string): string {
  const url = new URL(config.checkoutUrl);
  url.searchParams.set("plan", planCode);
  url.searchParams.set("from", "webapp");
  if (promoCode) {
    url.searchParams.set("promo", promoCode);
  }
  return url.toString();
}

function formatDuration(days: number): string {
  if (days >= 365) return `${Math.round(days / 30)} мес.`;
  if (days > 90) return `${Math.round(days / 30)} мес.`;
  return `${days} дней`;
}

function accessHint(accessState: string): string {
  if (accessState.includes("trial")) return "Сейчас действуют пробные 5 дней.";
  if (accessState.includes("paid")) return "Текущий доступ активен, можно продлить заранее.";
  if (accessState.includes("free")) return "Можно перейти на полный режим или остаться в базовом.";
  return "После оплаты или применения ключа статус обновится в этом же профиле.";
}

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<DisplayPlan[]>(SHARED_PLANS);
  const [promoInput, setPromoInput] = useState(() => normalizePromo(searchParams.get("promo") || ""));
  const [catalogError, setCatalogError] = useState("");
  const [selectedCode, setSelectedCode] = useState(() => normalizePlanCode(searchParams.get("plan"), "1_month"));

  useEffect(() => {
    let cancelled = false;
    const nextSelectedCode = normalizePlanCode(searchParams.get("plan"), "1_month");
    const nextPromoInput = normalizePromo(searchParams.get("promo") || "");

    queueMicrotask(() => {
      if (cancelled) return;
      setSelectedCode(nextSelectedCode);
      setPromoInput(nextPromoInput);
    });

    return () => {
      cancelled = true;
    };
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const payload = await fetchPublicCatalog();
        const nextPlans = (payload.plans || [])
          .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
          .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
          .map((plan) => ({
            code: plan.code,
            label: plan.label,
            badge: plan.badge || undefined,
            days: Number(plan.days || 0),
            amountRub: Number(plan.amount_rub || 0),
            deviceLimit: Number(plan.device_limit || 1),
            note: plan.label,
          }));

        if (!cancelled) {
          setPlans(nextPlans.length ? nextPlans : SHARED_PLANS);
          setCatalogError("");
        }
      } catch {
        if (!cancelled) {
          setPlans(SHARED_PLANS);
          setCatalogError("Не удалось обновить каталог автоматически.");
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  const activePlan = useMemo(
    () => plans.find((plan) => plan.code === selectedCode) || plans[0] || SHARED_PLANS[0],
    [plans, selectedCode],
  );
  const promoCode = normalizePromo(promoInput);
  const discountPercent = getPricingPreviewDiscountPercent(promoCode);
  const discountAmount = Math.round((Number(activePlan?.amountRub || 0) * discountPercent) / 100);
  const totalAmount = Math.max(0, Number(activePlan?.amountRub || 0) - discountAmount);
  const checkoutHref = buildHostedCheckoutHref(activePlan?.code || "1_month", discountPercent > 0 ? promoCode : undefined);
  const accessState = getAccessState(dash, user) || "free_monthly";
  const baseLimitGb = ACCESS_MATRIX.free_tier.traffic_limit_gb;
  const baseCycleDays = ACCESS_MATRIX.free_tier.cycle_days;

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-emerald-700 dark:text-emerald-300">Оплата и ключ доступа</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Продлите доступ или примените готовый ключ</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">
          Кабинет помогает выбрать срок и передает оплату на защищенную страницу. После оплаты вы получите ключ доступа, который активирует выбранный срок в текущем профиле.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <a href={checkoutHref} className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Перейти к оплате
          </a>
          <AppRouteLink href="/redeem/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            У меня уже есть ключ
          </AppRouteLink>
          <AppRouteLink href="/subscription/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Назад к тарифам
          </AppRouteLink>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.15fr,0.85fr]">
        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Выберите срок</h2>
          <div className="mt-4 space-y-3">
            {plans.map((plan) => {
              const selected = plan.code === activePlan?.code;
              return (
                <button
                  key={plan.code}
                  type="button"
                  onClick={() => setSelectedCode(plan.code)}
                  className={`w-full rounded-2xl border px-4 py-4 text-left transition ${
                    selected
                      ? "border-emerald-500 bg-emerald-50"
                      : "border-slate-200 bg-white hover:border-emerald-200 dark:border-white/10 dark:bg-white/5"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.14em] text-slate-500">{plan.badge || "план"}</p>
                      <h3 className="mt-1 text-lg font-semibold">{plan.label}</h3>
                    </div>
                    <p className="text-lg font-semibold">{plan.amountRub} ₽</p>
                  </div>
                  <p className="mt-2 text-xs text-slate-500">
                    {formatDuration(plan.days)} · до {plan.deviceLimit} устройств
                  </p>
                  <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{plan.note}</p>
                </button>
              );
            })}
          </div>
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Итог</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
            <p>
              Текущий режим: <strong>{resolvePlanLabel(dash, user)}</strong>
            </p>
            <p>{accessHint(accessState)}</p>
            <p>
              Выбранный срок: <strong>{activePlan?.label}</strong>
            </p>
            <p>Период: {activePlan?.days} дней</p>
            <p>Устройств: до {activePlan?.deviceLimit}</p>
            <p>
              Базовый режим остается доступен: {baseLimitGb} ГБ на {baseCycleDays} дней.
            </p>
          </div>

          <label className="mt-5 block text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Промокод
          </label>
          <input
            value={promoInput}
            onChange={(event) => setPromoInput(event.target.value)}
            placeholder="Например: POKROV10"
            className="mt-2 w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/5"
          />

          <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-white/5">
            <p>
              Базовая цена: <strong>{activePlan?.amountRub} ₽</strong>
            </p>
            <p>
              Скидка: <strong>{discountPercent}%</strong>
            </p>
            <p className="mt-2 text-base font-semibold text-slate-900 dark:text-white">К оплате: {totalAmount} ₽</p>
          </div>

          <div className="mt-5 grid gap-3">
            <a href={checkoutHref} className="btn-primary block rounded-xl py-3 text-center text-sm font-semibold uppercase tracking-[0.12em]">
              Перейти к оплате
            </a>
            <AppRouteLink href="/redeem/" className="outline-btn block rounded-xl py-3 text-center text-sm font-semibold uppercase tracking-[0.12em]">
              Применить ключ доступа
            </AppRouteLink>
          </div>

          <div className="mt-5 space-y-2 text-xs leading-6 text-slate-500 dark:text-slate-400">
            <p>Пробные 5 дней запускаются в приложении POKROV после первого корректного входа на устройстве.</p>
            <p>Telegram остается дополнительным способом для поддержки, восстановления и бонуса +10 дней.</p>
            <p>Если оплата прошла, но статус не обновился, откройте поддержку и продолжите один кейс.</p>
          </div>

          {catalogError ? (
            <p className="mt-4 text-xs text-amber-600 dark:text-amber-300">
              {catalogError} Показываем последние доступные варианты.
            </p>
          ) : null}
        </article>
      </section>
    </main>
  );
}
