"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { mintAcquisitionHandoff } from "../../lib/acquisition";
import { TELEGRAM_START_PROMISE } from "../../lib/seo-pages";
import {
  COMMERCIAL_REVISION,
  assertCommercialPlanProjection,
  getCheckoutTariffPlans,
  getPokrovPublicConfig,
  getPromoSlotsCatalog,
  normalizePlanCode,
} from "../../lib/pokrov";


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
  commercial_revision: string;
  commercial_contract_sha256: string;
  effective_from: string;
  terms_revision: string;
  price_authority: string;
  promo_authority: string;
  legal_launch_ready: boolean;
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
  providers: Array<{
    code?: string;
    title?: string;
    label?: string;
    supported_plan_codes?: string[];
    payment_methods?: Array<{
      code: string;
      label: string;
      hint?: string;
      available: boolean;
      unavailable_reason?: string | null;
    }>;
  }>;
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
  payment_return_token: string;
};

type CommercialOfferPreviewResponse = {
  ok: boolean;
  valid: boolean;
  reason_code: string;
  blocking_reasons: string[];
  plan_code: string;
  currency: string;
  base_price_rub: number;
  final_price_rub: number;
  benefit_rub: number;
  benefit_percent: number;
  server_time: string;
  offer_ends_at?: string | null;
  hold_expires_at?: string | null;
  terms_url: string;
  commercial_revision: string;
  offer_token?: string | null;
};

type PaymentReturnStatusResponse = {
  ok: boolean;
  state: "processing" | "paid" | "failed" | "cancelled" | "manual_review" | "expired";
  reason_code: string;
  surface: "marketing" | "cabinet";
  provider: string;
  server_time: string;
  next_poll_seconds: number;
  terminal: boolean;
  support_required: boolean;
  can_retry: boolean;
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

export const config = getPokrovPublicConfig({
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_PUBLIC_API_BASE_URL,
  NEXT_PUBLIC_WEBAPP_URL: process.env.NEXT_PUBLIC_WEBAPP_URL,
  NEXT_PUBLIC_TELEGRAM_BOT_URL: process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL,
  NEXT_PUBLIC_HELP_BOT_URL: process.env.NEXT_PUBLIC_HELP_BOT_URL,
});
const promoCatalog = getPromoSlotsCatalog();
export type PaymentMethodChoice = "sbp" | "card";

const PAYMENT_METHOD_FALLBACKS: Array<{
  code: PaymentMethodChoice;
  label: string;
  hint: string;
}> = [
  { code: "sbp", label: "СБП", hint: "Через приложение банка" },
  { code: "card", label: "Карта", hint: "Банковская карта" },
];

const PAYMENT_RETURN_STORAGE_KEY = "pokrov.payment-return.v1";

export const OFFER_REASON_TEXT: Record<string, string> = {
  subject_missing: "Укажите корректный email для расчёта, чека и кода доступа.",
  start_99_already_used: "Приветственный месяц уже использован. Выберите обычный тариф.",
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

export const RETURN_STATE_TEXT: Record<PaymentReturnStatusResponse["state"], string> = {
  processing: "Платёж обрабатывается. Статус обновится автоматически.",
  paid: "Оплата подтверждена. Код доступа готовится на сервере.",
  failed: "Платёж не подтверждён. Можно повторить попытку.",
  cancelled: "Оплата отменена. Можно выбрать способ и попробовать снова.",
  manual_review: "Платёж требует ручной проверки. Напишите в поддержку.",
  expired: "Платёжная сессия истекла. Создайте новый платёж.",
};

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

export function planSupportingText(plan: PlanOption): string {
  if (plan.code === "start_99") {
    return `Один раз · ${deviceCountLabel(plan.device_limit)}`;
  }
  const months = PLAN_MONTHS[plan.code] || 0;
  const monthly = months > 0 ? Math.round(plan.amount_rub / months) : 0;
  const monthlyText = monthly > 0 ? `${monthly} ₽/мес · ` : "";
  return `${monthlyText}${deviceCountLabel(plan.device_limit)}`;
}

export function planBadgeLabel(plan: PlanOption, compact = false): string | null {
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

function checkoutReadSignal(signal?: AbortSignal): AbortSignal {
  const deadline = AbortSignal.timeout(8_000);
  return signal ? AbortSignal.any([signal, deadline]) : deadline;
}

async function fetchCatalog(): Promise<PublicCatalogResponse | null> {
  const signal = checkoutReadSignal();
  for (const base of candidateApiBases()) {
    if (signal.aborted) return null;
    try {
      const response = await fetch(`${base}/api/public/catalog`, { cache: "no-store", signal });
      if (!response.ok) continue;
      const payload = (await response.json()) as PublicCatalogResponse;
      const responseRevision = String(response.headers.get("X-Pokrov-Commercial-Revision") || "");
      if (
        payload.commercial_revision !== COMMERCIAL_REVISION ||
        responseRevision !== COMMERCIAL_REVISION ||
        payload.price_authority !== "server_commercial_contract" ||
        payload.promo_authority !== "server_offer_preview_only"
      ) {
        continue;
      }
      assertCommercialPlanProjection(payload.plans);
      return payload;
    } catch {
      // Try next base.
    }
  }
  return null;
}

async function fetchAccessKeyStatus(key: string, signal?: AbortSignal): Promise<AccessKeyStatusResponse> {
  const requestSignal = checkoutReadSignal(signal);
  for (const base of candidateApiBases()) {
    if (requestSignal.aborted) break;
    try {
      const response = await fetch(`${base}/api/access-keys/status/${encodeURIComponent(key)}`, { cache: "no-store", signal: requestSignal });
      if (!response.ok) continue;
      return (await response.json()) as AccessKeyStatusResponse;
    } catch {
      // Try another base within the same read deadline.
    }
  }
  throw new Error("Не удалось проверить ключ. Попробуйте ещё раз.");
}

async function fetchPaymentProviderState(): Promise<PaymentProviderState | null> {
  const signal = checkoutReadSignal();
  for (const base of candidateApiBases()) {
    if (signal.aborted) return null;
    try {
      const response = await fetch(`${base}/api/payments/providers`, { cache: "no-store", signal });
      if (!response.ok) continue;
      return (await response.json()) as PaymentProviderState;
    } catch {
      // Try next base.
    }
  }
  return null;
}

async function fetchCommercialOfferPreview(payload: {
  buyer_email?: string;
  plan_code: string;
  promo_code: string;
  checkout_ticket?: string;
  acquisition_handle?: string;
}, signal?: AbortSignal): Promise<CommercialOfferPreviewResponse | null> {
  const requestSignal = checkoutReadSignal(signal);
  for (const base of candidateApiBases()) {
    if (requestSignal.aborted) return null;
    try {
      const response = await fetch(`${base}/api/public/offers/preview`, {
        signal: requestSignal,
        method: "POST",
        credentials: "omit",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...payload, channel: "owned_web" }),
      });
      if (!response.ok) continue;
      const result = (await response.json()) as CommercialOfferPreviewResponse;
      if (result.commercial_revision !== COMMERCIAL_REVISION || result.plan_code !== payload.plan_code) continue;
      return result;
    } catch {
      // Try next base.
    }
  }
  return null;
}

async function fetchPaymentReturnStatus(returnToken: string, signal?: AbortSignal): Promise<PaymentReturnStatusResponse> {
  const requestSignal = checkoutReadSignal(signal);
  for (const base of candidateApiBases()) {
    if (requestSignal.aborted) break;
    try {
      const response = await fetch(`${base}/api/payments/orders/status`, {
        signal: requestSignal,
        method: "POST",
        credentials: "omit",
        cache: "no-store",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ return_token: returnToken }),
      });
      if (!response.ok) continue;
      return (await response.json()) as PaymentReturnStatusResponse;
    } catch {
      // Try another base within the same read deadline.
    }
  }
  throw new Error("Не удалось проверить статус платежа. Попробуйте ещё раз.");
}

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

async function createPublicRubOrder(payload: {
  intent_id?: string;
  provider: string;
  plan_code: string;
  buyer_email?: string;
  checkout_ticket?: string;
  promo_code?: string;
  currency?: string;
  payment_method?: PaymentMethodChoice;
  acquisition_handle?: string;
  offer_token?: string;
}): Promise<PublicRubOrderResponse> {
  let response: Response;
  try {
    response = await fetch(`${candidateApiBases()[0]}/api/payments/orders/create-public`, {
      signal: AbortSignal.timeout(15_000),
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...payload, source: "site", promo_code: payload.promo_code || undefined, currency: payload.currency || "RUB" }),
    });
    if (response.ok) return (await response.json()) as PublicRubOrderResponse;
  } catch {
    // A timeout can follow a committed order. Only an explicit same-intent
    // retry may recover it; switching API bases must not create another bill.
    throw new CheckoutRequestError("Ответ не получен. Повторите попытку, чтобы проверить этот же заказ.", "checkout_outcome_unknown", "");
  }
  let code = "checkout_failed";
  try {
    const body = await response.json() as { detail?: string | { code?: string } };
    code = typeof body.detail === "string" ? body.detail : String(body.detail?.code || code);
  } catch {
    // Provider and transport response bodies are never user-facing copy.
  }
  if (code === "start_99_already_used") {
    throw new CheckoutRequestError("Приветственный месяц уже использован.", code, "1_month");
  }
  throw new CheckoutRequestError("Не удалось продолжить оплату. Повторите попытку или напишите в поддержку.", code, "");
}

async function fetchStart99Eligibility(checkoutTicket: string): Promise<Start99EligibilityResponse | null> {
  if (!checkoutTicket) return null;
  const signal = checkoutReadSignal();
  for (const base of candidateApiBases()) {
    if (signal.aborted) return null;
    try {
      const response = await fetch(`${base}/api/payments/start-99-eligibility`, {
        signal,
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

export function describePromoContent(contentId: string): { title: string; body: string } {
  if (contentId === "redeem_key") {
    return {
      title: "Код уже на руках? Не платите второй раз",
      body: "Проверьте его статус ниже и сразу активируйте в приложении или кабинете.",
    };
  }
  if (contentId === "telegram_bonus") {
    return {
      title: "Ещё 5 дней после первой оплаты",
      body: TELEGRAM_START_PROMISE,
    };
  }
  return {
    title: "Платёж проверим",
    body: "Если платёж или активация задержались, поддержка проверит статус и поможет продолжить с того же места.",
  };
}

export function formatPrice(price: number): string {
  return `${Math.max(1, Math.round(price))} ₽`;
}

export function formatServerDeadline(value?: string | null): string {
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

function buildRedeemHref(key: string): string {
  const url = new URL(config.webappUrl);
  url.pathname = "/redeem/";
  url.searchParams.set("key", key);
  return url.toString();
}

export function formatPlatformScope(items: string[] | undefined): string {
  return (items?.length ? items : ["android", "windows"])
    .map((item) => {
      if (item === "android") return "Android";
      if (item === "windows") return "Windows";
      return item;
    })
    .join(" + ");
}

export function maskAccessKey(key: string): string {
  const normalized = key.trim().toUpperCase();
  if (normalized.length <= 8) return "ключ скрыт";
  return `${normalized.slice(0, 6)}…${normalized.slice(-4)}`;
}

export function useCheckoutController() {
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
  const [acquisitionHandle, setAcquisitionHandle] = useState("");
  const [quoteRefresh, setQuoteRefresh] = useState(0);
  const [offerQuote, setOfferQuote] = useState<{
    input: object;
    preview: CommercialOfferPreviewResponse | null;
    expiresAt: number;
    expired: boolean;
  } | null>(null);
  const orderInFlight = useRef(false);
  const checkoutIntent = useRef<{ key: string; id: string; acquisitionHandle: string; offerToken: string } | null>(null);
  const [recoveredReturnToken, setRecoveredReturnToken] = useState("");
  const [checkoutRecoveryKey, setCheckoutRecoveryKey] = useState("");
  const [infrastructureRetry, setInfrastructureRetry] = useState(0);
  const [paymentReturn, setPaymentReturn] = useState<PaymentReturnStatusResponse | null>(null);
  const [paymentReturnError, setPaymentReturnError] = useState("");

  // Fetch commerce state on mount or explicit read retry; plan selection does not refetch.
  // Selection is reconciled through a functional update instead of a dep.
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const [catalogResult, providerResult] = await Promise.allSettled([
        fetchCatalog(),
        fetchPaymentProviderState(),
      ]);
      if (cancelled) return;
      const nextCatalog = catalogResult.status === "fulfilled" ? catalogResult.value : null;
      if (nextCatalog) {
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
      }
      setProviderState(providerResult.status === "fulfilled" ? providerResult.value : null);

    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [infrastructureRetry]);

  useEffect(() => {
    let cancelled = false;
    void mintAcquisitionHandoff("checkout", undefined, config.apiBaseUrl).then((result) => {
      if (!cancelled) setAcquisitionHandle(String(result?.handle || ""));
    });
    return () => { cancelled = true; };
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
    if (typeof window === "undefined" || (!recoveredReturnToken && !searchParams.get("payment_return"))) return;
    const returnToken = recoveredReturnToken || readPaymentReturnToken();
    const cleanedUrl = new URL(window.location.href);
    cleanedUrl.searchParams.delete("payment_return");
    window.history.replaceState(window.history.state, "", `${cleanedUrl.pathname}${cleanedUrl.search}${cleanedUrl.hash}`);
    if (!returnToken) {
      queueMicrotask(() => {
        setPaymentReturnError("Не найден локальный идентификатор платежа. Напишите в поддержку, если деньги списались.");
      });
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
        }
      } catch (error) {
        if (!cancelled) {
          setPaymentReturnError(String((error as { message?: string })?.message || error || "Не удалось проверить статус платежа."));
        }
      }
    };
    void poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [searchParams, recoveredReturnToken]);

  useEffect(() => {
    const normalized = keyInput.trim().toUpperCase();
    if (normalized.length < 6) {
      return;
    }
    let cancelled = false;
    const controller = new AbortController();
    const timer = setTimeout(() => {
    void fetchAccessKeyStatus(normalized, controller.signal)
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
    }, 250);
    return () => {
      cancelled = true;
      clearTimeout(timer);
      controller.abort();
    };
  }, [keyInput]);

  const updateKeyInput = (rawValue: string): void => {
    const normalized = rawValue.toUpperCase().trim();
    setKeyInput(normalized);
    setKeyStatus(null);
    setKeyStatusText("");
    setKeyBusy(normalized.length >= 6);
  };

  const activeProviderCode = String(providerState?.providers?.[0]?.code || "").trim();
  const activeProvider = providerState?.providers?.find((provider) => provider.code === activeProviderCode);
  const supportedPlanCodes = activeProvider?.supported_plan_codes || [];
  const availablePlans = supportedPlanCodes.length
    ? plans.filter((plan) => supportedPlanCodes.includes(plan.code))
    : plans;
  const activePlan = availablePlans.find((plan) => plan.code === selectedPlan)
    || availablePlans[0]
    || fallbackPlans()[0];

  const redeemHref = keyStatus?.key ? buildRedeemHref(keyStatus.key) : buildRedeemHref(keyInput);
  const marketingPromoIds =
    promoCatalog.slots.find((slot) => slot.id === "marketing.checkout.contextual")?.allowed_content_ids || [];
  const paymentMethods = activeProvider?.payment_methods?.length
    ? activeProvider.payment_methods
    : PAYMENT_METHOD_FALLBACKS.map((method) => ({ ...method, available: true }));
  const requestedPaymentMethod = paymentMethods.find((method) => method.code === paymentMethod);
  const fallbackPaymentMethod = paymentMethods.find(
    (method) => method.available && (method.code === "sbp" || method.code === "card"),
  );
  const effectivePaymentMethod = requestedPaymentMethod?.available
    ? requestedPaymentMethod.code as PaymentMethodChoice
    : fallbackPaymentMethod?.code as PaymentMethodChoice | undefined;
  const selectedPaymentMethod = paymentMethods.find((method) => method.code === effectivePaymentMethod);
  const quotePlanCode = String(activePlan.code);
  const quotePaymentMethod = String(effectivePaymentMethod || "");
  // Object identity also fences A -> B -> A input changes before debounce.
  const quoteInput = useMemo(() => ({
    plan_code: quotePlanCode,
    promo_code: promoCode,
    checkout_ticket: activeCheckoutTicket || undefined,
    acquisition_handle: activeCheckoutTicket ? undefined : acquisitionHandle || undefined,
    provider: activeProviderCode,
    currency: "RUB",
    payment_method: quotePaymentMethod,
    buyer_email: activeCheckoutTicket ? "" : buyerEmail.trim().toLowerCase(),
    refresh: quoteRefresh,
  }), [quotePlanCode, promoCode, activeCheckoutTicket, acquisitionHandle, activeProviderCode, quotePaymentMethod, buyerEmail, quoteRefresh]);
  const quoteMatchesInput = offerQuote?.input === quoteInput;
  const offerPreview = quoteMatchesInput ? offerQuote.preview : null;
  const offerPreviewPending = !quoteMatchesInput;
  const previewMatchesPlan = Boolean(
    offerPreview?.ok && offerPreview.valid && offerPreview.offer_token
      && offerPreview.plan_code === activePlan.code
      && offerPreview.commercial_revision === COMMERCIAL_REVISION
      && offerPreview.currency === quoteInput.currency
      && Number.isSafeInteger(offerPreview.base_price_rub) && offerPreview.base_price_rub > 0
      && Number.isSafeInteger(offerPreview.final_price_rub) && offerPreview.final_price_rub > 0
      && !offerQuote?.expired,
  );
  const infrastructureReady = Boolean(catalog && providerState?.ok && !providerState?.blocked && activeProviderCode);
  const checkoutReady = Boolean(infrastructureReady && previewMatchesPlan && selectedPaymentMethod?.available);
  const currentCheckoutIntentKey = JSON.stringify([activeProviderCode, activePlan.code, activeCheckoutTicket, buyerEmail.trim().toLowerCase(), promoCode, effectivePaymentMethod]);
  const recoveringCheckout = checkoutRecoveryKey === currentCheckoutIntentKey;
  const checkoutBlockedReasons = providerState?.blocked_reason_texts?.length
    ? providerState.blocked_reason_texts
    : providerState?.blocked_reasons || [];
  const activePlanMonths = PLAN_MONTHS[activePlan.code] || 0;
  const activePlanBase = previewMatchesPlan ? Math.round(offerPreview?.base_price_rub || 0) : 0;
  const activePlanTotal = previewMatchesPlan ? Math.round(offerPreview?.final_price_rub || 0) : 0;
  const activePlanMonthly = activePlanMonths > 0 ? Math.round(activePlanTotal / activePlanMonths) : 0;
  const offerMessage = promoCode && offerPreview && !offerPreview.valid
    ? OFFER_REASON_TEXT[offerPreview.reason_code] || "Промокод сейчас недоступен."
    : promoCode && previewMatchesPlan
      ? OFFER_REASON_TEXT.ready
      : "";

  useEffect(() => {
    if (!catalog || !quoteInput.plan_code) return;
    let cancelled = false;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const requestedAt = performance.now();
      void fetchCommercialOfferPreview({
        buyer_email: quoteInput.buyer_email || undefined,
        plan_code: quoteInput.plan_code,
        promo_code: quoteInput.promo_code,
        checkout_ticket: quoteInput.checkout_ticket,
        acquisition_handle: quoteInput.acquisition_handle,
      }, controller.signal).then((preview) => {
        if (cancelled) return;
        const serverTime = Date.parse(preview?.server_time || "");
        const deadline = Math.min(
          Date.parse(preview?.hold_expires_at || ""),
          Date.parse(preview?.offer_ends_at || ""),
        );
        const lifetime = deadline - serverTime;
        // Subtract request time conservatively; workstation clock skew cannot
        // extend the server's absolute hold.
        const expiresAt = requestedAt + (Number.isFinite(lifetime) ? Math.max(0, lifetime) : 0);
        setOfferQuote({ input: quoteInput, preview, expiresAt, expired: expiresAt <= performance.now() });
      });
    }, 250);
    return () => {
      cancelled = true;
      controller.abort();
      clearTimeout(timer);
    };
  }, [catalog, quoteInput]);

  useEffect(() => {
    if (!offerQuote || offerQuote.expired) return;
    const timer = setTimeout(() => {
      setOfferQuote((current) => current === offerQuote ? { ...current, expired: true } : current);
    }, Math.max(0, offerQuote.expiresAt - performance.now()));
    return () => clearTimeout(timer);
  }, [offerQuote]);

  const startPublicCheckout = async (submittedAt: number): Promise<void> => {
    if (orderInFlight.current || !activeProviderCode || recoveredReturnToken
      || (!recoveringCheckout && (!checkoutReady || !offerQuote || offerQuote.expiresAt <= submittedAt))) return;
    const email = buyerEmail.trim().toLowerCase();
    if (!activeCheckoutTicket && !validBuyerEmail(email)) {
      setEmailError(email ? "Проверьте адрес email." : "Укажите email для чека и кода активации.");
      setCheckoutStatusText("");
      document.getElementById("checkout-buyer-email")?.focus();
      return;
    }
    setEmailError("");
    orderInFlight.current = true;
    setCheckoutBusy(true);
    setCheckoutStatusText("");
    try {
      const intentKey = currentCheckoutIntentKey;
      if (checkoutIntent.current?.key !== intentKey) {
        checkoutIntent.current = {
          key: intentKey, id: crypto.randomUUID(), acquisitionHandle,
          offerToken: String(offerPreview?.offer_token || ""),
        };
      }
      setCheckoutRecoveryKey(intentKey);
      const order = await createPublicRubOrder({
        intent_id: checkoutIntent.current.offerToken ? undefined : checkoutIntent.current.id,
        provider: activeProviderCode,
        plan_code: activePlan.code,
        buyer_email: activeCheckoutTicket ? undefined : email,
        checkout_ticket: activeCheckoutTicket || undefined,
        promo_code: promoCode || undefined,
        currency: "RUB",
        payment_method: effectivePaymentMethod,
        acquisition_handle: activeCheckoutTicket ? undefined : checkoutIntent.current.acquisitionHandle || undefined,
        offer_token: checkoutIntent.current.offerToken || undefined,
      });
      const paymentUrl = String(order.payment_url || "").trim();
      if (!storePaymentReturnToken(order.payment_return_token)) {
        throw new Error("Браузер не сохранил безопасный идентификатор платежа. Разрешите временное хранилище и повторите.");
      }
      if (!paymentUrl) {
        setRecoveredReturnToken(order.payment_return_token);
        setCheckoutStatusText("Заказ уже создан. Проверяем его статус. Если деньги списались, не оплачивайте повторно.");
        return;
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
      } else if (error instanceof CheckoutRequestError && ["checkout_quote_expired", "checkout_quote_changed", "checkout_quote_invalid"].includes(error.code)) {
        checkoutIntent.current = null;
        setCheckoutRecoveryKey("");
        setQuoteRefresh((current) => current + 1);
        setCheckoutStatusText("Расчёт изменился или истёк. Проверьте обновлённую сумму перед оплатой.");
      } else {
        setCheckoutStatusText(String((error as { message?: string })?.message || error || "Не удалось создать платеж."));
      }
    } finally {
      orderInFlight.current = false;
      setCheckoutBusy(false);
    }
  };

  return {
    activeCheckoutTicket,
    infrastructureReady,
    paymentReturn,
    paymentReturnError,
    setPlanPickerOpen,
    planPickerOpen,
    activePlan,
    offerPreviewPending,
    previewMatchesPlan,
    activePlanTotal,
    availablePlans,
    selectedPlan,
    start99Eligibility,
    setSelectedPlan,
    catalog,
    activePlanMonthly,
    offerPreview,
    activePlanBase,
    buyerEmail,
    setBuyerEmail,
    setEmailError,
    emailError,
    paymentMethods,
    effectivePaymentMethod,
    setPaymentMethod,
    startPublicCheckout,
    checkoutBusy,
    recoveredReturnToken,
    checkoutReady,
    recoveringCheckout,
    offerQuote,
    setQuoteRefresh,
    checkoutStatusText,
    checkoutBlockedReasons,
    setInfrastructureRetry,
    promoCode,
    setPromoCode,
    offerMessage,
    keyInput,
    updateKeyInput,
    keyBusy,
    keyStatusText,
    keyStatus,
    redeemHref,
    marketingPromoIds,
  };
}
