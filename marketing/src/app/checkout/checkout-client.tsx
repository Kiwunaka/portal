"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { getCopyText, getPokrovPublicConfig, normalizePlanCode } from "../../lib/pokrov";

export type PlanOption = {
  code: string;
  label: string;
  amount_rub: number;
  days: number;
  device_limit: number;
};

type RubProviderOption = {
  code: string;
  label: string;
  accent?: string;
  checkout_hint?: string;
  supports_public?: boolean;
};

type PublicPlansResponse = {
  plans?: Array<{
    code: string;
    label: string;
    amount_rub: number;
    days: number;
    device_limit: number;
    is_active?: boolean;
  }>;
};

type RubProvidersResponse = {
  ok?: boolean;
  providers?: RubProviderOption[];
};

type CreatePublicOrderResponse = {
  ok: boolean;
  provider: string;
  provider_label?: string | null;
  order_id: string;
  payment_url?: string | null;
  amount_rub: number;
  currency: string;
  status: string;
  discount_applied?: boolean;
  base_amount_rub?: number | null;
  discount_pct?: number;
};

type CachedCheckoutPayment = {
  order_id: string;
  payment_url: string;
  plan_code: string;
  provider: string;
  provider_label: string;
  ticket_exp: number;
  saved_at: number;
};

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
const CHECKOUT_CACHE_PREFIX = "pokrov_checkout_payment_v2";

const FALLBACK_PLANS: PlanOption[] = [
  { code: "start_99", label: "Старт на 30 дней", amount_rub: 99, days: 30, device_limit: 1 },
  { code: "1_month", label: "1 месяц", amount_rub: 249, days: 30, device_limit: 5 },
  { code: "3_months", label: "3 месяца", amount_rub: 699, days: 91, device_limit: 5 },
  { code: "6_months", label: "6 месяцев", amount_rub: 1199, days: 182, device_limit: 5 },
  { code: "9_months", label: "9 месяцев", amount_rub: 1399, days: 273, device_limit: 5 },
  { code: "12_months", label: "12 месяцев", amount_rub: 1644, days: 365, device_limit: 5 },
];

function candidateApiBases(): string[] {
  const out: string[] = [];
  if (config.apiBaseUrl) out.push(config.apiBaseUrl.replace(/\/+$/, ""));
  if (typeof window !== "undefined") out.push(window.location.origin.replace(/\/+$/, ""));
  out.push("https://pokrov.space");
  return Array.from(new Set(out.filter(Boolean)));
}

function decodeTicketPayload(token: string): { exp?: number; tg_id?: number; plan_code?: string; source?: string } | null {
  const raw = String(token || "").trim();
  if (!raw || !raw.includes(".")) return null;
  const encoded = raw.split(".", 1)[0] || "";
  if (!encoded) return null;
  try {
    const padding = "=".repeat((4 - (encoded.length % 4)) % 4);
    const normalized = (encoded + padding).replace(/-/g, "+").replace(/_/g, "/");
    const decoded = typeof window !== "undefined" ? window.atob(normalized) : "";
    const bytes = Uint8Array.from(decoded, (char) => char.charCodeAt(0));
    const payloadText = new TextDecoder().decode(bytes);
    const parsed = JSON.parse(payloadText) as { exp?: number; tg_id?: number; plan_code?: string; source?: string };
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

function formatCountdown(secondsLeft: number): string {
  const safe = Math.max(0, Math.floor(secondsLeft));
  const minutes = Math.floor(safe / 60);
  const seconds = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function CheckoutLoadingFallback() {
  return (
    <main className="checkout-shell">
      <section className="checkout-hero">
        <div className="checkout-kicker">Продление и оплата</div>
        <div className="checkout-status-chip checkout-status-chip--fallback">Готовим страницу оплаты</div>
        <h1 className="checkout-title">
          <span>POKROV</span> <span>Персональный маршрут</span>
        </h1>
        <p className="checkout-sub">
          Проверяем персональную ссылку, тарифы и доступные способы оплаты. Если нужный маршрут временно недоступен, вернём вас в Telegram без лишних рисков.
        </p>
      </section>
      <section className="checkout-grid">
        <article className="glass-card">
          <div className="checkout-helper">Загружаем тарифы и сценарий оплаты…</div>
        </article>
        <article className="glass-card checkout-sticky">
          <div className="checkout-helper">Собираем итог и запасной маршрут, если понадобится поддержка…</div>
        </article>
      </section>
    </main>
  );
}

export default function CheckoutClient() {
  const searchParams = useSearchParams();
  const queryPlan = normalizePlanCode(searchParams.get("plan"), "1_month");
  const checkoutTicket = (searchParams.get("checkout_ticket") || "").trim();
  const promo = (searchParams.get("promo") || "").trim().toUpperCase();
  const entrySource = (searchParams.get("source") || "site").trim().toLowerCase() || "site";

  const [plans, setPlans] = useState<PlanOption[]>(FALLBACK_PLANS);
  const [providers, setProviders] = useState<RubProviderOption[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<string>(queryPlan);
  const [selectedProvider, setSelectedProvider] = useState<string>((searchParams.get("provider") || "").trim().toLowerCase());
  const [busy, setBusy] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [breakdown, setBreakdown] = useState<{ base: number; pct: number; final: number } | null>(null);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [cachedPayment, setCachedPayment] = useState<CachedCheckoutPayment | null>(null);

  const ticketPayload = useMemo(() => decodeTicketPayload(checkoutTicket), [checkoutTicket]);
  const ticketExp = Number(ticketPayload?.exp || 0);
  const ticketCountdownLabel = ticketExp > 0 ? formatCountdown(secondsLeft) : "";

  useEffect(() => {
    setSelectedPlan(queryPlan);
  }, [queryPlan]);

  useEffect(() => {
    if (!ticketExp) {
      setSecondsLeft(0);
      return;
    }
    const sync = () => setSecondsLeft(Math.max(0, ticketExp - Math.floor(Date.now() / 1000)));
    sync();
    const timer = window.setInterval(sync, 1000);
    return () => window.clearInterval(timer);
  }, [ticketExp]);

  useEffect(() => {
    let cancelled = false;
    const loadPlans = async () => {
      for (const base of candidateApiBases()) {
        try {
          const response = await fetch(`${base}/api/public/plans`, { cache: "no-store" });
          if (!response.ok) continue;
          const data = (await response.json()) as PublicPlansResponse;
          const mapped = (Array.isArray(data.plans) ? data.plans : [])
            .filter((item) => Boolean(item?.code) && Number(item?.amount_rub || 0) > 0 && item?.is_active !== false)
            .map((item) => ({
              code: String(item.code || "").trim().toLowerCase(),
              label: String(item.label || item.code || "").trim(),
              amount_rub: Number(item.amount_rub || 0),
              days: Math.max(1, Number(item.days || 30)),
              device_limit: Math.max(1, Number(item.device_limit || 1)),
            }));
          if (!mapped.length || cancelled) continue;
          setPlans(mapped);
          if (!mapped.some((item) => item.code === selectedPlan)) {
            setSelectedPlan(mapped[0].code);
          }
          return;
        } catch {
          // Try next base.
        }
      }
    };
    void loadPlans();
    return () => {
      cancelled = true;
    };
  }, [selectedPlan]);

  useEffect(() => {
    let cancelled = false;
    const loadProviders = async () => {
      for (const base of candidateApiBases()) {
        try {
          const response = await fetch(`${base}/api/payments/providers`, { cache: "no-store" });
          if (!response.ok) continue;
          const data = (await response.json()) as RubProvidersResponse;
          const mapped = (Array.isArray(data.providers) ? data.providers : []).filter((item) => item?.supports_public !== false && item?.code);
          if (cancelled) return;
          setProviders(mapped);
          const normalizedCurrent = String(selectedProvider || "").trim().toLowerCase();
          if (!mapped.some((item) => String(item.code || "").trim().toLowerCase() === normalizedCurrent)) {
            setSelectedProvider(String(mapped[0]?.code || ""));
          }
          return;
        } catch {
          // Try next base.
        }
      }
      if (!cancelled) {
        setProviders([]);
        setSelectedProvider("");
      }
    };
    void loadProviders();
    return () => {
      cancelled = true;
    };
  }, [selectedProvider]);

  const activePlan = useMemo(
    () => plans.find((item) => item.code === selectedPlan) || plans[0] || FALLBACK_PLANS[0],
    [plans, selectedPlan],
  );

  const activeProvider = useMemo(
    () =>
      providers.find(
        (item) => String(item.code || "").trim().toLowerCase() === String(selectedProvider || "").trim().toLowerCase(),
      ) ||
      providers[0] ||
      null,
    [providers, selectedProvider],
  );

  const hasCheckoutTicket = Boolean(checkoutTicket);
  const fromBot = entrySource === "bot";
  const ticketExpired = hasCheckoutTicket && ticketExp > 0 && secondsLeft <= 0;
  const cacheKey = `${CHECKOUT_CACHE_PREFIX}:${checkoutTicket}:${selectedPlan}:${activeProvider?.code || "none"}`;

  useEffect(() => {
    if (typeof window === "undefined" || !checkoutTicket) {
      setCachedPayment(null);
      return;
    }
    try {
      const raw = window.localStorage.getItem(cacheKey);
      if (!raw) {
        setCachedPayment(null);
        return;
      }
      const parsed = JSON.parse(raw) as CachedCheckoutPayment;
      const now = Math.floor(Date.now() / 1000);
      if (!parsed?.payment_url || !parsed?.order_id || Number(parsed.ticket_exp || 0) <= now) {
        window.localStorage.removeItem(cacheKey);
        setCachedPayment(null);
        return;
      }
      setCachedPayment(parsed);
    } catch {
      setCachedPayment(null);
    }
  }, [cacheKey, checkoutTicket]);

  async function createOrder(): Promise<void> {
    if (!activePlan?.code || !checkoutTicket) {
      setStatusText("Прямая оплата открывается только по персональной ссылке из Telegram или кабинета.");
      return;
    }
    if (!activeProvider?.code) {
      setStatusText("Сейчас нужный платёжный маршрут недоступен. Проще продолжить в Telegram и открыть новую персональную ссылку.");
      return;
    }
    if (ticketExpired) {
      setStatusText("Время этой ссылки закончилось. Вернитесь в Telegram и откройте оплату заново.");
      return;
    }

    setBusy(true);
    setStatusText("");
    setBreakdown(null);

    for (const base of candidateApiBases()) {
      try {
        const response = await fetch(`${base}/api/payments/orders/create-public`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: activeProvider.code,
            plan_code: activePlan.code,
            checkout_ticket: checkoutTicket,
            currency: "RUB",
          }),
        });
        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || `HTTP ${response.status}`);
        }
        const data = (await response.json()) as CreatePublicOrderResponse;
        setBreakdown({
          base: Number(data.base_amount_rub ?? data.amount_rub ?? activePlan.amount_rub),
          pct: Number(data.discount_pct ?? 0),
          final: Number(data.amount_rub ?? activePlan.amount_rub),
        });
        if (!data.payment_url) {
        throw new Error("Платёжная ссылка не получена.");
        }
        const cacheEntry: CachedCheckoutPayment = {
          order_id: String(data.order_id || ""),
          payment_url: String(data.payment_url || ""),
          plan_code: String(activePlan.code || ""),
          provider: String(data.provider || activeProvider.code || ""),
          provider_label: String(data.provider_label || activeProvider.label || activeProvider.code || ""),
          ticket_exp: Number(ticketExp || 0),
          saved_at: Math.floor(Date.now() / 1000),
        };
        if (typeof window !== "undefined") {
          window.localStorage.setItem(cacheKey, JSON.stringify(cacheEntry));
        }
        setCachedPayment(cacheEntry);
        setStatusText(`Ссылка готова. Переводим на страницу оплаты через ${cacheEntry.provider_label}…`);
        window.location.href = data.payment_url;
        return;
      } catch (error) {
        setStatusText(String((error as { message?: string })?.message || error || "Не удалось открыть оплату."));
      }
    }

    setBusy(false);
  }

  const heroStatus = hasCheckoutTicket ? "Персональная ссылка активна" : "Нужен личный вход";
  const heroText = hasCheckoutTicket
    ? fromBot
      ? "Вы открыли персональную ссылку из Telegram. Выберите срок, проверьте платёжный маршрут и переходите к оплате. Если что-то не отвечает, продолжайте в боте."
      : "Здесь можно завершить продление по персональной ссылке. Мы покажем только доступные платёжные маршруты и честный возврат в Telegram."
    : "Чтобы открыть оплату по-настоящему, сначала войдите в кабинет или получите персональную ссылку через Telegram. Без этого мы не будем отправлять вас на пустую кассу.";

  const primaryButtonLabel = busy
    ? "Готовим ссылку..."
    : ticketExpired
      ? "Ссылка истекла"
      : hasCheckoutTicket && activeProvider
        ? `Открыть оплату через ${activeProvider.label}`
        : "Открыть кабинет";

  return (
    <main className="checkout-shell">
      <section className="checkout-hero">
          <div className="checkout-kicker">{getCopyText("marketing.checkout.title", "Продление и оплата")}</div>
        <div className={`checkout-status-chip ${hasCheckoutTicket ? "checkout-status-chip--ready" : "checkout-status-chip--fallback"}`}>
          {heroStatus}
        </div>
        <h1 className="checkout-title">
          <span>POKROV VPN</span> <span>{hasCheckoutTicket ? "Продление доступа" : "Личный вход перед оплатой"}</span>
        </h1>
        <p className="checkout-sub">{heroText}</p>
      </section>

      <section className="checkout-grid">
        <article className="glass-card">
          <h2>{hasCheckoutTicket ? "Выберите срок" : "Что делать дальше"}</h2>

          {hasCheckoutTicket ? (
            <>
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
                    <span>{plan.amount_rub} ₽</span>
                  </button>
                ))}
              </div>

              {providers.length > 0 ? (
                <div className="checkout-provider-section">
                  <strong>Доступные способы оплаты</strong>
                  <div className="checkout-provider-list">
                    {providers.map((provider) => (
                      <button
                        key={provider.code}
                        type="button"
                        onClick={() => setSelectedProvider(provider.code)}
                        className={`checkout-provider ${provider.code === activeProvider?.code ? "checkout-provider--active" : ""}`}
                      >
                        <div>
                          <strong>{provider.label}</strong>
                          {provider.accent ? <p>{provider.accent}</p> : null}
                        </div>
                        {provider.checkout_hint ? <span>{provider.checkout_hint}</span> : null}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="checkout-provider-empty">
                  <strong>Платёжные маршруты временно недоступны</strong>
                  <p>Если нужный способ оплаты не появился, не тратьте время: вернитесь в Telegram и откройте новый персональный сценарий.</p>
                </div>
              )}
            </>
          ) : (
            <div className="checkout-empty">
              <p>Оплата открывается только после личного входа. Самый короткий путь сейчас такой: приложение или кабинет для входа, а Telegram остаётся как запасной сценарий и помощь.</p>
              <div className="checkout-actions">
                <a href={config.connectUrl} target="_blank" rel="noreferrer" className="checkout-secondary">
                  Открыть кабинет
                </a>
                <a href={config.botUrl} target="_blank" rel="noreferrer" className="checkout-secondary">
                  Продолжить в Telegram
                </a>
              </div>
            </div>
          )}

          <div className="checkout-trust">
                <strong>{hasCheckoutTicket ? "Что будет дальше" : "Почему нужен личный маршрут"}</strong>
            <ul className="checkout-trust-list">
              {hasCheckoutTicket ? (
                <>
                  <li>Откроется защищённая страница выбранного платёжного маршрута.</li>
                  <li>После подтверждения доступ обновится автоматически.</li>
                  <li>Если окно оплаты закроется, можно вернуться по сохранённой ссылке или продолжить в Telegram.</li>
                </>
              ) : (
                <>
                  <li>Кабинет или Telegram создают персональный сценарий именно для вашего профиля.</li>
                  <li>После этого мы показываем только рабочие способы оплаты и честную сумму.</li>
                  <li>Если маршрут оплаты временно недоступен, поддержка быстро переведёт вас на запасной путь.</li>
                </>
              )}
            </ul>
          </div>
        </article>

        <article className="glass-card checkout-sticky">
          <h2>{hasCheckoutTicket ? "Итог" : "Следующий шаг"}</h2>
          <p className="checkout-note">
            {hasCheckoutTicket
              ? "План уже привязан к вашему профилю. Мы не показываем лишние способы оплаты: только доступные платёжные маршруты и возврат в Telegram, если что-то пошло не так."
              : "Публичный checkout без личного входа не работает как касса. Сначала откройте кабинет или продолжите через Telegram, чтобы получить персональный маршрут."}
          </p>

          <div className="checkout-summary">
            <p>
              План: <strong>{activePlan.label}</strong>
            </p>
            <p>
              Срок: <strong>{activePlan.days} дней</strong>
            </p>
            <p>
              Устройства: <strong>до {activePlan.device_limit}</strong>
            </p>
            <p>
              Касса: <strong>{activeProvider?.label || "после личного входа"}</strong>
            </p>
            {promo ? (
              <p>
                Промокод: <strong>{promo}</strong>
              </p>
            ) : null}
            {breakdown ? (
              <div className="checkout-summary-breakdown">
                <p>База: {breakdown.base.toFixed(0)} ₽</p>
                <p>Скидка: {breakdown.pct}%</p>
                <p>
                  Итого: <strong>{breakdown.final.toFixed(0)} ₽</strong>
                </p>
              </div>
            ) : (
              <p className="checkout-summary-total">
                Сумма: <strong>{activePlan.amount_rub} ₽</strong>
              </p>
            )}
            {hasCheckoutTicket && ticketExp > 0 ? (
              <p className="checkout-summary-total">
                Ссылка активна ещё: <strong>{ticketCountdownLabel}</strong>
              </p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={() => {
              if (!hasCheckoutTicket || !activeProvider) {
                window.location.href = config.connectUrl;
                return;
              }
              void createOrder();
            }}
            disabled={busy || ticketExpired}
            className="checkout-submit"
          >
            {primaryButtonLabel}
          </button>

          <a href={config.botUrl} target="_blank" rel="noreferrer" className="checkout-secondary checkout-secondary-button">
            Продолжить в Telegram
          </a>

          {hasCheckoutTicket && cachedPayment?.payment_url && !ticketExpired ? (
            <button
              type="button"
              onClick={() => {
                window.location.href = cachedPayment.payment_url;
              }}
              className="checkout-secondary checkout-secondary-button"
            >
              Вернуться к оплате через {cachedPayment.provider_label}
            </button>
          ) : null}

          {hasCheckoutTicket ? (
            <p className="checkout-helper">
              {ticketExpired
                ? "Время этой ссылки закончилось. Вернитесь в Telegram и откройте оплату заново."
                : "Если способ оплаты не открывается или сумма выглядит странно, не продолжайте вслепую: вернитесь в Telegram или напишите в поддержку."}
            </p>
          ) : (
              <p className="checkout-helper">Сначала откройте кабинет или продолжите через Telegram, а продление уже запускайте из персонального сценария.</p>
          )}

          {statusText ? <p className="checkout-status">{statusText}</p> : null}
        </article>
      </section>
    </main>
  );
}
