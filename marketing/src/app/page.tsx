"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const TG_BOT_FALLBACK = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/swazist_bot";
const CHECKOUT_URL = process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL || TG_BOT_FALLBACK;

const FEATURES = [
  { type: "01×", title: "Мгновенное подключение", desc: "Ключ выдаётся через Telegram и импортируется в 1-2 шага. Без регистрации, без паролей.", num: "01" },
  { type: "04×", title: "4 страны в PRO", desc: "Польша, Германия, США и Италия. Полный доступ ко всем узлам в платных планах.", num: "02" },
  { type: "∞×", title: "Шифрованный канал", desc: "Весь трафик защищён между вашим устройством и выбранным узлом. Никаких логов.", num: "03" },
  { type: "05×", title: "До 5 устройств", desc: "Один профиль для телефона, планшета и компьютера. Одновременно и без ограничений.", num: "04" },
  { type: "02×", title: "Гибкие режимы", desc: "Базовый и полный режим с ясным апгрейдом. Без миграций, без потери данных.", num: "05" },
  { type: "24×", title: "Поддержка 24/7", desc: "Операторы помогают с диагностикой и подключением в Telegram. Мгновенная реакция.", num: "06" },
];

const PLANS = [
  { code: "1m", name: "1 месяц", desc: "5 устройств • 4 страны • поддержка", price: "199 ⭐", note: "Якорь", tag: "Старт", tone: "anchor" },
  { code: "3m", name: "3 месяца", desc: "5 устройств • 4 страны • полный доступ", price: "499 ⭐", note: "~166 ⭐/мес", tag: "" },
  { code: "6m", name: "6 месяцев", desc: "5 устройств • 4 страны • decoy", price: "949 ⭐", note: "~158 ⭐/мес", tag: "Decoy", tone: "decoy" },
  { code: "9m", name: "9 месяцев", desc: "5 устройств • 4 страны • новый тариф", price: "1299 ⭐", note: "~144 ⭐/мес", tag: "Новый" },
  { code: "12m", name: "12 месяцев", desc: "5 устройств • 4 страны • максимум выгоды", price: "1499 ⭐", note: "~125 ⭐/мес", tag: "Рекомендуем", tone: "recommended" },
];

const FAQS = [
  { q: "Как получить доступ?", a: "Откройте Telegram-бот, выберите тариф и получите персональный ключ. Без регистрации." },
  { q: "Какие устройства поддерживаются?", a: "iOS, Android, Windows, macOS, Linux. Один профиль работает на нескольких устройствах одновременно." },
  { q: "Есть бесплатный режим?", a: "Да, стартовый режим доступен без оплаты. Перейти на полный доступ можно в любой момент." },
  { q: "Что если узел недоступен?", a: "В личном кабинете можно быстро переключиться на другую страну и проверить качество соединения." },
  { q: "Сохраняются ли логи?", a: "Нет. Мы не ведём логов трафика и соединений. Политика no-logs — основа сервиса." },
  { q: "Можно ли поменять тариф?", a: "Да, апгрейд работает мгновенно. Оставшиеся дни пересчитываются и сохраняются." },
];

const TESTIMONIALS = [
  { text: "Подключился за минуту через бот. Работает стабильно уже 3 месяца без единого сбоя.", author: "Дмитрий", tag: "PRO 6 мес" },
  { text: "Наконец-то сервис, который просто работает. Без дурацких приложений с рекламой.", author: "Анна", tag: "PRO 12 мес" },
  { text: "Пинг до Германии 38ms — играю без лагов. Поддержка ответила за 2 минуты.", author: "Максим", tag: "PRO 3 мес" },
  { text: "Перешёл с другого сервиса. Здесь быстрее, дешевле и нет навязчивого маркетинга.", author: "Алексей", tag: "PRO 9 мес" },
];

const MARQUEE_ITEMS = [
  "ENCRYPTED", "●", "FAST", "●", "STABLE", "●", "GLOBAL", "●",
  "PRIVATE", "●", "TELEGRAM", "●", "SUPPORT 24/7", "●", "NO LOGS", "●",
];

const SEGMENT_CTA = {
  FREE: { label: "Мягкий апгрейд", price: "149⭐", period: "за первый месяц", note: "Все страны и полный режим без резкой смены сценария." },
  PAID: { label: "Продление без паузы", price: "1299⭐", period: "за 9 месяцев", note: "Сохраните текущий уровень и выгодную среднюю стоимость месяца." },
  EXPIRED: { label: "Возврат доступа", price: "199⭐", period: "за 1 месяц", note: "Чтобы защита не прерывалась и ключ оставался актуальным." },
  MANUAL: { label: "План для ручного профиля", price: "499⭐", period: "за 3 месяца", note: "Удобное стандартное продление для ручной выдачи." },
} as const;

type SegmentKey = keyof typeof SEGMENT_CTA;

function parseSegmentFromQuery(search: string): SegmentKey {
  const q = new URLSearchParams(search);
  const raw = (q.get("segment") || q.get("variant") || "FREE").toUpperCase().trim();
  if (raw === "PAID" || raw === "EXPIRED" || raw === "MANUAL") return raw;
  return "FREE";
}

function prefersReducedMotion(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/* ── Theme Toggle Hook ── */
function useTheme() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const saved = localStorage.getItem("portal-theme");
    if (saved === "light" || saved === "dark") setTheme(saved);
  }, []);

  const toggle = useCallback(() => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("portal-theme", next);
      document.documentElement.setAttribute("data-theme", next);
      return next;
    });
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  return { theme, toggle };
}

/* ── Cursor Follower ── */
function CursorFollower() {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const isTouchDevice = "ontouchstart" in window || navigator.maxTouchPoints > 0;
    if (isTouchDevice) { el.style.display = "none"; return; }
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      el.style.display = "none";
      return;
    }

    let mx = 0, my = 0, cx = 0, cy = 0;
    let raf: number;
    const onMove = (e: MouseEvent) => { mx = e.clientX; my = e.clientY; };
    const tick = () => {
      cx += (mx - cx) * 0.12;
      cy += (my - cy) * 0.12;
      el.style.left = cx + "px";
      el.style.top = cy + "px";
      raf = requestAnimationFrame(tick);
    };

    const onEnterInteractive = () => el.classList.add("hover");
    const onLeaveInteractive = () => el.classList.remove("hover");

    window.addEventListener("mousemove", onMove);
    const interactive = Array.from(document.querySelectorAll("a, button, .plan-card, .faq-item"));
    interactive.forEach((node) => {
      node.addEventListener("mouseenter", onEnterInteractive);
      node.addEventListener("mouseleave", onLeaveInteractive);
    });
    raf = requestAnimationFrame(tick);

    return () => {
      window.removeEventListener("mousemove", onMove);
      interactive.forEach((node) => {
        node.removeEventListener("mouseenter", onEnterInteractive);
        node.removeEventListener("mouseleave", onLeaveInteractive);
      });
      cancelAnimationFrame(raf);
    };
  }, []);
  return <div className="cursor-follower" ref={ref} />;
}

/* ── Preloader ── */
function Preloader({ onDone }: { onDone: () => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (prefersReducedMotion()) {
      onDone();
      return;
    }
    const tl = gsap.timeline({
      onComplete: () => {
        gsap.to(ref.current, {
          opacity: 0,
          duration: 0.4,
          onComplete: onDone,
        });
      },
    });
    tl.to(".preloader-fill", { width: "100%", duration: 1.2, ease: "power2.inOut" })
      .to(".preloader-text", { opacity: 1, y: 0, duration: 0.3 }, 0);
  }, [onDone]);

  return (
    <div className="preloader" ref={ref}>
      <div className="preloader-icon">●</div>
      <div className="preloader-text">PORTAL — LOADING</div>
      <div className="preloader-bar"><div className="preloader-fill" /></div>
    </div>
  );
}

/* ── Navbar ── */
function Navbar({ theme, onToggleTheme }: { theme: string; onToggleTheme: () => void }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`topbar ${scrolled ? "topbar--scrolled" : ""}`}>
      <div className="brand"><span>●</span> PORTAL</div>
      <nav className="topnav">
        <a href="#features">Возможности</a>
        <a href="#plans">Тарифы</a>
        <a href="#faq">FAQ</a>
        <button className="theme-toggle" onClick={onToggleTheme} type="button" aria-label="Toggle theme">
          {theme === "dark" ? "☀" : "☾"}
        </button>
        <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="nav-buy">Подключить</a>
      </nav>
    </header>
  );
}

/* ── Hero ── */
function Hero() {
  const heroRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    const ctx = gsap.context(() => {
      const tl = gsap.timeline({ defaults: { ease: "power4.out" } });

      tl.from(".hero-word-1", { y: 80, opacity: 0, duration: 0.8 })
        .from(".hero-word-2", { y: 60, opacity: 0, duration: 0.7 }, 0.15)
        .from(".hero-word-3", { y: 60, opacity: 0, duration: 0.7 }, 0.25)
        .from(".hero-badge", { opacity: 0, y: 20, duration: 0.5 }, 0.4)
        .from(".hero-sub", { opacity: 0, y: 15, duration: 0.5 }, 0.55)
        .from(".hero-scroll", { opacity: 0, duration: 0.4 }, 0.8);

      // Parallax on scroll
      gsap.to("#bgLine1", {
        x: -200,
        scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: 1 },
      });
      gsap.to("#bgLine2", {
        x: 150,
        scrollTrigger: { trigger: ".hero", start: "top top", end: "bottom top", scrub: 1 },
      });
    }, heroRef);

    return () => ctx.revert();
  }, []);

  return (
    <section className="hero" ref={heroRef}>
      <div className="bg-type">
        <div className="bg-type-line" id="bgLine1" style={{ fontSize: "20vw", top: "10%", left: "-5%" }}>
          SECURE SECURE SECURE SECURE
        </div>
        <div className="bg-type-line" id="bgLine2" style={{ fontSize: "15vw", top: "50%", right: "-5%" }}>
          PORTAL PORTAL PORTAL PORTAL
        </div>
      </div>

      <div className="hero-badge">[NETWORK_SECURITY] — PRIVATE ROUTING — 2025</div>
      <div className="hero-title">
        <span className="hero-word-1">SECURE</span>
        <span className="hero-word-2">ROUTING</span>
        <span className="hero-word-3">PORTAL</span>
      </div>
      <div className="hero-sub">
        Шифрование • 4 страны в PRO • Подключение за 1-2 минуты
      </div>
      <div className="hero-scroll">
        <span>SCROLL ↓</span>
      </div>
    </section>
  );
}

/* ── Marquee ── */
function Marquee() {
  const items = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS, ...MARQUEE_ITEMS];
  return (
    <div className="marquee-section">
      <div className="marquee-track">
        {items.map((item, i) => (
          <span key={`${item}-${i}`} className={item === "●" ? "" : "highlight"}>{item}</span>
        ))}
      </div>
    </div>
  );
}

/* ── Features ── */
function Features() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    const ctx = gsap.context(() => {
      gsap.from(".feature-card", {
        y: 50,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: "power3.out",
        scrollTrigger: { trigger: ".features-grid", start: "top 80%", once: true },
      });
      gsap.from(".features-header", {
        y: 30,
        opacity: 0,
        duration: 0.6,
        ease: "power3.out",
        scrollTrigger: { trigger: ".features", start: "top 85%", once: true },
      });
    }, ref);
    return () => ctx.revert();
  }, []);

  return (
    <section className="features" id="features" ref={ref}>
      <div className="section-tag">[CONTENTS]</div>
      <div className="features-header">
        <h2>ЧТО<br /><span className="stroke">ВНУТРИ</span></h2>
        <p>Понятный путь: подключение, контроль узлов, поддержка, продление.</p>
      </div>
      <div className="features-grid">
        {FEATURES.map((f) => (
          <div key={f.num} className="feature-card">
            <div className="feature-num">{f.num}</div>
            <div className="feature-type">{f.type}</div>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ── Testimonials ── */
function Testimonials() {
  const [activeIdx, setActiveIdx] = useState(0);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    const interval = setInterval(() => {
      setActiveIdx((prev) => (prev + 1) % TESTIMONIALS.length);
    }, 4500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    const ctx = gsap.context(() => {
      gsap.from(".testimonial-card", {
        opacity: 0, y: 20, duration: 0.5, ease: "power2.out",
        scrollTrigger: { trigger: ".testimonials", start: "top 80%", once: true },
      });
    }, ref);
    return () => ctx.revert();
  }, []);

  // Animate card change
  const cardRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (prefersReducedMotion()) return;
    if (cardRef.current) {
      gsap.fromTo(cardRef.current,
        { opacity: 0, x: 20 },
        { opacity: 1, x: 0, duration: 0.4, ease: "power2.out" },
      );
    }
  }, [activeIdx]);

  const t = TESTIMONIALS[activeIdx];

  return (
    <section className="testimonials" ref={ref}>
      <div className="section-tag">[FEEDBACK]</div>
      <h2>ОТЗЫВЫ</h2>
      <div className="testimonial-card" ref={cardRef} key={activeIdx}>
        <div className="testimonial-quote">"{t.text}"</div>
        <div className="testimonial-author">
          <span className="testimonial-name">{t.author}</span>
          <span className="testimonial-tag">{t.tag}</span>
        </div>
      </div>
      <div className="testimonial-dots">
        {TESTIMONIALS.map((_, i) => (
          <button
            key={i}
            type="button"
            className={`testimonial-dot ${i === activeIdx ? "active" : ""}`}
            onClick={() => setActiveIdx(i)}
            aria-label={`Testimonial ${i + 1}`}
          />
        ))}
      </div>
    </section>
  );
}

/* ── Plans ── */
function Plans() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    const ctx = gsap.context(() => {
      gsap.from(".plan-card", {
        y: 40,
        opacity: 0,
        duration: 0.6,
        stagger: 0.08,
        ease: "power3.out",
        scrollTrigger: { trigger: ".plans-track", start: "top 80%", once: true },
      });
    }, ref);
    return () => ctx.revert();
  }, []);

  return (
    <section className="plans" id="plans" ref={ref}>
      <div className="section-tag">[TARIFFS]</div>
      <div className="plans-header">
        <h2>ТАРИФЫ</h2>
      </div>
      <div className="plans-track">
        {PLANS.map((p) => (
          <div
            key={p.code}
            className={`plan-card ${p.tone === "recommended" ? "recommended" : ""} ${p.tone === "decoy" ? "decoy" : ""}`}
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

/* ── CTA ── */
function CTA() {
  const [segment, setSegment] = useState<SegmentKey>("FREE");
  const current = useMemo(() => SEGMENT_CTA[segment], [segment]);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    setSegment(parseSegmentFromQuery(window.location.search));
  }, []);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    const ctx = gsap.context(() => {
      gsap.from(".cta-content > *", {
        y: 30,
        opacity: 0,
        duration: 0.6,
        stagger: 0.1,
        ease: "power3.out",
        scrollTrigger: { trigger: ".cta-section", start: "top 75%", once: true },
      });

      // Sold counter
      ScrollTrigger.create({
        trigger: "#soldCount",
        start: "top 85%",
        once: true,
        onEnter: () => {
          gsap.to({ val: 0 }, {
            val: 2847,
            duration: 2,
            ease: "power2.out",
            onUpdate: function () {
              const el = document.getElementById("soldCount");
              if (el) el.textContent = Math.round(this.targets()[0].val).toLocaleString();
            },
          });
        },
      });
    }, ref);
    return () => ctx.revert();
  }, []);

  return (
    <section className="cta-section" id="cta" ref={ref}>
      <div className="section-tag">[ACQUIRE_ACCESS]</div>
      <div className="cta-content">
        <div className="cta-price-label">{current.label}</div>
        <div className="cta-price">{current.price}<span className="period">{current.period}</span></div>
        <div className="cta-disclaimer">{current.note}</div>
        <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="cta-btn">
          <span className="btn-icon">→</span>
          Открыть Telegram
        </a>
        <div className="cta-features">
          <span>Без лишних экранов</span>
          <span>Подключение за минуты</span>
          <span>Поддержка 24/7</span>
          <span>Понятные тарифы</span>
        </div>
        <div className="sold-counter">
          <div className="label">ПОЛЬЗОВАТЕЛЕЙ ПОДКЛЮЧЕНО</div>
          <div className="value" id="soldCount">0</div>
        </div>
      </div>
    </section>
  );
}

/* ── FAQ ── */
function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    const ctx = gsap.context(() => {
      gsap.from(".faq-item", {
        y: 20,
        opacity: 0,
        duration: 0.5,
        stagger: 0.06,
        ease: "power3.out",
        scrollTrigger: { trigger: ".faq", start: "top 80%", once: true },
      });
    }, ref);
    return () => ctx.revert();
  }, []);

  return (
    <section className="faq" id="faq" ref={ref}>
      <div className="section-tag">[FAQ]</div>
      <h2>ВОПРОСЫ</h2>
      <div>
        {FAQS.map((f, i) => (
          <div key={f.q} className="faq-item" onClick={() => setOpenIndex(openIndex === i ? null : i)}>
            <div className="faq-q">{f.q}<span className={`toggle ${openIndex === i ? "open" : ""}`}>+</span></div>
            <div className={`faq-a ${openIndex === i ? "open" : ""}`}>{f.a}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

/* ── Back to Top ── */
function BackToTop() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 600);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);
  if (!show) return null;
  return (
    <button
      className="back-to-top"
      type="button"
      onClick={() => window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? "auto" : "smooth" })}
      aria-label="Back to top"
    >
      ↑
    </button>
  );
}

/* ── Footer ── */
function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand"><span>●</span> PORTAL</div>
        <div className="footer-links">
          <a href="/offer">Оферта</a>
          <a href="/privacy">Конфиденциальность</a>
        </div>
        <div className="footer-legal">
          © {new Date().getFullYear()} PORTAL — ЗАЩИЩЁННЫЙ КАНАЛ СВЯЗИ ДЛЯ ЛИЧНОГО ИСПОЛЬЗОВАНИЯ
        </div>
      </div>
    </footer>
  );
}

/* ── Page ── */
export default function HomePage() {
  const { theme, toggle: toggleTheme } = useTheme();
  const [preloaded, setPreloaded] = useState(false);

  return (
    <>
      {!preloaded && <Preloader onDone={() => setPreloaded(true)} />}
      <div className="grain" />
      <CursorFollower />
      <Navbar theme={theme} onToggleTheme={toggleTheme} />
      <main style={{ visibility: preloaded ? "visible" : "hidden" }}>
        <Hero />
        <Marquee />
        <Features />
        <Testimonials />
        <Plans />
        <CTA />
        <FAQ />
        <Footer />
      </main>
      <BackToTop />
    </>
  );
}
