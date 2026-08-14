"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Chip } from "../../components/ui/chip";
import { cn } from "../../components/utils";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { mintAcquisitionHandoff } from "../../lib/acquisition";
import { TELEGRAM_START_PROMISE } from "../../lib/seo-pages";
import {
  getCheckoutTariffPlans,
  getPricingPreviewDiscountPercent,
  getPokrovPublicConfig,
  getPromoSlotsCatalog,
  normalizePlanCode,
  tariffPlanAllowsDiscount,
} from "../../lib/pokrov";

const INPUT_CLASS =
  "min-h-11 w-full rounded-(--radius-control) border border-line bg-surface px-4 text-[0.9375rem] text-ink placeholder:text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-brand";

type PlanOption = {
  code: string;
  label: string;
  amount_rub: number;
  days: number;
  device_limit: number;
  marketing_note?: string;
  badge?: string | null;
};

type PublicCatalogResponse = {
  catalog_version: string;
  commerce_model: {
    primary_purchase_flow: string;
    primary_fulfillment_flow: string;
    managed_access_mode: string;
    raw_subscription_link_policy: string;
  };
  public_surface_policy: {
    acquisition_owner: string;
    pricing_owner: string;
    webapp_mode: string;
    public_platform_scope: string[];
  };
  plans: Array<{
    code: string;
    label: string;
    amount_rub: number;
    days: number;
    device_limit: number;
    badge?: string | null;
    is_active?: boolean;
  }>;
  free_tier: {
    plan_code: string;
    location_code: string;
    traffic_limit_gb: number;
    cycle_days: number;
    speed_limit_mbps: number;
    device_limit: number;
  };
  public_defaults: {
    routing_mode: string;
    public_platform_scope: string[];
    logical_location_count: number;
    logical_location_label: string;
    hidden_transport_order: string[];
  };
  promo_slots: {
    mode: string;
    fallback_behavior: string;
    slot_ids: string[];
  };
};

type AccessKeyStatusResponse = {
  key: string;
  exists: boolean;
  redeemed: boolean;
  redeemed_at?: string | null;
  issued_at?: string | null;
  days: number;
  device_limit: number;
  kind: string;
  plan?: {
    code: string;
    label: string;
  } | null;
};

type PaymentProviderState = {
  ok: boolean;
  providers: Array<{ code?: string; title?: string; label?: string }>;
  blocked?: boolean;
  blocked_reasons?: string[];
  blocked_reason_texts?: string[];
};

type PublicRubOrderResponse = {
  ok: boolean;
  provider?: string;
  order_id: string;
  payment_url?: string | null;
  status: string;
};

type Start99EligibilityResponse = {
  known: boolean;
  eligible: boolean;
  reason?: string | null;
  replacement_plan?: string;
  replacement_checkout_ticket?: string | null;
};

class CheckoutRequestError extends Error {
  constructor(
    message: string,
    readonly code = "checkout_failed",
    readonly replacementPlan = "",
  ) {
    super(message);
  }
}

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
const promoCatalog = getPromoSlotsCatalog();
type PaymentMethodChoice = "sbp" | "card";

const PAYMENT_METHOD_OPTIONS: Array<{
  code: PaymentMethodChoice;
  label: string;
  hint: string;
}> = [
  { code: "sbp", label: "СБП", hint: "Через приложение банка" },
  { code: "card", label: "Карта", hint: "Банковская карта" },
];

const PLAN_MONTHS: Record<string, number> = {
  "1_month": 1,
  "3_months": 3,
  "6_months": 6,
  "9_months": 9,
  "12_months": 12,
};

function deviceCountLabel(count: number): string {
  const normalized = Math.max(1, Math.trunc(count || 1));
  if (normalized === 1) return "1 устройство";
  if (normalized >= 2 && normalized <= 4) return `${normalized} устройства`;
  return `${normalized} устройств`;
}

function planSupportingText(plan: PlanOption, discountPercent: number): string {
  if (plan.code === "start_99") {
    return `Один раз · ${deviceCountLabel(plan.device_limit)}`;
  }
  const months = PLAN_MONTHS[plan.code] || 0;
  const discountedTotal = Math.max(1, Math.round(plan.amount_rub * (1 - discountPercent / 100)));
  const monthly = months > 0 ? Math.round(discountedTotal / months) : 0;
  const monthlyText = monthly > 0 ? `${monthly} ₽/мес · ` : "";
  return `${monthlyText}${deviceCountLabel(plan.device_limit)}`;
}

function planBadgeLabel(plan: PlanOption, compact = false): string | null {
  if (plan.code === "start_99") return compact ? "1 раз" : "Только один раз";
  if (plan.code === "1_month") return null;
  return plan.badge || null;
}

function validBuyerEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function fallbackPlans(): PlanOption[] {
  return getCheckoutTariffPlans()
    .map((plan) => ({
      code: plan.code,
      label: plan.label,
      amount_rub: Number(plan.amount_rub || 0),
      days: Number(plan.duration_days || 0),
      device_limit: Number(plan.device_limit || 1),
      marketing_note: plan.marketing_note,
      badge: plan.badge || null,
    }));
}

function candidateApiBases(): string[] {
  const bases = [
    config.apiBaseUrl.replace(/\/+$/, ""),
    typeof window !== "undefined" ? window.location.origin.replace(/\/+$/, "") : "",
    "https://api.pokrov.space",
  ];
  return Array.from(new Set(bases.filter(Boolean)));
}

async function fetchCatalog(): Promise<PublicCatalogResponse | null> {
  for (const base of candidateApiBases()) {
    try {
      const response = await fetch(`${base}/api/public/catalog`, { cache: "no-store" });
      if (!response.ok) continue;
      return (await response.json()) as PublicCatalogResponse;
    } catch {
      // Try next base.
    }
  }
  return null;
}

async function fetchAccessKeyStatus(key: string): Promise<AccessKeyStatusResponse> {
  let lastError = "Не удалось проверить ключ.";
  for (const base of candidateApiBases()) {
    try {
      const response = await fetch(`${base}/api/access-keys/status/${encodeURIComponent(key)}`, { cache: "no-store" });
      if (!response.ok) {
        lastError = await response.text() || `HTTP ${response.status}`;
        continue;
      }
      return (await response.json()) as AccessKeyStatusResponse;
    } catch (error) {
      lastError = String((error as { message?: string })?.message || error || lastError);
    }
  }
  throw new Error(lastError);
}

async function fetchPaymentProviderState(): Promise<PaymentProviderState | null> {
  for (const base of candidateApiBases()) {
    try {
      const response = await fetch(`${base}/api/payments/providers`, { cache: "no-store" });
      if (!response.ok) continue;
      return (await response.json()) as PaymentProviderState;
    } catch {
      // Try next base.
    }
  }
  return null;
}

async function createPublicRubOrder(payload: {
  provider: string;
  plan_code: string;
  buyer_email?: string;
  checkout_ticket?: string;
  promo_code?: string;
  currency?: string;
  payment_method?: PaymentMethodChoice;
  acquisition_handle?: string;
}): Promise<PublicRubOrderResponse> {
  let lastError = "Не удалось создать платеж.";
  for (const base of candidateApiBases()) {
    try {
      const response = await fetch(`${base}/api/payments/orders/create-public`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: payload.provider,
          plan_code: payload.plan_code,
          buyer_email: payload.buyer_email,
          checkout_ticket: payload.checkout_ticket,
          source: "site",
          promo_code: payload.promo_code || undefined,
          currency: payload.currency || "RUB",
          payment_method: payload.payment_method,
          acquisition_handle: payload.acquisition_handle,
        }),
      });
      if (!response.ok) {
        const raw = await response.text();
        try {
          const parsed = JSON.parse(raw) as {
            detail?: string | { code?: string; message?: string; replacement_plan?: string };
          };
          const detail = parsed.detail;
          if (typeof detail === "object" && detail) {
            throw new CheckoutRequestError(
              String(detail.message || `HTTP ${response.status}`),
              String(detail.code || "checkout_failed"),
              String(detail.replacement_plan || ""),
            );
          }
        } catch (error) {
          if (error instanceof CheckoutRequestError) throw error;
        }
        lastError = raw || `HTTP ${response.status}`;
        continue;
      }
      return (await response.json()) as PublicRubOrderResponse;
    } catch (error) {
      if (error instanceof CheckoutRequestError) throw error;
      lastError = String((error as { message?: string })?.message || error || lastError);
    }
  }
  throw new Error(lastError);
}

async function fetchStart99Eligibility(checkoutTicket: string): Promise<Start99EligibilityResponse | null> {
  if (!checkoutTicket) return null;
  for (const base of candidateApiBases()) {
    try {
      const response = await fetch(`${base}/api/payments/start-99-eligibility`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ checkout_ticket: checkoutTicket }),
      });
      if (!response.ok) continue;
      return (await response.json()) as Start99EligibilityResponse;
    } catch {
      // Try next base.
    }
  }
  return null;
}

function describePromoContent(contentId: string): { title: string; body: string } {
  if (contentId === "redeem_key") {
    return {
      title: "Код уже на руках? Не платите второй раз",
      body: "Проверьте его статус ниже и сразу активируйте в приложении или кабинете.",
    };
  }
  if (contentId === "telegram_bonus") {
    return {
      title: "Доведите бесплатный старт до 10 дней",
      body: TELEGRAM_START_PROMISE,
    };
  }
  return {
    title: "Платёж проверим",
    body: "Если платёж или активация задержались, поддержка проверит статус и поможет продолжить с того же места.",
  };
}

function formatPrice(price: number, discountPercent: number): string {
  const total = Math.max(1, Math.round(price * (1 - discountPercent / 100)));
  return `${total} ₽`;
}

function planDiscountPercent(planCode: string, promoCode: string): number {
  return tariffPlanAllowsDiscount(planCode) ? getPricingPreviewDiscountPercent(promoCode) : 0;
}

function buildRedeemHref(key: string): string {
  const url = new URL(config.webappUrl);
  url.pathname = "/redeem/";
  url.searchParams.set("key", key);
  return url.toString();
}

function formatPlatformScope(items: string[] | undefined): string {
  return (items?.length ? items : ["android", "windows"])
    .map((item) => {
      if (item === "android") return "Android";
      if (item === "windows") return "Windows";
      return item;
    })
    .join(" + ");
}

function maskAccessKey(key: string): string {
  const normalized = key.trim().toUpperCase();
  if (normalized.length <= 8) return "ключ скрыт";
  return `${normalized.slice(0, 6)}…${normalized.slice(-4)}`;
}

export function CheckoutLoadingFallback() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-5 px-4 pt-12 pb-16 text-center sm:px-6 sm:pt-16">
      <Chip tone="neutral">Тарифы и код активации</Chip>
      <h1 className="font-display text-[2rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.5rem]">
        Выберите срок и проверьте сумму
      </h1>
      <p className="max-w-lg text-base leading-relaxed text-ink-soft">
        Подгружаем тарифы, условия доступа и действия для покупки или активации кода.
      </p>
      <div className="mt-4 grid w-full gap-4 sm:grid-cols-2">
        <Card>
          <p className="text-[0.9375rem] text-ink-soft">Готовим тарифы и сумму…</p>
        </Card>
        <Card>
          <p className="text-[0.9375rem] text-ink-soft">Проверяем доступные способы оплаты…</p>
        </Card>
      </div>
    </div>
  );
}

export default function CheckoutClient() {
  const searchParams = useSearchParams();
  const queryPlan = normalizePlanCode(searchParams.get("plan"), "start_99");
  const checkoutTicket = (searchParams.get("checkout_ticket") || "").trim();
  const initialKeyInput = (searchParams.get("key") || "").trim().toUpperCase();
  const [catalog, setCatalog] = useState<PublicCatalogResponse | null>(null);
  const [plans, setPlans] = useState<PlanOption[]>(() => fallbackPlans());
  const [selectedPlan, setSelectedPlan] = useState(queryPlan);
  const [planPickerOpen, setPlanPickerOpen] = useState(false);
  const [promoCode, setPromoCode] = useState((searchParams.get("promo") || "").trim().toUpperCase());
  const [keyInput, setKeyInput] = useState(initialKeyInput);
  const [keyStatus, setKeyStatus] = useState<AccessKeyStatusResponse | null>(null);
  const [providerState, setProviderState] = useState<PaymentProviderState | null>(null);
  const [keyStatusText, setKeyStatusText] = useState("");
  const [checkoutStatusText, setCheckoutStatusText] = useState("");
  const [emailError, setEmailError] = useState("");
  const [keyBusy, setKeyBusy] = useState(initialKeyInput.length >= 6);
  const [buyerEmail, setBuyerEmail] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethodChoice>("sbp");
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [start99Eligibility, setStart99Eligibility] = useState<"unknown" | "eligible" | "ineligible">("unknown");
  const [activeCheckoutTicket, setActiveCheckoutTicket] = useState(checkoutTicket);

  // Fetch the catalog exactly once on mount: plan selection must not refetch.
  // Selection is reconciled through a functional update instead of a dep.
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const nextCatalog = await fetchCatalog();
      if (!nextCatalog || cancelled) {
        return;
      }
      const nextPlans = (nextCatalog.plans || [])
        .filter((plan) => plan?.is_active !== false && Boolean(plan?.code) && Number(plan?.amount_rub || 0) > 0)
        .map((plan) => ({
          code: String(plan.code || "").trim().toLowerCase(),
          label: String(plan.label || plan.code || "").trim(),
          amount_rub: Number(plan.amount_rub || 0),
          days: Number(plan.days || 0),
          device_limit: Number(plan.device_limit || 1),
          badge: plan.badge || null,
        }));
      setCatalog(nextCatalog);
      if (nextPlans.length) {
        setPlans(nextPlans);
        setSelectedPlan((current) =>
          nextPlans.some((plan) => plan.code === current) ? current : nextPlans[0].code,
        );
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!checkoutTicket) return;
    let cancelled = false;
    void fetchStart99Eligibility(checkoutTicket).then((payload) => {
      if (cancelled || !payload?.known) return;
      const next = payload.eligible ? "eligible" : "ineligible";
      setStart99Eligibility(next);
      if (!payload.eligible) {
        setSelectedPlan((current) => (current === "start_99" ? payload.replacement_plan || "1_month" : current));
        setActiveCheckoutTicket(String(payload.replacement_checkout_ticket || ""));
        setCheckoutStatusText("Приветственный месяц уже использован. Выбран обычный месяц за 239 ₽.");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [checkoutTicket]);

  useEffect(() => {
    let cancelled = false;

    void fetchPaymentProviderState().then((payload) => {
      if (!cancelled) {
        setProviderState(payload);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const normalized = keyInput.trim().toUpperCase();
    if (normalized.length < 6) {
      return;
    }
    let cancelled = false;
    void fetchAccessKeyStatus(normalized)
      .then((payload) => {
        if (!cancelled) {
          setKeyStatus(payload);
        }
      })
      .catch((error) => {
        if (!cancelled) {
          setKeyStatus(null);
          setKeyStatusText(String((error as { message?: string })?.message || error || "Не удалось проверить ключ."));
        }
      })
      .finally(() => {
        if (!cancelled) {
          setKeyBusy(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [keyInput]);

  const updateKeyInput = (rawValue: string): void => {
    const normalized = rawValue.toUpperCase().trim();
    setKeyInput(normalized);
    setKeyStatus(null);
    setKeyStatusText("");
    setKeyBusy(normalized.length >= 6);
  };

  const activePlan = useMemo(
    () => plans.find((plan) => plan.code === selectedPlan) || plans[0] || fallbackPlans()[0],
    [plans, selectedPlan],
  );

  const rawDiscountPercent = getPricingPreviewDiscountPercent(promoCode);
  const discountPercent = planDiscountPercent(activePlan.code, promoCode);
  const activePlanDiscountBlocked = rawDiscountPercent > 0 && !tariffPlanAllowsDiscount(activePlan.code);
  const redeemHref = keyStatus?.key ? buildRedeemHref(keyStatus.key) : buildRedeemHref(keyInput);
  const marketingPromoIds =
    promoCatalog.slots.find((slot) => slot.id === "marketing.checkout.contextual")?.allowed_content_ids || [];
  const checkoutReady = Boolean(providerState?.ok && !providerState?.blocked && providerState.providers?.length);
  const activeProviderCode = String(providerState?.providers?.[0]?.code || "").trim();
  const checkoutBlockedReasons = providerState?.blocked_reason_texts?.length
    ? providerState.blocked_reason_texts
    : providerState?.blocked_reasons || [];
  const activePlanMonths = PLAN_MONTHS[activePlan.code] || 0;
  const activePlanTotal = Math.max(1, Math.round(activePlan.amount_rub * (1 - discountPercent / 100)));
  const activePlanMonthly = activePlanMonths > 0 ? Math.round(activePlanTotal / activePlanMonths) : 0;

  const startPublicCheckout = async (): Promise<void> => {
    if (!checkoutReady || !activeProviderCode) return;
    const email = buyerEmail.trim().toLowerCase();
    if (!activeCheckoutTicket && !validBuyerEmail(email)) {
      setEmailError(email ? "Проверьте адрес email." : "Укажите email для чека и кода активации.");
      setCheckoutStatusText("");
      document.getElementById("checkout-buyer-email")?.focus();
      return;
    }
    setEmailError("");
    setCheckoutBusy(true);
    setCheckoutStatusText("");
    try {
      const acquisition = await mintAcquisitionHandoff("checkout");
      const order = await createPublicRubOrder({
        provider: activeProviderCode,
        plan_code: activePlan.code,
        buyer_email: activeCheckoutTicket ? undefined : email,
        checkout_ticket: activeCheckoutTicket || undefined,
        promo_code: discountPercent > 0 ? promoCode : undefined,
        currency: "RUB",
        payment_method: paymentMethod,
        acquisition_handle: acquisition?.handle,
      });
      const paymentUrl = String(order.payment_url || "").trim();
      if (!paymentUrl) {
        throw new Error("Платежная ссылка не получена.");
      }
      window.location.assign(paymentUrl);
    } catch (error) {
      if (error instanceof CheckoutRequestError && error.code === "start_99_already_used") {
        const eligibility = checkoutTicket ? await fetchStart99Eligibility(checkoutTicket) : null;
        setStart99Eligibility("ineligible");
        setSelectedPlan(eligibility?.replacement_plan || error.replacementPlan || "1_month");
        setActiveCheckoutTicket(String(eligibility?.replacement_checkout_ticket || ""));
        setPlanPickerOpen(false);
        setCheckoutStatusText("Приветственный месяц уже использован. Выбран обычный месяц за 239 ₽.");
      } else {
        setCheckoutStatusText(String((error as { message?: string })?.message || error || "Не удалось создать платеж."));
      }
    } finally {
      setCheckoutBusy(false);
    }
  };

  return (
    <div className="pb-16">
      <section className="mx-auto max-w-5xl px-4 pt-5 sm:px-6 sm:pt-9">
        <Card className="overflow-hidden p-0 shadow-medium">
          <div className="flex flex-col gap-4 border-b border-line bg-canvas-alt px-5 py-5 sm:flex-row sm:items-end sm:justify-between sm:px-8 sm:py-7">
            <div className="flex max-w-2xl flex-col items-start gap-2.5">
              <Chip tone="neutral">POKROV PREMIUM</Chip>
              <div>
                <h1 className="font-display text-[1.75rem] leading-[1.08] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.25rem]">
                  Оформление доступа
                </h1>
                <p className="mt-2 text-[0.875rem] leading-relaxed text-ink-soft sm:text-[0.9375rem]">
                  {activeCheckoutTicket
                    ? "Один платёж, без автосписаний. Покупка привязана к вашему аккаунту."
                    : "Один платёж, без автосписаний. Код и чек придут на email."}
                </p>
              </div>
            </div>
            <Chip tone={checkoutReady ? "brand" : "neutral"}>
              <span className={cn("size-1.5 rounded-full", checkoutReady ? "bg-status-green" : "bg-ink-muted")} />
              {checkoutReady ? "Оплата доступна" : "Оплата временно недоступна"}
            </Chip>
          </div>

          <div className="grid lg:grid-cols-[1.08fr_0.92fr]">
            <div className="flex flex-col gap-5 border-b border-line px-5 py-6 sm:px-8 sm:py-8 lg:border-r lg:border-b-0">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[0.75rem] font-semibold tracking-[0.08em] text-brand-strong uppercase">Шаг 1</p>
                  <h2 className="font-display text-[1.25rem] font-bold text-ink">Выберите срок</h2>
                </div>
                <span className="text-[0.75rem] text-ink-muted">Безлимитный трафик</span>
              </div>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setPlanPickerOpen((value) => !value)}
                  aria-expanded={planPickerOpen}
                  aria-controls="checkout-plan-picker"
                  className="flex min-h-11 w-full items-center justify-between gap-4 rounded-(--radius-control) border border-brand bg-brand-soft px-4 py-4 text-left shadow-soft transition-[border-color,background-color,box-shadow] duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                >
                  <span className="flex min-w-0 flex-col gap-1">
                    <span className="flex flex-wrap items-center gap-2">
                      <strong className="text-[1rem] font-semibold text-ink">{activePlan.label}</strong>
                      {planBadgeLabel(activePlan) ? (
                        <span className="rounded-full bg-surface px-2 py-0.5 text-[0.6875rem] font-semibold text-brand-strong">
                          {planBadgeLabel(activePlan)}
                        </span>
                      ) : null}
                    </span>
                    <span className="text-[0.75rem] text-ink-soft">{planSupportingText(activePlan, discountPercent)}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <strong className="text-[1.25rem] text-ink">{activePlanTotal} ₽</strong>
                    <span aria-hidden="true" className={cn("text-[0.75rem] text-brand-strong transition-transform duration-200", planPickerOpen ? "rotate-180" : "")}>▼</span>
                  </span>
                </button>

                {planPickerOpen ? (
                  <div id="checkout-plan-picker" className="mt-2 grid grid-cols-2 gap-2 rounded-(--radius-control) border border-line bg-surface p-2 shadow-medium sm:grid-cols-3">
                    {plans.map((plan) => {
                      const planPreviewDiscountPercent = planDiscountPercent(plan.code, promoCode);
                      const selected = selectedPlan === plan.code;
                      const disabled = plan.code === "start_99" && start99Eligibility === "ineligible";
                      return (
                        <button
                          key={plan.code}
                          type="button"
                          onClick={() => {
                            if (disabled) return;
                            setSelectedPlan(plan.code);
                            setPlanPickerOpen(false);
                          }}
                          disabled={disabled}
                          aria-pressed={selected}
                          className={cn(
                            "flex min-h-20 flex-col justify-between gap-2 rounded-(--radius-control) border px-3 py-2.5 text-left transition-[border-color,background-color] duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
                            disabled
                              ? "cursor-not-allowed border-line bg-canvas-alt opacity-60"
                              : selected
                                ? "border-brand bg-brand-soft"
                                : "border-line bg-surface hover:border-line-strong",
                          )}
                        >
                          <span className="flex w-full items-start justify-between gap-1">
                            <strong className="text-[0.8125rem] font-semibold text-ink">{plan.label}</strong>
                            {disabled ? (
                              <span className="text-[0.625rem] font-semibold text-ink-muted">Уже использован</span>
                            ) : planBadgeLabel(plan, true) ? (
                              <span className="text-[0.625rem] font-semibold text-brand-strong">{planBadgeLabel(plan, true)}</span>
                            ) : null}
                          </span>
                          <strong className="text-[0.9375rem] text-ink">{formatPrice(plan.amount_rub, planPreviewDiscountPercent)}</strong>
                        </button>
                      );
                    })}
                  </div>
                ) : null}
              </div>

              <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
                Сменить срок — нажмите на карточку. Приветственные 99 ₽ доступны один раз.
              </p>
            </div>

            <div className="flex flex-col gap-5 px-5 py-6 sm:px-8 sm:py-8">
              <div className="flex items-end justify-between gap-4 border-b border-line pb-4">
                <div>
                  <p className="text-[0.75rem] font-semibold tracking-[0.08em] text-brand-strong uppercase">Шаг 2</p>
                  <h2 className="font-display text-[1.25rem] font-bold text-ink">Оплата</h2>
                  <p className="mt-1 text-[0.75rem] text-ink-soft">
                    {activePlan.days} дней · {formatPlatformScope(catalog?.public_surface_policy?.public_platform_scope)}
                  </p>
                </div>
                <div className="text-right">
                  <strong className="block font-display text-[1.75rem] leading-none text-brand">{activePlanTotal} ₽</strong>
                  {activePlanMonthly > 0 ? <span className="mt-1 block text-[0.75rem] text-ink-soft">≈ {activePlanMonthly} ₽/мес</span> : null}
                </div>
              </div>

              {checkoutReady && !activeCheckoutTicket ? (
                <label className="flex flex-col gap-2 text-[0.875rem] font-medium text-ink" htmlFor="checkout-buyer-email">
                  Email для чека и кода
                  <input
                    id="checkout-buyer-email"
                    type="email"
                    name="email"
                    autoComplete="email"
                    inputMode="email"
                    value={buyerEmail}
                    onChange={(event) => {
                      setBuyerEmail(event.target.value);
                      setEmailError("");
                    }}
                    placeholder="email@example.com"
                    className={cn(INPUT_CLASS, "scroll-mt-24", emailError ? "border-status-red" : "")}
                    aria-invalid={Boolean(emailError)}
                    aria-describedby={emailError ? "checkout-email-error" : undefined}
                    aria-errormessage={emailError ? "checkout-email-error" : undefined}
                    required
                  />
                  {emailError ? (
                    <span id="checkout-email-error" role="alert" className="text-[0.8125rem] font-normal text-status-red">
                      {emailError}
                    </span>
                  ) : null}
                </label>
              ) : null}

              {checkoutReady ? (
                <div className="flex flex-col gap-2">
                  <span className="text-[0.875rem] font-medium text-ink">Способ оплаты</span>
                  <div className="grid grid-cols-2 gap-2">
                    {PAYMENT_METHOD_OPTIONS.map((option) => {
                      const selected = option.code === paymentMethod;
                      return (
                        <button
                          key={option.code}
                          type="button"
                          onClick={() => setPaymentMethod(option.code)}
                          className={cn(
                            "min-h-11 rounded-(--radius-control) border px-3 py-2 text-left transition-[border-color,background-color] duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
                            selected ? "border-brand bg-brand-soft" : "border-line bg-surface hover:border-line-strong",
                          )}
                          aria-pressed={selected}
                        >
                          <span className="block text-[0.875rem] font-semibold text-ink">{option.label}</span>
                          <span className="block text-[0.6875rem] text-ink-soft">{option.hint}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              {checkoutReady ? (
                <Button onClick={startPublicCheckout} disabled={checkoutBusy} size="lg" className="w-full">
                  Оплатить {activePlanTotal} ₽
                </Button>
              ) : (
                <span aria-disabled="true" className="inline-flex min-h-11 w-full items-center justify-center rounded-full bg-canvas-alt px-6 text-[0.9375rem] font-semibold text-ink-muted">
                  Оплата временно недоступна
                </span>
              )}

              <p className="-mt-2 text-center text-[0.75rem] leading-relaxed text-ink-soft">
                {activeCheckoutTicket
                  ? "Разовая оплата · без автосписаний · доступ в аккаунт"
                  : "Разовая оплата · без автосписаний · код на email"}
              </p>

              {checkoutStatusText ? (
                <p role="alert" className="rounded-(--radius-control) bg-canvas-alt px-4 py-3 text-[0.875rem] text-ink">
                  {checkoutStatusText}
                </p>
              ) : null}

              {!checkoutReady ? (
                <div className="flex flex-col gap-3">
                  <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
                    {checkoutBlockedReasons.length
                      ? "Оплата временно недоступна. Начните с приложения или напишите в поддержку — подскажем следующий шаг."
                      : "Проверяем доступность оплаты. Если кнопка не появится, начните с приложения или напишите в поддержку."}
                  </p>
                  <div className="grid grid-cols-2 gap-2">
                    <Button href={MARKETING_CANONICAL_PATHS.install} variant="secondary" className="w-full">
                      Скачать
                    </Button>
                    <Button href={config.botUrl} variant="secondary" target="_blank" rel="noreferrer" className="w-full">
                      Поддержка
                    </Button>
                  </div>
                </div>
              ) : null}

              <div className="flex flex-col divide-y divide-line border-y border-line">
                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Есть промокод?</summary>
                  <label className="mt-3 flex flex-col gap-2 text-[0.8125rem] text-ink-soft" htmlFor="checkout-promo-code">
                    Введите код — сумма обновится сразу
                    <input
                      id="checkout-promo-code"
                      value={promoCode}
                      onChange={(event) => setPromoCode(event.target.value.toUpperCase().trim())}
                      placeholder="Например: POKROV10"
                      className={INPUT_CLASS}
                    />
                    <span>
                      {activePlanDiscountBlocked
                        ? "На приветственные 99 ₽ дополнительная скидка не действует."
                        : discountPercent > 0
                        ? `Скидка ${discountPercent}% учтена в сумме.`
                        : ""}
                    </span>
                  </label>
                </details>

                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Что входит в доступ?</summary>
                  <ul className="mt-3 mb-0 flex list-none flex-col gap-2 p-0 text-[0.8125rem] leading-relaxed text-ink-soft">
                    <li>Безлимитный трафик без пакетов гигабайтов.</li>
                    <li>Android + Windows, до {activePlan.device_limit} устройств.</li>
                    <li>Поддержка поможет с оплатой и активацией.</li>
                  </ul>
                </details>

                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Уже есть код активации?</summary>
                  <div className="mt-3 flex flex-col gap-3">
                    <label className="sr-only" htmlFor="checkout-access-key">Код активации</label>
                    <input
                      id="checkout-access-key"
                      value={keyInput}
                      onChange={(event) => updateKeyInput(event.target.value)}
                      placeholder="POKROV-XXXX-XXXX"
                      className={INPUT_CLASS}
                    />
                    {keyBusy ? <p className="text-[0.8125rem] text-ink-soft">Проверяем статус кода…</p> : null}
                    {keyStatusText ? <p role="alert" className="text-[0.8125rem] text-status-red">{keyStatusText}</p> : null}
                    {keyStatus ? (
                      <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
                        {maskAccessKey(keyStatus.key)} · {keyStatus.plan?.label || `${keyStatus.days} дней`} · {keyStatus.redeemed ? "уже активирован" : "готов к активации"}
                      </p>
                    ) : null}
                    <Button href={redeemHref} variant="secondary" target="_blank" rel="noreferrer" className="w-full">
                      Активировать код
                    </Button>
                  </div>
                </details>

                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Перед оплатой — важное</summary>
                  <ul className="mt-3 mb-0 flex list-none flex-col gap-2 p-0 text-[0.8125rem] leading-relaxed text-ink-soft">
                    <li>99 ₽ доступны один раз — для первой успешной оплаты.</li>
                    {marketingPromoIds.map((contentId) => {
                      const content = describePromoContent(contentId);
                      return (
                        <li key={contentId}>
                          <strong className="text-ink">{content.title}</strong>: {content.body}
                        </li>
                      );
                    })}
                  </ul>
                  <a href={config.webappUrl} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-[0.8125rem] font-semibold text-brand-strong underline-offset-4 hover:underline">
                    Открыть кабинет
                  </a>
                </details>
              </div>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
