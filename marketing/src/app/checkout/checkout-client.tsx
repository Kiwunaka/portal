"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { buildCheckoutHostHref, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
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
    title: "Поддержка рядом",
    body: "Если оплата или активация не прошли с первого раза, поддержка поможет спокойно продолжить.",
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

function formatRoutingMode(mode?: string): string {
  if (mode === "all_except_ru") return "Все, кроме RU";
  if (mode === "global") return "Весь трафик через POKROV";
  return "спокойный режим по умолчанию";
}

function formatPlatformScope(scope?: string[]): string {
  const values = scope?.length ? scope : ["android", "windows"];
  return values
    .map((item) => {
      if (item === "android") return "Android";
      if (item === "windows") return "Windows";
      return item;
    })
    .join(" + ");
}

function isTrialKey(status: AccessKeyStatusResponse | null): boolean {
  if (!status) return false;
  const kind = String(status.kind || "").toLowerCase();
  const planCode = String(status.plan?.code || "").toLowerCase();
  return kind.includes("trial") || planCode === "trial" || Number(status.days || 0) <= 5;
}

function normalizeAccessKeyError(message: string): { tone: "limit" | "unavailable"; text: string } {
  const raw = String(message || "").toLowerCase();
  if (raw.includes("429") || raw.includes("limit") || raw.includes("too many") || raw.includes("soft")) {
    return {
      tone: "limit",
      text:
        "Похоже, публичная проверка временно ограничена. Продолжите в приложении: там видно, доступна ли бесплатная проверка для этой установки.",
    };
  }
  return {
    tone: "unavailable",
    text:
      "Сейчас не удалось связаться с сервисом проверки ключей. Деньги на этом шаге не списываются; попробуйте позже или продолжите через приложение.",
  };
}

function describeTrialKeyState(options: {
  keyInput: string;
  keyBusy: boolean;
  keyStatus: AccessKeyStatusResponse | null;
  statusText: string;
}): { title: string; body: string; tone: "empty" | "loading" | "issued" | "continue" | "limit" | "unavailable" } {
  const { keyInput, keyBusy, keyStatus, statusText } = options;
  if (keyBusy) {
    return {
      title: "Проверяем ключ",
      body: "Смотрим, есть ли у ключа срок, план и свободная активация. Если сервис проверки не ответит, мы скажем об этом прямо.",
      tone: "loading",
    };
  }
  if (keyStatus?.exists && !keyStatus.redeemed) {
    return {
      title: isTrialKey(keyStatus) ? "Ключ на 5 дней готов" : "Ключ готов к активации",
      body: "Активируйте его в приложении или кабинете. После активации доступ привяжется к вашему аккаунту.",
      tone: "issued",
    };
  }
  if (keyStatus?.redeemed) {
    return {
      title: "Ключ уже активирован",
      body: "Продолжайте в приложении или кабинете: там видно текущий срок, устройства и следующий шаг.",
      tone: "continue",
    };
  }
  if (statusText) {
    const normalized = normalizeAccessKeyError(statusText);
    return {
      title: normalized.tone === "limit" ? "Проверка временно ограничена" : "Проверка недоступна",
      body: normalized.text,
      tone: normalized.tone,
    };
  }
  if (!keyInput) {
    return {
      title: "Ключа пока нет",
      body: "Бесплатные 5 дней начинаются в приложении на новой установке. Если ключ уже выдан после оплаты или поддержки, вставьте его сюда.",
      tone: "empty",
    };
  }
  return {
    title: "Введите ключ полностью",
    body: "Когда в поле будет полный ключ, мы проверим его статус и подскажем, куда продолжить.",
    tone: "empty",
  };
}

function describePaymentProviders(providers: PaymentProviderChoice[]): string {
  const publicProviders = providers.filter((provider) => provider.supports_public !== false);
  if (!publicProviders.length) {
    return "Доступные способы оплаты покажет платёжная страница, когда касса ответит.";
  }
  return publicProviders
    .map((provider) => {
      const accent = String(provider.accent || "").trim();
      return accent ? `${provider.label}: ${accent}` : provider.label;
    })
    .join("; ");
}

export function CheckoutLoadingFallback() {
  return (
    <main className="checkout-shell lp-route-shell lp-route-shell--checkout">
      <section className="checkout-hero">
        <div className="checkout-kicker">Спокойная касса</div>
        <div className="checkout-status-chip checkout-status-chip--fallback">Готовим варианты доступа</div>
        <h1 className="checkout-title">
          <span>POKROV</span>
          <span>Покупка и активация ключа доступа</span>
        </h1>
        <p className="checkout-sub">Подгружаем сроки, условия доступа и следующий шаг для оплаты или активации ключа.</p>
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
        <div className="checkout-kicker">Оплатить ключ {"->"} активировать {"->"} продолжить доступ</div>
        <div className="checkout-status-chip checkout-status-chip--ready">
          {catalog?.public_surface_policy?.pricing_owner === "marketing" ? "Оплата на сайте" : "Ключ доступа"}
        </div>
        <h1 className="checkout-title">
          <span>POKROV</span>
          <span>Ключ доступа без лишней настройки</span>
        </h1>
        <p className="checkout-sub">
          Выберите срок, оплатите ключ доступа и активируйте его в приложении или кабинете. Доступ продолжится в том же аккаунте, без ручной настройки на старте.
        </p>
      </section>

      <section className="lp-info-band checkout-info-band">
        <div className="lp-info-band__grid">
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Сначала попробовать</span>
            <h3>5 дней идут до покупки</h3>
            <p>Первый шаг остаётся за приложением: вы проверяете POKROV до оплаты.</p>
          </article>
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Потом оплатить</span>
            <h3>Оплата остаётся понятной</h3>
            <p>Вы покупаете ключ доступа, а не разбираетесь в сетевых терминах.</p>
          </article>
          <article className="lp-info-card">
            <span className="lp-info-card__eyebrow">Если нужна помощь</span>
            <h3>Кабинет и Telegram рядом</h3>
            <p>Если нужна помощь, рядом остаются кабинет, поддержка и Telegram.</p>
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
              <li>В приложении новая установка может получить 5 дней проверки без обязательной регистрации в Telegram.</li>
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
                <li>Ключ: {keyStatus.key}</li>
                <li>План: {keyStatus.plan?.label || `${keyStatus.days} дней`}</li>
                <li>Статус: {keyStatus.redeemed ? "уже активирован" : "готов к активации"}</li>
              </ul>
            ) : null}
          </div>
        </article>

        <article className="glass-card checkout-sticky">
          <h2>Итог</h2>
          <p className="checkout-note">
            Покупка проходит на платёжной странице POKROV и заканчивается ключом доступа. Гость активирует ключ сам, а пользователь с кабинетом может продолжить или продлить доступ сразу в своём аккаунте.
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
            Открыть платёжную страницу
          </a>

          <a href={redeemHref} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Активировать ключ в кабинете
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
            До открытия платёжной страницы деньги не списываются. Почтовый вход готовится; бесплатная проверка начинается из приложения на новой установке.
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
