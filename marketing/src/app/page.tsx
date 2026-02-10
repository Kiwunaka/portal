"use client";

import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

const TG_BOT_FALLBACK = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/portal_service_bot";
const CHECKOUT_URL = process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL || TG_BOT_FALLBACK;
const SOCIAL_PROOF_URL = (process.env.NEXT_PUBLIC_SOCIAL_PROOF_URL || "").trim();

const FEATURES = [
  { type: "01Г—", title: "РњРіРЅРѕРІРµРЅРЅРѕРµ РїРѕРґРєР»СЋС‡РµРЅРёРµ", desc: "РљР»СЋС‡ РІС‹РґР°С‘С‚СЃСЏ С‡РµСЂРµР· Telegram Рё РёРјРїРѕСЂС‚РёСЂСѓРµС‚СЃСЏ РІ 1-2 С€Р°РіР°. Р‘РµР· СЂРµРіРёСЃС‚СЂР°С†РёРё, Р±РµР· РїР°СЂРѕР»РµР№.", num: "01" },
  { type: "04Г—", title: "4 СЃС‚СЂР°РЅС‹ РІ PRO", desc: "РџРѕР»СЊС€Р°, Р“РµСЂРјР°РЅРёСЏ, РЎРЁРђ Рё РС‚Р°Р»РёСЏ. РџРѕР»РЅС‹Р№ РґРѕСЃС‚СѓРї РєРѕ РІСЃРµРј СѓР·Р»Р°Рј РІ РїР»Р°С‚РЅС‹С… РїР»Р°РЅР°С….", num: "02" },
  { type: "в€ћГ—", title: "РЁРёС„СЂРѕРІР°РЅРЅС‹Р№ РєР°РЅР°Р»", desc: "Р’РµСЃСЊ С‚СЂР°С„РёРє Р·Р°С‰РёС‰С‘РЅ РјРµР¶РґСѓ РІР°С€РёРј СѓСЃС‚СЂРѕР№СЃС‚РІРѕРј Рё РІС‹Р±СЂР°РЅРЅС‹Рј СѓР·Р»РѕРј. РќРёРєР°РєРёС… Р»РѕРіРѕРІ.", num: "03" },
  { type: "05Г—", title: "Р”Рѕ 5 СѓСЃС‚СЂРѕР№СЃС‚РІ", desc: "РћРґРёРЅ РїСЂРѕС„РёР»СЊ РґР»СЏ С‚РµР»РµС„РѕРЅР°, РїР»Р°РЅС€РµС‚Р° Рё РєРѕРјРїСЊСЋС‚РµСЂР°. РћРґРЅРѕРІСЂРµРјРµРЅРЅРѕ Рё Р±РµР· РѕРіСЂР°РЅРёС‡РµРЅРёР№.", num: "04" },
  { type: "02Г—", title: "Р“РёР±РєРёРµ СЂРµР¶РёРјС‹", desc: "Р‘Р°Р·РѕРІС‹Р№ Рё РїРѕР»РЅС‹Р№ СЂРµР¶РёРј СЃ СЏСЃРЅС‹Рј Р°РїРіСЂРµР№РґРѕРј. Р‘РµР· РјРёРіСЂР°С†РёР№, Р±РµР· РїРѕС‚РµСЂРё РґР°РЅРЅС‹С….", num: "05" },
  { type: "24Г—", title: "РџРѕРґРґРµСЂР¶РєР° 24/7", desc: "РћРїРµСЂР°С‚РѕСЂС‹ РїРѕРјРѕРіР°СЋС‚ СЃ РґРёР°РіРЅРѕСЃС‚РёРєРѕР№ Рё РїРѕРґРєР»СЋС‡РµРЅРёРµРј РІ Telegram. РњРіРЅРѕРІРµРЅРЅР°СЏ СЂРµР°РєС†РёСЏ.", num: "06" },
];

const PLANS = [
  { code: "1m", name: "1 РјРµСЃСЏС†", desc: "5 СѓСЃС‚СЂРѕР№СЃС‚РІ вЂў 4 СЃС‚СЂР°РЅС‹ вЂў РїРѕРґРґРµСЂР¶РєР°", price: "199 в­ђ", note: "РЇРєРѕСЂСЊ", tag: "РЎС‚Р°СЂС‚", tone: "anchor" },
  { code: "3m", name: "3 РјРµСЃСЏС†Р°", desc: "5 СѓСЃС‚СЂРѕР№СЃС‚РІ вЂў 4 СЃС‚СЂР°РЅС‹ вЂў РїРѕР»РЅС‹Р№ РґРѕСЃС‚СѓРї", price: "499 в­ђ", note: "~166 в­ђ/РјРµСЃ", tag: "" },
  { code: "6m", name: "6 РјРµСЃСЏС†РµРІ", desc: "5 СѓСЃС‚СЂРѕР№СЃС‚РІ вЂў 4 СЃС‚СЂР°РЅС‹ вЂў decoy", price: "949 в­ђ", note: "~158 в­ђ/РјРµСЃ", tag: "Decoy", tone: "decoy" },
  { code: "9m", name: "9 РјРµСЃСЏС†РµРІ", desc: "5 СѓСЃС‚СЂРѕР№СЃС‚РІ вЂў 4 СЃС‚СЂР°РЅС‹ вЂў РЅРѕРІС‹Р№ С‚Р°СЂРёС„", price: "1299 в­ђ", note: "~144 в­ђ/РјРµСЃ", tag: "РќРѕРІС‹Р№" },
  { code: "12m", name: "12 РјРµСЃСЏС†РµРІ", desc: "5 СѓСЃС‚СЂРѕР№СЃС‚РІ вЂў 4 СЃС‚СЂР°РЅС‹ вЂў РјР°РєСЃРёРјСѓРј РІС‹РіРѕРґС‹", price: "1499 в­ђ", note: "~125 в­ђ/РјРµСЃ", tag: "Р РµРєРѕРјРµРЅРґСѓРµРј", tone: "recommended" },
];

const FAQS = [
  { q: "РљР°Рє РїРѕР»СѓС‡РёС‚СЊ РґРѕСЃС‚СѓРї?", a: "РћС‚РєСЂРѕР№С‚Рµ Telegram-Р±РѕС‚, РІС‹Р±РµСЂРёС‚Рµ С‚Р°СЂРёС„ Рё РїРѕР»СѓС‡РёС‚Рµ РїРµСЂСЃРѕРЅР°Р»СЊРЅС‹Р№ РєР»СЋС‡. Р‘РµР· СЂРµРіРёСЃС‚СЂР°С†РёРё." },
  { q: "РљР°РєРёРµ СѓСЃС‚СЂРѕР№СЃС‚РІР° РїРѕРґРґРµСЂР¶РёРІР°СЋС‚СЃСЏ?", a: "iOS, Android, Windows, macOS, Linux. РћРґРёРЅ РїСЂРѕС„РёР»СЊ СЂР°Р±РѕС‚Р°РµС‚ РЅР° РЅРµСЃРєРѕР»СЊРєРёС… СѓСЃС‚СЂРѕР№СЃС‚РІР°С… РѕРґРЅРѕРІСЂРµРјРµРЅРЅРѕ." },
  { q: "Р•СЃС‚СЊ Р±РµСЃРїР»Р°С‚РЅС‹Р№ СЂРµР¶РёРј?", a: "Р”Р°, СЃС‚Р°СЂС‚РѕРІС‹Р№ СЂРµР¶РёРј РґРѕСЃС‚СѓРїРµРЅ Р±РµР· РѕРїР»Р°С‚С‹. РџРµСЂРµР№С‚Рё РЅР° РїРѕР»РЅС‹Р№ РґРѕСЃС‚СѓРї РјРѕР¶РЅРѕ РІ Р»СЋР±РѕР№ РјРѕРјРµРЅС‚." },
  { q: "Р§С‚Рѕ РµСЃР»Рё СѓР·РµР» РЅРµРґРѕСЃС‚СѓРїРµРЅ?", a: "Р’ Р»РёС‡РЅРѕРј РєР°Р±РёРЅРµС‚Рµ РјРѕР¶РЅРѕ Р±С‹СЃС‚СЂРѕ РїРµСЂРµРєР»СЋС‡РёС‚СЊСЃСЏ РЅР° РґСЂСѓРіСѓСЋ СЃС‚СЂР°РЅСѓ Рё РїСЂРѕРІРµСЂРёС‚СЊ РєР°С‡РµСЃС‚РІРѕ СЃРѕРµРґРёРЅРµРЅРёСЏ." },
  { q: "РЎРѕС…СЂР°РЅСЏСЋС‚СЃСЏ Р»Рё Р»РѕРіРё?", a: "РќРµС‚. РњС‹ РЅРµ РІРµРґС‘Рј Р»РѕРіРѕРІ С‚СЂР°С„РёРєР° Рё СЃРѕРµРґРёРЅРµРЅРёР№. РџРѕР»РёС‚РёРєР° no-logs вЂ” РѕСЃРЅРѕРІР° СЃРµСЂРІРёСЃР°." },
  { q: "РњРѕР¶РЅРѕ Р»Рё РїРѕРјРµРЅСЏС‚СЊ С‚Р°СЂРёС„?", a: "Р”Р°, Р°РїРіСЂРµР№Рґ СЂР°Р±РѕС‚Р°РµС‚ РјРіРЅРѕРІРµРЅРЅРѕ. РћСЃС‚Р°РІС€РёРµСЃСЏ РґРЅРё РїРµСЂРµСЃС‡РёС‚С‹РІР°СЋС‚СЃСЏ Рё СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ." },
];

type Testimonial = {
  text: string;
  author: string;
  tag: string;
};

type ApiReview = {
  username?: string;
  rating?: number;
  text?: string;
  date?: string;
};

const MARQUEE_ITEMS = [
  "ENCRYPTED", "в—Џ", "FAST", "в—Џ", "STABLE", "в—Џ", "GLOBAL", "в—Џ",
  "PRIVATE", "в—Џ", "TELEGRAM", "в—Џ", "SUPPORT 24/7", "в—Џ", "NO LOGS", "в—Џ",
];

const SEGMENT_CTA = {
  FREE: { label: "РњСЏРіРєРёР№ Р°РїРіСЂРµР№Рґ", price: "149в­ђ", period: "Р·Р° РїРµСЂРІС‹Р№ РјРµСЃСЏС†", note: "Р’СЃРµ СЃС‚СЂР°РЅС‹ Рё РїРѕР»РЅС‹Р№ СЂРµР¶РёРј Р±РµР· СЂРµР·РєРѕР№ СЃРјРµРЅС‹ СЃС†РµРЅР°СЂРёСЏ." },
  PAID: { label: "РџСЂРѕРґР»РµРЅРёРµ Р±РµР· РїР°СѓР·С‹", price: "1299в­ђ", period: "Р·Р° 9 РјРµСЃСЏС†РµРІ", note: "РЎРѕС…СЂР°РЅРёС‚Рµ С‚РµРєСѓС‰РёР№ СѓСЂРѕРІРµРЅСЊ Рё РІС‹РіРѕРґРЅСѓСЋ СЃСЂРµРґРЅСЋСЋ СЃС‚РѕРёРјРѕСЃС‚СЊ РјРµСЃСЏС†Р°." },
  EXPIRED: { label: "Р’РѕР·РІСЂР°С‚ РґРѕСЃС‚СѓРїР°", price: "199в­ђ", period: "Р·Р° 1 РјРµСЃСЏС†", note: "Р§С‚РѕР±С‹ Р·Р°С‰РёС‚Р° РЅРµ РїСЂРµСЂС‹РІР°Р»Р°СЃСЊ Рё РєР»СЋС‡ РѕСЃС‚Р°РІР°Р»СЃСЏ Р°РєС‚СѓР°Р»СЊРЅС‹Рј." },
  MANUAL: { label: "РџР»Р°РЅ РґР»СЏ СЂСѓС‡РЅРѕРіРѕ РїСЂРѕС„РёР»СЏ", price: "499в­ђ", period: "Р·Р° 3 РјРµСЃСЏС†Р°", note: "РЈРґРѕР±РЅРѕРµ СЃС‚Р°РЅРґР°СЂС‚РЅРѕРµ РїСЂРѕРґР»РµРЅРёРµ РґР»СЏ СЂСѓС‡РЅРѕР№ РІС‹РґР°С‡Рё." },
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

function normalizePositiveInt(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return 0;
  return Math.round(n);
}

/* в”Ђв”Ђ Theme Toggle Hook в”Ђв”Ђ */
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

/* в”Ђв”Ђ Cursor Follower в”Ђв”Ђ */
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

/* в”Ђв”Ђ Preloader в”Ђв”Ђ */
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
      <div className="preloader-icon">в—Џ</div>
      <div className="preloader-text">PORTAL вЂ” LOADING</div>
      <div className="preloader-bar"><div className="preloader-fill" /></div>
    </div>
  );
}

/* в”Ђв”Ђ Navbar в”Ђв”Ђ */
function Navbar({ theme, onToggleTheme }: { theme: string; onToggleTheme: () => void }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header className={`topbar ${scrolled ? "topbar--scrolled" : ""}`}>
      <div className="brand"><span>в—Џ</span> PORTAL</div>
      <nav className="topnav">
        <a href="#features">Р’РѕР·РјРѕР¶РЅРѕСЃС‚Рё</a>
        <a href="#plans">РўР°СЂРёС„С‹</a>
        <a href="#faq">FAQ</a>
        <button className="theme-toggle" onClick={onToggleTheme} type="button" aria-label="Toggle theme">
          {theme === "dark" ? "вЂ" : "вѕ"}
        </button>
        <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="nav-buy">РџРѕРґРєР»СЋС‡РёС‚СЊ</a>
      </nav>
    </header>
  );
}

/* в”Ђв”Ђ Hero в”Ђв”Ђ */
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

      <div className="hero-badge">[NETWORK_SECURITY] вЂ” PRIVATE ROUTING вЂ” 2025</div>
      <div className="hero-title">
        <span className="hero-word-1">SECURE</span>
        <span className="hero-word-2">ROUTING</span>
        <span className="hero-word-3">PORTAL</span>
      </div>
      <div className="hero-sub">
        РЁРёС„СЂРѕРІР°РЅРёРµ вЂў 4 СЃС‚СЂР°РЅС‹ РІ PRO вЂў РџРѕРґРєР»СЋС‡РµРЅРёРµ Р·Р° 1-2 РјРёРЅСѓС‚С‹
      </div>
      <div className="hero-scroll">
        <span>SCROLL в†“</span>
      </div>
    </section>
  );
}

/* в”Ђв”Ђ Marquee в”Ђв”Ђ */
function Marquee() {
  const items = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS, ...MARQUEE_ITEMS];
  return (
    <div className="marquee-section">
      <div className="marquee-track">
        {items.map((item, i) => (
          <span key={`${item}-${i}`} className={item === "в—Џ" ? "" : "highlight"}>{item}</span>
        ))}
      </div>
    </div>
  );
}

/* в”Ђв”Ђ Features в”Ђв”Ђ */
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
        <h2>Р§РўРћ<br /><span className="stroke">Р’РќРЈРўР Р</span></h2>
        <p>РџРѕРЅСЏС‚РЅС‹Р№ РїСѓС‚СЊ: РїРѕРґРєР»СЋС‡РµРЅРёРµ, РєРѕРЅС‚СЂРѕР»СЊ СѓР·Р»РѕРІ, РїРѕРґРґРµСЂР¶РєР°, РїСЂРѕРґР»РµРЅРёРµ.</p>
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

/* в”Ђв”Ђ Testimonials в”Ђв”Ђ */
function Testimonials() {
  const [activeIdx, setActiveIdx] = useState(0);
  const [testimonials, setTestimonials] = useState<Testimonial[]>([]);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    let aborted = false;
    const load = async () => {
      try {
        const r = await fetch("/api/reviews", { cache: "no-store" });
        if (!r.ok) return;
        const data = await r.json() as { reviews?: ApiReview[] };
        const rows = Array.isArray(data.reviews) ? data.reviews : [];
        const next = rows
          .filter((row) => typeof row.text === "string" && row.text.trim().length > 0)
          .slice(0, 10)
          .map((row) => ({
            text: (row.text || "").trim(),
            author: ((row.username || "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ").trim() || "РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ"),
            tag: `${Math.max(1, Math.min(5, Number(row.rating) || 5))}в…`,
          }));
        if (!aborted && next.length > 0) {
          setTestimonials(next);
          setActiveIdx(0);
        }
      } catch {
        // Keep empty state when API is unavailable.
      }
    };
    void load();
    return () => {
      aborted = true;
    };
  }, []);

  useEffect(() => {
    if (prefersReducedMotion()) return;
    if (testimonials.length < 2) return;
    const interval = setInterval(() => {
      setActiveIdx((prev) => (prev + 1) % testimonials.length);
    }, 4500);
    return () => clearInterval(interval);
  }, [testimonials.length]);

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

  const visibleTestimonials = testimonials.length > 0
    ? testimonials
    : [{ text: "РћС‚Р·С‹РІС‹ СЃРєРѕСЂРѕ РїРѕСЏРІСЏС‚СЃСЏ РїРѕСЃР»Рµ РјРѕРґРµСЂР°С†РёРё.", author: "PORTAL", tag: "" }];
  const t = visibleTestimonials[activeIdx] || visibleTestimonials[0];

  return (
    <section className="testimonials" ref={ref}>
      <div className="section-tag">[FEEDBACK]</div>
      <h2>РћРўР—Р«Р’Р«</h2>
      <div className="testimonial-card" ref={cardRef} key={activeIdx}>
        <div className="testimonial-quote">"{t.text}"</div>
        <div className="testimonial-author">
          <span className="testimonial-name">{t.author}</span>
          <span className="testimonial-tag">{t.tag}</span>
        </div>
      </div>
      <div className="testimonial-dots">
        {testimonials.map((_, i) => (
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

/* в”Ђв”Ђ Plans в”Ђв”Ђ */
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
        <h2>РўРђР РР¤Р«</h2>
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

/* в”Ђв”Ђ CTA в”Ђв”Ђ */
function CTA() {
  const [segment, setSegment] = useState<SegmentKey>("FREE");
  const [soldCountTarget, setSoldCountTarget] = useState(2847);
  const current = useMemo(() => SEGMENT_CTA[segment], [segment]);
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    setSegment(parseSegmentFromQuery(window.location.search));
  }, []);

  useEffect(() => {
    let aborted = false;
    const sources = [SOCIAL_PROOF_URL, "/api/public/social-proof"].map((x) => x.trim()).filter(Boolean);
    if (!sources.length) return;

    const load = async () => {
      for (const url of sources) {
        try {
          const r = await fetch(url, { cache: "no-store" });
          if (!r.ok) continue;
          const data = await r.json() as {
            connected_users?: number;
            total_users?: number;
            paid_users?: number;
          };
          const next =
            normalizePositiveInt(data.connected_users) ||
            normalizePositiveInt(data.total_users) ||
            normalizePositiveInt(data.paid_users);
          if (next > 0) {
            if (!aborted) setSoldCountTarget(next);
            return;
          }
        } catch {
          // Try next source.
        }
      }
    };

    void load();
    return () => {
      aborted = true;
    };
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
            val: soldCountTarget,
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
  }, [soldCountTarget]);

  return (
    <section className="cta-section" id="cta" ref={ref}>
      <div className="section-tag">[ACQUIRE_ACCESS]</div>
      <div className="cta-content">
        <div className="cta-price-label">{current.label}</div>
        <div className="cta-price">{current.price}<span className="period">{current.period}</span></div>
        <div className="cta-disclaimer">{current.note}</div>
        <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="cta-btn">
          <span className="btn-icon">в†’</span>
          РћС‚РєСЂС‹С‚СЊ Telegram
        </a>
        <div className="cta-features">
          <span>Р‘РµР· Р»РёС€РЅРёС… СЌРєСЂР°РЅРѕРІ</span>
          <span>РџРѕРґРєР»СЋС‡РµРЅРёРµ Р·Р° РјРёРЅСѓС‚С‹</span>
          <span>РџРѕРґРґРµСЂР¶РєР° 24/7</span>
          <span>РџРѕРЅСЏС‚РЅС‹Рµ С‚Р°СЂРёС„С‹</span>
        </div>
        <div className="sold-counter">
          <div className="label">РџРћР›Р¬Р—РћР’РђРўР•Р›Р•Р™ РџРћР”РљР›Р®Р§Р•РќРћ</div>
          <div className="value" id="soldCount">{soldCountTarget.toLocaleString()}</div>
        </div>
      </div>
    </section>
  );
}

/* в”Ђв”Ђ FAQ в”Ђв”Ђ */
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
      <h2>Р’РћРџР РћРЎР«</h2>
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

/* в”Ђв”Ђ Back to Top в”Ђв”Ђ */
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
      в†‘
    </button>
  );
}

function MobileCommandBar() {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 260);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className={`mobile-command ${visible ? "mobile-command--show" : ""}`} aria-hidden={!visible}>
      <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="mobile-command__cta">
        <span className="mobile-command__lead">РћС‚РєСЂС‹С‚СЊ Telegram</span>
        <span className="mobile-command__tail">в†’ РџРѕРґРєР»СЋС‡РёС‚СЊ / РџСЂРѕРґР»РёС‚СЊ</span>
      </a>
    </div>
  );
}

/* в”Ђв”Ђ Footer в”Ђв”Ђ */
function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand"><span>в—Џ</span> PORTAL</div>
        <div className="footer-links">
          <a href="/offer">РћС„РµСЂС‚Р°</a>
          <a href="/privacy">РљРѕРЅС„РёРґРµРЅС†РёР°Р»СЊРЅРѕСЃС‚СЊ</a>
        </div>
        <div className="footer-legal">
          В© {new Date().getFullYear()} PORTAL вЂ” Р—РђР©РР©РЃРќРќР«Р™ РљРђРќРђР› РЎР’РЇР—Р Р”Р›РЇ Р›РР§РќРћР“Рћ РРЎРџРћР›Р¬Р—РћР’РђРќРРЇ
        </div>
      </div>
    </footer>
  );
}

/* в”Ђв”Ђ Page в”Ђв”Ђ */
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
      <MobileCommandBar />
      <BackToTop />
    </>
  );
}
