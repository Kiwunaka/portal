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
import {
  createRubCheckoutOrder,
  fetchPaymentReturnStatus,
  fetchPublicCatalog,
  getRubPaymentProviders,
  previewCommercialOffer,
  type CommercialOfferPreviewResult,
  type PaymentReturnStatusResult,
  type PlanCatalogRow,
  type RubPaymentMethod,
  type RubPaymentProvidersResult,
} from "@/lib/api";
import { getCabinetFallbackPlans, resolveCabinetPlans } from "@/lib/cabinet-plans";
import { COMMERCIAL_REVISION, getCopyText, normalizePlanCode } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

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

const PAYMENT_METHOD_FALLBACKS: Array<{
  code: PaymentMethodChoice;
  label: string;
  hint: string;
}> = [
  { code: "sbp", label: "СБП", hint: "Быстро через приложение банка" },
  { code: "card", label: "Карта", hint: "Visa, Mastercard или МИР" },
];

const PAYMENT_RETURN_STORAGE_KEY = "pokrov.payment-return.v1";

const OFFER_REASON_TEXT: Record<string, string> = {
  ready: "Промокод применён сервером.",
  promo_unknown: "Промокод не найден.",
  promo_invalid: "Промокод недействителен.",
  promo_expired: "Срок промокода истёк.",
  promo_depleted: "Лимит промокода исчерпан.",
  offer_non_stackable: "Эта скидка не складывается с выбранным тарифом.",
  legal_blocked: "Предложение временно недоступно по условиям запуска.",
  capacity_blocked: "Предложение временно недоступно из-за лимита сервиса.",
  quota_reached: "Лимит предложения исчерпан.",
};

const RETURN_STATE_TEXT: Record<PaymentReturnStatusResult["state"], string> = {
  processing: "Платёж обрабатывается. Статус обновится автоматически.",
  paid: "Оплата подтверждена. Доступ обновляется на сервере.",
  failed: "Платёж не подтверждён. Можно повторить попытку.",
  cancelled: "Оплата отменена. Можно выбрать способ и попробовать снова.",
  manual_review: "Платёж требует ручной проверки. Откройте поддержку.",
  expired: "Платёжная сессия истекла. Создайте новый платёж.",
};

function storePaymentReturnToken(token: string): boolean {
  const normalized = String(token || "").trim();
  if (!normalized || typeof window === "undefined") return false;
  try {
    window.sessionStorage.setItem(PAYMENT_RETURN_STORAGE_KEY, normalized);
    return true;
  } catch {
    return false;
  }
}

function readPaymentReturnToken(): string {
  try {
    return String(window.sessionStorage.getItem(PAYMENT_RETURN_STORAGE_KEY) || "").trim();
  } catch {
    return "";
  }
}

function clearPaymentReturnToken(): void {
  try {
    window.sessionStorage.removeItem(PAYMENT_RETURN_STORAGE_KEY);
  } catch {
    // The terminal server state is already rendered; storage cleanup is best effort.
  }
}

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

function formatServerDeadline(value?: string | null): string {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const { user, dash, refresh } = usePortalSession();
  const [plans, setPlans] = useState<DisplayPlan[]>(SHARED_PLANS);
  const [promoInput, setPromoInput] = useState(() => normalizePromo(searchParams.get("promo") || ""));
  const [catalogError, setCatalogError] = useState("");
  const [catalogVerified, setCatalogVerified] = useState(false);
  const [selectedCode, setSelectedCode] = useState(() => normalizePlanCode(searchParams.get("plan"), "start_99"));
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethodChoice>(() => normalizePaymentMethod(searchParams.get("payment_method")));
  const [providerCode, setProviderCode] = useState("");
  const [providerState, setProviderState] = useState<RubPaymentProvidersResult | null>(null);
  const [providerProbePending, setProviderProbePending] = useState(true);
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [checkoutError, setCheckoutError] = useState("");
  const [planPickerOpen, setPlanPickerOpen] = useState(false);
  const [offerPreview, setOfferPreview] = useState<CommercialOfferPreviewResult | null>(null);
  const [offerPreviewPending, setOfferPreviewPending] = useState(true);
  const [paymentReturn, setPaymentReturn] = useState<PaymentReturnStatusResult | null>(null);
  const [paymentReturnError, setPaymentReturnError] = useState("");
  const [paymentAccessRefresh, setPaymentAccessRefresh] = useState<"idle" | "pending" | "complete" | "failed">("idle");
  const [paymentReturnRetry, setPaymentReturnRetry] = useState(0);

  const refreshPaidAccess = useCallback(async () => {
    setPaymentAccessRefresh("pending");
    try {
      await refresh();
      setPaymentAccessRefresh("complete");
    } catch {
      setPaymentAccessRefresh("failed");
    }
  }, [refresh]);

  useEffect(() => {
    setSelectedCode(normalizePlanCode(searchParams.get("plan"), "start_99"));
    setPromoInput(normalizePromo(searchParams.get("promo") || ""));
    setPaymentMethod(normalizePaymentMethod(searchParams.get("payment_method")));
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const [catalogResult, providerResult] = await Promise.allSettled([
        fetchPublicCatalog(),
        getRubPaymentProviders(),
      ]);
      if (cancelled) return;
      if (catalogResult.status === "fulfilled") {
        const nextPlans = toDisplayPlans(resolveCabinetPlans(catalogResult.value.plans));
        setPlans(nextPlans.length ? nextPlans : SHARED_PLANS);
        setCatalogError("");
        setCatalogVerified(true);
      } else {
        setPlans(SHARED_PLANS);
        setCatalogVerified(false);
        setCatalogError(userFacingErrorMessage(catalogResult.reason, "Проверьте соединение и обновите страницу."));
      }
      if (providerResult.status === "fulfilled") {
        const payload = providerResult.value;
        setProviderState(payload);
        setProviderCode(payload.ok && !payload.blocked ? String(payload.providers?.[0]?.code || "") : "");
      } else {
        setProviderState(null);
        setProviderCode("");
      }
      setProviderProbePending(false);
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || !searchParams.get("payment_return")) return;
    const returnToken = readPaymentReturnToken();
    const cleanedUrl = new URL(window.location.href);
    cleanedUrl.searchParams.delete("payment_return");
    window.history.replaceState(window.history.state, "", `${cleanedUrl.pathname}${cleanedUrl.search}${cleanedUrl.hash}`);
    if (!returnToken) {
      setPaymentReturnError("Не найден локальный идентификатор платежа. Откройте поддержку, если деньги списались.");
      return;
    }
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;
    const poll = async (): Promise<void> => {
      try {
        const result = await fetchPaymentReturnStatus(returnToken);
        if (cancelled) return;
        setPaymentReturn(result);
        setPaymentReturnError("");
        if (!result.terminal) {
          timer = setTimeout(() => void poll(), Math.max(1, result.next_poll_seconds || 2) * 1000);
        } else {
          clearPaymentReturnToken();
          if (result.state === "paid") {
            await refreshPaidAccess();
          }
        }
      } catch (error) {
        if (!cancelled) {
          setPaymentReturnError(userFacingErrorMessage(error, "Не удалось обновить статус платежа."));
        }
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [paymentReturnRetry, refreshPaidAccess, searchParams]);

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
  const activeProvider = providerState?.providers?.find((item) => item.code === providerCode);
  const paymentMethods: RubPaymentMethod[] = activeProvider?.payment_methods?.length
    ? activeProvider.payment_methods
    : PAYMENT_METHOD_FALLBACKS.map((item) => ({ ...item, available: true }));
  const selectedPaymentMethod = paymentMethods.find((item) => item.code === paymentMethod);
  const previewMatchesPlan = Boolean(
    offerPreview
      && offerPreview.plan_code === activePlan?.code
      && offerPreview.commercial_revision === COMMERCIAL_REVISION,
  );
  const baseAmount = previewMatchesPlan
    ? Math.max(0, Number(offerPreview?.base_price_rub || 0))
    : 0;
  const finalAmount = previewMatchesPlan
    ? Math.max(0, Number(offerPreview?.final_price_rub || 0))
    : 0;
  const promoAccepted = !promoCode || Boolean(offerPreview?.valid && offerPreview?.offer_token);
  const checkoutReady = Boolean(
    catalogVerified
      && providerState?.ok
      && !providerState?.blocked
      && providerCode
      && previewMatchesPlan
      && !offerPreviewPending
      && promoAccepted
      && selectedPaymentMethod?.available,
  );

  useEffect(() => {
    const firstAvailable = paymentMethods.find((item) => item.available && (item.code === "sbp" || item.code === "card"));
    if ((!selectedPaymentMethod || !selectedPaymentMethod.available) && firstAvailable) {
      setPaymentMethod(firstAvailable.code as PaymentMethodChoice);
    }
  }, [paymentMethods, selectedPaymentMethod]);

  useEffect(() => {
    if (!catalogVerified || !activePlan?.code) return;
    let cancelled = false;
    const timer = setTimeout(() => {
      setOfferPreviewPending(true);
      void previewCommercialOffer({
        plan_code: activePlan.code,
        promo_code: promoCode,
        channel: "owned_web",
      })
        .then((result) => {
          if (!cancelled) setOfferPreview(result);
        })
        .catch(() => {
          if (!cancelled) setOfferPreview(null);
        })
        .finally(() => {
          if (!cancelled) setOfferPreviewPending(false);
        });
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [activePlan?.code, catalogVerified, promoCode]);

  const startCheckout = async (): Promise<void> => {
    if (!activePlan?.code || !providerCode) return;
    setCheckoutBusy(true);
    setCheckoutError("");
    try {
      const order = await createRubCheckoutOrder({
        provider: providerCode,
        plan_code: activePlan.code,
        source: "site",
        promo_code: promoCode || undefined,
        currency: "RUB",
        payment_method: paymentMethod,
        offer_token: offerPreview?.valid ? String(offerPreview.offer_token || "") || undefined : undefined,
      });
      const paymentUrl = String(order.payment_url || "").trim();
      if (!paymentUrl) {
        throw new Error("Платежная ссылка не получена.");
      }
      if (!storePaymentReturnToken(order.payment_return_token)) {
        throw new Error("Браузер не сохранил безопасный идентификатор платежа. Разрешите временное хранилище и повторите.");
      }
      window.location.assign(paymentUrl);
    } catch (error) {
      setCheckoutError(userFacingErrorMessage(error, "Оплата сейчас недоступна. Попробуйте позже или откройте поддержку."));
    } finally {
      setCheckoutBusy(false);
    }
  };

  const infrastructureReady = Boolean(catalogVerified && providerState?.ok && !providerState?.blocked && providerCode);
  const providerWarning = !providerProbePending && !infrastructureReady
    ? "Оплата временно недоступна. Попробуйте позже или откройте поддержку."
    : "";
  const offerMessage = promoCode && offerPreview && !offerPreview.valid
    ? OFFER_REASON_TEXT[offerPreview.reason_code] || "Промокод сейчас недоступен."
    : promoCode && offerPreview?.valid
      ? OFFER_REASON_TEXT.ready
      : "";
  const heroTone = infrastructureReady ? "success" : providerProbePending ? "neutral" : "warning";
  const paidAccessReady = Boolean(
    paymentReturn?.state === "paid"
      && paymentAccessRefresh === "complete"
      && dash?.is_active,
  );
  const paidAccessStale = Boolean(
    paymentReturn?.state === "paid"
      && (paymentAccessRefresh === "complete" || paymentAccessRefresh === "failed")
      && !paidAccessReady,
  );
  const paymentReturnMessage = paymentReturn?.state === "paid"
    ? paymentAccessRefresh === "pending" || paymentAccessRefresh === "idle"
      ? "Оплата подтверждена. Проверяем доступ в аккаунте."
      : paidAccessReady
        ? "Оплата подтверждена. Доступ активен."
        : "Оплата подтверждена, но доступ ещё не обновился. Повторите проверку или откройте поддержку."
    : paymentReturn
      ? RETURN_STATE_TEXT[paymentReturn.state]
      : paymentReturnError;

  const focusCheckout = () => {
    const target = document.getElementById("checkout-form");
    target?.focus();
    target?.scrollIntoView({ behavior: "smooth", block: "center" });
  };

  return (
    <main className="mx-auto flex w-full max-w-[720px] flex-col gap-4">
      <StatusHero
        title={getCopyText("webapp.checkout.title", "Продлить доступ")}
        meta={resolvePlanLabel(dash, user)}
        body={getCopyText("webapp.checkout.subtitle", "Одна оплата без автосписаний. Доступ останется на текущем профиле.")}
        tone={heroTone}
        icon={checkoutReady || providerProbePending ? CreditCard : TriangleAlert}
      />

      {paymentReturn || paymentReturnError ? (
        <GroupedSection title="Статус платежа">
          <div className="space-y-2 p-4" role="status" aria-live="polite">
            <p className={cn("text-sm font-semibold", paidAccessReady ? "text-ok-text" : paymentReturn?.state === "manual_review" || paidAccessStale ? "text-warn-text" : "text-ink") }>
              {paymentReturnMessage}
            </p>
            {paymentReturn?.state === "processing" || paymentAccessRefresh === "pending" ? (
              <p className="flex items-center gap-2 text-sm text-ink-soft">
                <Loader2 size={15} strokeWidth={2.2} className="shrink-0 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                {paymentReturn?.state === "processing" ? "Проверяем подтверждение на сервере…" : "Обновляем состояние доступа…"}
              </p>
            ) : null}
            <div className="flex flex-wrap gap-2 pt-1">
              {paidAccessReady ? <Button href="/dashboard/" size="sm">Вернуться на главную</Button> : null}
              {paidAccessStale ? (
                <>
                  <Button size="sm" onClick={() => void refreshPaidAccess()}>Проверить доступ</Button>
                  <Button size="sm" variant="secondary" href="/support/">Поддержка</Button>
                </>
              ) : null}
              {paymentReturn?.state === "manual_review" ? <Button size="sm" href="/support/">Открыть поддержку</Button> : null}
              {paymentReturn && ["failed", "cancelled", "expired"].includes(paymentReturn.state) ? (
                <Button size="sm" onClick={focusCheckout}>Создать новый платёж</Button>
              ) : null}
              {paymentReturnError ? (
                <>
                  <Button size="sm" onClick={() => setPaymentReturnRetry((value) => value + 1)}>Обновить статус</Button>
                  <Button size="sm" variant="secondary" href="/support/">Поддержка</Button>
                </>
              ) : null}
            </div>
          </div>
        </GroupedSection>
      ) : null}

      <GroupedSection title="Оформление">
        <div className="p-4">
          <button
            id="checkout-form"
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
            {paymentMethods.map((option) => {
              const selected = option.code === paymentMethod;
              return (
                <Chip
                  key={option.code}
                  active={selected}
                  disabled={!option.available}
                  onClick={() => setPaymentMethod(option.code as PaymentMethodChoice)}
                  className="min-h-[60px] justify-start rounded-control px-3 py-2.5 text-left disabled:cursor-not-allowed disabled:opacity-55"
                >
                  <span className="flex min-w-0 flex-col gap-0.5">
                    <span className="text-sm font-semibold text-ink">{option.label}</span>
                    <span className="line-clamp-2 text-xs leading-4 font-normal text-ink-soft">
                      {option.available ? option.hint : "Временно недоступно"}
                    </span>
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
            {promoCode ? <p className={cn("text-sm", offerPreview?.valid ? "text-ok-text" : "text-warn-text")}>{offerPreviewPending ? "Проверяем промокод на сервере…" : offerMessage}</p> : null}
          </div>
        </details>

        <div className="space-y-3 p-4">
          <div className="rounded-control border border-line bg-canvas-alt px-4 py-3">
            <div className="flex items-end justify-between gap-3 text-ink">
              <span className="font-semibold">Итоговая сумма</span>
              <strong className="font-display text-2xl leading-none">{offerPreviewPending || !previewMatchesPlan ? "—" : `${finalAmount} ₽`}</strong>
            </div>
            {offerPreview?.valid && finalAmount < baseAmount ? (
              <p className="mt-2 text-xs text-ink-soft">Базовая цена {baseAmount} ₽ · выгода {offerPreview.benefit_rub} ₽</p>
            ) : null}
            {offerPreview?.valid && formatServerDeadline(offerPreview.hold_expires_at) ? (
              <p className="mt-1 text-xs text-ink-soft">Сумма зафиксирована до {formatServerDeadline(offerPreview.hold_expires_at)}.</p>
            ) : null}
            {offerPreview?.terms_url ? (
              <a href={offerPreview.terms_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex text-xs font-semibold text-brand-strong underline-offset-4 hover:underline">
                Условия предложения
              </a>
            ) : null}
          </div>
          <Button onClick={startCheckout} loading={checkoutBusy} disabled={!checkoutReady} block>
            Продолжить к оплате
          </Button>
          <p className="text-center text-xs leading-5 text-ink-soft">Сумма и условия получены с сервера · разовая оплата · без автосписаний</p>
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
