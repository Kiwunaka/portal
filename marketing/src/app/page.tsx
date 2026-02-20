"use client";

import { useEffect, useMemo, useState } from "react";

const TG_BOT_FALLBACK = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/portal_service_bot";
const CHECKOUT_URL = process.env.NEXT_PUBLIC_CHECKOUT_PAGE_URL || "/checkout/";
const BOT_FAST_URL = process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL || TG_BOT_FALLBACK;
const WEBAPP_URL = (process.env.NEXT_PUBLIC_WEBAPP_URL || "https://portal-privacy.online/webapp/").trim();
const TG_NEWS_CHANNEL = (process.env.NEXT_PUBLIC_NEWS_CHANNEL || "portal_privacy").replace("@", "").trim();
const PUBLIC_API_BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
const APP_ANDROID_PLAY_URL = (process.env.NEXT_PUBLIC_APP_ANDROID_PLAY_URL || "").trim();
const APP_ANDROID_APK_URL = (process.env.NEXT_PUBLIC_APP_ANDROID_APK_URL || "").trim();
const APP_ANDROID_MIRROR_URL = (process.env.NEXT_PUBLIC_APP_ANDROID_MIRROR_URL || "").trim();
const APP_WINDOWS_EXE_URL = (process.env.NEXT_PUBLIC_APP_WINDOWS_EXE_URL || "").trim();
const APP_WINDOWS_MIRROR_URL = (process.env.NEXT_PUBLIC_APP_WINDOWS_MIRROR_URL || "").trim();
const APP_DOCS_URL = (process.env.NEXT_PUBLIC_APP_DOCS_URL || "").trim();
const CONTACT_EMAIL = (process.env.NEXT_PUBLIC_CONTACT_EMAIL || "support@portal-privacy.online").trim();
const ENTERPRISE_EMAIL = (process.env.NEXT_PUBLIC_ENTERPRISE_EMAIL || "enterprise@portal-privacy.online").trim();
const CONTACT_TG_URL = (process.env.NEXT_PUBLIC_CONTACT_TG_URL || "https://t.me/portal_privacy_helpbot").trim();
const CONTACT_FORM_URL = (process.env.NEXT_PUBLIC_CONTACT_FORM_URL || "https://t.me/portal_privacy_helpbot").trim();

type LiveUpdate = {
  title: string;
  summary: string;
  date: string;
  link: string;
};

type SocialProof = {
  connected_users?: number;
  total_users?: number;
  paid_users?: number;
};

type Review = {
  username?: string;
  rating?: number;
  text?: string;
};

const FEATURES = [
  { type: "01×", title: "Запуск за 1-2 минуты", desc: "Вход через Telegram, быстрый импорт ключа и понятные шаги без ручной рутины.", num: "01" },
  { type: "04×", title: "4 страны в платных планах", desc: "Польша, Нидерланды, США и Италия с быстрым переключением в кабинете.", num: "02" },
  { type: "∞×", title: "Шифрование трафика", desc: "VPN-канал работает в зашифрованном режиме для повседневных и рабочих задач.", num: "03" },
  { type: "05×", title: "До 5 устройств", desc: "Один профиль для телефона, ноутбука и настольного ПК одновременно.", num: "04" },
  { type: "02×", title: "Start и полный режим", desc: "Мягкий вход с Start и быстрый переход на полный режим без переезда.", num: "05" },
  { type: "24×", title: "Поддержка в Telegram", desc: "Отвечаем по тикетам и помогаем с диагностикой по реальному сценарию.", num: "06" },
];

const PLANS = [
  { code: "start_99", name: "Start", desc: "30 дней • 1 устройство • NL", price: "99 ₽", note: "Мягкий вход для проверки сервиса", tag: "Вход" },
  { code: "pro_249", name: "Pro", desc: "1 месяц • до 5 устройств • все страны", price: "249 ₽", note: "Сбалансированный вариант на каждый день", tag: "Популярный", recommended: true },
  { code: "ultra_1499", name: "Ultra / Family", desc: "12 месяцев • до 5 устройств • полный пул", price: "1499 ₽", note: "Долгий горизонт с лучшей ценой в месяц", tag: "Выгода", micro: "≈300 ₽/чел при 5 устройствах" },
];

const PLAN_COMPARISON_ROWS = [
  { metric: "Устройства", start: "1", pro: "До 5", ultra: "До 5" },
  { metric: "Страны", start: "NL", pro: "Польша, Нидерланды, США, Италия", ultra: "Полный пул стран + приоритет" },
  { metric: "Маршрутизация", start: "VPN для базовых задач", pro: "Полный VPN-маршрут для ежедневного трафика", ultra: "VPN-маршрут + приоритет обработки" },
  { metric: "Скоростной профиль", start: "Базовый", pro: "Высокий", ultra: "Максимальный" },
  { metric: "Поддержка", start: "Стандартная", pro: "Быстрый Telegram-ответ", ultra: "Приоритет 24/7" },
];

const FAQS = [
  { q: "Как получить доступ?", a: "Откройте Telegram-бот, выберите план и получите персональный ключ для подключения." },
  { q: "Какие устройства поддерживаются?", a: "iOS, Android, Windows, macOS и Linux. В Pro/Ultra можно подключить до 5 устройств." },
  { q: "Есть бесплатный режим?", a: "Да, стартовый режим доступен без оплаты. На полный VPN-доступ можно перейти в любой момент." },
  { q: "Что делать при низкой скорости?", a: "Проверьте статус узлов, переключите страну и при необходимости создайте тикет в поддержке." },
  { q: "Есть гарантия абсолютной скорости?", a: "Нет. Мы работаем в best-effort режиме и регулярно обновляем узлы и рекомендации." },
];

const ROADMAP = [
  {
    title: "Retention",
    status: "Реализовано",
    points: ["Welcome / T-3 / T-1 / T0 / reactivation цепочки.", "Start99 offer и мягкие сценарии продления."],
  },
  {
    title: "UI-Polish",
    status: "Реализовано",
    points: ["Обновленный checkout и WebApp UX.", "Более понятный onboarding для Android / iOS / Desktop."],
  },
  {
    title: "Ops",
    status: "В работе",
    points: ["Автоматизация post-deploy smoke.", "Дальнейшее усиление rollout/rollback runbook."],
  },
];

const DEFAULT_LIVE_UPDATES: LiveUpdate[] = [
  { title: "Обновлены узлы NL/PL", summary: "Актуализированы маршруты и рекомендации по клиентам для мобильных устройств.", date: "2026-02-14", link: `https://t.me/${TG_NEWS_CHANNEL}/1` },
  { title: "Новые предложения для новых пользователей", summary: "Добавлены стартовые сценарии и бонусы за подписку на канал.", date: "2026-02-13", link: `https://t.me/${TG_NEWS_CHANNEL}/2` },
  { title: "Обновлен гайд по подключению", summary: "Упростили старт для Android, iOS и Windows.", date: "2026-02-12", link: `https://t.me/${TG_NEWS_CHANNEL}/3` },
];

function candidateApiBases(): string[] {
  const out: string[] = [];
  if (PUBLIC_API_BASE_URL) out.push(PUBLIC_API_BASE_URL.replace(/\/+$/, ""));
  if (typeof window !== "undefined") out.push(window.location.origin.replace(/\/+$/, ""));
  out.push("https://portal-privacy.online");
  return Array.from(new Set(out.filter(Boolean)));
}

function normalizePositiveInt(value: unknown): number {
  const n = Number(value);
  if (!Number.isFinite(n) || n <= 0) return 0;
  return Math.round(n);
}

function maskReviewUsername(username?: string): string {
  const raw = (username || "").trim().replace(/^@+/, "");
  if (!raw) return "Пользователь";
  return `${raw.slice(0, 2)}***`;
}

export default function HomePage() {
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [scrolled, setScrolled] = useState(false);
  const [openedFaq, setOpenedFaq] = useState<number | null>(0);
  const [liveUpdates, setLiveUpdates] = useState<LiveUpdate[]>(DEFAULT_LIVE_UPDATES);
  const [socialCount, setSocialCount] = useState(2847);
  const [reviews, setReviews] = useState<Array<{ text: string; author: string; tag: string }>>([]);

  const review = reviews[0];

  const androidLinks = useMemo(
    () =>
      [
        { key: "play", label: "Google Play", url: APP_ANDROID_PLAY_URL },
        { key: "apk", label: "APK", url: APP_ANDROID_APK_URL },
        { key: "mirror", label: "Mirror", url: APP_ANDROID_MIRROR_URL },
      ].filter((item) => item.url),
    [],
  );

  const windowsLinks = useMemo(
    () =>
      [
        { key: "exe", label: "EXE", url: APP_WINDOWS_EXE_URL },
        { key: "mirror", label: "Mirror", url: APP_WINDOWS_MIRROR_URL },
      ].filter((item) => item.url),
    [],
  );

  useEffect(() => {
    const saved = localStorage.getItem("portal-theme");
    const next = saved === "light" ? "light" : "dark";
    setTheme(next);
    document.documentElement.setAttribute("data-theme", next);
  }, []);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 80);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadLiveUpdates = async () => {
      for (const base of candidateApiBases()) {
        try {
          const resp = await fetch(`${base}/api/public/live-updates?limit=3`, { cache: "no-store" });
          if (!resp.ok) continue;
          const data = (await resp.json()) as { updates?: LiveUpdate[] };
          const normalized = (Array.isArray(data.updates) ? data.updates : [])
            .map((item) => ({
              title: String(item?.title || "").trim(),
              summary: String(item?.summary || "").trim(),
              date: String(item?.date || "").trim(),
              link: String(item?.link || "").trim(),
            }))
            .filter((item) => item.title && item.link)
            .slice(0, 3);
          if (normalized.length) {
            if (!cancelled) setLiveUpdates(normalized);
            return;
          }
        } catch {
          // try next base
        }
      }
    };

    const loadSocialProof = async () => {
      for (const base of candidateApiBases()) {
        try {
          const resp = await fetch(`${base}/api/public/social-proof`, { cache: "no-store" });
          if (!resp.ok) continue;
          const data = (await resp.json()) as SocialProof;
          const next =
            normalizePositiveInt(data.connected_users) ||
            normalizePositiveInt(data.total_users) ||
            normalizePositiveInt(data.paid_users);
          if (next > 0) {
            if (!cancelled) setSocialCount(next);
            return;
          }
        } catch {
          // try next base
        }
      }
    };

    const loadReviews = async () => {
      try {
        const resp = await fetch("/api/reviews", { cache: "no-store" });
        if (!resp.ok) return;
        const data = (await resp.json()) as { reviews?: Review[] };
        const mapped = (Array.isArray(data.reviews) ? data.reviews : [])
          .filter((item) => typeof item.text === "string" && item.text.trim().length > 0)
          .slice(0, 3)
          .map((item) => ({
            text: (item.text || "").trim(),
            author: maskReviewUsername(item.username),
            tag: `${Math.max(1, Math.min(5, Number(item.rating) || 5))}★`,
          }));
        if (!cancelled && mapped.length) setReviews(mapped);
      } catch {
        // fallback to default review state
      }
    };

    void loadLiveUpdates();
    void loadSocialProof();
    void loadReviews();

    return () => {
      cancelled = true;
    };
  }, []);

  const toggleTheme = () => {
    setTheme((prev) => {
      const next = prev === "dark" ? "light" : "dark";
      localStorage.setItem("portal-theme", next);
      document.documentElement.setAttribute("data-theme", next);
      return next;
    });
  };

  return (
    <>
      <div className="grain" aria-hidden="true" />

      <header className={`topbar ${scrolled ? "topbar--scrolled" : ""}`}>
        <div className="brand">
          <span>●</span> PORTAL
        </div>
        <nav className="topnav">
          <a href="#features">Преимущества</a>
          <a href="#plans">Тарифы</a>
          <a href="#download">Скачать</a>
          <a href="#roadmap">Roadmap</a>
          <a href="#faq">FAQ</a>
          <button className="theme-toggle" onClick={toggleTheme} type="button" aria-label="Переключить тему">
            {theme === "dark" ? "☀" : "☾"}
          </button>
          <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="nav-buy">
            Подключить
          </a>
        </nav>
      </header>

      <main id="main-content">
        <section className="hero">
          <div className="bg-type">
            <div className="bg-type-line" style={{ fontSize: "20vw", top: "10%", left: "-5%" }}>
              SECURE SECURE SECURE SECURE
            </div>
            <div className="bg-type-line" style={{ fontSize: "15vw", top: "54%", right: "-5%" }}>
              PORTAL PORTAL PORTAL PORTAL
            </div>
          </div>
          <div className="hero-badge">[SECURE DIGITAL ACCESS] — TRANSPARENT CHECKOUT — 2026</div>
          <div className="hero-title">
            <span className="hero-word-1">SECURE</span>
            <span className="hero-word-2">ROUTING</span>
            <span className="hero-word-3">PORTAL</span>
          </div>
          <div className="hero-sub">Понятный VPN-запуск • Прозрачная цена • Поддержка в Telegram</div>
          <div className="hero-scroll">
            <span>SCROLL ↓</span>
          </div>
        </section>

        <div className="marquee-section">
          <div className="marquee-track">
            {["ENCRYPTED", "●", "FAST", "●", "STABLE", "●", "GLOBAL", "●", "PRIVATE", "●", "SUPPORT 24/7", "●", "NO LOGS", "●"].map((item, idx) => (
              <span key={`${item}-${idx}`} className={item === "●" ? "" : "highlight"}>
                {item}
              </span>
            ))}
          </div>
        </div>

        <section className="features" id="features">
          <div className="section-tag">[CONTENTS]</div>
          <div className="features-header">
            <h2>
              ЧТО
              <br />
              <span className="stroke">ВНУТРИ</span>
            </h2>
            <p>Понятный путь: подключение, выбор плана, оплата и поддержка.</p>
          </div>
          <div className="features-grid">
            {FEATURES.map((item) => (
              <article key={item.num} className="feature-card">
                <div className="feature-num">{item.num}</div>
                <div className="feature-type">{item.type}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="testimonials">
          <div className="section-tag">[FEEDBACK]</div>
          <h2>ОТЗЫВЫ ПОЛЬЗОВАТЕЛЕЙ</h2>
          <div className="testimonial-card">
            <div className="testimonial-quote">"{review?.text || "Отзывы загружаются. После модерации покажем свежие кейсы пользователей."}"</div>
            <div className="testimonial-author">
              <span className="testimonial-name">{review?.author || "PORTAL"}</span>
              <span className="testimonial-tag">{review?.tag || ""}</span>
            </div>
          </div>
        </section>

        <section className="plans" id="plans">
          <div className="section-tag">[TARIFFS]</div>
          <div className="plans-header">
            <h2>ТАРИФЫ</h2>
          </div>
          <div className="plans-track">
            {PLANS.map((plan) => (
              <article key={plan.code} className={`plan-card ${plan.recommended ? "recommended" : ""}`}>
                {plan.tag ? <span className="plan-tag">{plan.tag}</span> : null}
                <span className="plan-emoji">{plan.code.toUpperCase()}</span>
                <h3>{plan.name}</h3>
                <p className="plan-desc">{plan.desc}</p>
                <div className="plan-price">{plan.price}</div>
                <div className="plan-note">{plan.note}</div>
                {plan.micro ? <div className="plan-micro">{plan.micro}</div> : null}
              </article>
            ))}
          </div>
        </section>

        <section className="downloads" id="plan-comparison">
          <div className="section-tag">[COMPARISON]</div>
          <div className="downloads-head">
            <h2>НАГЛЯДНОЕ СРАВНЕНИЕ ТАРИФОВ VPN</h2>
            <p>Сразу видно, где лимиты, где полный режим и какой профиль подходит под ваш сценарий.</p>
          </div>
          <div className="roadmap-list" style={{ marginTop: 18 }}>
            {PLAN_COMPARISON_ROWS.map((row) => (
              <p key={row.metric}>
                <strong>{row.metric}:</strong> Start — {row.start}; Pro — {row.pro}; Ultra — {row.ultra}
              </p>
            ))}
          </div>
          <div className="download-card" style={{ marginTop: 14 }}>
            <h3>Как работает маршрутизация по тарифам</h3>
            <p>
              Для части медиасценариев может использоваться прямой маршрут для меньшей задержки, а VPN-канал остается для основного защищенного трафика.
              В карточке тарифа всегда явно указано, какой режим применяется.
            </p>
          </div>
        </section>

        <section className="downloads" id="download">
          <div className="section-tag">[DOWNLOAD]</div>
          <div className="downloads-head">
            <h2>СКАЧАТЬ ПРИЛОЖЕНИЕ</h2>
            <p>Официальные сборки для Android и Windows. Ссылки обновляются после релизов.</p>
          </div>
          <div className="downloads-grid">
            <article className="download-card">
              <h3>Android</h3>
              <p>Установка из магазина или прямым APK.</p>
              <div className="download-actions">
                {androidLinks.length ? (
                  androidLinks.map((item) => (
                    <a key={item.key} href={item.url} target="_blank" rel="noreferrer" className="download-link">
                      {item.label}
                    </a>
                  ))
                ) : (
                  <span className="download-empty">Сборка появится после публикации</span>
                )}
              </div>
            </article>
            <article className="download-card">
              <h3>Windows</h3>
              <p>Установщик для ПК и резервный канал загрузки.</p>
              <div className="download-actions">
                {windowsLinks.length ? (
                  windowsLinks.map((item) => (
                    <a key={item.key} href={item.url} target="_blank" rel="noreferrer" className="download-link">
                      {item.label}
                    </a>
                  ))
                ) : (
                  <span className="download-empty">Сборка появится после публикации</span>
                )}
              </div>
            </article>
          </div>
          {APP_DOCS_URL ? (
            <a href={APP_DOCS_URL} target="_blank" rel="noreferrer" className="download-docs">
              Инструкция по установке →
            </a>
          ) : null}
        </section>

        <section className="downloads" id="access-paths">
          <div className="section-tag">[ACCESS]</div>
          <div className="downloads-head">
            <h2>САЙТ И TELEGRAM</h2>
            <p>Управляйте доступом через личный кабинет или через бота — как удобнее в моменте.</p>
          </div>
          <div className="downloads-grid">
            <article className="download-card">
              <h3>Личный кабинет</h3>
              <p>Статус подписки, ключ подключения, платежи и история поддержки.</p>
              <div className="download-actions">
                <a href={WEBAPP_URL} target="_blank" rel="noreferrer" className="download-link">
                  Открыть кабинет
                </a>
                <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="download-link">
                  Открыть оплату
                </a>
              </div>
            </article>
            <article className="download-card">
              <h3>Telegram-бот</h3>
              <p>Быстрый путь: продлить доступ, получить ключ и перейти в поддержку.</p>
              <div className="download-actions">
                <a href={BOT_FAST_URL} target="_blank" rel="noreferrer" className="download-link">
                  Открыть бота
                </a>
              </div>
            </article>
          </div>
        </section>

        <section className="cta-section" id="cta">
          <div className="section-tag">[ACQUIRE_ACCESS]</div>
          <div className="cta-content">
            <div className="cta-price-label">Прозрачный старт</div>
            <div className="cta-price">
              99 ₽<span className="period">за Start-план</span>
            </div>
            <div className="cta-disclaimer">Подключение за несколько шагов с понятной суммой до оплаты.</div>
            <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="cta-btn">
              <span className="btn-icon">→</span>
              Открыть оплату
            </a>
            <div className="cta-features">
              <span>Прозрачная сумма до оплаты</span>
              <span>Мгновенная активация</span>
              <span>Поддержка 24/7</span>
            </div>
            <div className="sold-counter">
              <div className="label">Пользователей подключено</div>
              <div className="value">{socialCount.toLocaleString()}</div>
            </div>
          </div>
        </section>

        <section className="downloads" id="news">
          <div className="section-tag">[LIVE UPDATES]</div>
          <div className="downloads-head">
            <h2>ПОСЛЕДНИЕ ОБНОВЛЕНИЯ</h2>
            <p>Свежие апдейты по узлам и сервису с прямым переходом в канал.</p>
          </div>
          <div className="downloads-grid">
            {liveUpdates.map((item) => (
              <article key={`${item.date}-${item.title}`} className="download-card">
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <div className="download-actions">
                  <a href={item.link} target="_blank" rel="noreferrer" className="download-link">
                    Открыть пост
                  </a>
                  <span className="download-empty">{item.date}</span>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="downloads roadmap-public" id="roadmap">
          <div className="section-tag">[ROADMAP]</div>
          <div className="downloads-head">
            <h2>ROADMAP НА БЛИЖАЙШИЕ СПРИНТЫ</h2>
            <p>Показываем подтвержденные треки и текущий статус.</p>
          </div>
          <div className="downloads-grid">
            {ROADMAP.map((item) => (
              <article key={item.title} className="download-card roadmap-card">
                <h3>{item.title}</h3>
                <div className="roadmap-status">{item.status}</div>
                <div className="roadmap-list">
                  {item.points.map((point) => (
                    <p key={point}>{point}</p>
                  ))}
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="faq" id="faq">
          <div className="section-tag">[FAQ]</div>
          <h2>ВОПРОСЫ</h2>
          <div>
            {FAQS.map((item, idx) => {
              const open = openedFaq === idx;
              return (
                <div key={item.q} className="faq-item">
                  <button
                    type="button"
                    className="faq-q"
                    onClick={() => setOpenedFaq(open ? null : idx)}
                    aria-expanded={open}
                    aria-controls={`faq-answer-${idx}`}
                  >
                    {item.q}
                    <span className={`toggle ${open ? "open" : ""}`}>+</span>
                  </button>
                  <div id={`faq-answer-${idx}`} className={`faq-a ${open ? "open" : ""}`}>
                    {item.a}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-brand">
            <span>●</span> PORTAL
          </div>
          <div className="footer-meta">
            <p className="footer-description">
              PORTAL предоставляет цифровой сервис VPN-доступа с маршрутами по странам, личным кабинетом и поддержкой через Telegram.
              Оплата взимается за выбранный период доступа.
            </p>
            <div className="footer-contacts">
              <span>Контакты:</span>
              <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
              <a href={`mailto:${ENTERPRISE_EMAIL}`}>{ENTERPRISE_EMAIL}</a>
              <a href={CONTACT_TG_URL} target="_blank" rel="noreferrer">
                Telegram
              </a>
              <a href={CONTACT_FORM_URL} target="_blank" rel="noreferrer">
                Форма связи
              </a>
            </div>
          </div>
          <div className="footer-links">
            <a href="/offer">Оферта</a>
            <a href="/privacy">Конфиденциальность</a>
          </div>
          <div className="footer-legal">© {new Date().getFullYear()} PORTAL — SECURE ACCESS SERVICE</div>
        </div>
      </footer>
    </>
  );
}
