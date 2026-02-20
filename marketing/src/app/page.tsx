"use client";

import { useEffect, useMemo, useState } from "react";

const TG_BOT_FALLBACK = process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL || "https://t.me/portal_service_bot";
const CHECKOUT_URL = process.env.NEXT_PUBLIC_CHECKOUT_PAGE_URL || "/checkout/";
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

type PlanCard = {
  code: string;
  name: string;
  price: string;
  period: string;
  badge?: string;
  traffic: string;
  devices: string;
  countries: string;
  speed: string;
  support: string;
  highlight?: boolean;
};

const FEATURES = [
  {
    title: "Запуск VPN за 1-2 минуты",
    desc: "Вход через Telegram, выдача ключа и быстрый импорт в клиент без ручной рутины.",
  },
  {
    title: "Честные тарифы без скрытых шагов",
    desc: "Сразу видно цену, лимиты по устройствам и что входит в Premium до оплаты.",
  },
  {
    title: "Стабильный трафик и fallback",
    desc: "Если узел перегружен, можно переключить страну в один клик из личного кабинета.",
  },
  {
    title: "Поддержка в Telegram 24/7",
    desc: "Тикеты, история обращений и понятные инструкции прямо в кабинете и в боте.",
  },
];

const PLANS: PlanCard[] = [
  {
    code: "start_99",
    name: "Start",
    price: "99 ₽",
    period: "30 дней",
    badge: "Мягкий вход",
    traffic: "Безлимитный трафик*",
    devices: "1 устройство",
    countries: "Нидерланды (NL)",
    speed: "Базовый профиль скорости",
    support: "Стандартная очередь",
  },
  {
    code: "pro_249",
    name: "Pro",
    price: "249 ₽",
    period: "1 месяц",
    badge: "Рекомендуем",
    traffic: "Безлимитный трафик*",
    devices: "До 5 устройств",
    countries: "PL • NL • USA • IT",
    speed: "Высокий профиль, типично 90-95% канала",
    support: "Быстрый ответ в Telegram",
    highlight: true,
  },
  {
    code: "ultra_1499",
    name: "Ultra / Family",
    price: "1499 ₽",
    period: "12 месяцев",
    badge: "Лучшая цена",
    traffic: "Безлимитный трафик*",
    devices: "До 5 устройств",
    countries: "Полный пул стран + приоритет",
    speed: "Максимальный профиль на близком узле",
    support: "Приоритет 24/7",
  },
];

const PLAN_COMPARISON = [
  { metric: "Цена", start: "99 ₽", pro: "249 ₽", ultra: "1499 ₽" },
  { metric: "Устройства", start: "1", pro: "до 5", ultra: "до 5" },
  { metric: "Трафик", start: "безлимит*", pro: "безлимит*", ultra: "безлимит*" },
  { metric: "Страны", start: "NL", pro: "PL/NL/USA/IT", ultra: "полный пул" },
  { metric: "Скорость", start: "базовая", pro: "высокая", ultra: "максимальная" },
  { metric: "Поддержка", start: "стандарт", pro: "ускоренная", ultra: "приоритет" },
];

const FAQS = [
  {
    q: "Что значит: часть медиасервисов может идти напрямую?",
    a: "Для некоторых потоковых сценариев прямой маршрут может дать меньшую задержку и стабильнее воспроизведение. VPN-канал при этом остается для основного трафика согласно вашему тарифу.",
  },
  {
    q: "Где наглядно видно, какой тариф лучше?",
    a: "В блоке сравнения выше: цена, устройства, скорость, страны и поддержка. Можно быстро понять разницу между Start, Pro и Ultra без скрытых условий.",
  },
  {
    q: "Premium (Pro/Ultra) безлимитный или лимитный?",
    a: "По трафику — безлимитный формат best-effort. Фактическая скорость зависит от вашей сети, локации и текущей нагрузки на узел.",
  },
  {
    q: "Как быстро начать использовать VPN?",
    a: "Откройте Telegram-бота или WebApp, выберите тариф, оплатите и импортируйте ключ в приложение. Обычно это 1-2 минуты.",
  },
];

const DEFAULT_LIVE_UPDATES: LiveUpdate[] = [
  {
    title: "Обновлены маршруты NL/PL",
    summary: "Снижена задержка для веба и видео, добавлены новые рекомендации по клиентам.",
    date: "2026-02-14",
    link: `https://t.me/${TG_NEWS_CHANNEL}/1`,
  },
  {
    title: "Улучшен личный кабинет",
    summary: "Обновили блок поддержки и сделали сравнение тарифов более наглядным.",
    date: "2026-02-13",
    link: `https://t.me/${TG_NEWS_CHANNEL}/2`,
  },
  {
    title: "Расширен checkout",
    summary: "Добавили более понятные состояния оплаты и отображение выгодных предложений.",
    date: "2026-02-12",
    link: `https://t.me/${TG_NEWS_CHANNEL}/3`,
  },
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

export default function HomePage() {
  const [scrolled, setScrolled] = useState(false);
  const [openedFaq, setOpenedFaq] = useState<number | null>(0);
  const [liveUpdates, setLiveUpdates] = useState<LiveUpdate[]>(DEFAULT_LIVE_UPDATES);
  const [socialCount, setSocialCount] = useState(2800);

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
    const onScroll = () => setScrolled(window.scrollY > 30);
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

    void loadLiveUpdates();
    void loadSocialProof();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <>
      <div className="lp-bg-blobs" aria-hidden="true" />

      <header className={`lp-nav ${scrolled ? "lp-nav--scrolled" : ""}`}>
        <a href="#main-content" className="lp-brand">
          <span>◍</span>
          PORTAL VPN
        </a>
        <nav className="lp-menu">
          <a href="#features">Преимущества</a>
          <a href="#pricing">Тарифы</a>
          <a href="#support">Поддержка</a>
          <a href="#faq">FAQ</a>
          <a href={WEBAPP_URL} target="_blank" rel="noreferrer" className="lp-chip">
            Войти через Telegram
          </a>
          <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
            Оплатить
          </a>
        </nav>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-kicker">PORTAL VPN • RUB CHECKOUT • ЛИЧНЫЙ КАБИНЕТ</div>
          <h1>
            Быстрый и понятный
            <br />
            <span>VPN для семьи и работы</span>
          </h1>
          <p>
            Подключение через Telegram, наглядное сравнение тарифов, оплата в рублях и поддержка 24/7.
            Всё, что нужно: ключ, устройства, тариф и помощь, в одном месте.
          </p>
          <div className="lp-hero-actions">
            <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
              Перейти к оплате
            </a>
            <a href={TG_BOT_FALLBACK} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
              Открыть Telegram-бота
            </a>
          </div>
          <div className="lp-proof">
            <div>
              <strong>{socialCount.toLocaleString("ru-RU")}</strong>
              <span>подключенных профилей</span>
            </div>
            <div>
              <strong>1-2 мин</strong>
              <span>средний запуск VPN</span>
            </div>
            <div>
              <strong>24/7</strong>
              <span>поддержка в Telegram</span>
            </div>
          </div>
        </section>

        <section id="features" className="lp-section">
          <div className="lp-section-head">
            <span>[Преимущества]</span>
            <h2>Что внутри сервиса</h2>
          </div>
          <div className="lp-feature-grid">
            {FEATURES.map((item, idx) => (
              <article className="lp-card" key={item.title}>
                <div className="lp-card-index">0{idx + 1}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>[Тарифы]</span>
            <h2>Наглядное сравнение VPN-планов</h2>
            <p>Чтобы сразу было понятно: где лимиты, где Premium и где максимальная скорость.</p>
          </div>

          <div className="lp-plan-grid">
            {PLANS.map((plan) => (
              <article key={plan.code} className={`lp-card lp-plan ${plan.highlight ? "lp-plan--highlight" : ""}`}>
                {plan.badge ? <div className="lp-badge">{plan.badge}</div> : null}
                <h3>{plan.name}</h3>
                <div className="lp-price">{plan.price}</div>
                <p className="lp-period">{plan.period}</p>
                <ul>
                  <li>{plan.traffic}</li>
                  <li>{plan.devices}</li>
                  <li>{plan.countries}</li>
                  <li>{plan.speed}</li>
                  <li>{plan.support}</li>
                </ul>
              </article>
            ))}
          </div>

          <div className="lp-compare-wrap">
            <table className="lp-compare-table">
              <thead>
                <tr>
                  <th>Параметр</th>
                  <th>Start</th>
                  <th>Pro</th>
                  <th>Ultra</th>
                </tr>
              </thead>
              <tbody>
                {PLAN_COMPARISON.map((row) => (
                  <tr key={row.metric}>
                    <td>{row.metric}</td>
                    <td>{row.start}</td>
                    <td>{row.pro}</td>
                    <td>{row.ultra}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="lp-clarify">
            <h3>Про «часть медиасервисов идёт напрямую» простыми словами</h3>
            <p>
              В отдельных сценариях прямой маршрут может снизить задержку для видео. При этом VPN-канал сохраняется
              для основного трафика по правилам выбранного тарифа. Ничего «скрытого» не происходит: параметры всегда
              отображаются в тарифе и в кабинете.
            </p>
            <p className="lp-disclaimer">
              * Безлимитный формат — по трафику. Скорость и стабильность зависят от вашей сети, маршрута и текущей нагрузки (best-effort).
            </p>
          </div>
        </section>

        <section id="support" className="lp-section">
          <div className="lp-section-head">
            <span>[Поддержка]</span>
            <h2>Раздел поддержки как в улучшенном mockup</h2>
            <p>FAQ, живой Telegram, тикеты и юридические документы — в одной точке.</p>
          </div>

          <div className="lp-support-grid">
            <article className="lp-card">
              <h3>Быстрые каналы</h3>
              <div className="lp-support-links">
                <a href={CONTACT_TG_URL} target="_blank" rel="noreferrer">
                  Telegram-поддержка
                </a>
                <a href={`mailto:${CONTACT_EMAIL}`}>Email support</a>
                <a href={`mailto:${ENTERPRISE_EMAIL}`}>Enterprise запрос</a>
                <a href={CONTACT_FORM_URL} target="_blank" rel="noreferrer">
                  Форма связи
                </a>
              </div>
            </article>

            <article className="lp-card">
              <h3>Личный кабинет</h3>
              <p>
                В кабинете доступны история тикетов, статус подписки, ключ подключения, устройства и оплата в рублях.
              </p>
              <div className="lp-hero-actions">
                <a href={WEBAPP_URL} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  Открыть кабинет
                </a>
                <a href={CHECKOUT_URL} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                  Открыть оплату
                </a>
              </div>
            </article>
          </div>
        </section>

        <section id="download" className="lp-section">
          <div className="lp-section-head">
            <span>[Скачать]</span>
            <h2>Клиенты для Android и Windows</h2>
          </div>
          <div className="lp-download-grid">
            <article className="lp-card">
              <h3>Android</h3>
              <p>Google Play и APK-канал для ручной установки.</p>
              <div className="lp-download-links">
                {androidLinks.length ? (
                  androidLinks.map((item) => (
                    <a key={item.key} href={item.url} target="_blank" rel="noreferrer">
                      {item.label}
                    </a>
                  ))
                ) : (
                  <span>Ссылки появятся после публикации сборки</span>
                )}
              </div>
            </article>

            <article className="lp-card">
              <h3>Windows</h3>
              <p>Основной установщик и резервный канал загрузки.</p>
              <div className="lp-download-links">
                {windowsLinks.length ? (
                  windowsLinks.map((item) => (
                    <a key={item.key} href={item.url} target="_blank" rel="noreferrer">
                      {item.label}
                    </a>
                  ))
                ) : (
                  <span>Ссылки появятся после публикации сборки</span>
                )}
              </div>
            </article>
          </div>
          {APP_DOCS_URL ? (
            <a href={APP_DOCS_URL} target="_blank" rel="noreferrer" className="lp-docs-link">
              Инструкция по установке
            </a>
          ) : null}
        </section>

        <section className="lp-section" id="news">
          <div className="lp-section-head">
            <span>[Обновления]</span>
            <h2>Свежие новости сервиса</h2>
          </div>
          <div className="lp-news-grid">
            {liveUpdates.map((item) => (
              <article key={`${item.date}-${item.title}`} className="lp-card">
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <a href={item.link} target="_blank" rel="noreferrer">
                  Открыть пост ({item.date})
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section" id="faq">
          <div className="lp-section-head">
            <span>[FAQ]</span>
            <h2>Вопросы и ответы</h2>
          </div>
          <div className="lp-faq-list">
            {FAQS.map((item, idx) => {
              const opened = openedFaq === idx;
              return (
                <article key={item.q} className="lp-faq-item">
                  <button
                    type="button"
                    onClick={() => setOpenedFaq(opened ? null : idx)}
                    aria-expanded={opened}
                    className="lp-faq-q"
                  >
                    <span>{item.q}</span>
                    <span>{opened ? "−" : "+"}</span>
                  </button>
                  {opened ? <p className="lp-faq-a">{item.a}</p> : null}
                </article>
              );
            })}
          </div>
        </section>
      </main>

      <footer className="lp-footer">
        <div>
          <h3>PORTAL VPN</h3>
          <p>
            Сервис VPN-доступа с управлением через Telegram и личный кабинет: подписка, ключи, устройства и поддержка.
          </p>
        </div>
        <div>
          <a href="/offer">Оферта</a>
          <a href="/privacy">Политика конфиденциальности</a>
          <a href={TG_BOT_FALLBACK} target="_blank" rel="noreferrer">
            Telegram-бот
          </a>
        </div>
      </footer>
    </>
  );
}
