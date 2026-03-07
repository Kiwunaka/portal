"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

import { getCopyText, getPortalPublicConfig, normalizePlanCode } from "../../lib/portal";

export type PlanOption = {
  code: string;
  label: string;
  amount_rub: number;
  days: number;
  device_limit: number;
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

type CreatePublicOrderResponse = {
  ok: boolean;
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
  ticket_exp: number;
  saved_at: number;
};

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const CHECKOUT_CACHE_PREFIX = "portal_checkout_payment_v1";

const FALLBACK_PLANS: PlanOption[] = [
  { code: "start_99", label: "Start 30 дней", amount_rub: 99, days: 30, device_limit: 1 },
  { code: "1_month", label: "Pro 1 месяц", amount_rub: 249, days: 30, device_limit: 5 },
  { code: "3_months", label: "Pro 3 месяца", amount_rub: 699, days: 91, device_limit: 5 },
  { code: "6_months", label: "Ultra 6 месяцев", amount_rub: 1199, days: 182, device_limit: 5 },
  { code: "9_months", label: "Ultra 9 месяцев", amount_rub: 1399, days: 273, device_limit: 5 },
  { code: "12_months", label: "Ultra 12 месяцев", amount_rub: 1499, days: 365, device_limit: 5 },
];

function candidateApiBases(): string[] {
  const out: string[] = [];
  if (config.apiBaseUrl) {
    out.push(config.apiBaseUrl.replace(/\/+$/, ""));
  }
  if (typeof window !== "undefined") {
    out.push(window.location.origin.replace(/\/+$/, ""));
  }
  out.push("https://portal-privacy.online");
  return Array.from(new Set(out.filter(Boolean)));
}

function decodeTicketPayload(token: string): { exp?: number; tg_id?: number; plan_code?: string; source?: string } | null {
  const raw = String(token || "").trim();
  if (!raw || !raw.includes(".")) {
    return null;
  }
  const encoded = raw.split(".", 1)[0] || "";
  if (!encoded) {
    return null;
  }
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
        <div className="checkout-kicker">Оплата в пару шагов</div>
        <div className="checkout-status-chip checkout-status-chip--fallback">Готовим страницу</div>
        <h1 className="checkout-title">
          <span>PORTAL</span> <span>Оплата</span>
        </h1>
        <p className="checkout-sub">Проверяем параметры ссылки и готовим экран оплаты.</p>
      </section>
      <section className="checkout-grid">
        <article className="glass-card">
          <div className="checkout-helper">Загрузка тарифов…</div>
        </article>
        <article className="glass-card checkout-sticky">
          <div className="checkout-helper">Сейчас покажем итог и кнопку оплаты.</div>
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
  const [selectedPlan, setSelectedPlan] = useState<string>(queryPlan);
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
    const sync = () => {
      setSecondsLeft(Math.max(0, ticketExp - Math.floor(Date.now() / 1000)));
    };
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
          if (!response.ok) {
            continue;
          }
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
          if (mapped.length && !cancelled) {
            setPlans(mapped);
            if (!mapped.some((item) => item.code === selectedPlan)) {
              setSelectedPlan(mapped[0].code);
            }
            return;
          }
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

  const activePlan = useMemo(
    () => plans.find((item) => item.code === selectedPlan) || plans[0] || FALLBACK_PLANS[0],
    [plans, selectedPlan],
  );

  const hasCheckoutTicket = Boolean(checkoutTicket);
  const fromBot = entrySource === "bot";
  const ticketExpired = hasCheckoutTicket && ticketExp > 0 && secondsLeft <= 0;
  const cacheKey = `${CHECKOUT_CACHE_PREFIX}:${checkoutTicket}:${selectedPlan}`;

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
    if (ticketExpired) {
      setStatusText("Ссылка на оплату уже истекла. Вернитесь в Telegram и откройте оплату заново.");
      return;
    }
    setBusy(true);
    setStatusText("");
    setBreakdown(null);

    for (const base of candidateApiBases()) {
      try {
        const response = await fetch(`${base}/api/payments/freekassa/orders/create-public`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
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
          ticket_exp: Number(ticketExp || 0),
          saved_at: Math.floor(Date.now() / 1000),
        };
        if (typeof window !== "undefined") {
          window.localStorage.setItem(cacheKey, JSON.stringify(cacheEntry));
        }
        setCachedPayment(cacheEntry);
        setStatusText("Ссылка готова. Переводим на страницу оплаты…");
        window.location.href = data.payment_url;
        return;
      } catch (error) {
        setStatusText(String((error as { message?: string })?.message || error || "Не удалось открыть оплату."));
      }
    }

    setBusy(false);
  }

  const heroStatus = hasCheckoutTicket ? "Персональная ссылка активна" : "Нужен переход через Telegram";
  const heroText = hasCheckoutTicket
    ? fromBot
      ? "Вы открыли персональную ссылку из Telegram. Выберите срок, проверьте сумму и переходите к оплате без лишних экранов."
      : "Выберите срок, проверьте итоговую сумму и переходите к оплате. После подтверждения доступ обновится автоматически."
    : "Эта страница работает как витрина. Для прямой оплаты нужна персональная ссылка из Telegram или кабинета.";

  return (
    <main className="checkout-shell">
      <section className="checkout-hero">
        <div className="checkout-kicker">{getCopyText("marketing.checkout.title", "Оплата в пару шагов")}</div>
        <div className={`checkout-status-chip ${hasCheckoutTicket ? "checkout-status-chip--ready" : "checkout-status-chip--fallback"}`}>
          {heroStatus}
        </div>
        <h1 className="checkout-title">
          <span>PORTAL</span> <span>{hasCheckoutTicket ? "Оплата" : "Продолжение через Telegram"}</span>
        </h1>
        <p className="checkout-sub">{heroText}</p>
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
                <span>{plan.amount_rub} ₽</span>
              </button>
            ))}
          </div>
          <div className="checkout-trust">
            <strong>Что будет дальше</strong>
            <ul className="checkout-trust-list">
              <li>Оплата откроется на стороне банка или платёжной страницы.</li>
              <li>После подтверждения доступ обновится автоматически.</li>
              <li>Если окно закрылось, можно вернуться сюда и продолжить оплату, пока ссылка ещё активна.</li>
            </ul>
          </div>
        </article>

        <article className="glass-card checkout-sticky">
          <h2>Итог</h2>
          <p className="checkout-note">
            {hasCheckoutTicket
              ? "План уже привязан к вашему профилю. После оплаты ничего заново настраивать не придётся."
              : "Прямую оплату мы открываем только по персональной ссылке, чтобы доступ сразу ушёл в нужный профиль."}
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
                  Итог: <strong>{breakdown.final.toFixed(0)} ₽</strong>
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
              if (!hasCheckoutTicket) {
                window.location.href = config.botUrl;
                return;
              }
              void createOrder();
            }}
            disabled={busy || ticketExpired}
            className="checkout-submit"
          >
            {busy
              ? "Готовим ссылку…"
              : ticketExpired
                ? "Ссылка истекла"
                : hasCheckoutTicket
                  ? getCopyText("marketing.checkout.primary_cta", "Перейти к оплате")
                  : "Продолжить в Telegram"}
          </button>

          {hasCheckoutTicket && cachedPayment?.payment_url && !ticketExpired ? (
            <button
              type="button"
              onClick={() => {
                window.location.href = cachedPayment.payment_url;
              }}
              className="checkout-secondary checkout-secondary-button"
            >
              Вернуться к оплате
            </button>
          ) : null}

          {hasCheckoutTicket ? (
            <p className="checkout-helper">
              {ticketExpired
                ? "Время этой ссылки закончилось. Вернитесь в Telegram и откройте оплату заново."
                : "Откроем безопасную страницу оплаты с уже выбранным тарифом."}
            </p>
          ) : (
            <div className="checkout-empty">
              <p>Чтобы открыть оплату без ошибок, продолжите путь из Telegram или кабинета. Там для вас создаётся персональная ссылка.</p>
              <div className="checkout-actions">
                <a href={config.botUrl} target="_blank" rel="noreferrer" className="checkout-secondary">
                  Продолжить в Telegram
                </a>
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="checkout-secondary">
                  Открыть кабинет
                </a>
              </div>
            </div>
          )}

          {statusText ? <p className="checkout-status">{statusText}</p> : null}
        </article>
      </section>
    </main>
  );
}
