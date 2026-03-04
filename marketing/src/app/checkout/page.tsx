"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";

type PlanOption = {
  code: string;
  label: string;
  amount_rub: number;
  days: number;
  device_limit: number;
  badge?: string | null;
  node_policy?: string | null;
};

type PlanComparisonRow = {
  metric: string;
  start: string;
  pro: string;
  ultra: string;
};

type PublicPlansResponse = {
  plans?: Array<{
    code: string;
    label: string;
    amount_rub: number;
    days: number;
    device_limit: number;
    badge?: string | null;
    node_policy?: string | null;
    is_active?: boolean;
  }>;
  widget_enabled?: boolean;
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
  widget_enabled?: boolean;
};

type SocialProofResponse = {
  connected_users?: number;
  active_users?: number;
  paid_users?: number;
  updated_at?: string;
};

const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
const TG_BOT_URL = (process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/net4ebur_bot").trim();
const TG_CHANNEL_LINK = (process.env.NEXT_PUBLIC_TG_CHANNEL_LINK || "https://t.me/portal_privacy").trim();

const FK_WIDGET_API_KEY = (process.env.NEXT_PUBLIC_FK_WIDGET_API_KEY || "").trim();
const FK_WIDGET_SHOP_ID = (process.env.NEXT_PUBLIC_FK_WIDGET_SHOP_ID || "").trim();
const FK_WIDGET_LANG = (process.env.NEXT_PUBLIC_FK_WIDGET_LANG || "ru").trim();
const FK_WIDGET_THEME = (process.env.NEXT_PUBLIC_FK_WIDGET_THEME || "light").trim();

const FALLBACK_PLANS: PlanOption[] = [
  { code: "start_99", label: "Start", amount_rub: 99, days: 30, device_limit: 1, node_policy: "nl_only", badge: "Вход" },
  { code: "1_month", label: "Pro 1 месяц", amount_rub: 249, days: 30, device_limit: 5, node_policy: "paid_pool" },
  { code: "3_months", label: "Pro 3 месяца", amount_rub: 699, days: 91, device_limit: 5, node_policy: "paid_pool" },
  { code: "6_months", label: "Ultra 6 месяцев", amount_rub: 1199, days: 182, device_limit: 5, node_policy: "paid_pool", badge: "Популярный" },
  { code: "9_months", label: "Ultra 9 месяцев", amount_rub: 1399, days: 273, device_limit: 5, node_policy: "paid_pool" },
  { code: "12_months", label: "Ultra 12 месяцев", amount_rub: 1499, days: 365, device_limit: 5, node_policy: "paid_pool", badge: "Выгода" },
];

const PLAN_COMPARISON_ROWS: PlanComparisonRow[] = [
  { metric: "Устройства", start: "1", pro: "До 5", ultra: "До 5" },
  { metric: "Страны", start: "NL", pro: "Польша, Нидерланды, США, Италия", ultra: "Полный пул + приоритет" },
  { metric: "Маршрутизация", start: "VPN для базовых задач", pro: "Полный VPN-маршрут ежедневно", ultra: "VPN + приоритет" },
  { metric: "Скоростной профиль", start: "Базовый", pro: "Высокий", ultra: "Максимальный" },
  { metric: "Поддержка", start: "Стандартная", pro: "Быстрый Telegram-ответ", ultra: "Приоритет 24/7" },
];

function mapPlanToColumn(code: string): "start" | "pro" | "ultra" {
  const normalized = String(code || "").trim().toLowerCase();
  if (normalized === "start_99") return "start";
  if (normalized === "1_month" || normalized === "3_months") return "pro";
  return "ultra";
}

function candidateApiBases(): string[] {
  const out: string[] = [];
  if (API_BASE) out.push(API_BASE.replace(/\/+$/, ""));
  if (typeof window !== "undefined") out.push(window.location.origin.replace(/\/+$/, ""));
  out.push("https://portal-privacy.online");
  return Array.from(new Set(out.filter(Boolean)));
}

function firstPlanCode(plans: PlanOption[]): string {
  return plans.find((p) => p.code === "start_99")?.code || plans[0]?.code || "start_99";
}

function planNote(plan: PlanOption): string {
  const devices = `${Math.max(1, Number(plan.device_limit || 1))} устройство${Number(plan.device_limit) === 1 ? "" : "(й)"}`;
  const pool = String(plan.node_policy || "").toLowerCase() === "nl_only" ? "NL" : "все страны";
  const perPerson =
    Number(plan.days || 0) >= 365 && Number(plan.device_limit || 0) >= 5
      ? ` • ≈${Math.round(Number(plan.amount_rub || 0) / Math.max(1, Number(plan.device_limit || 1)))} ₽/чел`
      : "";
  return `${plan.days} дней • ${devices} • ${pool}${perPerson}`;
}

export default function CheckoutPage() {
  const sceneRef = useRef<HTMLDivElement | null>(null);

  const [plans, setPlans] = useState<PlanOption[]>(FALLBACK_PLANS);
  const [widgetEnabled, setWidgetEnabled] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>(firstPlanCode(FALLBACK_PLANS));
  const [checkoutTicket, setCheckoutTicket] = useState("");
  const [queryPromo, setQueryPromo] = useState("");
  const [queryCampaign, setQueryCampaign] = useState("");
  const [queryTgId, setQueryTgId] = useState("");
  const [isBusy, setIsBusy] = useState(false);
  const [statusText, setStatusText] = useState("");
  const [breakdown, setBreakdown] = useState<{ base: number; pct: number; final: number; applied: boolean } | null>(null);
  const [socialProof, setSocialProof] = useState<{ connected: number; active: number; paid: number; updatedAt: string }>({
    connected: 0,
    active: 0,
    paid: 0,
    updatedAt: "",
  });

  useEffect(() => {
    const params = new URLSearchParams(window.location.search || "");
    const plan = (params.get("plan") || "").trim().toLowerCase();
    const ticket = (params.get("checkout_ticket") || "").trim();
    const promo = (params.get("promo") || "").trim().toUpperCase();
    const campaign = (params.get("campaign") || "").trim();
    const tgId = (params.get("tg_id") || "").trim();

    if (plan) setSelectedPlan(plan);
    if (ticket) setCheckoutTicket(ticket);
    setQueryPromo(promo);
    setQueryCampaign(campaign);
    setQueryTgId(tgId);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadPlans = async () => {
      for (const base of candidateApiBases()) {
        try {
          const r = await fetch(`${base}/api/public/plans`, { cache: "no-store" });
          if (!r.ok) continue;
          const data = (await r.json()) as PublicPlansResponse;
          const rows = Array.isArray(data.plans) ? data.plans : [];
          const mapped = rows
            .filter((x) => Boolean(x && x.code) && Number(x.amount_rub || 0) > 0)
            .map((x) => ({
              code: String(x.code || "").trim().toLowerCase(),
              label: String(x.label || x.code || "").trim(),
              amount_rub: Number(x.amount_rub || 0),
              days: Math.max(1, Number(x.days || 30)),
              device_limit: Math.max(1, Number(x.device_limit || 1)),
              badge: x.badge || null,
              node_policy: x.node_policy || null,
            }))
            .sort((a, b) => a.amount_rub - b.amount_rub);
          if (!mapped.length) continue;
          if (!cancelled) {
            setPlans(mapped);
            setWidgetEnabled(Boolean(data.widget_enabled));
            if (!mapped.some((p) => p.code === selectedPlan)) {
              setSelectedPlan(firstPlanCode(mapped));
            }
          }
          return;
        } catch {
          // Try next base.
        }
      }
      if (!cancelled) {
        setPlans(FALLBACK_PLANS);
      }
    };
    void loadPlans();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(".checkout-kicker", { y: 22, opacity: 0 }, { y: 0, opacity: 1, duration: 0.55, ease: "power3.out" });
      gsap.fromTo(".checkout-title > span", { y: 70, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, stagger: 0.08, ease: "power4.out", delay: 0.06 });
      gsap.fromTo(".checkout-sub", { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, delay: 0.24 });
      gsap.fromTo(".glass-card", { y: 28, opacity: 0 }, { y: 0, opacity: 1, duration: 0.65, stagger: 0.1, delay: 0.2, ease: "power3.out" });
      gsap.to(".orb-a", { y: 30, x: -24, duration: 6, repeat: -1, yoyo: true, ease: "sine.inOut" });
      gsap.to(".orb-b", { y: -26, x: 18, duration: 7, repeat: -1, yoyo: true, ease: "sine.inOut" });
    }, sceneRef);
    return () => ctx.revert();
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadSocialProof = async () => {
      for (const base of candidateApiBases()) {
        try {
          const r = await fetch(`${base}/api/public/social-proof`, { cache: "no-store" });
          if (!r.ok) continue;
          const data = (await r.json()) as SocialProofResponse;
          const connected = Number(data.connected_users || 0);
          const active = Number(data.active_users || 0);
          const paid = Number(data.paid_users || 0);
          if (!cancelled) {
            setSocialProof({
              connected: Math.max(0, Math.round(connected)),
              active: Math.max(0, Math.round(active)),
              paid: Math.max(0, Math.round(paid)),
              updatedAt: String(data.updated_at || ""),
            });
          }
          return;
        } catch {
          // Try next base.
        }
      }
    };
    void loadSocialProof();
    return () => {
      cancelled = true;
    };
  }, []);

  const activePlan = useMemo(
    () => plans.find((p) => p.code === selectedPlan) || plans[0] || FALLBACK_PLANS[0],
    [plans, selectedPlan],
  );
  const activeColumn = useMemo(() => mapPlanToColumn(activePlan?.code || ""), [activePlan?.code]);

  const widgetSrc = useMemo(() => {
    if (!widgetEnabled || !FK_WIDGET_API_KEY || !FK_WIDGET_SHOP_ID) return "";
    const params = new URLSearchParams({
      type: "payment-window",
      lang: FK_WIDGET_LANG || "ru",
      theme: FK_WIDGET_THEME || "light",
      default_amount: String(Math.max(1, Number(activePlan?.amount_rub || 0))),
      api_key: FK_WIDGET_API_KEY,
      shopID: FK_WIDGET_SHOP_ID,
    });
    return `https://widgets.freekassa.net?${params.toString()}`;
  }, [activePlan?.amount_rub, widgetEnabled]);

  const botHref = useMemo(() => {
    const url = new URL(TG_BOT_URL, "https://t.me");
    if (queryPromo || queryCampaign) {
      const campaignPart = queryCampaign ? `campaign_${queryCampaign}` : "";
      const promoPart = queryPromo ? `promo_${queryPromo}` : "";
      const payload = [campaignPart, promoPart].filter(Boolean).join("__");
      if (payload) url.searchParams.set("start", payload);
    }
    return url.toString();
  }, [queryCampaign, queryPromo]);

  async function createOrder(): Promise<void> {
    if (!activePlan?.code || !checkoutTicket) return;
    setIsBusy(true);
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
          const baseAmount = Number(data.base_amount_rub ?? data.amount_rub ?? activePlan.amount_rub);
          const finalAmount = Number(data.amount_rub ?? activePlan.amount_rub);
          const pct = Number(data.discount_pct ?? 0);
          setBreakdown({
            base: baseAmount,
            pct,
            final: finalAmount,
            applied: Boolean(data.discount_applied),
          });
          setStatusText("Заказ создан. Переводим на страницу оплаты провайдера...");
          if (data.payment_url) {
            window.location.href = data.payment_url;
            return;
          }
          throw new Error("Платёжная ссылка не получена. Попробуйте ещё раз или откройте поддержку.");
        } catch (err) {
          const msg = String((err as { message?: string })?.message || err);
          setStatusText(msg);
        }
      }
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <main className="checkout-shell" ref={sceneRef}>
      <section className="checkout-hero">
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="checkout-kicker">[SAFE CHECKOUT FLOW]</div>
        <h1 className="checkout-title">
          <span>PORTAL</span>
          <span>RUB</span>
          <span>CHECKOUT</span>
        </h1>
        <p className="checkout-sub">
          Заказ в рублях создаётся на сервере, затем открывается защищённая ссылка провайдера. Для оплаты нужен checkout ticket,
          который выдаётся после привязки Telegram-аккаунта.
        </p>
      </section>

      <section className="checkout-grid">
        <article className="glass-card">
          <h2>Тариф</h2>
          <div className="plan-list">
            {plans.map((plan) => (
              <button
                key={plan.code}
                className={plan.code === activePlan.code ? "plan-btn plan-btn--active" : "plan-btn"}
                type="button"
                onClick={() => setSelectedPlan(plan.code)}
              >
                <span>{`${plan.label}${plan.badge ? ` • ${plan.badge}` : ""}`}</span>
                <strong>{`${plan.amount_rub} ₽`}</strong>
              </button>
            ))}
          </div>
          <p className="plan-note">{planNote(activePlan)}</p>
          {(queryCampaign || queryPromo) && (
            <p className="meta-line">
              Контекст: {queryCampaign ? `campaign=${queryCampaign}` : ""}
              {queryCampaign && queryPromo ? " • " : ""}
              {queryPromo ? `promo=${queryPromo}` : ""}
            </p>
          )}
          {queryTgId ? <p className="meta-line">Профиль: tg_id={queryTgId}</p> : null}
          {!queryCampaign && !queryPromo && !queryTgId ? (
            <p className="meta-line">Контекст: campaign/promo/tg_id не передан</p>
          ) : null}
          <p className={checkoutTicket ? "meta-line" : "meta-line meta-line--bad"}>
            {checkoutTicket ? "Checkout ticket: получен" : "Checkout ticket: не найден"}
          </p>
          {breakdown ? (
            <div className="breakdown">
              <div>{`База: ${breakdown.base.toFixed(0)} ₽`}</div>
              <div>{`Скидка: ${breakdown.pct}%`}</div>
              <div>{`Итог: ${breakdown.final.toFixed(0)} ₽`}</div>
            </div>
          ) : null}

          <div className="plan-compare">
            <div className="plan-compare__title">Сравнение тарифов</div>
            <div className="plan-compare__head">
              <span>Параметр</span>
              <span className={activeColumn === "start" ? "plan-compare__active" : ""}>Start</span>
              <span className={activeColumn === "pro" ? "plan-compare__active" : ""}>Pro</span>
              <span className={activeColumn === "ultra" ? "plan-compare__active" : ""}>Ultra</span>
            </div>
            {PLAN_COMPARISON_ROWS.map((row) => (
              <div className="plan-compare__row" key={row.metric}>
                <span>{row.metric}</span>
                <span className={activeColumn === "start" ? "plan-compare__active" : ""}>{row.start}</span>
                <span className={activeColumn === "pro" ? "plan-compare__active" : ""}>{row.pro}</span>
                <span className={activeColumn === "ultra" ? "plan-compare__active" : ""}>{row.ultra}</span>
              </div>
            ))}
            <p className="plan-compare__note">
              Почему часть медиасервисов может идти напрямую: в отдельных сценариях это уменьшает задержку и стабилизирует
              воспроизведение. VPN-канал для основного трафика сохраняется по тарифной политике.
            </p>
          </div>
        </article>

        <article className="glass-card">
          <h2>Оплата</h2>
          {!checkoutTicket ? (
            <div className="notice notice--warn">
              Для оплаты нужен checkout ticket. Откройте бота, завершите привязку и вернитесь в checkout.
            </div>
          ) : null}
          {statusText ? <div className="notice">{statusText}</div> : null}
          <div className="checkout-proof">
            <div className="checkout-proof__title">Данные по активности сервиса</div>
            <div className="checkout-proof__grid">
              <div className="checkout-proof__item">
                <span>Подключено</span>
                <strong>{socialProof.connected > 0 ? socialProof.connected.toLocaleString("ru-RU") : "—"}</strong>
              </div>
              <div className="checkout-proof__item">
                <span>Активно сейчас</span>
                <strong>{socialProof.active > 0 ? socialProof.active.toLocaleString("ru-RU") : "—"}</strong>
              </div>
              <div className="checkout-proof__item">
                <span>Платные профили</span>
                <strong>{socialProof.paid > 0 ? socialProof.paid.toLocaleString("ru-RU") : "—"}</strong>
              </div>
            </div>
            {socialProof.updatedAt ? (
              <div className="meta-line">{`Обновлено: ${new Date(socialProof.updatedAt).toLocaleString("ru-RU")}`}</div>
            ) : null}
          </div>

          <div className="checkout-actions" style={{ marginTop: 10 }}>
            {checkoutTicket ? (
              <button className="checkout-btn" disabled={isBusy} onClick={() => void createOrder()}>
                {isBusy ? "Создаём заказ..." : "Открыть оплату"}
              </button>
            ) : (
              <a href={botHref} className="checkout-btn" target="_blank" rel="noreferrer">
                Перейти в бот для привязки
              </a>
            )}
            <a href={TG_CHANNEL_LINK} className="checkout-btn checkout-btn--ghost" target="_blank" rel="noreferrer">
              Канал проекта
            </a>
          </div>

          {widgetSrc ? (
            <>
              <div className="meta-line" style={{ marginTop: 14 }}>Виджет доступен как вспомогательный вариант оплаты</div>
              <iframe
                src={widgetSrc}
                width="100%"
                height="560"
                title="Freekassa widget"
                style={{ border: 0, borderRadius: 14, overflow: "hidden", marginTop: 10, background: "transparent" }}
              />
            </>
          ) : null}
        </article>
      </section>

      <section className="checkout-foot glass-card">
        <h3>Что будет после оплаты</h3>
        <p>После успешного платежа статус продления обновится автоматически. Если процесс прервался, можно вернуться в checkout или в бота — контекст кампании сохранится.</p>
      </section>

      <style jsx global>{`
        .checkout-shell {
          min-height: 100vh;
          padding: 110px 20px 40px;
          color: var(--text);
          background:
            radial-gradient(1200px 600px at 10% -10%, rgba(255, 71, 87, 0.16), transparent 60%),
            radial-gradient(900px 420px at 90% 10%, rgba(46, 213, 115, 0.08), transparent 65%),
            var(--bg);
        }

        .checkout-hero {
          max-width: 1080px;
          margin: 0 auto 24px;
          position: relative;
          overflow: hidden;
          border: 1px solid var(--line);
          padding: 24px;
          backdrop-filter: blur(8px);
          background: linear-gradient(140deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.01));
        }

        .checkout-kicker {
          font-family: var(--font-m);
          font-size: 0.72rem;
          letter-spacing: 0.2em;
          color: var(--red);
          margin-bottom: 14px;
        }

        .checkout-title {
          font-family: var(--font-h);
          font-size: clamp(2.6rem, 9vw, 8rem);
          line-height: 0.85;
          margin: 0;
          display: grid;
        }

        .checkout-title span { display: block; color: var(--text); }
        .checkout-title span:nth-child(2) {
          color: transparent;
          -webkit-text-stroke: 1px var(--text);
        }
        .checkout-title span:nth-child(3) { color: var(--red); }

        .checkout-sub {
          margin-top: 10px;
          max-width: 760px;
          color: var(--muted);
          line-height: 1.6;
          font-family: var(--font-b);
        }

        .checkout-grid {
          max-width: 1080px;
          margin: 0 auto;
          display: grid;
          gap: 14px;
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .glass-card {
          border: 1px solid var(--line);
          padding: 18px;
          background: linear-gradient(145deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.02));
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.09), 0 18px 50px rgba(0, 0, 0, 0.22);
        }

        .glass-card h2,
        .glass-card h3 {
          margin: 0 0 12px;
          font-family: var(--font-h);
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        .plan-list { display: grid; gap: 8px; }

        .plan-btn {
          border: 1px solid var(--line);
          background: rgba(0, 0, 0, 0.28);
          color: var(--text);
          padding: 12px;
          text-align: left;
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 10px;
          cursor: pointer;
          font-family: var(--font-b);
          transition: border-color 0.2s ease, transform 0.2s ease;
        }

        .plan-btn strong {
          color: var(--red);
          font-family: var(--font-m);
          letter-spacing: 0.06em;
        }

        .plan-btn:hover { border-color: var(--red); transform: translateY(-1px); }
        .plan-btn--active {
          border-color: var(--red);
          box-shadow: 0 0 0 1px rgba(255, 71, 87, 0.45) inset;
        }

        .plan-note,
        .meta-line {
          margin: 10px 0 0;
          color: var(--muted);
          font-family: var(--font-m);
          font-size: 0.72rem;
          letter-spacing: 0.05em;
        }

        .meta-line--bad { color: #ff7a7a; }

        .plan-compare {
          margin-top: 12px;
          border: 1px solid var(--line);
          padding: 10px;
          background: rgba(0, 0, 0, 0.2);
        }

        .plan-compare__title {
          font-family: var(--font-m);
          font-size: 0.68rem;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 8px;
        }

        .plan-compare__head,
        .plan-compare__row {
          display: grid;
          grid-template-columns: 1.3fr 1fr 1fr 1fr;
          gap: 6px;
          align-items: start;
          font-size: 0.75rem;
          line-height: 1.4;
        }

        .plan-compare__head {
          font-family: var(--font-m);
          letter-spacing: 0.06em;
          text-transform: uppercase;
          color: var(--muted);
          border-bottom: 1px solid var(--line);
          padding-bottom: 6px;
          margin-bottom: 6px;
        }

        .plan-compare__row {
          padding: 5px 0;
          border-bottom: 1px dashed rgba(255, 255, 255, 0.08);
        }

        .plan-compare__row:last-of-type {
          border-bottom: 0;
        }

        .plan-compare__active {
          color: var(--red);
          font-weight: 700;
        }

        .plan-compare__note {
          margin-top: 8px;
          font-size: 0.74rem;
          line-height: 1.5;
          color: var(--muted);
        }

        .checkout-actions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 12px;
        }

        .checkout-btn {
          border: 1px solid var(--red);
          color: #fff;
          background: var(--red);
          padding: 10px 14px;
          font-family: var(--font-m);
          font-size: 0.75rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          cursor: pointer;
        }

        .checkout-btn:disabled { opacity: 0.75; cursor: default; }

        .checkout-btn--ghost {
          background: transparent;
          color: var(--text);
          border-color: var(--line);
        }

        .checkout-btn--ghost:hover {
          border-color: var(--red);
          color: var(--red);
        }

        .notice {
          border: 1px solid var(--line);
          padding: 10px 12px;
          font-family: var(--font-m);
          font-size: 0.72rem;
          color: var(--muted);
          line-height: 1.5;
        }

        .notice--warn {
          border-color: rgba(255, 71, 87, 0.45);
          color: #ffb2b9;
        }

        .checkout-proof {
          margin-top: 12px;
          border: 1px dashed var(--line);
          padding: 10px 12px;
          background: rgba(0, 0, 0, 0.16);
        }

        .checkout-proof__title {
          font-family: var(--font-m);
          font-size: 0.68rem;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--muted);
          margin-bottom: 8px;
        }

        .checkout-proof__grid {
          display: grid;
          gap: 8px;
          grid-template-columns: repeat(3, minmax(0, 1fr));
        }

        .checkout-proof__item {
          border: 1px solid var(--line);
          padding: 8px;
          display: grid;
          gap: 4px;
          background: rgba(255, 255, 255, 0.02);
        }

        .checkout-proof__item span {
          font-family: var(--font-m);
          font-size: 0.64rem;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--muted);
        }

        .checkout-proof__item strong {
          font-family: var(--font-h);
          font-size: 1.05rem;
          line-height: 1;
        }

        .breakdown {
          margin-top: 12px;
          border: 1px dashed var(--line);
          padding: 10px 12px;
          display: grid;
          gap: 6px;
          font-family: var(--font-m);
          font-size: 0.7rem;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }

        .checkout-foot {
          max-width: 1080px;
          margin: 14px auto 0;
        }

        .checkout-foot p {
          margin: 0;
          color: var(--muted);
          line-height: 1.6;
        }

        .orb {
          position: absolute;
          width: 180px;
          height: 180px;
          border-radius: 999px;
          pointer-events: none;
          filter: blur(30px);
          opacity: 0.45;
        }

        .orb-a { right: -50px; top: -45px; background: rgba(255, 71, 87, 0.6); }
        .orb-b { left: -70px; bottom: -90px; background: rgba(46, 213, 115, 0.35); }

        @media (max-width: 900px) {
          .checkout-grid { grid-template-columns: 1fr; }
          .checkout-proof__grid { grid-template-columns: 1fr; }
        }

        @media (max-width: 620px) {
          .plan-compare__head,
          .plan-compare__row {
            grid-template-columns: 1fr;
            gap: 3px;
          }

          .plan-compare__head span:first-child {
            display: none;
          }
        }
      `}</style>
    </main>
  );
}

