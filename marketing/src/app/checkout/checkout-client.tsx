"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { buildCheckoutHostHref, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import {
  getPricingPreviewDiscountPercent,
  getCopyText,
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

type PaymentProviderChoice = {
  code: string;
  label: string;
  accent?: string;
  checkout_hint?: string;
  supports_public?: boolean;
};

type PaymentProvidersResponse = {
  ok: boolean;
  providers: PaymentProviderChoice[];
  blocked?: boolean;
  blocked_reason_texts?: string[];
  telegram_fallback_available?: boolean;
};

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
const promoCatalog = getPromoSlotsCatalog();

function fallbackPlans(): PlanOption[] {
  return getTariffPlans()
    .filter((plan) => Boolean(plan.is_active))
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

async function fetchPaymentProviders(): Promise<PaymentProvidersResponse | null> {
  for (const base of candidateApiBases()) {
    try {
      const response = await fetch(`${base}/api/payments/providers`, { cache: "no-store" });
      if (!response.ok) continue;
      return (await response.json()) as PaymentProvidersResponse;
    } catch {
      // Try next base.
    }
  }
  return null;
}

function describePromoContent(contentId: string): { title: string; body: string } {
  if (contentId === "redeem_key") {
    return {
      title: "Уже есть ключ доступа?",
      body: "Проверьте его статус ниже и сразу переходите к активации в приложении или кабинете.",
    };
  }
  if (contentId === "telegram_bonus") {
    return {
      title: "Telegram даёт +10 дней",
      body: "После привязки Telegram можно забрать бонус, если вы подписаны на канал POKROV.",
    };
  }
  return {
    title: "Support и manual recovery",
    body: "Если hosted checkout или redeem path недоступен, support помогает вручную и фиксирует спорный платеж без показа raw link в обычном UX.",
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

function maskAccessKey(key: string): string {
  const normalized = key.trim().toUpperCase();
  if (normalized.length <= 8) return "ключ скрыт";
  return `${normalized.slice(0, 6)}…${normalized.slice(-4)}`;
}

export function CheckoutLoadingFallback() {
  return (
    <main className="checkout-shell lp-route-shell lp-route-shell--checkout">
      <section className="checkout-hero">
        <div className="checkout-kicker">Попробовать {"->"} купить ключ {"->"} активировать</div>
        <div className="checkout-status-chip checkout-status-chip--fallback">Готовим варианты доступа</div>
        <h1 className="checkout-title">
          <span>POKROV</span>
          <span>Ключ доступа без лишних шагов</span>
        </h1>
        <p className="checkout-sub">Подгружаем сроки, покупку ключа и честный следующий шаг для активации.</p>
      </section>
      <section className="checkout-grid">
        <article className="glass-card">
          <div className="checkout-helper">Готовим тарифы и понятный путь покупки…</div>
        </article>
        <article className="glass-card checkout-sticky">
          <div className="checkout-helper">Проверяем условия и доступные шаги…</div>
        </article>
      </section>
    </main>
  );
}

export default function CheckoutClient() {
  const searchParams = useSearchParams();
  const queryPlan = normalizePlanCode(searchParams.get("plan"), "1_month");
  const [catalog, setCatalog] = useState<PublicCatalogResponse | null>(null);
  const [plans, setPlans] = useState<PlanOption[]>(() => fallbackPlans());
  const [selectedPlan, setSelectedPlan] = useState(queryPlan);
  const [promoCode, setPromoCode] = useState((searchParams.get("promo") || "").trim().toUpperCase());
  const [keyInput, setKeyInput] = useState((searchParams.get("key") || "").trim().toUpperCase());
  const [keyStatus, setKeyStatus] = useState<AccessKeyStatusResponse | null>(null);
  const [statusText, setStatusText] = useState("");
  const [keyBusy, setKeyBusy] = useState(false);
  const [providers, setProviders] = useState<PaymentProviderChoice[]>([]);
  const [providersBlocked, setProvidersBlocked] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const nextCatalog = await fetchCatalog();
      if (!nextCatalog || cancelled) {
        return;
      }
      const nextPlans = (nextCatalog.plans || [])
        .filter((plan) => plan?.is_active !== false && Boolean(plan?.code))
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

    const load = async () => {
      const payload = await fetchPaymentProviders();
      if (!payload || cancelled) return;
      setProviders(Array.isArray(payload.providers) ? payload.providers : []);
      setProvidersBlocked(Boolean(payload.blocked || !payload.ok));
    };

    void load();
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
        setStatusText(String((error as { message?: string })?.message || error || "api unavailable"));
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
  const checkoutHref = buildCheckoutHostHref(activePlan.code, promoCode || undefined);
  const redeemHref = keyStatus?.key ? buildRedeemHref(keyStatus.key) : buildRedeemHref(keyInput);
  const trialKeyState = describeTrialKeyState({ keyInput, keyBusy, keyStatus, statusText });
  const marketingPromoIds =
    promoCatalog.slots.find((slot) => slot.id === "marketing.checkout.contextual")?.allowed_content_ids || [];

  return (
    <main className="checkout-shell lp-route-shell lp-route-shell--checkout">
      <section className="checkout-hero">
        <div className="checkout-kicker">Публичная бета: купить ключ {"->"} погасить {"->"} продолжить доступ</div>
        <div className="checkout-status-chip checkout-status-chip--ready">
          {catalog?.public_surface_policy?.pricing_owner === "marketing" ? "Оплата на сайте" : "Ключ доступа"}
        </div>
        <h1 className="checkout-title">
          <span>POKROV</span>
          <span>{getCopyText("marketing.checkout.title", "Ключ доступа для POKROV")}</span>
        </h1>
        <p className="checkout-sub">
          Эта страница ведёт к покупке activation key для бета-доступа и не показывает сырой персональный маршрут. После оплаты ключ погашается в приложении или в кабинете, а доступ продолжается в том же app-first аккаунте. Если провайдер оплаты вернул спорный или неясный статус, поддержка помогает вручную.
        </p>
        <div className="lp-hero-actions">
          <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
            {getCopyText("marketing.checkout.primary_cta", "Попробовать 5 дней")}
          </Link>
          <a href={checkoutHref} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
            {getCopyText("marketing.checkout.purchase_cta", "Купить ключ доступа")}
          </a>
        </div>
      </section>

      <section className="lp-info-band checkout-info-band">
        <div className="lp-info-band__grid">
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Сначала попробовать</span>
            <h3>5 дней идут до покупки</h3>
            <p>Новая установка может начать в приложении и проверить POKROV до оплаты.</p>
          </article>
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Потом оплатить</span>
            <h3>Касса остаётся тихой и понятной</h3>
            <p>Публичная оплата продаёт activation key для беты и не уводит в сложные технические сценарии.</p>
          </article>
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Если вы уже вошли</span>
            <h3>Продление идёт в тот же аккаунт</h3>
            <p>Кабинет честно продолжает текущий доступ, а не создаёт отдельную покупку в стороне.</p>
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
              <li>В приложении новая установка может получить 5 дней проверки без обязательного Telegram.</li>
              <li>
                После пробного срока остается бесплатный базовый режим: {catalog?.free_tier?.traffic_limit_gb || 5} ГБ на{" "}
                {catalog?.free_tier?.cycle_days || 30} дней.
              </li>
              <li>Режим по умолчанию: {formatRoutingMode(catalog?.public_defaults?.routing_mode)}.</li>
              <li>Telegram нужен для восстановления, бонуса +10 дней и связи с поддержкой.</li>
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
                : "Промокод меняет только сумму покупки ключа доступа."}
            </p>
          </div>

          <div className="checkout-trust">
            <strong>Ключ доступа или бесплатной проверки</strong>
            <div className="checkout-actions">
              <input
                value={keyInput}
                onChange={(event) => setKeyInput(event.target.value.toUpperCase().trim())}
                placeholder="POKROV-XXXX-XXXX"
                className="checkout-secondary"
              />
            </div>
            {keyBusy ? <p className="checkout-helper">Проверяем статус ключа доступа…</p> : null}
            <div className={`checkout-empty checkout-empty--${trialKeyState.tone}`}>
              <strong>{trialKeyState.title}</strong>
              <p>{trialKeyState.body}</p>
            </div>
            {keyStatus ? (
              <ul className="checkout-trust-list">
                <li>Ключ: {maskAccessKey(keyStatus.key)}</li>
                <li>План: {keyStatus.plan?.label || `${keyStatus.days} дней`}</li>
                <li>Статус: {keyStatus.redeemed ? "уже активирован" : "готов к активации"}</li>
              </ul>
            ) : null}
          </div>
        </article>

        <article className="glass-card checkout-sticky">
          <h2>Итог</h2>
          <p className="checkout-note">
            Покупка заканчивается activation key. Дальше тот же app-first аккаунт продолжает доступ как managed premium без повторной ручной настройки и без лишней суеты. На время беты спорные платежи разбираются через поддержку и ручную сверку.
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

          <a href={checkoutHref} target="_blank" rel="noreferrer" className="checkout-submit">
            {getCopyText("marketing.checkout.purchase_cta", "Купить ключ доступа")}
          </a>

          <a href={redeemHref} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Активировать ключ в кабинете
          </a>

          <a href={config.webappUrl} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Открыть кабинет
          </a>

          <Link href={MARKETING_CANONICAL_PATHS.install} className="checkout-secondary checkout-secondary-button">
            Скачать приложение
          </Link>

          <p className="checkout-helper">
            Email-вход на сайте ещё помечен как soon. Premium trial начинается из приложения на первом валидном устройстве, а купленный activation key можно погасить в приложении или кабинете.
          </p>

          {statusText ? <p className="checkout-status">{normalizeAccessKeyError(statusText).text}</p> : null}

          <div className="checkout-trust">
            <strong>Оплата и доверие</strong>
            <ul className="checkout-trust-list">
              <li>Платёж открывается отдельно на странице оплаты POKROV.</li>
              <li>{providersBlocked ? "Сейчас касса не показывает доступные способы оплаты." : describePaymentProviders(providers)}</li>
              <li>Ключ выдаётся после подтверждения платежа платёжным партнёром.</li>
            </ul>
          </div>

          <div className="checkout-trust">
            <strong>Полезно знать</strong>
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
