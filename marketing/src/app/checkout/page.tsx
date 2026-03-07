"use client";

import { getCopyText, getPortalPublicConfig, normalizePlanCode } from "../../lib/portal";
import { useEffect, useMemo, useState } from "react";

type PlanOption = {
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

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

const FALLBACK_PLANS: PlanOption[] = [
  { code: "start_99", label: "Start 30 дней", amount_rub: 99, days: 30, device_limit: 1 },
  { code: "1_month", label: "Pro 1 месяц", amount_rub: 249, days: 30, device_limit: 5 },
  { code: "3_months", label: "Pro 3 месяца", amount_rub: 699, days: 91, device_limit: 5 },
  { code: "6_months", label: "Ultra 6 месяцев", amount_rub: 1199, days: 182, device_limit: 5 },
  { code: "12_months", label: "Ultra 12 месяцев", amount_rub: 1499, days: 365, device_limit: 5 },
];

function candidateApiBases(): string[] {
  const out: string[] = [];
  if (config.apiBaseUrl) out.push(config.apiBaseUrl.replace(/\/+$/, ""));
  if (typeof window !== "undefined") out.push(window.location.origin.replace(/\/+$/, ""));
  out.push("https://portal-privacy.online");
  return Array.from(new Set(out.filter(Boolean)));
}

export default function CheckoutPage() {
  const [plans, setPlans] = useState<PlanOption[]>(FALLBACK_PLANS);
  const [selectedPlan, setSelectedPlan] = useState<string>("1_month");
  const [checkoutTicket, setCheckoutTicket] = useState("");
  const [promo, setPromo] = useState("");
  const [busy, setBusy] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [breakdown, setBreakdown] = useState<{ base: number; pct: number; final: number } | null>(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search || "");
    setSelectedPlan(normalizePlanCode(params.get("plan"), "1_month"));
    setCheckoutTicket((params.get("checkout_ticket") || "").trim());
    setPromo((params.get("promo") || "").trim().toUpperCase());
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadPlans = async () => {
      for (const base of candidateApiBases()) {
        try {
          const r = await fetch(`${base}/api/public/plans`, { cache: "no-store" });
          if (!r.ok) continue;
          const data = (await r.json()) as PublicPlansResponse;
          const mapped = (Array.isArray(data.plans) ? data.plans : [])
            .filter((x) => Boolean(x?.code) && Number(x?.amount_rub || 0) > 0 && x?.is_active !== false)
            .map((x) => ({
              code: String(x.code || "").trim().toLowerCase(),
              label: String(x.label || x.code || "").trim(),
              amount_rub: Number(x.amount_rub || 0),
              days: Math.max(1, Number(x.days || 30)),
              device_limit: Math.max(1, Number(x.device_limit || 1)),
            }));
          if (mapped.length && !cancelled) {
            setPlans(mapped);
            if (!mapped.some((item) => item.code === selectedPlan)) {
              setSelectedPlan(mapped[0].code);
            }
            return;
          }
        } catch {
          // Try the next base.
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

  async function createOrder(): Promise<void> {
    if (!activePlan?.code || !checkoutTicket) {
      setStatusText("Эта страница работает только по персональной ссылке из Telegram или кабинета.");
      return;
    }
    setBusy(true);
    setStatusText("");
    setBreakdown(null);
    try {
      for (const base of candidateApiBases()) {
        try {
          const r = await fetch(`${base}/api/payments/freekassa/orders/create-public`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              plan_code: activePlan.code,
              checkout_ticket: checkoutTicket,
              currency: "RUB",
            }),
          });
          if (!r.ok) {
            const txt = await r.text();
            throw new Error(txt || `HTTP ${r.status}`);
          }
          const data = (await r.json()) as CreatePublicOrderResponse;
          setBreakdown({
            base: Number(data.base_amount_rub ?? data.amount_rub ?? activePlan.amount_rub),
            pct: Number(data.discount_pct ?? 0),
            final: Number(data.amount_rub ?? activePlan.amount_rub),
          });
          if (data.payment_url) {
            setStatusText("Ссылка получена. Переводим на страницу оплаты...");
            window.location.href = data.payment_url;
            return;
          }
          throw new Error("Платёжная ссылка не получена.");
        } catch (error) {
          setStatusText(String((error as { message?: string })?.message || error || "Не удалось открыть оплату"));
        }
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="checkout-shell">
      <section className="checkout-hero">
        <div className="checkout-kicker">{getCopyText("marketing.checkout.title", "Оплата в пару шагов")}</div>
        <h1 className="checkout-title">
          <span>PORTAL</span>
          {" "}
          <span>{hasCheckoutTicket ? "Оплата" : "Продолжение через Telegram"}</span>
        </h1>
        <p className="checkout-sub">
          {getCopyText(
            "marketing.checkout.subtitle",
            "Здесь продолжается персональная оплата: сумма видна заранее, а после оплаты доступ обновится автоматически.",
          )}
        </p>
      </section>

      <section className="checkout-grid">
        <article className="glass-card">
          <h2>План</h2>
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
                  <p>{plan.days} дней • до {plan.device_limit} устройств</p>
                </div>
                <span>{plan.amount_rub} ₽</span>
              </button>
            ))}
          </div>
        </article>

        <article className="glass-card">
          <h2>Что будет дальше</h2>
          <p className="checkout-note">
              После подтверждения оплаты страница банка закроется, а доступ обновится автоматически. Если что-то пойдёт не так, продолжить можно через Telegram или кабинет.
          </p>
          <div className="checkout-summary">
            <p>План: <strong>{activePlan.label}</strong></p>
            <p>Сумма: <strong>{activePlan.amount_rub} ₽</strong></p>
            {promo ? <p>Промокод: <strong>{promo}</strong></p> : null}
            {breakdown ? (
              <>
                <p>База: {breakdown.base.toFixed(0)} ₽</p>
                <p>Скидка: {breakdown.pct}%</p>
                <p>Итог: <strong>{breakdown.final.toFixed(0)} ₽</strong></p>
              </>
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
            disabled={busy}
            className="checkout-submit"
          >
            {busy
              ? "Создаём заказ..."
              : hasCheckoutTicket
                ? getCopyText("marketing.checkout.primary_cta", "Перейти к оплате")
                : "Получить ссылку в Telegram"}
          </button>

          {!hasCheckoutTicket ? (
            <div className="checkout-empty">
              <p>Для прямой оплаты нужна персональная ссылка. Если вы открыли страницу вручную, продолжите через Telegram или кабинет.</p>
              <div className="checkout-actions">
                <a href={config.botUrl} target="_blank" rel="noreferrer" className="checkout-secondary">Получить персональную ссылку в Telegram</a>
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="checkout-secondary">Уже есть доступ? Открыть кабинет</a>
              </div>
            </div>
          ) : null}

          {statusText ? <p className="checkout-status">{statusText}</p> : null}
        </article>
      </section>
    </main>
  );
}
