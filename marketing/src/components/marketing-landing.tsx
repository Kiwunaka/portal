import type { Metadata } from "next";
import Link from "next/link";

import JsonLd from "./json-ld";
import {
  buildFaqJsonLd,
  buildMarketingUrl,
  buildSoftwareApplicationJsonLd,
  DEFAULT_MARKETING_SHARE_IMAGE_HEIGHT,
  DEFAULT_MARKETING_SHARE_IMAGE_PATH,
  DEFAULT_MARKETING_SHARE_IMAGE_WIDTH,
  DEFAULT_MARKETING_TWITTER_IMAGE_PATH,
  MARKETING_CANONICAL_PATHS,
  MARKETING_FAQ,
} from "../lib/marketing-site";
import {
  CANONICAL_PLATFORM_BRAND,
  CANONICAL_PUBLIC_PLATFORM_SCOPE,
  getPokrovPublicConfig,
  getTariffPlans,
} from "../lib/pokrov";

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

type ScenarioCard = {
  eyebrow: string;
  glyph: GlyphName;
  title: string;
  desc: string;
};

type HeroFact = {
  label: string;
  value: string;
  detail: string;
};

type DownloadCard = {
  title: string;
  status: string;
  desc: string;
  href: string;
  cta: string;
};

type PlanCard = {
  code: string;
  label: string;
  price: string;
  note: string;
  badge?: string | null;
  duration: string;
  devices: string;
};

type GlyphName = "route" | "shield" | "signal" | "window" | "orbit" | "arc";

const DEFAULT_REVIEWS: MarketingReview[] = [
  {
    name: "mikh****",
    role: "ANDROID • 28.12.2025",
    text: "Поставил приложение, включил пробные 5 дней и спокойно проверил всё в обычном режиме. Потом уже купил ключ доступа.",
  },
  {
    name: "anna****",
    role: "WINDOWS • 17.01.2026",
    text: "Понравилось, что не пришлось идти в чат до первого запуска. Сначала приложение, потом кабинет и продление.",
  },
  {
    name: "twst****",
    role: "TELEGRAM • 07.01.2026",
    text: "Telegram пригодился для бонуса и поддержки, но пользоваться можно без постоянной переписки.",
  },
];

const HERO_FACTS: HeroFact[] = [
  {
    label: "Публично сейчас",
    value: "Android и Windows",
    detail: "Apple пока в подготовке, без лишних обещаний и фиктивных кнопок.",
  },
  {
    label: "Стартовый доступ",
    value: "5 дней",
    detail: "Первое устройство может спокойно проверить продукт без обязательного Telegram.",
  },
  {
    label: "Режим по умолчанию",
    value: "Все, кроме RU",
    detail: "Понятный выбор для ежедневного доступа, без ручной настройки на старте.",
  },
];

const DEFAULT_SCENARIOS: ScenarioCard[] = [
  {
    eyebrow: "Сначала приложение",
    glyph: "route",
    title: "Старт без лишней переписки",
    desc: "Сайт ведёт к установке, приложение даёт 5 дней проверки, а кабинет помогает с доступом, поддержкой и ключами.",
  },
  {
    eyebrow: "Ключ доступа",
    glyph: "shield",
    title: "Оплата понятным ключом",
    desc: "После оплаты вы получаете ключ доступа и активируете его в приложении или кабинете.",
  },
  {
    eyebrow: "Telegram по делу",
    glyph: "signal",
    title: "Восстановление, поддержка и бонус +10 дней",
    desc: "Telegram нужен для восстановления, поддержки и бонуса, но не заменяет основной старт через приложение.",
  },
];

const KEY_FLOW_STEPS = [
  "Установите приложение для Android или Windows.",
  "Нажмите «Попробовать 5 дней» на первом устройстве.",
  "Если срок закончился, останется базовый бесплатный доступ.",
  "Выберите срок, купите ключ доступа и активируйте его в приложении или кабинете.",
];

const RELATED_PAGES = [
  { href: MARKETING_CANONICAL_PATHS.mobile, label: "На телефоне" },
  { href: MARKETING_CANONICAL_PATHS.devices, label: "Android и Windows" },
  { href: MARKETING_CANONICAL_PATHS.telegram, label: "Telegram +10 дней" },
  { href: MARKETING_CANONICAL_PATHS.youtube, label: "Длинные видео" },
  { href: MARKETING_CANONICAL_PATHS.tiktok, label: "Короткие видео" },
];

function firstNonEmpty(...values: Array<string | undefined>): string {
  return values.find((value) => Boolean(String(value || "").trim()))?.trim() || "";
}

function buildInstallHref(): string {
  return buildMarketingUrl(MARKETING_CANONICAL_PATHS.install);
}

function buildCheckoutHref(planCode: string): string {
  return `/checkout/?plan=${encodeURIComponent(planCode)}`;
}

function buildDownloadCards(): DownloadCard[] {
  const installHref = buildInstallHref();

  return [
    {
      title: "Android",
      status: "Основной путь",
      desc: "Установите приложение, нажмите «Попробовать 5 дней» и проверьте доступ в привычных мобильных задачах.",
      href: firstNonEmpty(config.androidApkUrl, config.androidPlayUrl, installHref),
      cta: "Попробовать 5 дней",
    },
    {
      title: "Windows",
      status: "Основной путь",
      desc: "Проверьте POKROV на компьютере, а продление и ключи оставьте кабинету.",
      href: firstNonEmpty(config.windowsExeUrl, installHref),
      cta: "Попробовать 5 дней",
    },
    {
      title: "Apple",
      status: "Готовится",
      desc: "iPhone и Mac пока показываются только как подготовка. Без дат, обещаний запуска и кнопок скачивания.",
      href: installHref,
      cta: "Что готовится",
    },
  ];
}

function buildPlanCards(): PlanCard[] {
  return getTariffPlans()
    .filter((plan) => Boolean(plan.is_active))
    .slice()
    .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
    .map((plan) => ({
      code: plan.code,
      label: plan.label,
      price: `${Number(plan.amount_rub || 0)} ₽`,
      note: plan.marketing_note || plan.cabinet_note || plan.label,
      badge: plan.badge || null,
      duration: `${Number(plan.duration_days || 0)} дней`,
      devices: `До ${Number(plan.device_limit || 1)} устройств`,
    }));
}

export function buildMarketingMetadata(
  title = "POKROV | Спокойный доступ без возни",
  description =
    "Попробуйте POKROV 5 дней в приложении для Android или Windows, а затем продолжайте через понятный ключ доступа.",
  options: MarketingMetadataOptions = {},
): Metadata {
  const canonical = buildMarketingUrl(options.path || "/");
  const shareAlt = `${title} | ${CANONICAL_PLATFORM_BRAND}`;

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
      siteName: CANONICAL_PLATFORM_BRAND,
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

function ThemeToggleIcon({ mode }: { mode: "sun" | "moon" }) {
  if (mode === "sun") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="4.1" />
        <path d="M12 2.8v2.5" />
        <path d="M12 18.7v2.5" />
        <path d="m5.5 5.5 1.8 1.8" />
        <path d="m16.7 16.7 1.8 1.8" />
        <path d="M2.8 12h2.5" />
        <path d="M18.7 12h2.5" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M18.2 15.4A6.7 6.7 0 0 1 9.1 6.3 7.8 7.8 0 1 0 18.2 15.4Z" />
    </svg>
  );
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
      </svg>
    );
  }

  if (name === "arc") {
    return (
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 14.5c1.9-4.9 11.8-8.1 14-4.5 1.4 2.3-1 6.3-4.6 8.1-4.3 2.2-10.2 1.5-10.9-1.8-.3-1.4.3-2.7 1.5-3.7Z" />
      </svg>
    );
  }

  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="6.5" cy="6.5" r="1.8" />
      <circle cx="17.5" cy="17.5" r="1.8" />
      <path d="M8.2 6.5h3.2c2.7 0 4.1 1.4 4.1 4.1v2.9" />
      <path d="m13.7 14.9 1.8 1.8 2-2" />
    </svg>
  );
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
  const plans = buildPlanCards();
  const downloadCards = buildDownloadCards();
  const relatedPages = RELATED_PAGES.filter((item) => item.href !== pagePath);
  const currentScenarios = scenarioCards?.length ? scenarioCards : DEFAULT_SCENARIOS;
  const defaultCheckoutHref = buildCheckoutHref(plans[0]?.code || "1_month");
  const softwareApplicationJsonLd = buildSoftwareApplicationJsonLd({
    pagePath,
    reviews: buildReviewJsonLdInput(reviews),
  });
  const faqJsonLd = pagePath === "/" ? buildFaqJsonLd(MARKETING_FAQ) : null;

  return (
    <>
      <JsonLd data={softwareApplicationJsonLd} />
      {faqJsonLd ? <JsonLd data={faqJsonLd} /> : null}

      <header className="lp-header">
        <div className="lp-header-shell">
          <div className="lp-brand">
            <span className="lp-nav-branding">
              <img src="/pokrov-logo.svg" alt="" className="lp-brand-logo" aria-hidden="true" />
              <Link href="/">POKROV</Link>
            </span>
          </div>
          <div className="lp-theme-toggle-wrap">
            <button
              type="button"
              className="lp-theme-toggle"
              data-theme-toggle
              aria-pressed="false"
              aria-label="Переключить тему"
              title="Переключить тему"
            >
              <span className="lp-theme-toggle__track" aria-hidden="true">
                <span className="lp-theme-toggle__icon lp-theme-toggle__icon--sun">
                  <ThemeToggleIcon mode="sun" />
                </span>
                <span className="lp-theme-toggle__thumb" />
                <span className="lp-theme-toggle__icon lp-theme-toggle__icon--moon">
                  <ThemeToggleIcon mode="moon" />
                </span>
              </span>
              <span className="sr-only">Переключить тему</span>
            </button>
          </div>
          <nav className="lp-menu" aria-label="Главная навигация">
            <div className="lp-nav-links">
              <Link href="/">Главная</Link>
              <Link href={MARKETING_CANONICAL_PATHS.install}>Установить</Link>
              <Link href={MARKETING_CANONICAL_PATHS.devices}>Устройства</Link>
              <a href="#pricing">Тарифы</a>
              <a href="#faq">FAQ</a>
            </div>
            <div className="lp-nav-actions">
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
                Кабинет
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
                Поддержка
              </a>
            </div>
          </nav>
        </div>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-hero-copy">
            <div className="lp-kicker">{heroKicker || "POKROV • Android + Windows"}</div>
            <p className="lp-overline">
              Публичный старт этой волны идёт через приложение. Сайт объясняет следующий шаг, а кабинет помогает продлить или восстановить доступ.
            </p>
            <h1>{heroTitle || "Спокойный доступ без возни: приложение, 5 дней проверки и понятное продление"}</h1>
            <p className="lp-hero-lead">
              {heroSubtitle ||
                "POKROV не заставляет разбираться в настройках до первого запуска. Сначала приложение для Android или Windows, затем 5 дней проверки, потом бесплатный базовый режим или ключ доступа."}
            </p>
            <div className="lp-hero-actions">
              <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                Попробовать 5 дней
              </Link>
              <Link href={defaultCheckoutHref} className="lp-btn lp-btn--ghost">
                Выбрать срок
              </Link>
            </div>
            <dl className="lp-proof">
              {HERO_FACTS.map((fact) => (
                <div key={fact.label}>
                  <dt>{fact.label}</dt>
                  <dd>
                    <span className="lp-proof-value">{fact.value}</span>
                    <span className="lp-proof-detail">{fact.detail}</span>
                  </dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="lp-hero-stage">
            <article className="lp-stage-card lp-stage-card--primary">
              <div className="lp-stage-label">
                <LandingGlyph name="route" />
                Как начать
              </div>
              <h2>Одна понятная история: попробовать, подключиться, продлить.</h2>
              <p>
                На публичных страницах видно главное: текущие платформы{" "}
                <strong>{CANONICAL_PUBLIC_PLATFORM_SCOPE.join(" + ")}</strong>, пробные 5 дней и честный следующий шаг.
              </p>
              <ol className="lp-stage-steps">
                {KEY_FLOW_STEPS.map((step, index) => (
                  <li key={step}>
                    <span>{`0${index + 1}`}</span>
                    <div>
                      <strong>{step}</strong>
                    </div>
                  </li>
                ))}
              </ol>
            </article>

            <article className="lp-stage-card">
              <div className="lp-stage-label">
                <LandingGlyph name="signal" />
                Telegram остаётся дополнительным
              </div>
              <p>
                Telegram остаётся для восстановления, бонуса +10 дней, новостей и поддержки. Он не подменяет основной старт через приложение.
              </p>
              <div className="lp-stage-links">
                <a href={config.newsChannelUrl} target="_blank" rel="noreferrer">
                  Канал
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
                Отзыв
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
            <span>Обещание</span>
            <h2>Публичные страницы объясняют продукт спокойно и не тащат пользователя в настройки.</h2>
            <p>
              Сайт не обещает больше, чем реально доступно. Android и Windows ведут в продукт, Apple помечен как «Готовится», а сложные детали не мешают первому шагу.
            </p>
          </div>
          <div className="lp-trust-grid">
            {currentScenarios.map((item) => (
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

        <section id="downloads" className="lp-section">
          <div className="lp-section-head">
            <span>Приложение</span>
            <h2>Публичный вход начинается с приложения, а не с ручной настройки.</h2>
            <p>
              Android и Windows уже составляют публичный путь. Apple остаётся в подготовке и не показывается как готовая платформа.
            </p>
          </div>
          <div className="lp-download-grid">
            {downloadCards.map((card, index) => (
              <article key={card.title} className={`lp-platform-card${index === 0 ? " lp-platform-card--featured" : ""}`}>
                <div className="lp-stage-label">
                  <LandingGlyph name={card.title === "Android" ? "arc" : card.title === "Windows" ? "window" : "orbit"} />
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
            <h2>Тарифы ведут к ключу доступа, который легко активировать.</h2>
            <p>
              Вы выбираете срок, переходите к оплате и получаете ключ доступа. Активировать его можно в приложении или кабинете.
            </p>
          </div>
          <div className="lp-pricing-shell">
            <aside className="lp-pricing-intro">
              <div className="lp-stage-label">
                <LandingGlyph name="shield" />
                Ключ доступа
              </div>
              <h3>Купите ключ, активируйте его и продолжайте тот же аккаунт.</h3>
              <p>
                Кабинет и приложение работают с одним аккаунтом. Сайт показывает честные сроки, понятные условия и следующий шаг.
              </p>
              <ul className="lp-pricing-points">
                <li>После 5 дней остаётся бесплатный базовый режим.</li>
                <li>Telegram используется по необходимости: восстановление, поддержка и бонус.</li>
                <li>Промо в приложении и кабинете остаются собственными предложениями POKROV.</li>
              </ul>
            </aside>

            <div className="lp-plan-grid">
              {plans.map((plan, index) => (
                <article key={plan.code} className={`lp-plan-card${index === plans.length - 1 ? " lp-plan-card--highlight" : ""}`}>
                  {plan.badge ? <span className="lp-badge">{plan.badge}</span> : null}
                  <h3>{plan.label}</h3>
                  <div className="lp-price">{plan.price}</div>
                  <p>{plan.note}</p>
                  <ul className="lp-pricing-points">
                    <li>{plan.duration}</li>
                    <li>{plan.devices}</li>
                  </ul>
                  <Link href={buildCheckoutHref(plan.code)} className="lp-btn lp-btn--ghost">
                    Выбрать срок
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
                <span>Путь</span>
                <h2>{scenarioTitle || "Проверка, бесплатный режим и активация ключа собираются в один понятный путь"}</h2>
                <p>
                  {scenarioBody ||
                    "Сначала 5 дней проверки, потом честный бесплатный режим, затем покупка ключа доступа. Сайт, кабинет и Telegram не спорят друг с другом о следующем шаге."}
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
                <h2>Короткие ответы для публичных страниц</h2>
                <p>Ниже только те ответы, которые помогают выбрать следующий шаг без лишних терминов.</p>
              </div>
              <div className="lp-faq-list">
                {MARKETING_FAQ.map((item) => (
                  <div key={item.question}>
                    <details className="lp-faq-item">
                      <summary className="lp-faq-q">
                        <span>{item.question}</span>
                        <span className="lp-faq-icon" aria-hidden="true">
                          +
                        </span>
                      </summary>
                      <p className="lp-faq-a">{item.answer}</p>
                    </details>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>Рядом</span>
            <h2>{clusterTitle || "Отдельные страницы под разные задачи"}</h2>
            <p>
              {clusterBody ||
                "Эти страницы отдельно объясняют установку, устройства, Telegram и просмотр видео, но ведут к тому же спокойному старту."}
            </p>
          </div>
          <div className="lp-related-grid">
            {relatedPages.map((item) => (
              <article key={item.href} className="lp-related-card">
                <div className="lp-stage-label">
                  <LandingGlyph name="route" />
                  Связанная страница
                </div>
                <h3>{item.label}</h3>
                <p>Тот же принцип: сайт объясняет продукт, а приложение, кабинет и Telegram помогают сделать следующий шаг.</p>
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
              <span>Финальный шаг</span>
              <h2>POKROV: сначала попробуйте 5 дней, потом решайте о продлении.</h2>
              <p>
                Если вы только начинаете, установите приложение. Если продукт уже подошёл, выберите срок, купите ключ доступа и активируйте его в том же аккаунте.
              </p>
            </div>
            <div className="lp-footer-rail">
              <div>
                <strong>Android + Windows</strong>
                <span>публичные платформы</span>
              </div>
              <div>
                <strong>5 дней</strong>
                <span>проверка в приложении</span>
              </div>
              <div>
                <strong>+10 дней</strong>
                <span>после привязки Telegram</span>
              </div>
            </div>
            <div className="lp-footer-actions">
              <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                Попробовать 5 дней
              </Link>
              <Link href={defaultCheckoutHref} className="lp-btn lp-btn--ghost">
                Выбрать срок
              </Link>
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Открыть кабинет
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Поддержка
              </a>
              <Link href={MARKETING_CANONICAL_PATHS.offer} className="lp-btn lp-btn--ghost">
                Оферта
              </Link>
              <Link href={MARKETING_CANONICAL_PATHS.privacy} className="lp-btn lp-btn--ghost">
                Политика
              </Link>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
