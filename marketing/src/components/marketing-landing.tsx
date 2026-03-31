import type { Metadata } from "next";
import Link from "next/link";

import { getCopyText, getPokrovPublicConfig } from "../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export type MarketingReview = {
  name: string;
  role: string;
  text: string;
};

const DEFAULT_REVIEWS: MarketingReview[] = [
  {
    name: "mikh****",
    role: "Android",
    text: "POKROV VPN — это реальное спасение! Установил, попробовал бесплатно и сразу понял: скорость супер, всё летает. Оплатил без раздумий.",
  },
  {
    name: "anna****",
    role: "Windows",
    text: "Потрясающее приложение: всё на русском, очень стильно и понятно. А главное — живая служба заботы отвечает реально за минуту!",
  },
  {
    name: "serg****",
    role: "Telegram",
    text: "Очень удобно! Зашёл через Telegram, выбрал тариф и всё заработало за пару секунд. Лучший VPN, что я пробовал за последнее время.",
  },
];

const PROMISE_CARDS = [
  {
    title: "Пользуйтесь 5 дней бесплатно",
    desc: "Оцените все преимущества POKROV VPN абсолютно бесплатно: невероятно быстрое подключение и стабильная скорость без привязки карты.",
  },
  {
    title: "Совершенный дизайн и удобство",
    desc: "Мы сделали современное и красивое приложение, где безопасное и мгновенное подключение происходит буквально в один клик.",
  },
  {
    title: "Комфорт везде: личный кабинет в Telegram",
    desc: "Управляйте подпиской, легко оплачивайте тарифы и получайте премиальную помощь от нашей службы заботы прямо в мессенджере.",
  },
];

const STEPS = [
  {
    title: "1. Скачайте наше приложение",
    desc: "Стильные приложения для Android и Windows уже полностью готовы к работе и подарят вам невероятный комфорт при серфинге.",
  },
  {
    title: "2. Начните бесплатный тестовый период",
    desc: "Легко оцените свободу без границ: целых 5 дней видео в 4K, соцсетей и любых задач на максимальной скорости.",
  },
  {
    title: "3. Выберите свой выгодный тариф",
    desc: "Оплачивайте удобным для вас способом прямо в личном кабинете. Прозрачные цены, моментальная активация и никаких скрытых платежей.",
  },
];

const RELATED_PAGES = [
  { href: "/vpn-dlya-youtube/", label: "VPN для YouTube" },
  { href: "/vpn-telegram-bot/", label: "Всегда на связи через Telegram" },
  { href: "/vpn-dlya-tiktok/", label: "VPN для TikTok" },
];

function firstNonEmpty(...values: Array<string | undefined>): string {
  return values.find((value) => Boolean(String(value || "").trim()))?.trim() || "";
}

function buildCheckoutHref(planCode: string): string {
  const joiner = config.checkoutUrl.includes("?") ? "&" : "?";
  return `${config.checkoutUrl}${joiner}plan=${encodeURIComponent(planCode)}`;
}

function buildMarketingPlans() {
  return [
    { code: "start_99", name: "Старт на 30 дней", price: "99 ₽", note: getCopyText("marketing.plan.start.note", "Отличное начало, чтобы почувствовать все возможности POKROV VPN.") },
    { code: "1_month", name: "1 месяц", price: "249 ₽", note: getCopyText("marketing.plan.month.note", "Удобный и гибкий вариант оплаты каждый месяц.") },
    { code: "3_months", name: "3 месяца", price: "699 ₽", note: getCopyText("marketing.plan.quarter.note", "Идеальный баланс между ценой и комфортом использования.") },
    { code: "6_months", name: "6 месяцев", price: "1199 ₽", note: getCopyText("marketing.plan.half.note", "Выгодное предложение для самого стабильного доступа надолго.") },
    { code: "12_months", name: "12 месяцев", price: "1644 ₽", note: getCopyText("marketing.plan.long.note", "Максимальная экономия для тех, кто ценит комфорт, качество и надежность.") },
  ];
}

function buildDownloadCards() {
  const androidHref = firstNonEmpty(config.androidPlayUrl, config.androidApkUrl, config.androidMirrorUrl, config.connectUrl);
  const windowsHref = firstNonEmpty(config.windowsExeUrl, config.windowsMirrorUrl, config.connectUrl);

  return [
    {
      title: "Android",
      status: "Уже Релиз",
      desc: "Наша гордость: невероятно удобное приложение. Подключайтесь быстро, стильно и наслаждайтесь интернетом без задержек.",
      cta: getCopyText("marketing.download.android.cta", "Скачать для Android"),
      href: androidHref,
    },
    {
      title: "Windows",
      status: "Уже Релиз",
      desc: "Мощное решение для вашего ПК: современный дизайн, феноменальная стабильность и бескомпромиссная защита данных.",
      cta: getCopyText("marketing.download.windows.cta", "Скачать для Windows"),
      href: windowsHref,
    },
    {
      title: "iPhone и Mac",
      status: "Скоро Релиз",
      desc: "Мы уже трудимся над нативными приложениями для iOS и macOS, чтобы обеспечить стабильную работу экосистемы Apple.",
      cta: getCopyText("marketing.download.apple.cta", "Открыть кабинет"),
      href: config.connectUrl,
    },
  ];
}

const FAQ = [
  {
    q: getCopyText("marketing.faq.1.q", "Как мне начать пользоваться сервисом?"),
    a: getCopyText(
      "marketing.faq.1.a",
      "Всё невероятно просто! Установите наше приложение, нажмите кнопку старта для бесплатных 5 дней и наслаждайтесь безопасным интернетом!",
    ),
  },
  {
    q: getCopyText("marketing.faq.2.q", "Что я получу во время бесплатного теста?"),
    a: getCopyText(
      "marketing.faq.2.a",
      "Вам предоставляется полный премиум-доступ на максимальной скорости: без ограничений по выбранным локациям, трафику и функциям!",
    ),
  },
  {
    q: getCopyText("marketing.faq.3.q", "Как оформить платную подписку?"),
    a: getCopyText(
      "marketing.faq.3.a",
      "Оплата быстро и безопасно осуществляется в вашем личном кабинете. Выбирайте среди множества удобных способов оплаты без скрытых подписок.",
    ),
  },
  {
    q: getCopyText("marketing.faq.4.q", "Куда обратиться, если возникнут вопросы?"),
    a: getCopyText(
      "marketing.faq.4.a",
      "Служба заботы POKROV VPN с радостью ответит на все вопросы. Мы на связи 24/7 в Telegram, чтобы ваш интернет всегда был идеальным.",
    ),
  },
];

export function buildMarketingMetadata(
  title = getCopyText("marketing.meta.title", "POKROV VPN - понятный VPN для телефона и компьютера"),
  description = getCopyText(
    "marketing.meta.description",
    "Скачайте приложение для Android или Windows, получите 5 дней бесплатно и управляйте доступом без сложной настройки.",
  ),
): Metadata {

  return {
    title,
    description,
    openGraph: {
      title,
      description,
      type: "website",
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
          <a href={config.connectUrl} target="_blank" rel="noreferrer" className="lp-chip">
            Открыть кабинет
          </a>
          <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
            Написать в службу заботы
          </a>
        </nav>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-kicker">{heroKicker || getCopyText("marketing.hero.kicker", "POKROV VPN • Первые 5 дней абсолютно бесплатно")}</div>
          <h1>{heroTitle || getCopyText("marketing.hero.title", "Быстрый интернет без границ и блокировок")}</h1>
          <p>
            {heroSubtitle ||
              getCopyText(
                "marketing.hero.subtitle",
                "Основной путь начинается с приложения: устанавливаете POKROV VPN, получаете 5 дней бесплатно и проверяете сервис в своих обычных сценариях.",
              )}
          </p>
          <div className="lp-hero-actions">
            <a href="#downloads" className="lp-btn lp-btn--primary">
              {getCopyText("marketing.hero.primary_cta", "Начать пользоваться")}
            </a>
            <a href={config.connectUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
              {getCopyText("marketing.hero.secondary_cta", "Открыть кабинет")}
            </a>
          </div>
          <div className="lp-proof">
            <div>
              <strong>{getCopyText("marketing.hero.proof_1.title", "5 дней")}</strong>
              <span>{getCopyText("marketing.hero.proof_1.text", "реального бесплатного премиум-доступа")}</span>
            </div>
            <div>
              <strong>{getCopyText("marketing.hero.proof_2.title", "Android + Windows")}</strong>
              <span>{getCopyText("marketing.hero.proof_2.text", "идеальные приложения для ваших устройств")}</span>
            </div>
            <div>
              <strong>{getCopyText("marketing.hero.proof_3.title", "Живой человек рядом")}</strong>
              <span>{getCopyText("marketing.hero.proof_3.text", "быстрая помощь дружелюбной поддержки 24/7")}</span>
            </div>
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Обещание]</span>
            <h2>{getCopyText("marketing.promise.title", "Ваши преимущества с POKROV VPN")}</h2>
            <p>{getCopyText("marketing.promise.subtitle", "Оптимальное сочетание скорости, безопасности и непревзойденного комфорта использования.")}</p>
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
            <h2>{getCopyText("marketing.downloads.title", "Установите легкое приложение")}</h2>
            <p>{getCopyText("marketing.downloads.subtitle", "Начните с мобильной и десктоп платформ — они уже готовы обеспечить вас бесперебойным обходом блокировок.")}</p>
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
            <h2>{getCopyText("marketing.steps.title", "Как присоединиться к нам всего за три шага")}</h2>
            <p>{getCopyText("marketing.steps.subtitle", "Никаких сложностей и долгой настройки: всё интуитивно понятно и проработано до мелочей.")}</p>
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
            <span>[Планы]</span>
            <h2>{getCopyText("marketing.pricing.title", "Прозрачные и выгодные тарифы")}</h2>
            <p>{getCopyText("marketing.pricing.subtitle", "Выбирайте комфортный для себя период: чем больше месяцев, тем ярче ваша экономия. Оставайтесь онлайн выгодно!")}</p>
          </div>
          <div className="lp-plan-grid">
            {plans.map((plan, index) => (
              <article key={plan.code} className={`lp-card lp-plan ${index === plans.length - 1 ? "lp-plan--highlight" : ""}`}>
                <h3>{plan.name}</h3>
                <div className="lp-price">{plan.price}</div>
                <p>{plan.note}</p>
                <a href={buildCheckoutHref(plan.code)} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost" style={{ marginTop: 20 }}>
                  {getCopyText("marketing.plan.cta", "Открыть кабинет и продолжить")}
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Отзывы]</span>
            <h2>{getCopyText("marketing.reviews.title", "Нас любят тысячи пользователей")}</h2>
            <p>{getCopyText("marketing.reviews.subtitle", "Искренние слова наших клиентов — лучшее доказательство потрясающего качества POKROV VPN.")}</p>
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
            <h2>{getCopyText("marketing.faq.title", "Частые вопросы от наших пользователей")}</h2>
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
                  <p>Полезные инструкции, советы и крутые подборки, чтобы вы мгновенно получали максимум пользы от нашего сервиса.</p>
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
              <h3>{getCopyText("marketing.footer.title", "POKROV VPN: ваш лучший премиум-помощник")}</h3>
              <p>{getCopyText("marketing.footer.body", "Станьте свободнее: качайте приложение, тестируйте качество и наслаждайтесь интернетом без ограничений.")}</p>
            </div>
            <div className="lp-footer-actions">
              <a href={config.connectUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                Открыть кабинет
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Служба заботы
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
