import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

import { CANONICAL_CLIENT_BRAND, CANONICAL_MARKETING_SITE_URL, getCopyText, getPokrovPublicConfig } from "../lib/pokrov";
import { buildMarketingUrl, DEFAULT_MARKETING_SHARE_IMAGE_PATH, DEFAULT_MARKETING_TWITTER_IMAGE_PATH } from "../lib/marketing-site";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export type MarketingReview = {
  name: string;
  role: string;
  text: string;
};

type MarketingMetadataOptions = {
  path?: string;
  keywords?: string[];
  noIndex?: boolean;
};

type IconName = "app" | "arrow" | "cabinet" | "chat" | "compass" | "desktop" | "mobile" | "shield" | "spark";

type PromiseCard = {
  tag: string;
  icon: IconName;
  title: string;
  desc: string;
};

type StepCard = {
  icon: IconName;
  title: string;
  desc: string;
};

type HeroPanelPoint = {
  icon: IconName;
  title: string;
  text: string;
};

type DownloadCard = {
  title: string;
  status: string;
  desc: string;
  cta: string;
  href: string;
  icon: IconName;
};

const DEFAULT_REVIEWS: MarketingReview[] = [
  {
    name: "mikh****",
    role: "TELEGRAM • 28.12.2025",
    text: "Приложение поставил за пару минут, тест включился без карты, а дальше уже спокойно продлил доступ через кабинет без лишней суеты.",
  },
  {
    name: "anna****",
    role: "WINDOWS • 17.01.2026",
    text: "Наконец-то VPN, где всё понятно по-русски: скачать, проверить 5 дней, потом уже решить по оплате. И поддержка отвечает без лишних кругов.",
  },
  {
    name: "twst****",
    role: "TELEGRAM • 07.01.2026",
    text: "Хороший сервис, приятные цены и понятный путь от установки до продления без лишней суеты.",
  },
];

const PROMISE_CARDS: PromiseCard[] = [
  {
    tag: "Тест без карты",
    icon: "shield",
    title: "Сначала пробуете, потом решаете",
    desc: "Первые 5 дней нужны, чтобы спокойно проверить сервис в привычных сценариях. Без карты и без скрытого автосписания.",
  },
  {
    tag: "App-first",
    icon: "app",
    title: "Основной путь начинается в приложении",
    desc: "Android и Windows остаются главной точкой входа: быстрый запуск, понятные экраны и минимум лишних действий до первого подключения.",
  },
  {
    tag: "Поддержка под рукой",
    icon: "chat",
    title: "Кабинет и Telegram помогают, а не отвлекают",
    desc: "Личный кабинет, служба заботы и бонус за канал появляются в нужный момент и не подменяют сам продукт на первом шаге.",
  },
];

const STEPS: StepCard[] = [
  {
    icon: "mobile",
    title: "1. Скачайте приложение",
    desc: "Начните с Android или Windows: это основной и самый понятный вход в продукт.",
  },
  {
    icon: "spark",
    title: "2. Проверьте сервис в своих сценариях",
    desc: "Включите 5 дней теста, откройте привычные сайты и сервисы и посмотрите, подходит ли вам такой режим подключения.",
  },
  {
    icon: "cabinet",
    title: "3. Откройте кабинет, когда будете готовы",
    desc: "Продление и управление доступом начинаются только после личного входа, чтобы вы видели понятную сумму и рабочие способы оплаты.",
  },
];

const HERO_PANEL_POINTS: HeroPanelPoint[] = [
  {
    icon: "shield",
    title: "5 дней теста",
    text: "Можно спокойно проверить сервис без карты и без навязчивого сценария оплаты.",
  },
  {
    icon: "desktop",
    title: "Android и Windows уже готовы",
    text: "Публичная страница ведёт только к релизным приложениям или к честной инструкции.",
  },
  {
    icon: "chat",
    title: "Telegram остаётся рядом",
    text: "Служба заботы, новости и бонус за канал подключаются после старта, а не до него.",
  },
];

const FAQ = [
  {
    q: getCopyText("marketing.faq.1.q", "Как мне начать пользоваться сервисом?"),
    a: getCopyText(
      "marketing.faq.1.a",
      "Скачайте приложение для Android или Windows, включите бесплатный 5-дневный период и проверьте сервис в своих обычных сценариях.",
    ),
  },
  {
    q: getCopyText("marketing.faq.2.q", "Что я получу во время бесплатного теста?"),
    a: getCopyText(
      "marketing.faq.2.a",
      "Вы получаете полноценный доступ к сервису: те же основные локации, скорость и стабильность, что и после продления.",
    ),
  },
  {
    q: getCopyText("marketing.faq.3.q", "Как оформить платную подписку?"),
    a: getCopyText(
      "marketing.faq.3.a",
      "Сначала откройте кабинет или продолжите из Telegram. Уже после этого система покажет доступные способы оплаты и переведёт к завершению продления.",
    ),
  },
  {
    q: getCopyText("marketing.faq.4.q", "Куда обратиться, если возникнут вопросы?"),
    a: getCopyText(
      "marketing.faq.4.a",
      "Напишите в @pokrov_supportbot или на support@pokrov.space. Если нужно, поддержка подскажет понятный следующий шаг по оплате или подключению.",
    ),
  },
];

const RELATED_PAGES = [
  { href: "/vpn-dlya-youtube/", label: "VPN для YouTube" },
  { href: "/vpn-dlya-tiktok/", label: "VPN для TikTok" },
  { href: "/vpn-telegram-bot/", label: "Telegram и служба заботы" },
];

function firstNonEmpty(...values: Array<string | undefined>): string {
  return values.find((value) => Boolean(String(value || "").trim()))?.trim() || "";
}

function buildInstallHelpHref(): string {
  return firstNonEmpty(config.docsUrl, `${CANONICAL_MARKETING_SITE_URL}/`);
}

function buildCheckoutHref(planCode: string): string {
  return `/checkout/?plan=${encodeURIComponent(planCode)}`;
}

function buildMarketingPlans() {
  return [
    {
      code: "start_99",
      name: "Старт на 30 дней",
      price: "99 ₽",
      note: getCopyText("marketing.plan.start.note", "Хороший мягкий вход, если хотите продолжить после бесплатного периода."),
    },
    {
      code: "1_month",
      name: "1 месяц",
      price: "249 ₽",
      note: getCopyText("marketing.plan.month.note", "Гибкий ежемесячный вариант без длинных обязательств."),
    },
    {
      code: "3_months",
      name: "3 месяца",
      price: "699 ₽",
      note: getCopyText("marketing.plan.quarter.note", "Баланс между ценой и удобством для регулярного использования."),
    },
    {
      code: "6_months",
      name: "6 месяцев",
      price: "1199 ₽",
      note: getCopyText("marketing.plan.half.note", "Выгодный вариант, если сервис уже вписался в ваши ежедневные сценарии."),
    },
    {
      code: "12_months",
      name: "12 месяцев",
      price: "1644 ₽",
      note: getCopyText("marketing.plan.long.note", "Максимальная экономия для долгого стабильного доступа."),
    },
  ];
}

function buildDownloadCards(): DownloadCard[] {
  const installHelpHref = buildInstallHelpHref();

  return [
    {
      title: "Android",
      status: "Релиз",
      desc: "Основной мобильный путь: скачать APK, включить тест и проверить сервис без долгой настройки.",
      cta: getCopyText("marketing.download.android.cta", "Скачать для Android"),
      href: firstNonEmpty(config.androidApkUrl, installHelpHref),
      icon: "mobile",
    },
    {
      title: "Windows",
      status: "Релиз",
      desc: "Десктопный путь для постоянной работы и повседневных сценариев на ПК.",
      cta: getCopyText("marketing.download.windows.cta", "Скачать для Windows"),
      href: firstNonEmpty(config.windowsExeUrl, installHelpHref),
      icon: "desktop",
    },
    {
      title: "iPhone и Mac",
      status: "Подготовка",
      desc: "Для Apple пока держим только инструкцию и обновления. Публичная страница не обещает то, что ещё не выведено в релиз.",
      cta: getCopyText("marketing.download.apple.cta", "Инструкция и новости"),
      href: installHelpHref,
      icon: "compass",
    },
  ];
}

function MarketingIcon({ name, className }: { name: IconName; className?: string }) {
  switch (name) {
    case "app":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <rect x="5" y="3.5" width="14" height="17" rx="3" />
          <path d="M9 7h6" />
          <circle cx="12" cy="16.5" r="1" fill="currentColor" stroke="none" />
        </svg>
      );
    case "arrow":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <path d="M5 12h14" />
          <path d="m13 6 6 6-6 6" />
        </svg>
      );
    case "cabinet":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <rect x="4" y="4" width="16" height="7" rx="2" />
          <rect x="4" y="13" width="16" height="7" rx="2" />
          <path d="M9 7.5h6M9 16.5h6" />
        </svg>
      );
    case "chat":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <path d="M6 18.5c-1.3 0-2.5-1-2.5-2.4V8.4C3.5 7 4.7 6 6 6h12c1.3 0 2.5 1 2.5 2.4v7.7c0 1.4-1.2 2.4-2.5 2.4H11l-4 3v-3H6Z" />
        </svg>
      );
    case "compass":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <circle cx="12" cy="12" r="8" />
          <path d="m15.5 8.5-2.8 6.2-6.2 2.8 2.8-6.2 6.2-2.8Z" />
        </svg>
      );
    case "desktop":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <rect x="3.5" y="4.5" width="17" height="11" rx="2" />
          <path d="M8.5 19.5h7M12 15.5v4" />
        </svg>
      );
    case "mobile":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <rect x="7" y="3.5" width="10" height="17" rx="2.5" />
          <path d="M10 6.5h4" />
          <circle cx="12" cy="17" r="1" fill="currentColor" stroke="none" />
        </svg>
      );
    case "shield":
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <path d="M12 3.5 18 6v5c0 4.2-2.5 7.3-6 9.5-3.5-2.2-6-5.3-6-9.5V6l6-2.5Z" />
          <path d="m9.5 12.5 1.8 1.8 3.7-4" />
        </svg>
      );
    case "spark":
    default:
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
          <path d="M12 3.5 13.8 9l5.7 1.2-5.7 1.3L12 17l-1.8-5.5-5.7-1.3L10.2 9 12 3.5Z" />
          <path d="M18.5 3.5v3M20 5h-3M5.5 17.5v3M7 19h-3" />
        </svg>
      );
  }
}

export function buildMarketingMetadata(
  title = getCopyText("marketing.meta.title", "POKROV VPN — приложение VPN для Android и Windows"),
  description = getCopyText(
    "marketing.meta.description",
    "Скачайте приложение для Android или Windows, включите 5 дней бесплатного теста и переходите в кабинет только когда будете готовы.",
  ),
  options: MarketingMetadataOptions = {},
): Metadata {
  const canonical = buildMarketingUrl(options.path || "/");

  return {
    title,
    description,
    keywords: options.keywords,
    alternates: {
      canonical,
    },
    robots: options.noIndex
      ? {
          index: false,
          follow: true,
        }
      : {
          index: true,
          follow: true,
        },
    openGraph: {
      type: "website",
      locale: "ru_RU",
      siteName: CANONICAL_CLIENT_BRAND,
      title,
      description,
      url: canonical,
      images: [buildMarketingUrl(DEFAULT_MARKETING_SHARE_IMAGE_PATH)],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [buildMarketingUrl(DEFAULT_MARKETING_TWITTER_IMAGE_PATH)],
    },
  };
}

type MarketingLandingProps = {
  heroKicker?: string;
  heroTitle?: string;
  heroSubtitle?: string;
  clusterTitle?: string;
  clusterBody?: string;
  featuredReviews?: MarketingReview[];
};

export default function MarketingLanding({
  heroKicker,
  heroTitle,
  heroSubtitle,
  clusterTitle,
  clusterBody,
  featuredReviews,
}: MarketingLandingProps) {
  const reviews = featuredReviews?.length ? featuredReviews : DEFAULT_REVIEWS;
  const plans = buildMarketingPlans();
  const downloadCards = buildDownloadCards();

  return (
    <>
      <div className="lp-bg-blobs" aria-hidden="true" />
      <header className="lp-nav">
        <a href="#main-content" className="lp-brand">
          <Image src="/pokrov-logo.svg" alt="POKROV VPN" className="lp-brand-logo" width={28} height={28} priority />
          <span>POKROV VPN</span>
        </a>
        <nav className="lp-menu">
          <a href="#downloads">Приложение</a>
          <a href="#pricing">Планы</a>
          <a href="#faq">FAQ</a>
          <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
            <MarketingIcon name="cabinet" className="lp-chip-icon" />
            <span>Открыть кабинет</span>
          </a>
          <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
            <MarketingIcon name="chat" className="lp-chip-icon" />
            <span>Служба заботы</span>
          </a>
        </nav>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-hero-grid">
            <div className="lp-hero-copy">
              <div className="lp-kicker">
                {heroKicker || getCopyText("marketing.hero.kicker", "POKROV VPN • приложение сначала, кабинет потом")}
              </div>
              <h1>{heroTitle || getCopyText("marketing.hero.title", "Свободный интернет без лишней настройки")}</h1>
              <p>
                {heroSubtitle ||
                  getCopyText(
                    "marketing.hero.subtitle",
                    "Скачайте приложение для Android или Windows, включите 5 дней бесплатного теста и проверьте сервис в привычных сценариях. Кабинет и Telegram пригодятся позже — для продления, поддержки и бонуса за канал.",
                  )}
              </p>
              <div className="lp-hero-actions">
                <a href="#downloads" className="lp-btn lp-btn--primary">
                  <span>{getCopyText("marketing.hero.primary_cta", "Скачать приложение")}</span>
                  <MarketingIcon name="arrow" className="lp-btn-icon" />
                </a>
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                  <MarketingIcon name="cabinet" className="lp-btn-icon" />
                  <span>{getCopyText("marketing.hero.secondary_cta", "Открыть кабинет")}</span>
                </a>
              </div>
              <div className="lp-proof">
                <div>
                  <strong>{getCopyText("marketing.hero.proof_1.title", "5 дней")}</strong>
                  <span>{getCopyText("marketing.hero.proof_1.text", "бесплатного теста")}</span>
                </div>
                <div>
                  <strong>{getCopyText("marketing.hero.proof_2.title", "Android + Windows")}</strong>
                  <span>{getCopyText("marketing.hero.proof_2.text", "основные релизные платформы")}</span>
                </div>
                <div>
                  <strong>{getCopyText("marketing.hero.proof_3.title", "Живая поддержка")}</strong>
                  <span>{getCopyText("marketing.hero.proof_3.text", "служба заботы и продолжение через Telegram")}</span>
                </div>
              </div>
            </div>

            <aside className="lp-hero-panel">
              <div className="lp-panel-kicker">
                <span className="lp-icon-wrap lp-icon-wrap--small">
                  <MarketingIcon name="spark" className="lp-icon" />
                </span>
                <span>Consumer-first старт</span>
              </div>
              <h2>Понятный вход без лишних кругов</h2>
              <p>Публичная страница объясняет следующий шаг, а не прячет пользователя за техническими доменами и лишними обещаниями.</p>
              <div className="lp-panel-list">
                {HERO_PANEL_POINTS.map((item) => (
                  <article key={item.title} className="lp-panel-item">
                    <span className="lp-icon-wrap lp-icon-wrap--small">
                      <MarketingIcon name={item.icon} className="lp-icon" />
                    </span>
                    <div>
                      <strong>{item.title}</strong>
                      <span>{item.text}</span>
                    </div>
                  </article>
                ))}
              </div>
            </aside>
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Почему это удобно]</span>
            <h2>{getCopyText("marketing.promise.title", "Спокойный старт без лишних переходов")}</h2>
            <p>
              {getCopyText(
                "marketing.promise.subtitle",
                "Приложение остаётся первым шагом, кабинет нужен для управления, а Telegram помогает с поддержкой и продолжением только тогда, когда он действительно нужен.",
              )}
            </p>
          </div>
          <div className="lp-feature-grid">
            {PROMISE_CARDS.map((item) => (
              <article key={item.title} className="lp-card">
                <div className="lp-card-top">
                  <span className="lp-icon-wrap">
                    <MarketingIcon name={item.icon} className="lp-icon" />
                  </span>
                  <div className="lp-card-index">{item.tag}</div>
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="downloads" className="lp-section">
          <div className="lp-section-head">
            <span>[Приложение]</span>
            <h2>{getCopyText("marketing.downloads.title", "Выберите платформу и начните")}</h2>
            <p>
              {getCopyText(
                "marketing.downloads.subtitle",
                "Публичный сайт ведёт либо в реальную загрузку релизного приложения, либо в понятную инструкцию. Без скрытых переходов и запутанных адресов.",
              )}
            </p>
          </div>
          <div className="lp-download-grid">
            {downloadCards.map((card) => (
              <article key={card.title} className="lp-card lp-plan">
                <div className="lp-card-top">
                  <span className="lp-icon-wrap">
                    <MarketingIcon name={card.icon} className="lp-icon" />
                  </span>
                  <div className="lp-card-index">{card.status}</div>
                </div>
                <h3>{card.title}</h3>
                <p>{card.desc}</p>
                <a href={card.href} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary" style={{ marginTop: 20 }}>
                  <span>{card.cta}</span>
                  <MarketingIcon name="arrow" className="lp-btn-icon" />
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Как это работает]</span>
            <h2>{getCopyText("marketing.steps.title", "Как присоединиться за три шага")}</h2>
            <p>
              {getCopyText(
                "marketing.steps.subtitle",
                "Лендинг объясняет следующий шаг, а не пытается увести пользователя на случайный технический хост или на неясную страницу оплаты.",
              )}
            </p>
          </div>
          <div className="lp-feature-grid">
            {STEPS.map((item) => (
              <article key={item.title} className="lp-card">
                <div className="lp-card-top">
                  <span className="lp-icon-wrap">
                    <MarketingIcon name={item.icon} className="lp-icon" />
                  </span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>[Тарифы]</span>
            <h2>{getCopyText("marketing.pricing.title", "Тарифы без лишней путаницы")}</h2>
            <p>
              {getCopyText(
                "marketing.pricing.subtitle",
                "Публичная страница показывает стоимость и следующий шаг, а сам checkout открывается позже — уже внутри персонального сценария.",
              )}
            </p>
          </div>
          <div className="lp-plan-grid">
            {plans.map((plan, index) => (
              <article key={plan.code} className={`lp-card lp-plan ${index === plans.length - 1 ? "lp-plan--highlight" : ""}`}>
                <h3>{plan.name}</h3>
                <div className="lp-price">{plan.price}</div>
                <p>{plan.note}</p>
                <Link href={buildCheckoutHref(plan.code)} className="lp-btn lp-btn--ghost" style={{ marginTop: 20 }}>
                  <span>{getCopyText("marketing.plan.cta", "Открыть кабинет и продолжить")}</span>
                  <MarketingIcon name="arrow" className="lp-btn-icon" />
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Отзывы]</span>
            <h2>{getCopyText("marketing.reviews.title", "Что говорят пользователи")}</h2>
            <p>
              {getCopyText(
                "marketing.reviews.subtitle",
                "На лендинге остаются только аккуратные отзывы без лишней драмы и без обещаний, которых продукт не выполняет.",
              )}
            </p>
          </div>
          <div className="lp-feature-grid">
            {reviews.map((item) => (
              <article key={`${item.name}-${item.role}`} className="lp-card">
                <h3>{item.name}</h3>
                <p style={{ marginTop: 4, fontSize: 12, letterSpacing: "0.12em", textTransform: "uppercase" }}>{item.role}</p>
                <p>{item.text}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="faq" className="lp-section">
          <div className="lp-section-head">
            <span>[FAQ]</span>
            <h2>{getCopyText("marketing.faq.title", "Частые вопросы")}</h2>
          </div>
          <div className="lp-feature-grid">
            {FAQ.map((item) => (
              <article key={item.q} className="lp-card">
                <h3>{item.q}</h3>
                <p>{item.a}</p>
              </article>
            ))}
          </div>
        </section>

        {clusterTitle && clusterBody ? (
          <section className="lp-section">
            <div className="lp-section-head">
              <span>[Полезное]</span>
              <h2>{clusterTitle}</h2>
              <p>{clusterBody}</p>
            </div>
            <div className="lp-feature-grid">
              {RELATED_PAGES.map((item) => (
                <article key={item.href} className="lp-card">
                  <h3>{item.label}</h3>
                  <p>Полезный соседний сценарий, чтобы не дублировать одни и те же обещания на главной странице.</p>
                  <Link href={item.href} className="lp-btn lp-btn--ghost" style={{ marginTop: 20 }}>
                    <span>Открыть страницу</span>
                    <MarketingIcon name="arrow" className="lp-btn-icon" />
                  </Link>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section className="lp-section">
          <div className="lp-card lp-footer-card">
            <div>
              <h3>{getCopyText("marketing.footer.title", "POKROV VPN: спокойный старт с приложения")}</h3>
              <p>
                {getCopyText(
                  "marketing.footer.body",
                  "Скачайте приложение, проверьте сервис бесплатно и только потом переходите к кабинету, продлению и поддержке. Это честный и аккуратный путь для публичного запуска.",
                )}
              </p>
            </div>
            <div className="lp-footer-actions">
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                <MarketingIcon name="cabinet" className="lp-btn-icon" />
                <span>Открыть кабинет</span>
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                <MarketingIcon name="chat" className="lp-btn-icon" />
                <span>Служба заботы</span>
              </a>
              <a href={config.newsChannelUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                <MarketingIcon name="spark" className="lp-btn-icon" />
                <span>Канал новостей</span>
              </a>
              <a href={config.feedbackbotUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                <MarketingIcon name="chat" className="lp-btn-icon" />
                <span>Оставить отзыв</span>
              </a>
              <Link href="/offer/" className="lp-btn lp-btn--ghost">
                <MarketingIcon name="shield" className="lp-btn-icon" />
                <span>Оферта</span>
              </Link>
              <Link href="/privacy/" className="lp-btn lp-btn--ghost">
                <MarketingIcon name="shield" className="lp-btn-icon" />
                <span>Политика</span>
              </Link>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
