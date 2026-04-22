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

function describePromoContent(contentId: string): { title: string; body: string } {
  if (contentId === "redeem_key") {
    return {
      title: "Уже есть activation key?",
      body: "Проверьте его статус ниже и сразу переходите к redeem в приложении или cabinet continuation.",
    };
  }
  if (contentId === "telegram_bonus") {
    return {
      title: "Telegram остаётся вторичным бонусом",
      body: "После привязки аккаунта Telegram может дать +10 дней, но не заменяет app-first старт.",
    };
  }
  return {
    title: "Support и manual recovery",
    body: "Если hosted checkout или redeem path недоступен, support проводит в ручной recovery без показа raw link в обычном UX.",
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

export function CheckoutLoadingFallback() {
  return (
    <main className="checkout-shell">
      <section className="checkout-hero">
        <div className="checkout-kicker">Key-first checkout</div>
        <div className="checkout-status-chip checkout-status-chip--fallback">Собираем публичный catalog</div>
        <h1 className="checkout-title">
          <span>POKROV</span>
          <span>Activation key flow</span>
        </h1>
        <p className="checkout-sub">Подгружаем тарифы, free-tier facts и следующий шаг для покупки и redeem.</p>
      </section>
      <section className="checkout-grid">
        <article className="glass-card">
          <div className="checkout-helper">Готовим key-first pricing и checkout host…</div>
        </article>
        <article className="glass-card checkout-sticky">
          <div className="checkout-helper">Проверяем public defaults и fallback paths…</div>
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
  const checkoutHref = buildCheckoutHostHref(activePlan.code, promoCode || undefined);
  const redeemHref = keyStatus?.key ? buildRedeemHref(keyStatus.key) : buildRedeemHref(keyInput);
  const marketingPromoIds =
    promoCatalog.slots.find((slot) => slot.id === "marketing.checkout.contextual")?.allowed_content_ids || [];

  return (
    <main className="checkout-shell">
      <section className="checkout-hero">
        <div className="checkout-kicker">Buy key {"->"} redeem key {"->"} managed premium</div>
        <div className="checkout-status-chip checkout-status-chip--ready">
          {catalog?.public_surface_policy?.pricing_owner === "marketing" ? "Marketing owns pricing" : "Public checkout"}
        </div>
        <h1 className="checkout-title">
          <span>POKROV</span>
          <span>Публичный key-first checkout</span>
        </h1>
        <p className="checkout-sub">
          Эта страница продаёт activation key и не показывает raw subscription link. После покупки ключ погашается в приложении или cabinet continuation.
        </p>
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
              <li>В приложении первый валидный device получает 5 дней premium trial без обязательной регистрации.</li>
              <li>
                После trial доступ падает в {catalog?.free_tier?.location_code || "NL-free"} с лимитом{" "}
                {catalog?.free_tier?.traffic_limit_gb || 5} GB / {catalog?.free_tier?.cycle_days || 30} days.
              </li>
              <li>Публичный routing story остаётся {catalog?.public_defaults?.routing_mode || "all_except_ru"}.</li>
              <li>Telegram нужен для recovery, restore premium, бонуса +10 дней и support fallback.</li>
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
                : "Промокод меняет только итог покупки activation key и не открывает raw manual route."}
            </p>
          </div>

          <div className="checkout-trust">
            <strong>Уже есть key?</strong>
            <div className="checkout-actions">
              <input
                value={keyInput}
                onChange={(event) => setKeyInput(event.target.value.toUpperCase().trim())}
                placeholder="POKROV-XXXX-XXXX"
                className="checkout-secondary"
              />
            </div>
            {keyBusy ? <p className="checkout-helper">Проверяем статус activation key…</p> : null}
            {keyStatus ? (
              <ul className="checkout-trust-list">
                <li>Ключ: {keyStatus.key}</li>
                <li>План: {keyStatus.plan?.label || `${keyStatus.days} дней`}</li>
                <li>Статус: {keyStatus.redeemed ? "уже погашен" : "готов к redeem"}</li>
              </ul>
            ) : null}
          </div>
        </article>

        <article className="glass-card checkout-sticky">
          <h2>Итог</h2>
          <p className="checkout-note">
            Покупка заканчивается activation key. Дальше тот же app-first аккаунт продолжает доступ как managed premium без повторной ручной настройки.
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
              Публичный scope: <strong>{(catalog?.public_surface_policy?.public_platform_scope || ["android", "windows"]).join(" + ")}</strong>
            </p>
            <p className="checkout-summary-total">
              Сумма: <strong>{formatPrice(activePlan.amount_rub, discountPercent)}</strong>
            </p>
          </div>

          <a href={checkoutHref} target="_blank" rel="noreferrer" className="checkout-submit">
            Купить activation key
          </a>

          <a href={redeemHref} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Погасить key в cabinet
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
            Email signup на сайте даёт только Free Monthly. Premium trial начинается именно из приложения на первом валидном устройстве.
          </p>

          {statusText ? <p className="checkout-status">{statusText}</p> : null}

          <div className="checkout-trust">
            <strong>First-party promo slots</strong>
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
