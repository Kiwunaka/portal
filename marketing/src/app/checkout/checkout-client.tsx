"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import {
  getPricingPreviewDiscountPercent,
  getPokrovPublicConfig,
  getPromoSlotsCatalog,
  getTariffPlans,
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
const CHECKOUT_READY_PLAN_CODES = new Set(["start_99"]);

function fallbackPlans(): PlanOption[] {
  return getTariffPlans()
    .filter((plan) => Boolean(plan.is_active) && CHECKOUT_READY_PLAN_CODES.has(String(plan.code || "").trim().toLowerCase()))
    .slice()
    .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
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
      title: "Уже есть ключ доступа?",
      body: "Проверьте его статус ниже и переходите к погашению в приложении или кабинете.",
    };
  }
  if (contentId === "telegram_bonus") {
    return {
      title: "Telegram остаётся бонусом и запасным путем",
      body: "После привязки аккаунта Telegram может дать +10 дней, но первый старт остается в приложении.",
    };
  }
  return {
    title: "Поддержка при спорной оплате",
    body: "Если касса или погашение ключа недоступны, поддержка поможет вручную и не попросит открывать технические ссылки.",
  };
}

function formatPrice(price: number, discountPercent: number): string {
  const total = Math.max(1, Math.round(price * (1 - discountPercent / 100)));
  return `${total} ₽`;
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
    <main id="main-content" className="checkout-shell lp-route-shell lp-route-shell--checkout">
      <section className="checkout-hero">
        <div className="checkout-brand" aria-label="POKROV">
          <img src="/pokrov-logo.svg" alt="" aria-hidden="true" />
          <span>POKROV</span>
        </div>
        <div className="checkout-kicker">Спокойная касса</div>
        <div className="checkout-status-chip checkout-status-chip--fallback">Собираем публичный каталог</div>
        <h1 className="checkout-title">Маршрут оплаты через ключ доступа</h1>
        <p className="checkout-sub">Подгружаем тарифы, условия доступа и следующий шаг для покупки или погашения ключа.</p>
      </section>
      <section className="checkout-grid">
        <article className="glass-card">
          <div className="checkout-helper">Готовим тарифы и спокойный маршрут покупки…</div>
        </article>
        <article className="glass-card checkout-sticky">
          <div className="checkout-helper">Проверяем публичные условия и резервные шаги…</div>
        </article>
      </section>
    </main>
  );
}

export default function CheckoutClient() {
  const searchParams = useSearchParams();
  const queryPlan = normalizePlanCode(searchParams.get("plan"), "start_99");
  const [catalog, setCatalog] = useState<PublicCatalogResponse | null>(null);
  const [plans, setPlans] = useState<PlanOption[]>(() => fallbackPlans());
  const [selectedPlan, setSelectedPlan] = useState(queryPlan);
  const [promoCode, setPromoCode] = useState((searchParams.get("promo") || "").trim().toUpperCase());
  const [keyInput, setKeyInput] = useState((searchParams.get("key") || "").trim().toUpperCase());
  const [keyStatus, setKeyStatus] = useState<AccessKeyStatusResponse | null>(null);
  const [providerState, setProviderState] = useState<PaymentProviderState | null>(null);
  const [statusText, setStatusText] = useState("");
  const [keyBusy, setKeyBusy] = useState(false);
  const [buyerEmail, setBuyerEmail] = useState("");
  const [checkoutBusy, setCheckoutBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const nextCatalog = await fetchCatalog();
      if (!nextCatalog || cancelled) {
        return;
      }
      const nextPlans = (nextCatalog.plans || [])
        .filter((plan) => plan?.is_active !== false && Boolean(plan?.code) && CHECKOUT_READY_PLAN_CODES.has(String(plan.code || "").trim().toLowerCase()))
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
        if (!nextPlans.some((plan) => plan.code === selectedPlan)) {
          setSelectedPlan(nextPlans[0].code);
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, [selectedPlan]);

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
    if (!keyInput) {
      setKeyStatus(null);
      return;
    }
    const normalized = keyInput.trim().toUpperCase();
    if (normalized.length < 6) {
      return;
    }
    setKeyBusy(true);
    setStatusText("");
    void fetchAccessKeyStatus(normalized)
      .then((payload) => {
        setKeyStatus(payload);
      })
      .catch((error) => {
        setKeyStatus(null);
        setStatusText(String((error as { message?: string })?.message || error || "Не удалось проверить ключ."));
      })
      .finally(() => {
        setKeyBusy(false);
      });
  }, [keyInput]);

  const activePlan = useMemo(
    () => plans.find((plan) => plan.code === selectedPlan) || plans[0] || fallbackPlans()[0],
    [plans, selectedPlan],
  );

  const discountPercent = getPricingPreviewDiscountPercent(promoCode);
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
      setStatusText("Укажите email для доставки ключа после оплаты.");
      return;
    }
    setCheckoutBusy(true);
    setStatusText("");
    try {
      const order = await createPublicRubOrder({
        provider: activeProviderCode,
        plan_code: activePlan.code,
        buyer_email: email,
        promo_code: promoCode || undefined,
        currency: "RUB",
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
    <main id="main-content" className="checkout-shell lp-route-shell lp-route-shell--checkout">
      <section className="checkout-hero">
        <div className="checkout-brand" aria-label="POKROV">
          <img src="/pokrov-logo.svg" alt="" aria-hidden="true" />
          <span>POKROV</span>
        </div>
        <div className="checkout-kicker">Бета-контур: после пробного подключения выбрать срок и продолжить доступ</div>
        <div className={`checkout-status-chip ${checkoutReady ? "checkout-status-chip--ready" : "checkout-status-chip--fallback"}`}>
          {checkoutReady ? "Касса доступна" : "Оплата пока в ручной проверке"}
        </div>
        <h1 className="checkout-title">Спокойная оплата без технических ссылок</h1>
        <p className="checkout-sub">
          Эта страница помогает выбрать срок после личной проверки в приложении. После оплаты ключ доступа погашается в приложении или кабинете, а если касса временно недоступна, поддержка подскажет ручной следующий шаг.
        </p>
      </section>

      <section className="lp-info-band checkout-info-band">
        <div className="lp-info-band__grid">
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Сначала попробовать</span>
            <h3>Установка и пробный период идут до покупки</h3>
            <p>Первый шаг остаётся за приложением: 5 дней теста и первое подключение помогают понять продукт до оплаты.</p>
          </article>
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Потом оплатить</span>
            <h3>Касса остаётся тихой и понятной</h3>
            <p>Оплата должна выдавать ключ доступа для беты и не уводить в сложные технические сценарии.</p>
          </article>
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Если нужна помощь</span>
            <h3>Кабинет и Telegram рядом</h3>
            <p>Когда нужно восстановление или помощь, рядом остаются кабинет, поддержка и спокойный путь продолжения.</p>
          </article>
        </div>
      </section>

      <section className="checkout-grid">
        <article className="glass-card">
          <h2>Выберите срок</h2>
          <div className="checkout-plan-list">
            {plans.map((plan) => (
              <button
                key={plan.code}
                type="button"
                onClick={() => setSelectedPlan(plan.code)}
                className={`checkout-plan ${selectedPlan === plan.code ? "checkout-plan--active" : ""}`}
              >
                <div>
                  <strong>{plan.label}</strong>
                  <p>
                    {plan.days} дней • до {plan.device_limit} устройств
                  </p>
                </div>
                <span>{formatPrice(plan.amount_rub, discountPercent)}</span>
              </button>
            ))}
          </div>

          <div className="checkout-trust">
            <strong>Как это работает</strong>
            <ul className="checkout-trust-list">
              <li>В приложении первое валидное устройство получает 5 дней бесплатного доступа без обязательной регистрации.</li>
              <li>
                После бесплатного периода остается базовый режим: {catalog?.free_tier?.traffic_limit_gb || 5} ГБ на {catalog?.free_tier?.cycle_days || 30} дней.
              </li>
              <li>На первом экране остается понятный маршрут без ручных технических настроек.</li>
              <li>Telegram нужен для бонуса +10 дней, восстановления и связи с поддержкой.</li>
            </ul>
          </div>

          <div className="checkout-trust">
            <strong>Промокод</strong>
            <div className="checkout-actions">
              <input
                value={promoCode}
                onChange={(event) => setPromoCode(event.target.value.toUpperCase().trim())}
                placeholder="Например: POKROV10"
                className="checkout-secondary"
              />
            </div>
            <p className="checkout-helper">
              {discountPercent > 0
                ? `Скидка ${discountPercent}% уже заложена в итог для ${activePlan.label}.`
                : "Промокод меняет только итоговую сумму и не открывает ручные технические сценарии."}
            </p>
          </div>

          <div className="checkout-trust">
            <strong>Уже есть ключ?</strong>
            <div className="checkout-actions">
              <input
                value={keyInput}
                onChange={(event) => setKeyInput(event.target.value.toUpperCase().trim())}
                placeholder="POKROV-XXXX-XXXX"
                className="checkout-secondary"
              />
            </div>
            {keyBusy ? <p className="checkout-helper">Проверяем статус ключа…</p> : null}
            {keyStatus ? (
              <ul className="checkout-trust-list">
                <li>Ключ: {maskAccessKey(keyStatus.key)}</li>
                <li>План: {keyStatus.plan?.label || `${keyStatus.days} дней`}</li>
                <li>Статус: {keyStatus.redeemed ? "уже погашен" : "готов к погашению"}</li>
              </ul>
            ) : null}
          </div>
        </article>

        <article className="glass-card checkout-sticky">
          <h2>Итог</h2>
          <p className="checkout-note">
            Продление должно заканчиваться ключом доступа. Дальше тот же аккаунт продолжает работу без повторной ручной настройки. Пока касса не готова, спорные платежи и ручные заявки разбираются через поддержку.
          </p>

          <div className="checkout-summary">
            <p>
              Тариф: <strong>{activePlan.label}</strong>
            </p>
            <p>
              Срок: <strong>{activePlan.days} дней</strong>
            </p>
            <p>
              Устройства: <strong>до {activePlan.device_limit}</strong>
            </p>
            <p>
              Платформы: <strong>{formatPlatformScope(catalog?.public_surface_policy?.public_platform_scope)}</strong>
            </p>
            <p className="checkout-summary-total">
              Сумма: <strong>{formatPrice(activePlan.amount_rub, discountPercent)}</strong>
            </p>
          </div>

          {checkoutReady ? (
            <label className="checkout-helper" htmlFor="checkout-buyer-email">
              Email для доставки ключа
              <input
                id="checkout-buyer-email"
                type="email"
                value={buyerEmail}
                onChange={(event) => setBuyerEmail(event.target.value)}
                placeholder="email@example.com"
                className="checkout-secondary"
                required
              />
            </label>
          ) : null}

          {checkoutReady ? (
            <button type="button" onClick={startPublicCheckout} disabled={checkoutBusy} className="checkout-submit">
              Перейти к оплате
            </button>
          ) : (
            <span className="checkout-submit checkout-submit--disabled" aria-disabled="true">
              Оплата временно недоступна
            </span>
          )}

          {!checkoutReady ? (
            <p className="checkout-helper checkout-helper--warning">
              {checkoutBlockedReasons.length
                ? "Касса ждет включения провайдера оплаты. Пока продолжайте через поддержку или кабинет."
                : "Проверяем доступность кассы. Если кнопка не появится, продолжайте через поддержку или кабинет."}
            </p>
          ) : null}

          <a href={redeemHref} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Погасить ключ в кабинете
          </a>

          <a href={config.webappUrl} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Открыть кабинет
          </a>

          <a href={config.botUrl} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Продолжить в Telegram
          </a>

          <Link href={MARKETING_CANONICAL_PATHS.install} className="checkout-secondary checkout-secondary-button">
            Сначала установить приложение
          </Link>

          <p className="checkout-helper">
            Email нужен для доставки купленного ключа и может использоваться как дополнительный способ входа. Бесплатный период начинается из приложения на первом валидном устройстве, а купленный ключ можно погасить в приложении или кабинете.
          </p>

          {statusText ? <p className="checkout-status">{statusText}</p> : null}

          <div className="checkout-trust">
            <strong>Подсказки рядом с оплатой</strong>
            <ul className="checkout-trust-list">
              {marketingPromoIds.map((contentId) => {
                const content = describePromoContent(contentId);
                return (
                  <li key={contentId}>
                    <strong>{content.title}</strong>: {content.body}
                  </li>
                );
              })}
            </ul>
          </div>
        </article>
      </section>
    </main>
  );
}
