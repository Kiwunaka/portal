"use client";

import { useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

const TG_BOT_FALLBACK = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/swazist_bot";
const CHECKOUT_URL = process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL || TG_BOT_FALLBACK;

const FEATURES = [
  { icon: "⚡", title: "Подключение за минуту", desc: "Ключ выдаётся через Telegram и импортируется в 1-2 шага.", num: "01" },
  { icon: "🌍", title: "4 страны в PRO", desc: "Польша, Германия, США и Италия доступны в платных планах.", num: "02" },
  { icon: "🔐", title: "Шифрованный канал", desc: "Трафик защищён между вашим устройством и выбранным узлом.", num: "03" },
  { icon: "📱", title: "До 5 устройств", desc: "Один профиль для телефона, планшета и компьютера.", num: "04" },
  { icon: "🧩", title: "Гибкие режимы", desc: "Есть базовый и полный режим с ясным апгрейдом без миграций.", num: "05" },
  { icon: "💬", title: "Поддержка 24/7", desc: "Операторы помогают с диагностикой и подключением в Telegram.", num: "06" },
];

const PLANS = [
  { code: "1m", name: "1 месяц", desc: "5 устройств • 4 страны • поддержка", price: "199 ⭐", note: "Якорь", tag: "Якорь", tone: "anchor" },
  { code: "3m", name: "3 месяца", desc: "5 устройств • 4 страны • полный доступ", price: "499 ⭐", note: "~166 ⭐/мес", tag: "" },
  { code: "6m", name: "6 месяцев", desc: "5 устройств • 4 страны • decoy-план", price: "949 ⭐", note: "~158 ⭐/мес", tag: "Decoy", tone: "decoy" },
  { code: "9m", name: "9 месяцев", desc: "5 устройств • 4 страны • новый тариф", price: "1299 ⭐", note: "~144 ⭐/мес", tag: "Новый" },
  { code: "12m", name: "12 месяцев", desc: "5 устройств • 4 страны • максимум выгоды", price: "1499 ⭐", note: "~125 ⭐/мес", tag: "Рекомендуем", tone: "recommended" },
];

const FAQS = [
  { q: "Как получить доступ?", a: "Откройте Telegram-бот, выберите тариф и получите персональный ключ." },
  { q: "Какие устройства поддерживаются?", a: "iOS, Android, Windows, macOS, Linux. Один профиль работает на нескольких устройствах." },
  { q: "Есть бесплатный режим?", a: "Да, стартовый режим доступен без оплаты. Можно перейти на полный доступ в любой момент." },
  { q: "Что если узел недоступен?", a: "В личном кабинете можно быстро переключиться на другую страну и проверить качество." },
];

const MARQUEE_ITEMS = [
  "ENCRYPTED",
  "FAST",
  "STABLE",
  "GLOBAL",
  "PRIVATE",
  "TELEGRAM",
  "SUPPORT 24/7",
  "NO NOISE",
];

const SEGMENT_CTA = {
  FREE: {
    label: "Мягкий апгрейд",
    price: "149⭐",
    period: "за первый месяц",
    note: "Все страны и полный режим без резкой смены сценария.",
  },
  PAID: {
    label: "Продление без паузы",
    price: "1299⭐",
    period: "за 9 месяцев",
    note: "Сохраните текущий уровень и выгодную среднюю стоимость месяца.",
  },
  EXPIRED: {
    label: "Возврат доступа",
    price: "199⭐",
    period: "за 1 месяц",
    note: "Чтобы защита не прерывалась и ключ оставался актуальным.",
  },
  MANUAL: {
    label: "План для ручного профиля",
    price: "499⭐",
    period: "за 3 месяца",
    note: "Удобное стандартное продление для ручной выдачи.",
  },
} as const;

type SegmentKey = keyof typeof SEGMENT_CTA;

function parseSegmentFromQuery(search: string): SegmentKey {
  const q = new URLSearchParams(search);
  const raw = (q.get("segment") || q.get("variant") || "FREE").toUpperCase().trim();
  if (raw === "PAID" || raw === "EXPIRED" || raw === "MANUAL") return raw;
  return "FREE";
}

function Navbar() {
  return (
    <header className="topbar">
      <div className="brand">PORTAL<span>.</span></div>
      <nav className="topnav">
        <a href="#features">Возможности</a>
        <a href="#plans">Тарифы</a>
        <a href="#faq">FAQ</a>
        <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="nav-buy">Подключить</a>
      </nav>
    </header>
  );
}

function Hero() {
  const word1Ref = useRef<HTMLSpanElement>(null);
  const word2Ref = useRef<HTMLSpanElement>(null);
  const word3Ref = useRef<HTMLSpanElement>(null);
  const subRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const splitIntoChars = (el: HTMLElement, text: string) => {
      el.innerHTML = text.split("").map((ch) => `<span class="char">${ch}</span>`).join("");
    };

    if (word1Ref.current) splitIntoChars(word1Ref.current, "SECURE");
    if (word2Ref.current) splitIntoChars(word2Ref.current, "ROUTING");
    if (word3Ref.current) splitIntoChars(word3Ref.current, "PORTAL");
    if (subRef.current) {
      subRef.current.innerHTML = "Шифрование • 4 страны в PRO • Подключение за 1-2 минуты"
        .split(" ")
        .map((w) => `<span class="word">${w}</span>`)
        .join(" ");
    }

    const tl = gsap.timeline();
    tl.from(".hero-title .line-inner", { y: 120, duration: 0.9, stagger: 0.12, ease: "power4.out" })
      .from("#heroWord1 .char", { y: 60, opacity: 0, stagger: 0.04, duration: 0.4 }, 0.25)
      .from("#heroWord2 .char", { x: 30, opacity: 0, stagger: 0.03, duration: 0.35 }, 0.45)
      .from("#heroWord3 .char", { x: -30, opacity: 0, stagger: 0.03, duration: 0.35 }, 0.55)
      .from(".hero-sub .word", { y: 16, opacity: 0, stagger: 0.02, duration: 0.25 }, 0.75);
  }, []);

  return (
    <section className="hero">
      <div className="hero-badge">Кинетическая витрина маршрутов</div>
      <div className="hero-title">
        <span className="line"><span className="line-inner hero-word-1" id="heroWord1" ref={word1Ref} /></span>
        <span className="line"><span className="line-inner hero-word-2" id="heroWord2" ref={word2Ref} /></span>
        <span className="line"><span className="line-inner hero-word-3" id="heroWord3" ref={word3Ref} /></span>
      </div>
      <div className="hero-sub" ref={subRef} />
    </section>
  );
}

function Marquee() {
  const items = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS, ...MARQUEE_ITEMS];
  return (
    <div className="marquee-section">
      <div className="marquee-track">
        {items.map((item, i) => <span key={`${item}-${i}`}>{item}</span>)}
      </div>
    </div>
  );
}

function Features() {
  return (
    <section className="features" id="features">
      <div className="features-header reveal">
        <h2>Что внутри</h2>
        <p>Понятный путь: подключение, контроль узлов, поддержка, продление.</p>
      </div>
      <div className="features-grid">
        {FEATURES.map((f, i) => (
          <div key={f.num} className="feature-card reveal" style={{ "--delay": `${i * 0.08}s` } as CSSProperties}>
            <div className="feature-num">{f.num}</div>
            <span className="feature-icon">{f.icon}</span>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function Plans() {
  return (
    <section className="plans" id="plans">
      <div className="plans-header reveal">
        <h2>Тарифы</h2>
      </div>
      <div className="plans-track">
        {PLANS.map((p, i) => (
          <div
            key={p.code}
            className={`plan-card reveal ${p.tone === "recommended" ? "recommended" : ""} ${p.tone === "decoy" ? "decoy" : ""}`}
            style={{ "--delay": `${i * 0.1}s` } as CSSProperties}
          >
            {p.tag ? <span className="plan-tag">{p.tag}</span> : null}
            <span className="plan-emoji">{p.code.toUpperCase()}</span>
            <h3>{p.name}</h3>
            <p className="plan-desc">{p.desc}</p>
            <div className="plan-price">{p.price}</div>
            <div className="plan-note">{p.note}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function CTA() {
  const [segment, setSegment] = useState<SegmentKey>("FREE");
  const current = useMemo(() => SEGMENT_CTA[segment], [segment]);

  useEffect(() => {
    setSegment(parseSegmentFromQuery(window.location.search));
  }, []);

  return (
    <section className="cta-section" id="cta">
      <div className="cta-content">
        <div className="cta-price-label reveal">{current.label}</div>
        <div className="cta-price reveal">{current.price}<span className="period">{current.period}</span></div>
        <div className="cta-disclaimer reveal">{current.note}</div>
        <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="cta-btn reveal">
          <span className="btn-icon">→</span>
          Открыть Telegram
        </a>
        <div className="cta-features reveal">
          <span>Без лишних экранов</span>
          <span>Подключение за минуты</span>
          <span>Поддержка 24/7</span>
          <span>Понятные тарифы</span>
        </div>
      </div>
    </section>
  );
}

function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="faq" id="faq">
      <h2 className="reveal">FAQ</h2>
      <div>
        {FAQS.map((f, i) => (
          <div key={f.q} className="faq-item reveal" onClick={() => setOpenIndex(openIndex === i ? null : i)}>
            <div className="faq-q">{f.q}<span className={`toggle ${openIndex === i ? "open" : ""}`}>+</span></div>
            <div className={`faq-a ${openIndex === i ? "open" : ""}`}>{f.a}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="footer">
      <div className="footer-brand">PORTAL<span>.</span></div>
      <div className="footer-links">
        <a href="/offer">Оферта</a>
        <a href="/privacy">Политика конфиденциальности</a>
      </div>
      <div className="footer-legal">
        © {new Date().getFullYear()} PORTAL. Защищённый канал связи для личного использования.
      </div>
    </footer>
  );
}

export default function HomePage() {
  useEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    gsap.utils.toArray<HTMLElement>(".reveal").forEach((el) => {
      gsap.fromTo(
        el,
        { opacity: 0, y: 24 },
        {
          opacity: 1,
          y: 0,
          duration: 0.7,
          ease: "power3.out",
          scrollTrigger: { trigger: el, start: "top 88%", once: true },
          delay: parseFloat(el.style.getPropertyValue("--delay") || "0"),
        },
      );
    });
  }, []);

  return (
    <>
      <Navbar />
      <main>
        <Hero />
        <Marquee />
        <Features />
        <Plans />
        <CTA />
        <FAQ />
        <Footer />
      </main>
    </>
  );
}
