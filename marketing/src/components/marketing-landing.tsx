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
  CANONICAL_PUBLIC_DEFAULT_ROUTE_MODE,
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

type HeroSignal = {
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
    text: "Поставил приложение, получил 5 дней trial без суеты и уже потом спокойно решил вопрос с платным доступом через key-first сценарий.",
  },
  {
    name: "anna****",
    role: "WINDOWS • 17.01.2026",
    text: "Нравится, что здесь не заставляют идти в чат ради старта. Сначала приложение и проверка, потом уже продление и cabinet continuation.",
  },
  {
    name: "twst****",
    role: "TELEGRAM • 07.01.2026",
    text: "Telegram здесь реально вторичный: помог восстановить доступ и забрать бонус, но сам основной путь живёт внутри приложения.",
  },
];

const HERO_SIGNALS: HeroSignal[] = [
  {
    label: "Публичный scope",
    value: "Android + Windows",
    detail: "Apple hosts остаются в кодовой базе, но не входят в публичное promise этой волны.",
  },
  {
    label: "Стартовый доступ",
    value: "5 дней trial",
    detail: "Первый валидный device получает premium trial без обязательной регистрации.",
  },
  {
    label: "Default route",
    value: "All except RU",
    detail: "Одна логическая локация POKROV, а transport variants скрыты в auto/diagnostics/admin.",
  },
];

const DEFAULT_SCENARIOS: ScenarioCard[] = [
  {
    eyebrow: "App-first",
    glyph: "route",
    title: "Один спокойный consumer path",
    desc: "Сайт ведёт в приложение, приложение даёт trial, а cabinet остаётся continuation слоем для доступа, support и redeem.",
  },
  {
    eyebrow: "Key-first commerce",
    glyph: "shield",
    title: "Buy key -> redeem key -> managed premium",
    desc: "Публичные страницы больше не ведут к raw subscription link. Покупка заканчивается activation key, который потом погашается в app или cabinet.",
  },
  {
    eyebrow: "Telegram по делу",
    glyph: "signal",
    title: "Recovery, support и бонус +10 дней",
    desc: "Telegram нужен для continuation и ручных recovery-сценариев, а не как primary wall или основная коммерческая история.",
  },
];

const KEY_FLOW_STEPS = [
  "Установите приложение для Android или Windows.",
  "Запустите 5-дневный premium trial на первом валидном устройстве.",
  "Если trial закончился, продолжайте на Free Monthly: NL-free, 5 GB / 30 days, 50 Mbps, 1 device.",
  "Выберите срок, купите activation key и погасите его в app или cabinet.",
];

const RELATED_PAGES = [
  { href: MARKETING_CANONICAL_PATHS.mobile, label: "Мобильный старт" },
  { href: MARKETING_CANONICAL_PATHS.devices, label: "Android и Windows" },
  { href: MARKETING_CANONICAL_PATHS.telegram, label: "Telegram и recovery" },
  { href: MARKETING_CANONICAL_PATHS.youtube, label: "YouTube" },
  { href: MARKETING_CANONICAL_PATHS.tiktok, label: "TikTok" },
];

function firstNonEmpty(...values: Array<string | undefined>): string {
  return values.find((value) => Boolean(String(value || "").trim()))?.trim() || "";
}

function buildInstallHref(): string {
  return buildMarketingUrl(MARKETING_CANONICAL_PATHS.install);
}

function buildCheckoutHref(planCode: string): string {
  return `${MARKETING_CANONICAL_PATHS.checkout}?plan=${encodeURIComponent(planCode)}`;
}

function buildDownloadCards(): DownloadCard[] {
  const installHref = buildInstallHref();

  return [
    {
      title: "Android",
      status: "Public release",
      desc: "Основной мобильный путь этой волны: установить приложение, получить trial и дальше продолжать доступ в app-first аккаунте.",
      href: firstNonEmpty(config.androidApkUrl, config.androidPlayUrl, installHref),
      cta: "Скачать для Android",
    },
    {
      title: "Windows",
      status: "Public release",
      desc: "Desktop lane для публичной поставки этой волны: тот же managed profile и тот же key-first сценарий.",
      href: firstNonEmpty(config.windowsExeUrl, installHref),
      cta: "Скачать для Windows",
    },
    {
      title: "Apple hosts",
      status: "Engineering lane",
      desc: "iPhone и Mac остаются в кодовой базе и readiness notes, но не входят в public promise и release acceptance этой волны.",
      href: installHref,
      cta: "Смотреть readiness notes",
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
  title = "POKROV | App-first доступ без лишнего шума",
  description =
    "Скачайте приложение для Android или Windows, получите 5 дней premium trial и продолжайте доступ через key-first managed premium flow.",
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
            <Link href="/">POKROV</Link>
            <span>App-first access</span>
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
                Support
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
              Публичный старт этой волны идёт через приложение. Маркетинг объясняет следующий шаг, а cabinet остаётся continuation слоем.
            </p>
            <h1>{heroTitle || "Один спокойный путь: установить приложение, проверить trial и только потом покупать managed premium"}</h1>
            <p className="lp-hero-lead">
              {heroSubtitle ||
                "POKROV не раскладывает массовый UX по десяткам технических решений. Сначала приложение для Android или Windows, затем 5 дней premium trial, потом Free Monthly или покупка activation key с погашением в app-first аккаунте."}
            </p>
            <div className="lp-hero-actions">
              <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                Установить приложение
              </Link>
              <Link href={MARKETING_CANONICAL_PATHS.checkout} className="lp-btn lp-btn--ghost">
                Выбрать key-first план
              </Link>
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
                Public defaults
              </div>
              <h2>Одна логическая локация и один понятный маршрут.</h2>
              <p>
                В public surfaces пользователь видит один managed location, default route mode <strong>{CANONICAL_PUBLIC_DEFAULT_ROUTE_MODE}</strong> и только релизный scope <strong>{CANONICAL_PUBLIC_PLATFORM_SCOPE.join(" + ")}</strong>.
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
                Telegram remains secondary
              </div>
              <p>
                Telegram остаётся для recovery, restore premium, бонуса +10 дней, community и support fallback. Он не подменяет основной app-first старт и не является primary commerce wall.
              </p>
              <div className="lp-stage-links">
                <a href={config.newsChannelUrl} target="_blank" rel="noreferrer">
                  Канал
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer">
                  Support
                </a>
                <a href={config.webappUrl} target="_blank" rel="noreferrer">
                  Cabinet
                </a>
              </div>
            </article>

            <article className="lp-stage-card lp-stage-card--quote">
              <div className="lp-stage-label">
                <LandingGlyph name="arc" />
                Trust signal
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
            <h2>Маркетинг владеет acquisition и pricing, а не тащит пользователя в legacy-полумеры.</h2>
            <p>
              Сайт не обещает больше, чем реально публично релизится. Android и Windows ведут в продукт, Apple hosts остаются engineering-only, а raw subscription link скрыт из default UX.
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
            <h2>Публичный вход начинается с установки, а не с технических ссылок.</h2>
            <p>
              Android и Windows уже составляют публичный delivery scope. Apple shells остаются в кодовой базе, но эта волна не обещает их как публичный релиз.
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
            <h2>Тарифы теперь ведут к activation key, а не к raw personal link.</h2>
            <p>
              Публичный pricing принадлежит только маркетингу. Дальше покупка продолжается через hosted checkout и заканчивается issuance activation key для managed premium.
            </p>
          </div>
          <div className="lp-pricing-shell">
            <aside className="lp-pricing-intro">
              <div className="lp-stage-label">
                <LandingGlyph name="shield" />
                Key-first model
              </div>
              <h3>Buy key, redeem key, keep the same app-first account.</h3>
              <p>
                Cabinet и приложение работают как continuation surfaces. Сайт показывает только честный pricing, public defaults и следующий шаг без pricing drift и без manual config story.
              </p>
              <ul className="lp-pricing-points">
                <li>Free Monthly остаётся видимым fallback после trial.</li>
                <li>Telegram используется только по необходимости: recovery, support и бонус.</li>
                <li>Промо в приложении и cabinet остаются first-party only.</li>
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
                    Купить activation key
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
                <span>Сценарий</span>
                <h2>{scenarioTitle || "Проверка, fallback и погашение ключа собираются в один спокойный опыт"}</h2>
                <p>
                  {scenarioBody ||
                    "Сначала trial, потом честный free tier, затем key-first upgrade. Это тот же продуктовый маршрут, который должны видеть сайт, webapp и bot без противоречий."}
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
                <h2>Короткие ответы для public surfaces</h2>
                <p>Ниже только те ответы, которые помогают выбрать следующий шаг без marketing drift и без лишнего техно-языка.</p>
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
            <h2>{clusterTitle || "Отдельные страницы под конкретные continuation и trust-сценарии"}</h2>
            <p>
              {clusterBody ||
                "Эти страницы помогают раскрыть install, devices, Telegram и social contexts без того, чтобы расползался базовый acquisition path."}
            </p>
          </div>
          <div className="lp-related-grid">
            {relatedPages.map((item) => (
              <article key={item.href} className="lp-related-card">
                <div className="lp-stage-label">
                  <LandingGlyph name="route" />
                  Related surface
                </div>
                <h3>{item.label}</h3>
                <p>Тот же канон: marketing владеет public story, а cabinet и Telegram остаются continuation/recovery слоями.</p>
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
              <h2>POKROV: сначала приложение, потом key-first managed premium.</h2>
              <p>
                Если нужен public start, идите в приложение. Если нужен upgrade, выбирайте срок, покупайте activation key и погашайте его в том же app-first аккаунте.
              </p>
            </div>
            <div className="lp-footer-rail">
              <div>
                <strong>Android + Windows</strong>
                <span>публичный release scope</span>
              </div>
              <div>
                <strong>5 дней</strong>
                <span>premium trial в приложении</span>
              </div>
              <div>
                <strong>+10 дней</strong>
                <span>после привязки Telegram</span>
              </div>
            </div>
            <div className="lp-footer-actions">
              <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                Установить приложение
              </Link>
              <Link href={MARKETING_CANONICAL_PATHS.checkout} className="lp-btn lp-btn--ghost">
                Купить activation key
              </Link>
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Открыть cabinet
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Support
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
