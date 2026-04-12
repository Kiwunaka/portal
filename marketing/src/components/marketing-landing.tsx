import type { Metadata } from "next";
import Link from "next/link";

import JsonLd from "./json-ld";
import { CANONICAL_CLIENT_BRAND, CANONICAL_MARKETING_SITE_URL, getCopyText, getPokrovPublicConfig } from "../lib/pokrov";
import {
  buildFaqJsonLd,
  buildMarketingUrl,
  buildSoftwareApplicationJsonLd,
  DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
  DEFAULT_MARKETING_SHARE_IMAGE_PATH,
  DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
  DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
} from "../lib/marketing-site";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export type MarketingReview = {
  name: string;
  role: string;
  text: string;
  date?: string;
};

type MarketingMetadataOptions = {
  path?: string;
  keywords?: string[];
  noIndex?: boolean;
};

type DownloadCard = {
  title: string;
  status: string;
  desc: string;
  cta: string;
  href: string;
};

type PlanCard = {
  code: string;
  name: string;
  price: string;
  note: string;
};

type PromiseCard = {
  eyebrow: string;
  glyph: GlyphName;
  title: string;
  desc: string;
};

type ScenarioCard = {
  eyebrow: string;
  glyph: GlyphName;
  title: string;
  desc: string;
};

type HeroSignal = {
  label: string;
  value: string;
  detail: string;
};

type GlyphName = "arc" | "orbit" | "route" | "shield" | "signal" | "window";

const DEFAULT_REVIEWS: MarketingReview[] = [
  {
    name: "mikh****",
    role: "TELEGRAM • 28.12.2025",
    text: "Приложение поставил за пару минут, тест включился без карты, а дальше уже спокойно продлил доступ через личный маршрут.",
  },
  {
    name: "anna****",
    role: "WINDOWS • 17.01.2026",
    text: "Наконец-то VPN, где всё понятно по-русски: скачать, проверить 5 дней, потом уже решить по оплате. И поддержка отвечает быстро.",
  },
  {
    name: "twst****",
    role: "TELEGRAM • 07.01.2026",
    text: "Хороший сервис, приятные цены и честный маршрут без пустых касс и лишней суеты.",
  },
];

const PROMISE_CARDS: PromiseCard[] = [
  {
    eyebrow: "Trial без декора",
    glyph: "shield",
    title: "Первые 5 дней действительно бесплатно",
    desc: "Сначала пробуете сервис в приложении, потом решаете, нужен ли вам платный доступ. Без карты и без скрытого автосписания.",
  },
  {
    eyebrow: "Тихий premium UI",
    glyph: "window",
    title: "Красивое и понятное приложение",
    desc: "Основной старт идёт через Android и Windows-приложения: быстрый запуск, понятные экраны и минимум лишних действий.",
  },
  {
    eyebrow: "Telegram по делу",
    glyph: "signal",
    title: "Поддержка и продолжение через Telegram",
    desc: "Telegram у нас не заменяет продукт, а помогает с поддержкой, бонусом за канал и безопасным продолжением маршрута, если это нужно.",
  },
];

const STEPS = [
  {
    title: "Скачайте приложение",
    desc: "Начните с Android или Windows: это основной и самый понятный вход в продукт.",
  },
  {
    title: "Проверьте сервис бесплатно",
    desc: "Получите 5 дней теста, запустите свои обычные сценарии и убедитесь, что маршрут работает стабильно.",
  },
  {
    title: "Продлите доступ через личный маршрут",
    desc: "Оплата и продление начинаются только после личного входа, чтобы пользователь видел только рабочие способы оплаты и честную сумму.",
  },
];

const HERO_SIGNALS: HeroSignal[] = [
  {
    label: "Премиум-тест",
    value: "5 дней",
    detail: "Реальный доступ без карты и без декоративного демо.",
  },
  {
    label: "Релизные платформы",
    value: "Android + Windows",
    detail: "Главный public маршрут уже строится вокруг приложений.",
  },
  {
    label: "Telegram бонус",
    value: "+10 дней",
    detail: "После привязки аккаунта и проверки канала.",
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
      "Вы получаете полноценный маршрут сервиса: те же основные локации, скорость и стабильность, что и у платного доступа.",
    ),
  },
  {
    q: getCopyText("marketing.faq.3.q", "Как оформить платную подписку?"),
    a: getCopyText(
      "marketing.faq.3.a",
      "Сначала откройте кабинет или персональный маршрут из Telegram. Уже после этого система покажет доступные способы оплаты и переведёт в кассу.",
    ),
  },
  {
    q: getCopyText("marketing.faq.4.q", "Куда обратиться, если возникнут вопросы?"),
    a: getCopyText(
      "marketing.faq.4.a",
      "Напишите в @pokrov_supportbot или на support@pokrov.space. Если нужно, поддержка переведёт и в резервный маршрут оплаты.",
    ),
  },
];

const RELATED_PAGES = [
  { href: "/bystryy-vpn-na-telefon/", label: "VPN на телефон" },
  { href: "/vpn-na-iphone-android-windows/", label: "VPN на Android и Windows" },
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

function buildMarketingPlans(): PlanCard[] {
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
      status: "Уже доступно",
      desc: "Основной мобильный путь: скачать APK, включить тест и проверить сервис без долгой настройки.",
      cta: getCopyText("marketing.download.android.cta", "Скачать для Android"),
      href: firstNonEmpty(config.androidApkUrl, installHelpHref),
    },
    {
      title: "Windows",
      status: "Уже доступно",
      desc: "Десктопный путь для постоянной работы и повседневных сценариев на ПК.",
      cta: getCopyText("marketing.download.windows.cta", "Скачать для Windows"),
      href: firstNonEmpty(config.windowsExeUrl, installHelpHref),
    },
    {
      title: "iPhone и Mac",
      status: "Readiness only",
      desc: "Apple-линейка пока не релизнута. Здесь мы честно ведём только в инструкцию и обновления без ложного обещания доступности.",
      cta: getCopyText("marketing.download.apple.cta", "Инструкция и новости"),
      href: installHelpHref,
    },
  ];
}

function glyphForPlatform(title: string): GlyphName {
  if (title === "Android") return "arc";
  if (title === "Windows") return "window";
  return "orbit";
}

function LandingGlyph({ name }: { name: GlyphName }) {
  if (name === "shield") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M12 3.5 18.5 6v5.6c0 4.3-2.4 7.7-6.5 8.9-4.1-1.2-6.5-4.6-6.5-8.9V6L12 3.5Z" />
        <path d="m9.4 12 1.7 1.8 3.5-4" />
      </svg>
    );
  }

  if (name === "signal") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 17c1.9-2.1 4.2-3.2 7-3.2s5.1 1.1 7 3.2" />
        <path d="M8 13.3c1.1-1.1 2.5-1.7 4-1.7s2.9.6 4 1.7" />
        <path d="M10.8 10c.4-.3.8-.4 1.2-.4s.8.1 1.2.4" />
        <circle cx="12" cy="18.2" r="1.2" />
      </svg>
    );
  }

  if (name === "window") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <rect x="4.5" y="4.5" width="15" height="15" rx="3" />
        <path d="M4.5 10.5h15" />
        <path d="M12 10.5v9" />
      </svg>
    );
  }

  if (name === "orbit") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="2.2" />
        <path d="M12 4.5c3.9 0 7.5 2.2 7.5 7.5S15.9 19.5 12 19.5 4.5 15.9 4.5 12 8.1 4.5 12 4.5Z" />
        <path d="M6 7.5c2.2 1.3 4.5 2 6 2 1.5 0 3.8-.7 6-2" />
      </svg>
    );
  }

  if (name === "route") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="6.5" cy="6.5" r="1.8" />
        <circle cx="17.5" cy="17.5" r="1.8" />
        <path d="M8.2 6.5h3.2c2.7 0 4.1 1.4 4.1 4.1v2.9" />
        <path d="m13.7 14.9 1.8 1.8 2-2" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m12 3.5 2.1 4.8 5.2.4-4 3.5 1.2 5-4.5-2.7-4.5 2.7 1.2-5-4-3.5 5.2-.4L12 3.5Z" />
    </svg>
  );
}

export function buildMarketingMetadata(
  title = getCopyText("marketing.meta.title", "POKROV VPN — быстрый VPN для Android и Windows"),
  description = getCopyText(
    "marketing.meta.description",
    "Скачайте приложение для Android или Windows, получите 5 дней бесплатно и продолжайте через личный кабинет и безопасный checkout-маршрут.",
  ),
  options: MarketingMetadataOptions = {},
): Metadata {
  const canonical = buildMarketingUrl(options.path || "/");
  const shareAlt = `${title} | ${CANONICAL_CLIENT_BRAND}`;

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
      images: [
        {
          url: buildMarketingUrl(DEFAULT_MARKETING_SHARE_IMAGE_PATH),
          width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
          height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
          alt: shareAlt,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description,
      images: [
        {
          url: buildMarketingUrl(DEFAULT_MARKETING_TWITTER_IMAGE_PATH),
          width: DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
          height: DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
          alt: shareAlt,
        },
      ],
    },
  };
}

function resolveReviewDate(review: MarketingReview): string | undefined {
  if (review.date?.trim()) {
    return review.date.trim();
  }

  const match = review.role.match(/(\d{2})\.(\d{2})\.(\d{4})/);
  if (!match) {
    return undefined;
  }

  const [, day, month, year] = match;
  return `${year}-${month}-${day}`;
}

function buildReviewJsonLdInput(reviews: MarketingReview[]) {
  return reviews
    .filter((item) => item.name.trim() && item.text.trim())
    .map((item) => ({
      author: item.name,
      body: item.text,
      datePublished: resolveReviewDate(item),
    }));
}

type MarketingLandingProps = {
  pagePath?: string;
  heroKicker?: string;
  heroTitle?: string;
  heroSubtitle?: string;
  scenarioTitle?: string;
  scenarioBody?: string;
  scenarioCards?: ScenarioCard[];
  clusterTitle?: string;
  clusterBody?: string;
  featuredReviews?: MarketingReview[];
};

export default function MarketingLanding({
  pagePath = "/",
  heroKicker,
  heroTitle,
  heroSubtitle,
  scenarioTitle,
  scenarioBody,
  scenarioCards,
  clusterTitle,
  clusterBody,
  featuredReviews,
}: MarketingLandingProps) {
  const reviews = featuredReviews?.length ? featuredReviews : DEFAULT_REVIEWS;
  const spotlightReview = reviews[0] || DEFAULT_REVIEWS[0];
  const plans = buildMarketingPlans();
  const downloadCards = buildDownloadCards();
  const relatedPages = RELATED_PAGES.filter((item) => item.href !== pagePath);
  const softwareApplicationJsonLd = buildSoftwareApplicationJsonLd({
    pagePath,
    reviews: buildReviewJsonLdInput(reviews),
  });
  const faqJsonLd =
    pagePath === "/"
      ? buildFaqJsonLd(
          FAQ.map((item) => ({
            question: item.q,
            answer: item.a,
          })),
        )
      : null;
  const relatedTitle = clusterTitle || "Сценарии и ответы под ваш запрос";
  const relatedBody =
    clusterBody ||
    "Отсюда удобно перейти к соседним страницам по сценариям использования и выбрать тот маршрут, который ближе именно вам.";

  return (
    <>
      <JsonLd data={softwareApplicationJsonLd} />
      {faqJsonLd ? <JsonLd data={faqJsonLd} /> : null}
      <div className="lp-bg-blobs" aria-hidden="true" />

      <header className="lp-nav">
        <div className="lp-nav-shell">
          <Link href="/" className="lp-brand">
            <img src="/pokrov-logo.svg" alt="POKROV VPN" className="lp-brand-logo" />
            <span>POKROV VPN</span>
          </Link>
          <nav className="lp-menu" aria-label="Главная навигация">
            <Link href="/">Главная</Link>
            <Link href="/bystryy-vpn-na-telefon/">На телефон</Link>
            <Link href="/vpn-na-iphone-android-windows/">Устройства</Link>
            <a href="#downloads">Приложение</a>
            <a href="#pricing">Планы</a>
            <a href="#faq">FAQ</a>
            <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
              Открыть кабинет
            </a>
            <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
              Служба заботы
            </a>
          </nav>
        </div>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-hero-copy">
            <div className="lp-kicker">{heroKicker || getCopyText("marketing.hero.kicker", "POKROV VPN • первые 5 дней бесплатно")}</div>
            <p className="lp-overline">Consumer-first VPN с тихим premium маршрутом для Android и Windows.</p>
            <h1>{heroTitle || getCopyText("marketing.hero.title", "Свободный интернет, который начинается с приложения")}</h1>
            <p className="lp-hero-lead">
              {heroSubtitle ||
                getCopyText(
                  "marketing.hero.subtitle",
                  "Сначала скачиваете приложение для Android или Windows, потом спокойно проверяете сервис в реальных сценариях. Кабинет и Telegram остаются для управления, оплаты и поддержки, а не подменяют сам продукт.",
                )}
            </p>
            <div className="lp-hero-actions">
              <a href="#downloads" className="lp-btn lp-btn--primary">
                {getCopyText("marketing.hero.primary_cta", "Начать бесплатно")}
              </a>
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                {getCopyText("marketing.hero.secondary_cta", "Открыть кабинет")}
              </a>
            </div>
            <dl className="lp-proof">
              {HERO_SIGNALS.map((signal) => (
                <div key={signal.label}>
                  <dt>{signal.label}</dt>
                  <dd>
                    <span className="lp-proof-value">{signal.value}</span>
                    <span className="lp-proof-detail">{signal.detail}</span>
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="lp-hero-stage">
            <article className="lp-stage-card lp-stage-card--primary">
              <div className="lp-stage-label">
                <LandingGlyph name="route" />
                App-first маршрут
              </div>
              <h2>Один спокойный путь без шума и ложных shortcut.</h2>
              <p>
                Лендинг не уводит в технический host и не делает Telegram обязательным: сначала приложение, затем кабинет и checkout только в личном контексте.
              </p>
              <ol className="lp-stage-steps">
                {STEPS.map((item, index) => (
                  <li key={item.title}>
                    <span>{`0${index + 1}`}</span>
                    <div>
                      <strong>{item.title}</strong>
                      <p>{item.desc}</p>
                    </div>
                  </li>
                ))}
              </ol>
            </article>

            <article className="lp-stage-card">
              <div className="lp-stage-label">
                <LandingGlyph name="signal" />
                Telegram остаётся вторичным
              </div>
              <p>
                Он нужен для бонуса, продолжения покупки, поддержки и новостей, но не заменяет старт внутри приложения и не ломает app-first truth.
              </p>
              <div className="lp-stage-links">
                <a href={config.newsChannelUrl} target="_blank" rel="noreferrer">
                  Канал POKROV
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer">
                  Поддержка
                </a>
                <a href={config.webappUrl} target="_blank" rel="noreferrer">
                  Кабинет
                </a>
              </div>
            </article>

            <article className="lp-stage-card lp-stage-card--quote">
              <div className="lp-stage-label">
                <LandingGlyph name="arc" />
                Сигнал доверия
              </div>
              <blockquote>{spotlightReview.text}</blockquote>
              <span>
                {spotlightReview.name} • {spotlightReview.role}
              </span>
            </article>
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>Преимущества</span>
            <h2>{getCopyText("marketing.promise.title", "Тихая роскошь здесь не про шум, а про контроль маршрута")}</h2>
            <p>
              {getCopyText(
                "marketing.promise.subtitle",
                "POKROV ведёт пользователя через приложение, честный trial, личный кабинет и спокойное продление. Каждая секция отвечает только за один шаг этой истории.",
              )}
            </p>
          </div>
          <div className="lp-trust-grid">
            {PROMISE_CARDS.map((item) => (
              <article key={item.title} className="lp-trust-card">
                <div className="lp-stage-label">
                  <LandingGlyph name={item.glyph} />
                  {item.eyebrow}
                </div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        {scenarioCards?.length ? (
          <section className="lp-section">
            <div className="lp-section-head">
              <span>Сценарий</span>
              <h2>{scenarioTitle || "Маршрут под конкретный запрос"}</h2>
              <p>{scenarioBody || "Ниже собрали только те шаги и детали, которые важны именно для этого сценария использования."}</p>
            </div>
            <div className="lp-trust-grid">
              {scenarioCards.map((item) => (
                <article key={item.title} className="lp-trust-card">
                  <div className="lp-stage-label">
                    <LandingGlyph name={item.glyph} />
                    {item.eyebrow}
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.desc}</p>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section id="downloads" className="lp-section">
          <div className="lp-section-head">
            <span>Приложение</span>
            <h2>{getCopyText("marketing.downloads.title", "Установите приложение и начните именно с него")}</h2>
            <p>
              {getCopyText(
                "marketing.downloads.subtitle",
                "Публичный сайт должен вести либо в реальную загрузку релизного приложения, либо в понятную инструкцию. Без скрытого прыжка в connect-host.",
              )}
            </p>
          </div>
          <div className="lp-download-grid">
            {downloadCards.map((card, index) => (
              <article key={card.title} className={`lp-platform-card${index === 0 ? " lp-platform-card--featured" : ""}`}>
                <div className="lp-stage-label">
                  <LandingGlyph name={glyphForPlatform(card.title)} />
                  {card.status}
                </div>
                <h3>{card.title}</h3>
                <p>{card.desc}</p>
                <a href={card.href} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                  {card.cta}
                </a>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>Тарифы</span>
            <h2>{getCopyText("marketing.pricing.title", "Тарифы выглядят premium, но ведут только в честный checkout")}</h2>
            <p>
              {getCopyText(
                "marketing.pricing.subtitle",
                "Публичная страница может показать стоимость и следующий шаг, но сама касса открывается уже из персонального сценария, когда понятен пользователь и доступны реальные способы оплаты.",
              )}
            </p>
          </div>
          <div className="lp-pricing-shell">
            <aside className="lp-pricing-intro">
              <div className="lp-stage-label">
                <LandingGlyph name="orbit" />
                Честный checkout
              </div>
              <h3>Сначала личный кабинет, потом касса.</h3>
              <p>
                Это сохраняет app-first truth: маркетинг объясняет следующий шаг, а оплата открывается только после личного входа или продолжения через Telegram по необходимости.
              </p>
              <ul className="lp-pricing-points">
                <li>Показываем только доступные способы оплаты и честную сумму.</li>
                <li>Не отправляем пользователя в raw connect-host.</li>
                <li>Оставляем Telegram как опциональный контур поддержки и бонуса.</li>
              </ul>
            </aside>

            <div className="lp-plan-grid">
              {plans.map((plan, index) => (
                <article key={plan.code} className={`lp-plan-card${index === plans.length - 1 ? " lp-plan-card--highlight" : ""}`}>
                  {index === plans.length - 1 ? <span className="lp-badge">Макс. выгода</span> : null}
                  <h3>{plan.name}</h3>
                  <div className="lp-price">{plan.price}</div>
                  <p>{plan.note}</p>
                  <Link href={buildCheckoutHref(plan.code)} className="lp-btn lp-btn--ghost">
                    {getCopyText("marketing.plan.cta", "Открыть кабинет и продолжить")}
                  </Link>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="lp-section lp-section--split">
          <div className="lp-conversation-grid">
            <div>
              <div className="lp-section-head">
                <span>Отзывы</span>
                <h2>{getCopyText("marketing.reviews.title", "Доверие собирается из спокойных, конкретных отзывов")}</h2>
                <p>
                  {getCopyText(
                    "marketing.reviews.subtitle",
                    "На лендинге остаются только аккуратные отзывы без лишней драмы и без обещаний, которых продукт не выполняет.",
                  )}
                </p>
              </div>
              <div className="lp-review-list">
                {reviews.map((item) => (
                  <article key={`${item.name}-${item.role}`} className="lp-review-card">
                    <p className="lp-review-text">{item.text}</p>
                    <div className="lp-review-meta">
                      <strong>{item.name}</strong>
                      <span>{item.role}</span>
                    </div>
                  </article>
                ))}
              </div>
            </div>

            <div id="faq">
              <div className="lp-section-head">
                <span>FAQ</span>
                <h2>{getCopyText("marketing.faq.title", "Частые вопросы без лишнего слоя интерфейса")}</h2>
                <p>Короткие ответы держат маршрут понятным: приложение сначала, кабинет и Telegram только там, где они действительно нужны.</p>
              </div>
              <div className="lp-faq-list">
                {FAQ.map((item) => (
                  <div key={item.q}>
                    <details className="lp-faq-item">
                      <summary className="lp-faq-q">
                        <span>{item.q}</span>
                        <span className="lp-faq-icon" aria-hidden="true">
                          +
                        </span>
                      </summary>
                      <p className="lp-faq-a">{item.a}</p>
                    </details>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>Полезное</span>
            <h2>{relatedTitle}</h2>
            <p>{relatedBody}</p>
          </div>
          <div className="lp-related-grid">
            {relatedPages.map((item) => (
              <article key={item.href} className="lp-related-card">
                <div className="lp-stage-label">
                  <LandingGlyph name="route" />
                  Связанный сценарий
                </div>
                <h3>{item.label}</h3>
                <p>Отдельная страница под конкретный запрос, но с тем же app-first маршрутом и без doorway-шума.</p>
                <Link href={item.href} className="lp-btn lp-btn--ghost">
                  Открыть страницу
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-footer-cta">
            <div className="lp-footer-copy">
              <span>Финальный CTA</span>
              <h2>{getCopyText("marketing.footer.title", "POKROV VPN: сначала приложение, потом всё остальное")}</h2>
              <p>
                {getCopyText(
                  "marketing.footer.body",
                  "Скачайте приложение, проверьте сервис бесплатно и только потом переходите к кабинету, продлению и поддержке. Это честный и безопасный путь для публичного запуска.",
                )}
              </p>
            </div>
            <div className="lp-footer-rail">
              <div>
                <strong>Android + Windows</strong>
                <span>основной релизный контур</span>
              </div>
              <div>
                <strong>5 дней</strong>
                <span>реального premium-теста</span>
              </div>
              <div>
                <strong>+10 дней</strong>
                <span>за канал после привязки Telegram</span>
              </div>
            </div>
            <div className="lp-footer-actions">
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                Открыть кабинет
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Служба заботы
              </a>
              <a href={config.newsChannelUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Канал новостей
              </a>
              <a href={config.feedbackbotUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Оставить отзыв
              </a>
              <Link href="/offer/" className="lp-btn lp-btn--ghost">
                Оферта
              </Link>
              <Link href="/privacy/" className="lp-btn lp-btn--ghost">
                Политика
              </Link>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
