"use client";

import { ArrowLeft, CalendarClock, CircleCheck, CreditCard, KeyRound, LifeBuoy, TriangleAlert } from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { GroupedSection } from "@/components/ui/grouped";
import { Input } from "@/components/ui/input";
import { ActionCard, ActionGrid } from "@/components/ui/tiles";
import { cn } from "@/components/utils";
import { resolvePlanLabel } from "@/lib/access-policy";
import { createRubCheckoutOrder, fetchPublicCatalog, getRubPaymentProviders, type RubPaymentProvidersResult } from "@/lib/api";
import { getCheckoutTariffPlans, getCopyText, getPricingPreviewDiscountPercent, normalizePlanCode, tariffPlanAllowsDiscount } from "@/lib/portal";
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

const SHARED_PLANS: DisplayPlan[] = getCheckoutTariffPlans()
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
              Number(plan.amount_rub || 0) > 0,
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
      setCheckoutError(String((error as { message?: string })?.message || error || "Оплата сейчас недоступна."));
    } finally {
      setCheckoutBusy(false);
    }
  };

  const providerWarning = !checkoutReady
    ? "Оплата временно недоступна. Попробуйте позже или откройте поддержку."
    : "";

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title={getCopyText("webapp.checkout.title", "Продлить доступ")}
        meta={resolvePlanLabel(dash, user)}
        body={getCopyText("webapp.checkout.subtitle", "Выберите срок, проверьте итог и перейдите к оплате. Продление останется на текущем профиле.")}
        tone={checkoutReady ? "success" : "warning"}
        icon={checkoutReady ? CreditCard : TriangleAlert}
        action={
          <Button
            onClick={startCheckout}
            loading={checkoutBusy}
            disabled={!checkoutReady}
            className="w-full sm:w-auto"
          >
            Перейти к оплате
          </Button>
        }
      />

      <GroupedSection title="Срок">
        {plans.map((plan) => {
          const selected = plan.code === activePlan?.code;
          return (
            <button
              key={plan.code}
              type="button"
              role="radio"
              aria-checked={selected}
              onClick={() => setSelectedCode(plan.code)}
              className={cn(
                "flex min-h-[56px] w-full items-center gap-3 px-4 py-2.5 text-left transition-colors duration-150 motion-reduce:transition-none",
                selected ? "bg-brand-soft/60" : "hover:bg-canvas-alt",
              )}
            >
              <span
                className={cn(
                  "grid size-9 shrink-0 place-items-center rounded-[10px] transition-colors duration-150 motion-reduce:transition-none",
                  selected ? "bg-brand text-brand-contrast" : "bg-brand-soft text-brand",
                )}
              >
                {selected ? (
                  <CircleCheck size={18} strokeWidth={2} aria-hidden="true" />
                ) : (
                  <CalendarClock size={18} strokeWidth={2} aria-hidden="true" />
                )}
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-center gap-2">
                  <span className="block truncate text-sm font-semibold text-ink">{plan.label}</span>
                  {plan.badge ? (
                    <span className="inline-flex shrink-0 items-center rounded-full border border-ok-line bg-ok-bg px-1.5 py-0.5 text-[10px] font-bold text-ok-text uppercase">
                      {plan.badge}
                    </span>
                  ) : null}
                </span>
                <span className="mt-0.5 block truncate text-[13px] leading-5 text-ink-muted">
                  {formatDuration(plan.days)} · до {plan.deviceLimit} устройств
                </span>
              </span>
              <span className="shrink-0 text-sm font-bold text-ink">{plan.amountRub} ₽</span>
              <span
                className={cn(
                  "shrink-0 text-sm font-semibold",
                  selected ? "text-ok-text" : "text-brand",
                )}
              >
                {selected ? "Выбрано" : "Выбрать"}
              </span>
            </button>
          );
        })}
      </GroupedSection>
      {catalogError ? <p className="px-1 text-sm text-warn-text">Каталог не обновился: {catalogError}</p> : null}

      <GroupedSection title="Способ оплаты">
        <div className="grid gap-2 p-4 sm:grid-cols-2">
          {PAYMENT_METHOD_OPTIONS.map((option) => {
            const selected = option.code === paymentMethod;
            return (
              <Chip
                key={option.code}
                active={selected}
                onClick={() => setPaymentMethod(option.code)}
                className="min-h-[72px] justify-start rounded-control px-4 py-3 text-left"
              >
                <span className="flex min-w-0 flex-col gap-1">
                  <span className="text-sm font-semibold text-ink">{option.label}</span>
                  <span className="text-xs leading-5 font-normal text-ink-soft">{option.hint}</span>
                </span>
              </Chip>
            );
          })}
        </div>
      </GroupedSection>

      <GroupedSection title="Итог">
        <div className="space-y-3 p-4">
          <Input
            value={promoInput}
            onChange={(event) => setPromoInput(event.target.value)}
            placeholder="Промокод"
          />
          {promoBlockedByPlan ? (
            <p className="text-sm text-warn-text">
              Для приветственного тарифа 99 ₽ промокод не применяется.
            </p>
          ) : null}
          <div className="rounded-control border border-line bg-canvas-alt px-4 py-3 text-sm leading-6 text-ink-soft">
            <div className="flex justify-between gap-3">
              <span>Базовая цена</span>
              <strong className="text-ink">{activePlan?.amountRub} ₽</strong>
            </div>
            <div className="flex justify-between gap-3">
              <span>Скидка</span>
              <strong className="text-ink">{discountAmount > 0 ? `${discountAmount} ₽` : "нет"}</strong>
            </div>
            <div className="mt-2 flex justify-between gap-3 text-base text-ink">
              <span className="font-semibold">К оплате</span>
              <strong>{totalAmount} ₽</strong>
            </div>
          </div>
          <Button onClick={startCheckout} loading={checkoutBusy} disabled={!checkoutReady} block>
            Перейти к оплате
          </Button>
          {providerWarning ? <p className="text-sm text-warn-text">{providerWarning}</p> : null}
          {checkoutError ? <p className="text-sm text-danger-text">{checkoutError}</p> : null}
        </div>
      </GroupedSection>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Что дальше</h2>
        <ActionGrid className="sm:grid-cols-3">
          <ActionCard icon={KeyRound} title="У меня уже есть код" hint="Активировать оплату, подарок или промокод" href="/redeem/" />
          <ActionCard icon={LifeBuoy} title="Оплата не обновилась" hint="Откройте одно обращение в поддержке" href="/support/" />
          <ActionCard icon={ArrowLeft} title="Назад к доступу" hint="Сроки, ссылка подключения и загрузки" href="/subscription/" />
        </ActionGrid>
      </section>
    </main>
  );
}
