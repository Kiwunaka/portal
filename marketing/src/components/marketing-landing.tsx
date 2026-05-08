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

type GlyphName = "route" | "shield" | "signal" | "window" | "readiness" | "arc";

const HERO_SIGNALS: HeroSignal[] = [
  {
    label: "Платформы",
    value: "Android + Windows",
    detail: "Основной путь сейчас собран для телефона и компьютера. Apple-направление остается в подготовке.",
  },
  {
    label: "Стартовый доступ",
    value: "5 дней бесплатно",
    detail: "Сначала можно спокойно проверить сервис на своем устройстве без обязательной регистрации.",
  },
  {
    label: "Маршрут",
    value: "Все, кроме RU",
    detail: "На первом экране остается понятный повседневный режим без технических вариантов.",
  },
];

const DEFAULT_SCENARIOS: ScenarioCard[] = [
  {
    eyebrow: "Приложение сначала",
    glyph: "route",
    title: "Один спокойный путь",
    desc: "Сайт помогает начать, приложение дает первый опыт, а кабинет остается рядом для срока доступа, поддержки и продления.",
  },
  {
    eyebrow: "Продление",
    glyph: "shield",
    title: "Ключ доступа без технических ссылок",
    desc: "Оплата заканчивается ключом доступа. Его можно погасить в приложении или кабинете и продолжить тот же аккаунт.",
  },
  {
    eyebrow: "Telegram по делу",
    glyph: "signal",
    title: "Восстановление, поддержка и бонус +10 дней",
    desc: "Telegram остается запасным путем для помощи, бонуса и восстановления, но не заменяет основной старт в приложении.",
  },
];

const KEY_FLOW_STEPS = [
  "Установите приложение для Android или Windows.",
  "Запустите 5 дней бесплатного доступа на первом устройстве.",
  "Если бесплатный период закончился, остается базовый режим с лимитом на месяц.",
  "Выберите срок, получите ключ доступа и погасите его в приложении или кабинете.",
];

const RELATED_PAGES = [
  { href: MARKETING_CANONICAL_PATHS.mobile, label: "Мобильный старт" },
  { href: MARKETING_CANONICAL_PATHS.devices, label: "Android и Windows" },
  { href: MARKETING_CANONICAL_PATHS.telegram, label: "Telegram и поддержка" },
  { href: MARKETING_CANONICAL_PATHS.youtube, label: "YouTube" },
  { href: MARKETING_CANONICAL_PATHS.tiktok, label: "TikTok" },
];

function buildInstallHref(): string {
  return buildMarketingUrl(MARKETING_CANONICAL_PATHS.install);
}

function buildPlatformLabel(): string {
  return CANONICAL_PUBLIC_PLATFORM_SCOPE.map((item) => {
    if (item === "android") return "Android";
    if (item === "windows") return "Windows";
    return item;
  }).join(" + ");
}

function buildRouteLabel(): string {
  if (CANONICAL_PUBLIC_DEFAULT_ROUTE_MODE === "all_except_ru") {
    return "Все, кроме RU";
  }
  if (CANONICAL_PUBLIC_DEFAULT_ROUTE_MODE === "global") {
    return "Полный маршрут";
  }
  return "Спокойный маршрут";
}

function buildDownloadCards(): DownloadCard[] {
  const installHref = buildInstallHref();

  return [
    {
      title: "Android",
      status: "Внутренняя бета",
      desc: "Android доступен как внутренний APK для одобренных бета-пользователей. Публичная публикация остается заблокированной до доверенной подписи и физического аудита.",
      href: installHref,
      cta: "Открыть установку",
    },
    {
      title: "Windows",
      status: "Закрытая бета",
      desc: "Windows можно выдавать как кабинет-гейтированную бета-сборку. Если сборка не подписана, пользователь должен увидеть предупреждение до установки.",
      href: installHref,
      cta: "Открыть установку",
    },
    {
      title: "iPhone и Mac",
      status: "В подготовке",
      desc: "Apple-направление остается в инженерной подготовке и не входит в обещание этой волны.",
      href: installHref,
      cta: "Открыть статус",
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
  title = "POKROV | Спокойный доступ без лишнего шума",
  description =
    "Скачайте приложение для Android или Windows, получите 5 дней бесплатного доступа и продолжайте тот же путь через кабинет.",
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
  const downloadCards = buildDownloadCards();
  const relatedPages = RELATED_PAGES.filter((item) => item.href !== pagePath);
  const currentScenarios = scenarioCards?.length ? scenarioCards : DEFAULT_SCENARIOS;
  const paidBetaHref = MARKETING_CANONICAL_PATHS.install;
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
            <span>спокойный цифровой маршрут</span>
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
              Эта волна — бета-контур с честными ограничениями. Сайт объясняет следующий шаг, а кабинет помогает продолжить путь.
            </p>
            <h1>{heroTitle || "Один спокойный путь: установить приложение, проверить сервис и только потом продлевать доступ"}</h1>
            <p className="lp-hero-lead">
              {heroSubtitle ||
                "POKROV не отправляет вас разбираться в настройках с первого экрана. Сначала приложение для Android или Windows, затем 5 дней бесплатного доступа, потом базовый режим или продление через ключ доступа."}
            </p>
            <div className="lp-hero-actions">
              <Link href={MARKETING_CANONICAL_PATHS.install} className="lp-btn lp-btn--primary">
                Установить приложение
              </Link>
              <Link href={paidBetaHref} className="lp-btn lp-btn--ghost">
                Выбрать срок
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
                Бета-настройка
              </div>
              <h2>Одна логическая локация и один понятный маршрут.</h2>
              <p>
                На пользовательских экранах виден один понятный маршрут <strong>{buildRouteLabel()}</strong> и текущая платформа <strong>{buildPlatformLabel()}</strong>.
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
                Telegram остается рядом
              </div>
              <p>
                Telegram помогает с восстановлением, бонусом +10 дней, новостями и поддержкой. Основной старт все равно начинается в приложении.
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
                Статус беты
              </div>
              <blockquote>Доступ работает в бета-контуре для Android и Windows; загрузки остаются в кабинете, а поддержка отвечает без декоративных обещаний.</blockquote>
              <span>Бета-контур • Android + Windows</span>
            </article>
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>Обещание</span>
            <h2>Сайт помогает выбрать следующий шаг, не раскрывая техническую кухню.</h2>
            <p>
              Мы не обещаем стабильный публичный релиз раньше времени. Android и Windows уже ведут в бета-путь, Apple остается в подготовке, а технические ссылки не показываются в обычном сценарии.
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
            <h2>Бета-вход начинается с установки, а не с технических ссылок.</h2>
            <p>
              Android и Windows составляют текущий пользовательский путь. Apple-сборки остаются в подготовке и не обещаются как готовый релиз этой волны.
            </p>
          </div>
          <div className="lp-download-grid">
            {downloadCards.map((card, index) => (
              <article key={card.title} className={`lp-platform-card${index === 0 ? " lp-platform-card--featured" : ""}`}>
                <div className="lp-stage-label">
                  <LandingGlyph name={card.title === "Android" ? "arc" : card.title === "Windows" ? "window" : "readiness"} />
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
            <h2>Тарифы ведут к ключу доступа, а не к технической ссылке.</h2>
            <p>
              Вы выбираете срок, смотрите честный статус кассы и погашаете ключ в приложении или кабинете, когда маршрут оплаты прошел проверку.
            </p>
          </div>
          <div className="lp-pricing-shell">
            <aside className="lp-pricing-intro">
              <div className="lp-stage-label">
                <LandingGlyph name="shield" />
                Ключ доступа
              </div>
              <h3>Выберите срок, получите ключ, продолжайте тот же доступ.</h3>
              <p>
                Приложение и кабинет продолжают одну историю. Сайт показывает цену, ограничения беты и следующий шаг без ручных настроек.
              </p>
              <ul className="lp-pricing-points">
                <li>После бесплатного периода остается базовый режим с месячным лимитом.</li>
                <li>Telegram используется для восстановления, поддержки и бонуса.</li>
                <li>Промо остаются собственными и не превращаются в стороннюю рекламу.</li>
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
                  <Link href={paidBetaHref} className="lp-btn lp-btn--ghost">
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
                <span>Сценарий</span>
                <h2>{scenarioTitle || "Проверка, помощь и продление собираются в один спокойный опыт"}</h2>
                <p>
                  {scenarioBody ||
                    "Сначала бесплатная проверка, потом базовый режим, затем продление через ключ доступа. Это один маршрут для сайта, кабинета и Telegram без противоречий."}
                </p>
              </div>
              {reviews.length ? (
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
              ) : (
                <div className="lp-review-list">
                  <article className="lp-review-card">
                    <p className="lp-review-text">
                      Публичные отзывы появятся только после модерации через официальный канал обратной связи.
                    </p>
                    <div className="lp-review-meta">
                      <strong>POKROV</strong>
                      <span>только проверенная обратная связь</span>
                    </div>
                  </article>
                </div>
              )}
            </div>

            <div id="faq">
              <div className="lp-section-head">
                <span>FAQ</span>
                <h2>Короткие ответы для выбора следующего шага</h2>
                <p>Ниже только то, что помогает начать, установить приложение, открыть кабинет или обратиться в поддержку.</p>
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
            <h2>{clusterTitle || "Отдельные страницы под конкретные сценарии"}</h2>
            <p>
              {clusterBody ||
                "Эти страницы раскрывают установку, устройства, Telegram и видеосценарии без смешивания ролей сайта, приложения и кабинета."}
            </p>
          </div>
          <div className="lp-related-grid">
            {relatedPages.map((item) => (
              <article key={item.href} className="lp-related-card">
                <div className="lp-stage-label">
                  <LandingGlyph name="route" />
                  Соседний сценарий
                </div>
                <h3>{item.label}</h3>
                <p>Та же логика: сайт объясняет, приложение дает первый опыт, кабинет и Telegram помогают продолжить или восстановить доступ.</p>
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
              <h2>POKROV: сначала приложение, потом спокойное продление.</h2>
              <p>
                Если нужен первый старт, идите в приложение. Если сервис подошел, выбирайте срок и продолжайте тот же доступ через ключ в кабинете.
              </p>
            </div>
            <div className="lp-footer-rail">
              <div>
                <strong>Android + Windows</strong>
                <span>бета-путь с честными ограничениями</span>
              </div>
              <div>
                <strong>5 дней</strong>
                <span>бесплатно в приложении</span>
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
              <Link href={paidBetaHref} className="lp-btn lp-btn--ghost">
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
