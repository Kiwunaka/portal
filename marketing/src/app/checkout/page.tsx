"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import gsap from "gsap";

type PlanOption = { code: string; label: string; amount: number; note: string };

const PLAN_OPTIONS: PlanOption[] = [
  { code: "start_99", label: "Start 30 дней", amount: 99, note: "1 устройство • NL" },
  { code: "1_month", label: "Pro 1 месяц", amount: 249, note: "до 5 устройств • все страны" },
  { code: "3_months", label: "Pro 3 месяца", amount: 699, note: "средняя цена ниже за месяц" },
  { code: "6_months", label: "Ultra 6 месяцев", amount: 1199, note: "приоритетные узлы и стабильный запас" },
  { code: "9_months", label: "Ultra 9 месяцев", amount: 1399, note: "оптимальный горизонт продления" },
  { code: "12_months", label: "Ultra 12 месяцев", amount: 1499, note: "максимальная выгода по месяцу" },
];

const FK_WIDGET_API_KEY = (process.env.NEXT_PUBLIC_FK_WIDGET_API_KEY || "").trim();
const FK_WIDGET_SHOP_ID = (process.env.NEXT_PUBLIC_FK_WIDGET_SHOP_ID || "").trim();
const FK_WIDGET_LANG = (process.env.NEXT_PUBLIC_FK_WIDGET_LANG || "ru").trim();
const FK_WIDGET_THEME = (process.env.NEXT_PUBLIC_FK_WIDGET_THEME || "light").trim();
const CHECKOUT_FALLBACK_URL = (
  process.env.NEXT_PUBLIC_FK_CHECKOUT_FALLBACK_URL ||
  process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL ||
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ||
  "https://t.me/portal_service_bot"
).trim();
const TG_CHANNEL_LINK = (process.env.NEXT_PUBLIC_TG_CHANNEL_LINK || "https://t.me/portal_privacy").trim();

function findPlan(code: string): PlanOption {
  const normalized = (code || "").trim().toLowerCase();
  return PLAN_OPTIONS.find((p) => p.code === normalized) || PLAN_OPTIONS[0];
}

export default function CheckoutPage() {
  const [queryPlan, setQueryPlan] = useState("start_99");
  const [queryTgId, setQueryTgId] = useState("");
  const [queryCampaign, setQueryCampaign] = useState("");
  const [queryPromo, setQueryPromo] = useState("");
  const initialPlan = useMemo(() => findPlan(queryPlan || "start_99"), [queryPlan]);
  const [planCode, setPlanCode] = useState<string>(initialPlan.code);
  const heroRef = useRef<HTMLElement | null>(null);
  const sceneRef = useRef<HTMLDivElement | null>(null);
  const orderSeedRef = useRef<string>(`${Date.now()}_${Math.random().toString(16).slice(2, 8)}`);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search || "");
    setQueryPlan((params.get("plan") || "start_99").trim().toLowerCase());
    setQueryTgId((params.get("tg_id") || "").trim());
    setQueryCampaign((params.get("campaign") || "").trim());
    setQueryPromo((params.get("promo") || "").trim().toUpperCase());
  }, []);

  useEffect(() => {
    setPlanCode(initialPlan.code);
  }, [initialPlan.code]);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    const ctx = gsap.context(() => {
      gsap.fromTo(".checkout-kicker", { y: 20, opacity: 0 }, { y: 0, opacity: 1, duration: 0.55, ease: "power3.out" });
      gsap.fromTo(".checkout-title > span", { y: 70, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, stagger: 0.08, ease: "power4.out", delay: 0.05 });
      gsap.fromTo(".checkout-sub", { y: 14, opacity: 0 }, { y: 0, opacity: 1, duration: 0.45, delay: 0.24 });
      gsap.fromTo(".glass-card", { y: 28, opacity: 0 }, { y: 0, opacity: 1, duration: 0.65, stagger: 0.1, delay: 0.2, ease: "power3.out" });
      gsap.to(".orb-a", { y: 30, x: -24, duration: 6, repeat: -1, yoyo: true, ease: "sine.inOut" });
      gsap.to(".orb-b", { y: -26, x: 18, duration: 7, repeat: -1, yoyo: true, ease: "sine.inOut" });
    }, sceneRef);
    return () => ctx.revert();
  }, []);

  const activePlan = useMemo(() => findPlan(planCode), [planCode]);
  const tgId = queryTgId;
  const campaign = queryCampaign;
  const promo = queryPromo;

  const widgetSrc = useMemo(() => {
    if (!FK_WIDGET_API_KEY || !FK_WIDGET_SHOP_ID) return "";
    const params = new URLSearchParams({
      type: "payment-window",
      lang: FK_WIDGET_LANG || "ru",
      theme: FK_WIDGET_THEME || "light",
      default_amount: String(activePlan.amount),
      api_key: FK_WIDGET_API_KEY,
      shopID: FK_WIDGET_SHOP_ID,
    });
    return `https://widgets.freekassa.net?${params.toString()}`;
  }, [activePlan.amount]);

  const fallbackHref = useMemo(() => {
    const base = new URL(CHECKOUT_FALLBACK_URL, "https://portal-privacy.online");
    if (!base.searchParams.get("source")) base.searchParams.set("source", "site");
    base.searchParams.set("plan", activePlan.code);
    if (tgId) base.searchParams.set("tg_id", tgId);
    if (campaign) base.searchParams.set("campaign", campaign);
    if (promo) base.searchParams.set("promo", promo);
    base.searchParams.set("ref", orderSeedRef.current);
    return base.toString();
  }, [activePlan.code, campaign, promo, tgId]);

  return (
    <main className="checkout-shell" ref={sceneRef}>
      <section className="checkout-hero" ref={heroRef}>
        <div className="orb orb-a" />
        <div className="orb orb-b" />
        <div className="checkout-kicker">[HYBRID CHECKOUT]</div>
        <h1 className="checkout-title">
          <span>PORTAL</span>
          <span>RUB</span>
          <span>PAY</span>
        </h1>
        <p className="checkout-sub">
          Оформление доступа в рублях: карта/СБП через виджет, резервный путь через Telegram.
        </p>
      </section>

      <section className="checkout-grid">
        <article className="glass-card">
          <h2>Тариф</h2>
          <div className="plan-list">
            {PLAN_OPTIONS.map((plan) => (
              <button
                key={plan.code}
                className={plan.code === activePlan.code ? "plan-btn plan-btn--active" : "plan-btn"}
                type="button"
                onClick={() => setPlanCode(plan.code)}
              >
                <span>{plan.label}</span>
                <strong>{plan.amount} ₽</strong>
              </button>
            ))}
          </div>
          <p className="plan-note">{activePlan.note}</p>
          {campaign || promo ? (
            <p className="meta-line">
              Контекст: {campaign ? `campaign=${campaign}` : ""}{campaign && promo ? " • " : ""}{promo ? `promo=${promo}` : ""}
            </p>
          ) : null}
          {tgId ? <p className="meta-line">Профиль: tg_id={tgId}</p> : <p className="meta-line">Профиль: guest checkout</p>}
        </article>

        <article className="glass-card">
          <h2>Оплата</h2>
          {widgetSrc ? (
            <iframe
              src={widgetSrc}
              width="100%"
              height="600"
              title="Freekassa widget"
              style={{ border: 0, borderRadius: 14, overflow: "hidden", background: "transparent" }}
            />
          ) : (
            <div className="widget-offline">
              Виджет не сконфигурирован. Добавьте `NEXT_PUBLIC_FK_WIDGET_API_KEY` и `NEXT_PUBLIC_FK_WIDGET_SHOP_ID`.
            </div>
          )}
          <div className="checkout-actions">
            <a href={fallbackHref} className="checkout-btn" target="_blank" rel="noreferrer">Открыть оплату</a>
            <a href={TG_CHANNEL_LINK} className="checkout-btn checkout-btn--ghost" target="_blank" rel="noreferrer">Канал проекта</a>
          </div>
        </article>
      </section>

      <section className="checkout-foot glass-card">
        <h3>Почему подписка на канал полезна</h3>
        <p>Там выходят обновления узлов, инструкции по подключению и персональные офферы продления без пропуска срока.</p>
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

        .checkout-title span {
          display: block;
          color: var(--text);
        }

        .checkout-title span:nth-child(2) {
          color: transparent;
          -webkit-text-stroke: 1px var(--text);
        }

        .checkout-title span:nth-child(3) {
          color: var(--red);
        }

        .checkout-sub {
          margin-top: 10px;
          max-width: 720px;
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

        .plan-list {
          display: grid;
          gap: 8px;
        }

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

        .plan-btn:hover {
          border-color: var(--red);
          transform: translateY(-1px);
        }

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

        .widget-offline {
          border: 1px dashed var(--line);
          color: var(--muted);
          padding: 18px;
          line-height: 1.5;
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
        }

        .checkout-btn--ghost {
          background: transparent;
          color: var(--text);
          border-color: var(--line);
        }

        .checkout-btn--ghost:hover {
          border-color: var(--red);
          color: var(--red);
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

        .orb-a {
          right: -50px;
          top: -45px;
          background: rgba(255, 71, 87, 0.6);
        }

        .orb-b {
          left: -70px;
          bottom: -90px;
          background: rgba(46, 213, 115, 0.35);
        }

        @media (max-width: 900px) {
          .checkout-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </main>
  );
}
