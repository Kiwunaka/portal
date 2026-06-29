"use client";

import { icon } from "@/components/cabinet/icon";
import { CabinetActionCard, CabinetActionGrid, CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { Button, Chip, Input } from "@/components/cabinet/ui";
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

type PaymentMethodChoice = "sbp" | "card";

const CHECKOUT_READY_PLAN_CODES = new Set(["start_99"]);

const PAYMENT_METHOD_OPTIONS: Array<{
  code: PaymentMethodChoice;
  label: string;
  hint: string;
}> = [
  { code: "sbp", label: "СБП", hint: "Быстро через приложение банка" },
  { code: "card", label: "Карта", hint: "Visa, Mastercard или МИР" },
];

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

function normalizePromo(raw: string): string {
  return String(raw || "").trim().toUpperCase();
}

function normalizePaymentMethod(raw: string | null): PaymentMethodChoice {
  return raw === "card" ? "card" : "sbp";
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
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethodChoice>(() => normalizePaymentMethod(searchParams.get("payment_method")));
  const [providerCode, setProviderCode] = useState("");
  const [providerState, setProviderState] = useState<RubPaymentProvidersResult | null>(null);
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [checkoutError, setCheckoutError] = useState("");

  useEffect(() => {
    setSelectedCode(normalizePlanCode(searchParams.get("plan"), "start_99"));
    setPromoInput(normalizePromo(searchParams.get("promo") || ""));
    setPaymentMethod(normalizePaymentMethod(searchParams.get("payment_method")));
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
        payment_method: paymentMethod,
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
    <main className="cab-page">
      <CabinetStatus
        title="Продлить доступ"
        meta={resolvePlanLabel(dash, user)}
        body="Выберите срок, проверьте итог и перейдите к оплате. Продление останется на текущем профиле."
        tone={checkoutReady ? "success" : "warning"}
        emblem={icon(checkoutReady ? "payments" : "warning", "h-7 w-7")}
        action={
          <Button
            onClick={startCheckout}
            disabled={!checkoutReady || checkoutBusy}
            className="w-full sm:w-auto"
          >
            {checkoutBusy ? "Открываем..." : "Перейти к оплате"}
          </Button>
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
                  className="cab-link"
                >
                  {selected ? "Выбрано" : "Выбрать"}
                </button>
              }
            />
          );
        })}
      </CabinetGroup>
      {catalogError ? <p className="px-1 text-sm text-[color:var(--atlas-status-warning-text)]">Каталог не обновился: {catalogError}</p> : null}

      <CabinetGroup title="Способ оплаты">
        <div className="grid gap-2 p-4 sm:grid-cols-2">
          {PAYMENT_METHOD_OPTIONS.map((option) => {
            const selected = option.code === paymentMethod;
            return (
              <Chip
                key={option.code}
                active={selected}
                onClick={() => setPaymentMethod(option.code)}
                className="min-h-[72px] justify-start px-4 py-3 text-left"
                aria-pressed={selected}
              >
                <span className="flex min-w-0 flex-col gap-1">
                  <span className="text-sm font-semibold text-[color:var(--atlas-text)]">{option.label}</span>
                  <span className="text-xs leading-5 text-[color:var(--atlas-text-soft)]">{option.hint}</span>
                </span>
              </Chip>
            );
          })}
        </div>
      </CabinetGroup>

      <CabinetGroup title="Итог">
        <div className="space-y-3 p-4">
          <Input
            value={promoInput}
            onChange={(event) => setPromoInput(event.target.value)}
            placeholder="Промокод"
          />
          <div className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-4 py-3 text-sm leading-6 text-[color:var(--atlas-text-soft)]">
            <div className="flex justify-between gap-3">
              <span>Базовая цена</span>
              <strong className="text-[color:var(--atlas-text)]">{activePlan?.amountRub} ₽</strong>
            </div>
            <div className="flex justify-between gap-3">
              <span>Скидка</span>
              <strong className="text-[color:var(--atlas-text)]">{discountAmount > 0 ? `${discountAmount} ₽` : "нет"}</strong>
            </div>
            <div className="mt-2 flex justify-between gap-3 text-base text-[color:var(--atlas-text)]">
              <span className="font-semibold">К оплате</span>
              <strong>{totalAmount} ₽</strong>
            </div>
          </div>
          <Button onClick={startCheckout} disabled={!checkoutReady || checkoutBusy} block>
            {checkoutBusy ? "Открываем..." : "Перейти к оплате"}
          </Button>
          {providerWarning ? <p className="text-sm text-[color:var(--atlas-status-warning-text)]">{providerWarning}</p> : null}
          {checkoutError ? <p className="text-sm text-[color:var(--atlas-status-danger-text)]">{checkoutError}</p> : null}
        </div>
      </CabinetGroup>

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Что дальше</h2>
        <CabinetActionGrid>
          <CabinetActionCard icon={icon("key")} title="У меня уже есть код" hint="Активировать оплату, подарок или промокод" href="/redeem/" />
          <CabinetActionCard icon={icon("support_agent")} title="Оплата не обновилась" hint="Откройте одно обращение в поддержке" href="/support/" />
          <CabinetActionCard icon={icon("arrow_back")} title="Назад к доступу" hint="Сроки, ссылка подключения и загрузки" href="/subscription/" />
        </CabinetActionGrid>
      </section>
    </main>
  );
}
