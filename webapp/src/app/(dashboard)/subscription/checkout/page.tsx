"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { resolvePlanLabel } from "@/lib/access-policy";
import { createRubCheckoutOrder, fetchPublicCatalog, getRubPaymentProviders, type RubPaymentProvidersResult } from "@/lib/api";
import { getPricingPreviewDiscountPercent, getTariffPlans, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type DisplayPlan = {
  code: string;
  label: string;
  badge?: string;
  days: number;
  amountRub: number;
  deviceLimit: number;
  note: string;
};

const CHECKOUT_READY_PLAN_CODES = new Set(["start_99"]);

const SHARED_PLANS: DisplayPlan[] = getTariffPlans()
  .slice()
  .filter(
    (plan) =>
      Boolean(plan.is_active) &&
      Number(plan.amount_rub || 0) > 0 &&
      CHECKOUT_READY_PLAN_CODES.has(String(plan.code || "").trim().toLowerCase()),
  )
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

function icon(name: string) {
  return <span className="material-symbols-rounded text-[20px]">{name}</span>;
}

function normalizePromo(raw: string): string {
  return String(raw || "").trim().toUpperCase();
}

function formatDuration(days: number): string {
  if (days >= 365) return `${Math.round(days / 30)} мес.`;
  if (days > 90) return `${Math.round(days / 30)} мес.`;
  return `${days} дней`;
}

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<DisplayPlan[]>(SHARED_PLANS);
  const [promoInput, setPromoInput] = useState(() => normalizePromo(searchParams.get("promo") || ""));
  const [catalogError, setCatalogError] = useState("");
  const [selectedCode, setSelectedCode] = useState(() => normalizePlanCode(searchParams.get("plan"), "start_99"));
  const [providerCode, setProviderCode] = useState("");
  const [providerState, setProviderState] = useState<RubPaymentProvidersResult | null>(null);
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [checkoutError, setCheckoutError] = useState("");

  useEffect(() => {
    setSelectedCode(normalizePlanCode(searchParams.get("plan"), "start_99"));
    setPromoInput(normalizePromo(searchParams.get("promo") || ""));
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const payload = await fetchPublicCatalog();
        const nextPlans = (payload.plans || [])
          .filter(
            (plan) =>
              Boolean(plan.is_active) &&
              Number(plan.amount_rub || 0) > 0 &&
              CHECKOUT_READY_PLAN_CODES.has(String(plan.code || "").trim().toLowerCase()),
          )
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
      } catch (nextError) {
        if (!cancelled) {
          setPlans(SHARED_PLANS);
          setCatalogError(String((nextError as { message?: string })?.message || nextError || ""));
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void getRubPaymentProviders()
      .then((payload) => {
        if (!cancelled) {
          setProviderState(payload);
          setProviderCode(payload.ok && !payload.blocked ? String(payload.providers?.[0]?.code || "") : "");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setProviderState(null);
          setProviderCode("");
        }
      });
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
  const checkoutReady = Boolean(providerState?.ok && !providerState?.blocked && providerCode);

  const startCheckout = async (): Promise<void> => {
    if (!activePlan?.code || !providerCode) return;
    setCheckoutBusy(true);
    setCheckoutError("");
    try {
      const order = await createRubCheckoutOrder({
        provider: providerCode,
        plan_code: activePlan.code,
        source: "site",
        promo_code: discountPercent > 0 ? promoCode : undefined,
        currency: "RUB",
      });
      const paymentUrl = String(order.payment_url || "").trim();
      if (!paymentUrl) {
        throw new Error("Платежная ссылка не получена.");
      }
      window.location.assign(paymentUrl);
    } catch (error) {
      setCheckoutError(String((error as { message?: string })?.message || error || "Оплата сейчас недоступна."));
    } finally {
      setCheckoutBusy(false);
    }
  };

  const providerWarning = !checkoutReady
    ? "Оплата временно недоступна. Попробуйте позже или откройте поддержку."
    : "";

  return (
    <main className="mx-auto w-full max-w-[840px] space-y-5">
      <CabinetStatus
        title="Продлить доступ"
        meta={resolvePlanLabel(dash, user)}
        body="Выберите срок, проверьте итог и перейдите к оплате. Продление останется на текущем профиле."
        tone={checkoutReady ? "success" : "warning"}
        action={
          <button
            type="button"
            onClick={startCheckout}
            disabled={!checkoutReady || checkoutBusy}
            className="btn-primary w-full rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60 sm:w-auto"
          >
            {checkoutBusy ? "Открываем..." : "Перейти к оплате"}
          </button>
        }
      />

      <CabinetGroup title="Срок">
        {plans.map((plan) => {
          const selected = plan.code === activePlan?.code;
          return (
            <CabinetRow
              key={plan.code}
              icon={icon(selected ? "check_circle" : "calendar_month")}
              label={plan.label}
              hint={`${formatDuration(plan.days)} · до ${plan.deviceLimit} устройств`}
              value={`${plan.amountRub} ₽`}
              action={
                <button
                  type="button"
                  onClick={() => setSelectedCode(plan.code)}
                  className="text-sm font-semibold text-emerald-800 dark:text-emerald-300"
                >
                  {selected ? "Выбрано" : "Выбрать"}
                </button>
              }
            />
          );
        })}
      </CabinetGroup>
      {catalogError ? <p className="px-1 text-sm text-amber-700 dark:text-amber-200">Каталог не обновился: {catalogError}</p> : null}

      <CabinetGroup title="Итог">
        <div className="space-y-3 p-4">
          <input
            value={promoInput}
            onChange={(event) => setPromoInput(event.target.value)}
            placeholder="Промокод"
            className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
          />
          <div className="rounded-2xl border border-slate-200/80 bg-slate-50/90 px-4 py-3 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200">
            <div className="flex justify-between gap-3">
              <span>Базовая цена</span>
              <strong>{activePlan?.amountRub} ₽</strong>
            </div>
            <div className="flex justify-between gap-3">
              <span>Скидка</span>
              <strong>{discountAmount > 0 ? `${discountAmount} ₽` : "нет"}</strong>
            </div>
            <div className="mt-2 flex justify-between gap-3 text-base text-slate-950 dark:text-white">
              <span className="font-semibold">К оплате</span>
              <strong>{totalAmount} ₽</strong>
            </div>
          </div>
          <button
            type="button"
            onClick={startCheckout}
            disabled={!checkoutReady || checkoutBusy}
            className="btn-primary w-full rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
          >
            {checkoutBusy ? "Открываем..." : "Перейти к оплате"}
          </button>
          {providerWarning ? <p className="text-sm text-amber-700 dark:text-amber-200">{providerWarning}</p> : null}
          {checkoutError ? <p className="text-sm text-rose-700 dark:text-rose-200">{checkoutError}</p> : null}
        </div>
      </CabinetGroup>

      <CabinetGroup title="Что дальше">
        <CabinetRow icon={icon("key")} label="У меня уже есть код" hint="Активировать оплату, подарок или промокод" href="/redeem/" />
        <CabinetRow icon={icon("support_agent")} label="Оплата не обновилась" hint="Откройте одно обращение в поддержке" href="/support/" />
        <CabinetRow icon={icon("arrow_back")} label="Назад к доступу" hint="Сроки, ссылка подключения и загрузки" href="/subscription/" />
      </CabinetGroup>
    </main>
  );
}
