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
const CHECKOUT_READY_PLAN_CODES = new Set(["start_99"]);

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

type PlanCard = {
  code: string;
  label: string;
  price: string;
  note: string;
  badge?: string | null;
  duration: string;
  devices: string;
};

type GlyphName = "route" | "shield" | "signal" | "window" | "readiness" | "arc";

const DEFAULT_SCENARIOS: ScenarioCard[] = [
  {
    eyebrow: "Приложение сначала",
    glyph: "route",
    title: "Скачайте, включите, получите 5 дней",
    desc: "Сайт ведет к приложению, приложение дает первый опыт, кабинет остается для срока, устройств, поддержки и продления.",
  },
  {
    eyebrow: "Продление",
    glyph: "shield",
    title: "Цена и срок видны до оплаты",
    desc: "Вы выбираете срок, проверяете сумму и продолжаете тот же аккаунт POKROV. Если нужен код активации, кабинет покажет, что делать.",
  },
  {
    eyebrow: "Telegram по делу",
    glyph: "signal",
    title: "Восстановление, поддержка и бонус +10 дней",
    desc: "Telegram остается дополнительным способом для помощи, бонуса и восстановления, но не нужен для первого старта.",
  },
];

const LANDING_FLOW_STEPS = [
  "Установите приложение.",
  "Включите 5 дней бесплатно.",
  "Продлите срок или напишите в поддержку.",
];

const RELATED_PAGES = [
  { href: MARKETING_CANONICAL_PATHS.mobile, label: "Мобильный старт" },
  { href: MARKETING_CANONICAL_PATHS.devices, label: "Android и Windows" },
  { href: MARKETING_CANONICAL_PATHS.telegram, label: "Telegram и поддержка" },
  { href: MARKETING_CANONICAL_PATHS.youtube, label: "YouTube" },
  { href: MARKETING_CANONICAL_PATHS.tiktok, label: "TikTok" },
];

function buildCheckoutHref(planCode: string): string {
  return `/checkout/?plan=${encodeURIComponent(planCode)}`;
}

function buildPlatformLabel(): string {
  return CANONICAL_PUBLIC_PLATFORM_SCOPE.map((item) => {
    if (item === "android") return "Android";
    if (item === "windows") return "Windows";
    return item;
  }).join(" + ");
}

function buildPlanCards(): PlanCard[] {
  return getTariffPlans()
    .filter((plan) => Boolean(plan.is_active) && CHECKOUT_READY_PLAN_CODES.has(String(plan.code || "").trim().toLowerCase()))
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
  title = "POKROV | 5 дней бесплатно без карты",
  description =
    "Скачайте приложение для Android или Windows, получите 5 дней бесплатно без карты и продолжайте через кабинет.",
  options: MarketingMetadataOptions = {},
): Metadata {
  const canonical = buildMarketingUrl(options.path || "/");
  const shareAlt = `${title} | ${CANONICAL_PLATFORM_BRAND}`;

  return {
    title,
    description,
    keywords: options.keywords,
    category: "technology",
    creator: CANONICAL_PLATFORM_BRAND,
    publisher: CANONICAL_PLATFORM_BRAND,
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
          googleBot: {
            index: true,
            follow: true,
            "max-image-preview": "large",
            "max-snippet": -1,
            "max-video-preview": -1,
          },
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

  if (name === "readiness") {
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
  const reviews = featuredReviews?.length ? featuredReviews : [];
  const plans = buildPlanCards();
  const relatedPages = RELATED_PAGES.filter((item) => item.href !== pagePath);
  const currentScenarios = scenarioCards?.length ? scenarioCards : DEFAULT_SCENARIOS;
  const defaultCheckoutHref = buildCheckoutHref(plans.find((plan) => plan.code === "start_99")?.code || plans[0]?.code || "start_99");
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
            <span>Android и Windows beta</span>
          </div>
          <div className="lp-theme-toggle-wrap">
            <button
              type="button"
              className="lp-theme-toggle"
              data-theme-toggle
              aria-pressed="false"
              aria-label="Переключить на тёмную тему"
              title="Переключить на тёмную тему"
              suppressHydrationWarning
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
            <div className="lp-kicker">{heroKicker || "POKROV • 5 дней без карты"}</div>
            <p className="lp-overline">
              Android и Windows beta: приложение для старта, кабинет для продления и поддержки.
            </p>
            <h1>{heroTitle || "POKROV для YouTube, TikTok и нужных вам сайтов"}</h1>
            <p className="lp-hero-lead">
              {heroSubtitle ||
                "Сначала приложение для Android или Windows и 5 дней бесплатно без карты. Дальше выберите срок и продолжайте в том же аккаунте."}
            </p>
            <div className="lp-hero-actions">
              <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                Попробовать 5 дней бесплатно
              </Link>
              <Link href={defaultCheckoutHref} className="lp-btn lp-btn--ghost">
                Посмотреть тарифы
              </Link>
            </div>
          </div>

          <aside className="lp-hero-stage" aria-label="Короткий сценарий">
            <article className="lp-stage-card lp-stage-card--primary">
              <div className="lp-stage-label">
                <LandingGlyph name="route" />
                Один путь
              </div>
              <h2>Сначала приложение. Остальное рядом.</h2>
              <p>
                {buildPlatformLabel()}, 5 дней бесплатно и кабинет для продления, устройств и поддержки.
              </p>
              <ol className="lp-stage-steps">
                {LANDING_FLOW_STEPS.map((step, index) => (
                  <li key={step}>
                    <span>{`0${index + 1}`}</span>
                    <div>
                      <strong>{step}</strong>
                    </div>
                  </li>
                ))}
              </ol>
            </article>
          </aside>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>Почему удобно</span>
            <h2>{scenarioTitle || "Один сценарий под эту задачу."}</h2>
            <p>
              {scenarioBody ||
                "Сайт объясняет, приложение дает первый опыт, кабинет помогает продолжить. Без серверных списков и ручных профилей на первом шаге."}
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

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>Тарифы</span>
            <h2>Цена, срок и лимит видны до оплаты.</h2>
            <p>
              В beta-кассе открыт стартовый срок. Сначала 5 дней в приложении без карты, затем продление того же аккаунта.
            </p>
          </div>
          <div className="lp-pricing-shell">
            <aside className="lp-pricing-intro">
              <div className="lp-stage-label">
                <LandingGlyph name="shield" />
                Продление
              </div>
              <h3>Платная часть только после теста.</h3>
              <p>
                Приложение, кабинет и checkout продолжают один аккаунт POKROV. Без автосписания на первом старте.
              </p>
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

        <section className="lp-section" id="faq">
          <div className="lp-section-head">
            <span>FAQ</span>
            <h2>Короткие ответы перед следующим шагом.</h2>
            <p>Только то, что помогает начать, установить приложение, открыть кабинет или обратиться в поддержку.</p>
          </div>
          <div className="lp-faq-list">
            {MARKETING_FAQ.map((item) => (
              <details key={item.question} className="lp-faq-item">
                <summary className="lp-faq-q">
                  <span>{item.question}</span>
                  <span className="lp-faq-icon" aria-hidden="true">
                    +
                  </span>
                </summary>
                <p className="lp-faq-a">{item.answer}</p>
              </details>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>Рядом</span>
            <h2>{clusterTitle || "Отдельные страницы под конкретные задачи"}</h2>
            <p>
              {clusterBody ||
                "Эти страницы раскрывают установку, устройства, Telegram и видео-задачи без смешивания ролей сайта, приложения и кабинета."}
            </p>
          </div>
          <nav className="lp-related-strip" aria-label="Похожие страницы">
            {relatedPages.map((item) => (
              <Link key={item.href} href={item.href} className="lp-related-pill">
                {item.label}
              </Link>
            ))}
          </nav>
        </section>

        <section className="lp-section">
          <div className="lp-footer-cta">
            <div className="lp-footer-copy">
              <span>Финальный шаг</span>
              <h2>POKROV: сначала приложение, потом продление.</h2>
              <p>
                Если нужен первый старт, идите в приложение. Если нужен платный срок, выбирайте тариф и продолжайте тот же доступ через ключ в кабинете.
              </p>
            </div>
            <div className="lp-footer-actions">
              <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                Установить приложение
              </Link>
              <Link href={defaultCheckoutHref} className="lp-btn lp-btn--ghost">
                Выбрать срок
              </Link>
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Открыть кабинет
              </a>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
