"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Chip } from "../../components/ui/chip";
import { cn } from "../../components/utils";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
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
  buyer_email: string;
  promo_code?: string;
  currency?: string;
  payment_method?: PaymentMethodChoice;
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
          source: "site",
          promo_code: payload.promo_code || undefined,
          currency: payload.currency || "RUB",
          payment_method: payload.payment_method,
        }),
      });
      if (!response.ok) {
        lastError = (await response.text()) || `HTTP ${response.status}`;
        continue;
      }
      return (await response.json()) as PublicRubOrderResponse;
    } catch (error) {
      lastError = String((error as { message?: string })?.message || error || lastError);
    }
  }
  throw new Error(lastError);
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
  const initialKeyInput = (searchParams.get("key") || "").trim().toUpperCase();
  const [catalog, setCatalog] = useState<PublicCatalogResponse | null>(null);
  const [plans, setPlans] = useState<PlanOption[]>(() => fallbackPlans());
  const [selectedPlan, setSelectedPlan] = useState(queryPlan);
  const [promoCode, setPromoCode] = useState((searchParams.get("promo") || "").trim().toUpperCase());
  const [keyInput, setKeyInput] = useState(initialKeyInput);
  const [keyStatus, setKeyStatus] = useState<AccessKeyStatusResponse | null>(null);
  const [providerState, setProviderState] = useState<PaymentProviderState | null>(null);
  const [statusText, setStatusText] = useState("");
  const [keyBusy, setKeyBusy] = useState(initialKeyInput.length >= 6);
  const [buyerEmail, setBuyerEmail] = useState("");
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethodChoice>("sbp");
  const [checkoutBusy, setCheckoutBusy] = useState(false);

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
          setStatusText(String((error as { message?: string })?.message || error || "Не удалось проверить ключ."));
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
    setStatusText("");
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

  const startPublicCheckout = async (): Promise<void> => {
    if (!checkoutReady || !activeProviderCode) return;
    const email = buyerEmail.trim().toLowerCase();
    if (!email) {
      setStatusText("Укажите email для доставки ключа доступа после оплаты.");
      return;
    }
    setCheckoutBusy(true);
    setStatusText("");
    try {
      const order = await createPublicRubOrder({
        provider: activeProviderCode,
        plan_code: activePlan.code,
        buyer_email: email,
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
      setStatusText(String((error as { message?: string })?.message || error || "Не удалось создать платеж."));
    } finally {
      setCheckoutBusy(false);
    }
  };

  return (
    <div className="pb-16">
      <section className="mx-auto flex max-w-3xl flex-col items-center gap-4 px-4 pt-12 pb-10 text-center sm:px-6 sm:pt-16">
        <Chip tone="neutral">POKROV PREMIUM · безлимитный трафик от 99 ₽</Chip>
        <Chip tone={checkoutReady ? "brand" : "neutral"}>
          <span className={cn("size-1.5 rounded-full", checkoutReady ? "bg-status-green" : "bg-ink-muted")} />
          {checkoutReady ? "Оплата доступна" : "Оплата временно недоступна"}
        </Chip>
        <h1 className="font-display text-[2rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.5rem]">
          Безлимитный VPN от 99 ₽
        </h1>
        <p className="max-w-lg text-base leading-relaxed text-ink-soft">
          5 дней бесплатно без карты. Затем — безлимитный трафик, без тарифного ограничения скорости, до 5 устройств
          и ни одного автосписания.
        </p>
      </section>

      <section className="mx-auto mb-10 grid max-w-6xl gap-4 px-4 sm:px-6 md:grid-cols-3">
        <Card className="flex flex-col gap-1.5">
          <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Без счётчика гигабайтов</span>
          <h3 className="text-[1.0625rem] font-semibold text-ink">Безлимитный трафик</h3>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            На платном сроке трафик не заканчивается и не требует покупки дополнительных пакетов.
          </p>
        </Card>
        <Card className="flex flex-col gap-1.5">
          <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Без урезания по тарифу</span>
          <h3 className="text-[1.0625rem] font-semibold text-ink">Без тарифного ограничения*</h3>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            POKROV не режет скорость по тарифу. Фактическая скорость зависит от сети, устройства, локации и нагрузки.
          </p>
        </Card>
        <Card className="flex flex-col gap-1.5">
          <span className="text-[0.8125rem] font-semibold tracking-[0.08em] text-brand uppercase">Один аккаунт</span>
          <h3 className="text-[1.0625rem] font-semibold text-ink">До 5 устройств</h3>
          <p className="text-[0.9375rem] leading-relaxed text-ink-soft">
            Android и Windows в одном аккаунте. Точный лимит каждого тарифа виден до оплаты.
          </p>
        </Card>
      </section>

      <section className="mx-auto grid max-w-6xl items-start gap-6 px-4 sm:px-6 lg:grid-cols-[1.5fr_1fr]">
        <Card className="flex flex-col gap-7">
          <h2 className="font-display text-[1.375rem] font-bold text-ink">Выберите тариф</h2>
          <div className="flex flex-col gap-2.5">
            {plans.map((plan) => {
              const planPreviewDiscountPercent = planDiscountPercent(plan.code, promoCode);
              return (
                <button
                  key={plan.code}
                  type="button"
                  onClick={() => setSelectedPlan(plan.code)}
                  className={cn(
                    "flex min-h-11 items-center justify-between gap-4 rounded-(--radius-control) border px-4 py-3.5 text-left transition-[border-color,background-color,box-shadow] duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
                    selectedPlan === plan.code
                      ? "border-brand bg-brand-soft shadow-soft"
                      : "border-line bg-surface hover:border-line-strong",
                  )}
                >
                  <span className="flex flex-col gap-0.5">
                    <span className="flex items-center gap-2">
                      <strong className="text-[0.9375rem] font-semibold text-ink">{plan.label}</strong>
                      {plan.badge ? (
                        <span
                          className={cn(
                            "inline-flex shrink-0 items-center rounded-full px-2 py-0.5 text-[0.6875rem] font-semibold text-brand-strong",
                            selectedPlan === plan.code ? "bg-surface" : "bg-brand-soft",
                          )}
                        >
                          {plan.badge}
                        </span>
                      ) : null}
                    </span>
                    <span className="text-[0.8125rem] text-ink-soft">
                      {plan.days} дней • до {plan.device_limit} устройств
                    </span>
                  </span>
                  <span className="text-[1.0625rem] font-bold text-ink">{formatPrice(plan.amount_rub, planPreviewDiscountPercent)}</span>
                </button>
              );
            })}
          </div>

          <div className="flex flex-col gap-2.5">
            <strong className="text-[0.9375rem] font-semibold text-ink">Что вы получаете</strong>
            <ul className="m-0 flex list-none flex-col gap-2 p-0 text-[0.875rem] leading-relaxed text-ink-soft">
              <li>Безлимитный трафик на любом платном сроке.</li>
              <li>Без тарифного ограничения скорости; фактическая скорость зависит от условий подключения.</li>
              <li>До 5 устройств на основных тарифах; точный лимит выбранного плана виден до оплаты.</li>
              <li>5 дней бесплатного доступа на первом подтверждённом устройстве — без карты.</li>
              <li>Код после оплаты продлевает тот профиль, где вы его активируете: в приложении или кабинете.</li>
              <li>{TELEGRAM_START_PROMISE}</li>
            </ul>
          </div>

          <div className="flex flex-col gap-2.5">
            <strong className="text-[0.9375rem] font-semibold text-ink">Промокод</strong>
            <input
              value={promoCode}
              onChange={(event) => setPromoCode(event.target.value.toUpperCase().trim())}
              placeholder="Например: POKROV10"
              className={INPUT_CLASS}
            />
            <p className="text-[0.8125rem] text-ink-soft">
              {activePlanDiscountBlocked
                ? "Для приветственного тарифа 99 ₽ промокод не применяется."
                : discountPercent > 0
                ? `Скидка ${discountPercent}% уже заложена в итог для ${activePlan.label}.`
                : "Промокод меняет только итоговую сумму."}
            </p>
          </div>

          <div className="flex flex-col gap-2.5">
            <strong className="text-[0.9375rem] font-semibold text-ink">Уже есть код?</strong>
            <input
              value={keyInput}
              onChange={(event) => updateKeyInput(event.target.value)}
              placeholder="POKROV-XXXX-XXXX"
              className={INPUT_CLASS}
            />
            {keyBusy ? <p className="text-[0.8125rem] text-ink-soft">Проверяем статус кода…</p> : null}
            {keyStatus ? (
              <ul className="m-0 flex list-none flex-col gap-1.5 p-0 text-[0.875rem] text-ink-soft">
                <li>Код: {maskAccessKey(keyStatus.key)}</li>
                <li>План: {keyStatus.plan?.label || `${keyStatus.days} дней`}</li>
                <li>Статус: {keyStatus.redeemed ? "уже активирован" : "готов к активации"}</li>
              </ul>
            ) : null}
          </div>
        </Card>

        <Card className="flex flex-col gap-5 lg:sticky lg:top-24">
          <h2 className="font-display text-[1.375rem] font-bold text-ink">К оплате</h2>
          <p className="text-[0.875rem] leading-relaxed text-ink-soft">
            После разовой оплаты придёт код. Введите его в нужном профиле POKROV — в приложении или кабинете — и срок
            обновится без автосписаний.
          </p>

          <dl className="m-0 flex flex-col gap-2 border-y border-line py-4 text-[0.9375rem]">
            <div className="flex justify-between gap-3">
              <dt className="text-ink-soft">Тариф</dt>
              <dd className="m-0 font-semibold text-ink">{activePlan.label}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-ink-soft">Срок</dt>
              <dd className="m-0 font-semibold text-ink">{activePlan.days} дней</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-ink-soft">Устройства</dt>
              <dd className="m-0 font-semibold text-ink">до {activePlan.device_limit}</dd>
            </div>
            <div className="flex justify-between gap-3">
              <dt className="text-ink-soft">Платформы</dt>
              <dd className="m-0 font-semibold text-ink">{formatPlatformScope(catalog?.public_surface_policy?.public_platform_scope)}</dd>
            </div>
            <div className="mt-1 flex justify-between gap-3 text-[1.0625rem]">
              <dt className="font-semibold text-ink">Сумма</dt>
              <dd className="m-0 font-bold text-brand">{formatPrice(activePlan.amount_rub, discountPercent)}</dd>
            </div>
          </dl>

          {checkoutReady ? (
            <label className="flex flex-col gap-2 text-[0.875rem] font-medium text-ink" htmlFor="checkout-buyer-email">
              Email для чека и кода активации
              <input
                id="checkout-buyer-email"
                type="email"
                value={buyerEmail}
                onChange={(event) => setBuyerEmail(event.target.value)}
                placeholder="email@example.com"
                className={INPUT_CLASS}
                required
              />
            </label>
          ) : null}

          {checkoutReady ? (
            <div className="flex flex-col gap-2">
              <span className="text-[0.875rem] font-medium text-ink">Способ оплаты</span>
              <div className="grid gap-2 sm:grid-cols-2">
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
                      <span className="block text-[0.75rem] text-ink-soft">{option.hint}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : null}

          {checkoutReady ? (
            <Button onClick={startPublicCheckout} disabled={checkoutBusy} size="lg" className="w-full">
              Оплатить {formatPrice(activePlan.amount_rub, discountPercent)}
            </Button>
          ) : (
            <span
              aria-disabled="true"
              className="inline-flex min-h-11 w-full items-center justify-center rounded-full bg-canvas-alt px-6 text-[0.9375rem] font-semibold text-ink-muted"
            >
              Оплата временно недоступна
            </span>
          )}

          {!checkoutReady ? (
            <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
              {checkoutBlockedReasons.length
                ? "Оплата временно недоступна. Откройте кабинет или напишите в поддержку — подскажем следующий шаг."
                : "Проверяем доступность оплаты. Если кнопка не появится, продолжайте через поддержку или кабинет."}
            </p>
          ) : null}

          <div className="flex flex-col gap-2">
            <Button href={redeemHref} variant="secondary" target="_blank" rel="noreferrer" className="w-full">
              Активировать код в кабинете
            </Button>
            <Button href={config.webappUrl} variant="secondary" target="_blank" rel="noreferrer" className="w-full">
              Открыть кабинет
            </Button>
            <Button href={config.botUrl} variant="secondary" target="_blank" rel="noreferrer" className="w-full">
              Продолжить в Telegram
            </Button>
            <Button href={MARKETING_CANONICAL_PATHS.install} variant="ghost" className="w-full">
              Сначала забрать 5 дней бесплатно
            </Button>
          </div>

          <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
            Email нужен для чека и кода активации. Уже начали в приложении? Введите код именно там или откройте кабинет
            из приложения, чтобы продлить тот же профиль.
          </p>

          {statusText ? (
            <p className="rounded-(--radius-control) bg-canvas-alt px-4 py-3 text-[0.875rem] text-ink">{statusText}</p>
          ) : null}

          <div className="flex flex-col gap-2">
            <strong className="text-[0.9375rem] font-semibold text-ink">Перед оплатой — самое важное</strong>
            <ul className="m-0 flex list-none flex-col gap-2 p-0 text-[0.875rem] leading-relaxed text-ink-soft">
              {marketingPromoIds.map((contentId) => {
                const content = describePromoContent(contentId);
                return (
                  <li key={contentId}>
                    <strong className="text-ink">{content.title}</strong>: {content.body}
                  </li>
                );
              })}
            </ul>
          </div>
        </Card>
      </section>
    </div>
  );
}
