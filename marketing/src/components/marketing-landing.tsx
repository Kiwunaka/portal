import type { Metadata } from "next";
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

type DownloadCard = {
  title: string;
  status: string;
  desc: string;
  cta: string;
  href: string;
};

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

const PROMISE_CARDS = [
  {
    title: "Первые 5 дней действительно бесплатно",
    desc: "Сначала пробуете сервис в приложении, только потом решаете, нужен ли вам платный доступ. Без карты и без скрытого автосписания.",
  },
  {
    title: "Красивое и понятное приложение",
    desc: "Основной старт идёт через Android и Windows-приложения: быстрый запуск, понятные экраны и минимум лишних действий.",
  },
  {
    title: "Поддержка и продолжение через Telegram",
    desc: "Telegram у нас не заменяет продукт, а помогает с поддержкой, бонусом за канал и безопасным продолжением маршрута, если это нужно.",
  },
];

const STEPS = [
  {
    title: "1. Скачайте приложение",
    desc: "Начните с Android или Windows: это основной и самый понятный вход в продукт.",
  },
  {
    title: "2. Проверьте сервис бесплатно",
    desc: "Получите 5 дней теста, запустите свои обычные сценарии и убедитесь, что маршрут работает стабильно.",
  },
  {
    title: "3. Продлите доступ через личный маршрут",
    desc: "Оплата и продление начинаются только после личного входа, чтобы пользователь видел только рабочие способы оплаты и честную сумму.",
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

export function buildMarketingMetadata(
  title = getCopyText("marketing.meta.title", "POKROV VPN — быстрый VPN для Android и Windows"),
  description = getCopyText(
    "marketing.meta.description",
    "Скачайте приложение для Android или Windows, получите 5 дней бесплатно и продолжайте через личный кабинет и безопасный checkout-маршрут.",
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
          <img src="/pokrov-logo.svg" alt="POKROV VPN" className="lp-brand-logo" />
          <span>POKROV VPN</span>
        </a>
        <nav className="lp-menu">
          <a href="#downloads">Приложение</a>
          <a href="#pricing">Планы</a>
          <a href="#faq">FAQ</a>
          <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
            Открыть кабинет
          </a>
          <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
            Написать в службу заботы
          </a>
        </nav>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-kicker">
            {heroKicker || getCopyText("marketing.hero.kicker", "POKROV VPN • первые 5 дней бесплатно")}
          </div>
          <h1>{heroTitle || getCopyText("marketing.hero.title", "Свободный интернет на максимальной скорости")}</h1>
          <p>
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
          <div className="lp-proof">
            <div>
              <strong>{getCopyText("marketing.hero.proof_1.title", "5 дней")}</strong>
              <span>{getCopyText("marketing.hero.proof_1.text", "полноценного бесплатного доступа")}</span>
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
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Преимущества]</span>
            <h2>{getCopyText("marketing.promise.title", "Почему POKROV VPN удобно запускать перед релизом")}</h2>
            <p>
              {getCopyText(
                "marketing.promise.subtitle",
                "Маршрут честный и предсказуемый: приложение сначала, личный кабинет для управления, checkout только после персонального входа.",
              )}
            </p>
          </div>
          <div className="lp-feature-grid">
            {PROMISE_CARDS.map((item, idx) => (
              <article key={item.title} className="lp-card">
                <div className="lp-card-index">0{idx + 1}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="downloads" className="lp-section">
          <div className="lp-section-head">
            <span>[Приложение]</span>
            <h2>{getCopyText("marketing.downloads.title", "Установите приложение и начните с него")}</h2>
            <p>
              {getCopyText(
                "marketing.downloads.subtitle",
                "Публичный сайт должен вести либо в реальную загрузку релизного приложения, либо в понятную инструкцию. Без скрытого прыжка в connect-хост.",
              )}
            </p>
          </div>
          <div className="lp-download-grid">
            {downloadCards.map((card) => (
              <article key={card.title} className="lp-card lp-plan">
                <div className="lp-card-index">{card.status}</div>
                <h3>{card.title}</h3>
                <p>{card.desc}</p>
                <a href={card.href} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary" style={{ marginTop: 20 }}>
                  {card.cta}
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Маршрут]</span>
            <h2>{getCopyText("marketing.steps.title", "Как присоединиться за три шага")}</h2>
            <p>
              {getCopyText(
                "marketing.steps.subtitle",
                "Лендинг объясняет маршрут, а не пытается увести пользователя в случайный технический хост или в анонимную кассу.",
              )}
            </p>
          </div>
          <div className="lp-feature-grid">
            {STEPS.map((item) => (
              <article key={item.title} className="lp-card">
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>[Тарифы]</span>
            <h2>{getCopyText("marketing.pricing.title", "Прозрачные тарифы без скрытого перехода в кассу")}</h2>
            <p>
              {getCopyText(
                "marketing.pricing.subtitle",
                "Публичный сайт может показать стоимость и следующий шаг, но сам checkout открывается уже из персонального сценария.",
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
                  {getCopyText("marketing.plan.cta", "Открыть кабинет и продолжить")}
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
                  <p>Связанный сценарий для поиска и навигации, без дублирования смысла главной страницы.</p>
                  <Link href={item.href} className="lp-btn lp-btn--ghost" style={{ marginTop: 20 }}>
                    Открыть страницу
                  </Link>
                </article>
              ))}
            </div>
          </section>
        ) : null}

        <section className="lp-section">
          <div className="lp-card lp-footer-card">
            <div>
              <h3>{getCopyText("marketing.footer.title", "POKROV VPN: приложение сначала, маршрут потом")}</h3>
              <p>
                {getCopyText(
                  "marketing.footer.body",
                  "Скачайте приложение, проверьте сервис бесплатно и только потом переходите к кабинету, продлению и поддержке. Это честный и безопасный путь для публичного запуска.",
                )}
              </p>
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
