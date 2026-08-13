"use client";

import { ArrowLeft, ChevronDown, CircleCheck, CreditCard, KeyRound, LifeBuoy, Loader2, TriangleAlert } from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { GroupedSection } from "@/components/ui/grouped";
import { Input } from "@/components/ui/input";
import { ActionCard, ActionGrid } from "@/components/ui/tiles";
import { cn } from "@/components/utils";
import { formatDays, formatDevicesLimit } from "@/lib/ru-plural";
import { resolvePlanLabel } from "@/lib/access-policy";
import { createRubCheckoutOrder, fetchPublicCatalog, getRubPaymentProviders, type PlanCatalogRow, type RubPaymentProvidersResult } from "@/lib/api";
import { getCabinetFallbackPlans, resolveCabinetPlans } from "@/lib/cabinet-plans";
import { getCopyText, getPricingPreviewDiscountPercent, normalizePlanCode, tariffPlanAllowsDiscount } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
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

const PAYMENT_METHOD_OPTIONS: Array<{
  code: PaymentMethodChoice;
  label: string;
  hint: string;
}> = [
  { code: "sbp", label: "СБП", hint: "Быстро через приложение банка" },
  { code: "card", label: "Карта", hint: "Visa, Mastercard или МИР" },
];

function toDisplayPlans(plans: PlanCatalogRow[]): DisplayPlan[] {
  return plans.map((plan) => ({
    code: plan.code,
    label: plan.label,
    badge: plan.badge || undefined,
    days: Number(plan.days || 0),
    amountRub: Number(plan.amount_rub || 0),
    deviceLimit: Number(plan.device_limit || 1),
    note: plan.label,
  }));
}

const SHARED_PLANS: DisplayPlan[] = toDisplayPlans(getCabinetFallbackPlans());

function normalizePromo(raw: string): string {
  return String(raw || "").trim().toUpperCase();
}

function normalizePaymentMethod(raw: string | null): PaymentMethodChoice {
  return raw === "card" ? "card" : "sbp";
}

function formatDuration(days: number): string {
  if (days > 90) return `${Math.round(days / 30)} мес.`;
  return formatDays(days);
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
  const [providerProbePending, setProviderProbePending] = useState(true);
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [checkoutError, setCheckoutError] = useState("");
  const [planPickerOpen, setPlanPickerOpen] = useState(false);

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
        const nextPlans = toDisplayPlans(resolveCabinetPlans(payload.plans));

        if (!cancelled) {
          setPlans(nextPlans.length ? nextPlans : SHARED_PLANS);
          setCatalogError("");
        }
      } catch (nextError) {
        if (!cancelled) {
          setPlans(SHARED_PLANS);
          setCatalogError(userFacingErrorMessage(nextError, "Проверьте соединение и обновите страницу."));
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
          setProviderProbePending(false);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setProviderState(null);
          setProviderCode("");
          setProviderProbePending(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const availablePlans = useMemo(() => {
    const provider = providerState?.providers?.find((item) => item.code === providerCode);
    const supported = Array.isArray(provider?.supported_plan_codes) ? provider.supported_plan_codes : null;
    return supported ? plans.filter((plan) => supported.includes(plan.code)) : plans;
  }, [plans, providerCode, providerState]);
  const activePlan = useMemo(
    () => availablePlans.find((plan) => plan.code === selectedCode) || availablePlans[0] || SHARED_PLANS[0],
    [availablePlans, selectedCode],
  );
  const promoCode = normalizePromo(promoInput);
  const rawDiscountPercent = getPricingPreviewDiscountPercent(promoCode);
  const discountPercent = tariffPlanAllowsDiscount(activePlan?.code) ? rawDiscountPercent : 0;
  const promoBlockedByPlan = rawDiscountPercent > 0 && !tariffPlanAllowsDiscount(activePlan?.code);
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
      setCheckoutError(userFacingErrorMessage(error, "Оплата сейчас недоступна. Попробуйте позже или откройте поддержку."));
    } finally {
      setCheckoutBusy(false);
    }
  };

  const providerWarning = !providerProbePending && !checkoutReady
    ? "Оплата временно недоступна. Попробуйте позже или откройте поддержку."
    : "";
  const heroTone = checkoutReady ? "success" : providerProbePending ? "neutral" : "warning";

  return (
    <main className="mx-auto flex w-full max-w-[720px] flex-col gap-4">
      <StatusHero
        title={getCopyText("webapp.checkout.title", "Продлить доступ")}
        meta={resolvePlanLabel(dash, user)}
        body={getCopyText("webapp.checkout.subtitle", "Одна оплата без автосписаний. Доступ останется на текущем профиле.")}
        tone={heroTone}
        icon={checkoutReady || providerProbePending ? CreditCard : TriangleAlert}
      />

      <GroupedSection title="Оформление">
        <div className="p-4">
          <button
            type="button"
            onClick={() => setPlanPickerOpen((value) => !value)}
            aria-expanded={planPickerOpen}
            aria-controls="cabinet-checkout-plans"
            className="flex min-h-[64px] w-full items-center gap-3 rounded-control border border-brand bg-brand-soft/60 px-4 py-3 text-left outline-none transition-colors duration-150 hover:bg-brand-soft focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 motion-reduce:transition-none"
          >
            <span className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-brand text-brand-contrast">
              <CircleCheck size={18} strokeWidth={2} aria-hidden="true" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2">
                <span className="truncate text-sm font-semibold text-ink">{activePlan?.label}</span>
                {activePlan?.badge ? (
                  <span className="inline-flex shrink-0 items-center rounded-full border border-ok-line bg-ok-bg px-1.5 py-0.5 text-[10px] font-bold text-ok-text uppercase">
                    {activePlan.badge}
                  </span>
                ) : null}
              </span>
              <span className="mt-0.5 block truncate text-[13px] leading-5 text-ink-soft">
                {formatDuration(activePlan?.days || 0)} · {formatDevicesLimit(activePlan?.deviceLimit || 1)}
              </span>
            </span>
            <strong className="shrink-0 text-base text-ink">{activePlan?.amountRub} ₽</strong>
            <ChevronDown
              size={18}
              strokeWidth={2}
              aria-hidden="true"
              className={cn("shrink-0 text-ink-soft transition-transform duration-150 motion-reduce:transition-none", planPickerOpen && "rotate-180")}
            />
          </button>

          {planPickerOpen ? (
            <div id="cabinet-checkout-plans" role="radiogroup" aria-label="Срок доступа" className="mt-2 grid gap-2 sm:grid-cols-2">
              {availablePlans.map((plan) => {
                const selected = plan.code === activePlan?.code;
                return (
                  <button
                    key={plan.code}
                    type="button"
                    role="radio"
                    aria-checked={selected}
                    onClick={() => {
                      setSelectedCode(plan.code);
                      setPlanPickerOpen(false);
                    }}
                    className={cn(
                      "flex min-h-[58px] items-center gap-3 rounded-control border px-3 py-2.5 text-left outline-none transition-colors duration-150 focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 motion-reduce:transition-none",
                      selected ? "border-brand bg-brand-soft/60" : "border-line bg-surface hover:bg-canvas-alt",
                    )}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-semibold text-ink">{plan.label}</span>
                      <span className="mt-0.5 block text-xs text-ink-soft">{formatDuration(plan.days)} · {formatDevicesLimit(plan.deviceLimit)}</span>
                    </span>
                    <strong className="shrink-0 text-sm text-ink">{plan.amountRub} ₽</strong>
                  </button>
                );
              })}
            </div>
          ) : null}
          {catalogError ? <p className="mt-2 text-sm text-warn-text">Каталог не обновился: {catalogError}</p> : null}
        </div>

        <div className="p-4">
          <p className="mb-2 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Способ оплаты</p>
          <div className="grid grid-cols-2 gap-2">
            {PAYMENT_METHOD_OPTIONS.map((option) => {
              const selected = option.code === paymentMethod;
              return (
                <Chip
                  key={option.code}
                  active={selected}
                  onClick={() => setPaymentMethod(option.code)}
                  className="min-h-[60px] justify-start rounded-control px-3 py-2.5 text-left"
                >
                  <span className="flex min-w-0 flex-col gap-0.5">
                    <span className="text-sm font-semibold text-ink">{option.label}</span>
                    <span className="line-clamp-2 text-xs leading-4 font-normal text-ink-soft">{option.hint}</span>
                  </span>
                </Chip>
              );
            })}
          </div>
        </div>

        <details className="group px-4">
          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 rounded-control py-2 text-sm font-semibold text-ink outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2">
            Есть промокод?
            <ChevronDown size={18} strokeWidth={2} aria-hidden="true" className="shrink-0 text-ink-soft transition-transform duration-150 group-open:rotate-180 motion-reduce:transition-none" />
          </summary>
          <div className="space-y-2 pb-4">
            <Input
              value={promoInput}
              onChange={(event) => setPromoInput(event.target.value)}
              placeholder="Промокод"
            />
            {promoBlockedByPlan ? <p className="text-sm text-warn-text">Для приветственных 99 ₽ промокод не применяется.</p> : null}
            {discountAmount > 0 ? <p className="text-sm text-ok-text">Скидка {discountPercent}% применена.</p> : null}
          </div>
        </details>

        <div className="space-y-3 p-4">
          <div className="rounded-control border border-line bg-canvas-alt px-4 py-3">
            {discountAmount > 0 ? (
              <div className="mb-1 flex justify-between gap-3 text-sm text-ink-soft">
                <span>Цена до скидки</span>
                <span className="line-through">{activePlan?.amountRub} ₽</span>
              </div>
            ) : null}
            <div className="flex items-end justify-between gap-3 text-ink">
              <span className="font-semibold">К оплате</span>
              <strong className="font-display text-2xl leading-none">{totalAmount} ₽</strong>
            </div>
          </div>
          <Button onClick={startCheckout} loading={checkoutBusy} disabled={!checkoutReady} block>
            Оплатить {totalAmount} ₽
          </Button>
          <p className="text-center text-xs leading-5 text-ink-soft">Разовая оплата · без автосписаний</p>
          {providerProbePending ? (
            <p className="flex items-center gap-2 text-sm text-ink-soft" role="status">
              <Loader2 size={15} strokeWidth={2.2} className="shrink-0 animate-spin motion-reduce:animate-none" aria-hidden="true" />
              Проверяем способы оплаты…
            </p>
          ) : null}
          {providerWarning ? <p className="text-sm text-warn-text">{providerWarning}</p> : null}
          {checkoutError ? <p className="text-sm text-danger-text">{checkoutError}</p> : null}
        </div>

        <details className="group px-4">
          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 rounded-control py-2 text-sm font-semibold text-ink outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2">
            Код активации или помощь
            <ChevronDown size={18} strokeWidth={2} aria-hidden="true" className="shrink-0 text-ink-soft transition-transform duration-150 group-open:rotate-180 motion-reduce:transition-none" />
          </summary>
          <ActionGrid className="pb-4 sm:grid-cols-3">
            <ActionCard icon={KeyRound} title="Есть код" hint="Активировать доступ" href="/redeem/" />
            <ActionCard icon={LifeBuoy} title="Нужна помощь" hint="Открыть поддержку" href="/support/" />
            <ActionCard icon={ArrowLeft} title="Назад" hint="К управлению доступом" href="/subscription/" />
          </ActionGrid>
        </details>
      </GroupedSection>
    </main>
  );
}
