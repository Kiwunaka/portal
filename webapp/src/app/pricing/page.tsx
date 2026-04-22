"use client";

import AppRouteLink from "@/components/app-route-link";
import { fetchPublicCatalog } from "@/lib/api";
import { getAccessMatrix, getTariffPlans } from "@/lib/portal";
import { useEffect, useState } from "react";

type DisplayPlan = {
  code: string;
  label: string;
  badge?: string;
  days: number;
  amountRub: number;
  deviceLimit: number;
  note: string;
};

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

function formatDays(days: number): string {
  if (days >= 365) return `${Math.round(days / 30)} мес.`;
  if (days > 90) return `${Math.round(days / 30)} мес.`;
  return `${days} дней`;
}

export default function PricingPage() {
  const [plans, setPlans] = useState<DisplayPlan[]>(SHARED_PLANS);
  const [error, setError] = useState("");

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
          setError("");
        }
      } catch (nextError) {
        if (!cancelled) {
          setPlans(SHARED_PLANS);
          setError(String((nextError as { message?: string })?.message || nextError || ""));
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">continuation only</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Продление и redeem без публичной витрины</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">
          Этот маршрут больше не играет роль публичного pricing-слоя. Маркетинг владеет acquisition и
          ценой, а кабинет ведёт только в renewal continuation, redeem ключа и support/recovery.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <AppRouteLink href="/subscription/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Открыть кабинет доступа
          </AppRouteLink>
          <AppRouteLink href="/subscription/checkout/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Renewal continuation
          </AppRouteLink>
          <AppRouteLink href="/redeem/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Redeem key
          </AppRouteLink>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.05fr,0.95fr]">
        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-emerald-500">что это теперь</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Совместимый continuation alias</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            Маршрут сохранён для плавного перехода старых ссылок и Telegram back-flow, но больше не должен вести
            свою pricing-логику отдельно от cabinet renewal и marketing acquisition.
          </p>
          <div className="mt-4 rounded-2xl border border-white/40 bg-white/55 p-4 text-sm text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
            <p>Основные кабинетные действия теперь живут в `/subscription/`, `/subscription/checkout/` и `/redeem/`.</p>
            <p className="mt-2">Если пользователь пришёл сюда по старому маршруту, мы всё равно держим его внутри continuation-only мира.</p>
          </div>
        </article>

        <article className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">free monthly</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Бесплатный режим как безопасный baseline</h2>
          <div className="mt-4 space-y-3 text-sm leading-6 text-slate-600 dark:text-slate-300">
            <p>
              {ACCESS_MATRIX.free_tier.location_code} • {ACCESS_MATRIX.free_tier.traffic_limit_gb} GB /{" "}
              {ACCESS_MATRIX.free_tier.cycle_days} days
            </p>
            <p>
              {ACCESS_MATRIX.free_tier.speed_limit_mbps} Mbps per IP • до {ACCESS_MATRIX.free_tier.device_limit}{" "}
              устройства
            </p>
            <p>
              Trial стартует в приложении на первом валидном устройстве и после завершения опускается в
              этот monthly reset режим.
            </p>
          </div>
        </article>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {plans.map((plan) => (
          <article key={plan.code} className="glass-card p-6">
            <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">{plan.badge || "план"}</p>
            <h2 className="mt-2 font-display text-3xl font-bold">{plan.label}</h2>
            <p className="mt-3 text-2xl font-semibold">{plan.amountRub} ₽</p>
            <p className="mt-1 text-xs text-slate-500">
              {formatDays(plan.days)} • до {plan.deviceLimit} устройств
            </p>
            <p className="mt-4 text-sm leading-6 text-slate-600 dark:text-slate-300">{plan.note}</p>
            <div className="mt-5 flex gap-3">
              <AppRouteLink
                href={`/subscription/checkout/?plan=${encodeURIComponent(plan.code)}`}
                className="btn-primary rounded-xl px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.12em]"
              >
                Продолжить
              </AppRouteLink>
              <AppRouteLink
                href={`/redeem/?plan=${encodeURIComponent(plan.code)}`}
                className="outline-btn rounded-xl px-5 py-2.5 text-xs font-semibold uppercase tracking-[0.12em]"
              >
                Есть ключ
              </AppRouteLink>
            </div>
          </article>
        ))}
      </section>

      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">граница поверхностей</p>
        <h2 className="mt-2 font-display text-3xl font-bold">Маркетинг продаёт, кабинет продолжает</h2>
        <div className="mt-4 space-y-3 text-sm leading-7 text-slate-600 dark:text-slate-300">
          <p>Публичный pricing и paywall живут в `marketing/`. Этот кабинет не должен расходиться по цене, CTA и обещаниям.</p>
          <p>Email signup выдаёт только Free Monthly. Telegram здесь нужен как continuation, recovery и support fallback, а не как primary wall.</p>
          <p>Если нужен ручной recovery по старой ссылке, это отдельный support/manual-request path, а не default UX.</p>
        </div>
        {error ? (
          <p className="mt-4 text-xs text-amber-600 dark:text-amber-300">
            Не все данные каталога загрузились автоматически: {error}
          </p>
        ) : null}
      </section>
    </main>
  );
}
