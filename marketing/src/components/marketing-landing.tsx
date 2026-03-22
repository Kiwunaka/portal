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
    text: "Поставил приложение, спокойно проверил на своих сайтах и только потом решил продлевать. Наконец-то путь без суеты.",
  },
  {
    name: "anna****",
    role: "Windows",
    text: "Понравилось, что сначала дают реальный тест, а не декоративную витрину. И поддержка отвечает по-человечески.",
  },
  {
    name: "serg****",
    role: "Telegram",
    text: "Telegram остался как удобный запасной канал, но сам сервис стал заметно понятнее и чище.",
  },
];

const PROMISE_CARDS = [
  {
    title: "Сначала пробуете, потом решаете",
    desc: "Пять дней бесплатного доступа помогают проверить скорость, удобство и ваши обычные сценарии без оплаты вслепую.",
  },
  {
    title: "Приложение — главный вход",
    desc: "В релизе делаем ставку на Android и Windows: понятный стартовый экран, крупная кнопка подключения и меньше лишнего шума.",
  },
  {
    title: "Telegram помогает, а не мешает",
    desc: "Через Telegram удобно продолжить вход, получить персональную ссылку на оплату, задать вопрос или восстановить доступ.",
  },
];

const STEPS = [
  {
    title: "1. Выберите устройство",
    desc: "Ниже есть основные карточки для Android и Windows. Для iPhone и Mac сейчас честно показываем статус подготовки, без ложных обещаний.",
  },
  {
    title: "2. Запустите бесплатный тест",
    desc: "Пять дней хватает, чтобы понять, подходит ли сервис по скорости, удобству и вашему обычному ритму использования.",
  },
  {
    title: "3. Продлите доступ по реальному маршруту",
    desc: "Оплата открывается только после входа в кабинет или по персональной ссылке. Без декоративной витрины и странных тупиков.",
  },
];

const RELATED_PAGES = [
  { href: "/vpn-dlya-youtube/", label: "VPN для YouTube" },
  { href: "/vpn-telegram-bot/", label: "Telegram как резервный путь" },
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
    { code: "start_99", name: "Старт на 30 дней", price: "99 ₽", note: getCopyText("marketing.plan.start.note", "Для короткого платного старта после теста.") },
    { code: "1_month", name: "1 месяц", price: "249 ₽", note: getCopyText("marketing.plan.month.note", "Понятный вариант на каждый месяц без лишней переплаты.") },
    { code: "3_months", name: "3 месяца", price: "699 ₽", note: getCopyText("marketing.plan.quarter.note", "Если уже всё проверили и не хотите часто возвращаться к продлению.") },
    { code: "6_months", name: "6 месяцев", price: "1199 ₽", note: getCopyText("marketing.plan.half.note", "Удобный баланс между сроком, экономией и редкими продлениями.") },
    { code: "12_months", name: "12 месяцев", price: "1644 ₽", note: getCopyText("marketing.plan.long.note", "Для тех, кто хочет надолго закрыть вопрос с доступом.") },
  ];
}

function buildDownloadCards() {
  const androidHref = firstNonEmpty(config.androidPlayUrl, config.androidApkUrl, config.androidMirrorUrl, config.connectUrl);
  const windowsHref = firstNonEmpty(config.windowsExeUrl, config.windowsMirrorUrl, config.connectUrl);

  return [
    {
      title: "Android",
      status: "Главный релиз",
      desc: "Ставка на простой первый запуск, аккуратный интерфейс и быстрый переход к реальному подключению без ручной настройки.",
      cta: getCopyText("marketing.download.android.cta", "Скачать для Android"),
      href: androidHref,
    },
    {
      title: "Windows",
      status: "Главный релиз",
      desc: "Новый клиент POKROV VPN для Windows готовим как отдельное приложение с собственным брендингом и понятной установкой.",
      cta: getCopyText("marketing.download.windows.cta", "Скачать для Windows"),
      href: windowsHref,
    },
    {
      title: "iPhone и Mac",
      status: "В подготовке",
      desc: "Публикацию для Apple готовим отдельно: сейчас собираем подпись, сертификаты и store readiness, не обещая сроки раньше времени.",
      cta: getCopyText("marketing.download.apple.cta", "Открыть кабинет"),
      href: config.connectUrl,
    },
  ];
}

const FAQ = [
  {
    q: getCopyText("marketing.faq.1.q", "Почему теперь упор на приложение, а не только на Telegram?"),
    a: getCopyText(
      "marketing.faq.1.a",
      "Потому что для обычного пользователя так проще: приложение даёт понятный первый экран и быстрый путь к подключению, а Telegram остаётся как запасной маршрут и поддержка.",
    ),
  },
  {
    q: getCopyText("marketing.faq.2.q", "Что входит в бесплатные 5 дней?"),
    a: getCopyText(
      "marketing.faq.2.a",
      "Доступ к реальному пользовательскому сценарию: приложение, подключение, кабинет и основные действия без декоративного демо-режима.",
    ),
  },
  {
    q: getCopyText("marketing.faq.3.q", "Можно ли оплатить доступ прямо с сайта?"),
    a: getCopyText(
      "marketing.faq.3.a",
      "Да, но только по реальному сценарию: после входа в кабинет или по персональной ссылке. Мы не отправляем пользователя на фальшивую витрину вместо оплаты.",
    ),
  },
  {
    q: getCopyText("marketing.faq.4.q", "Что делать, если нужна помощь или что-то не сработало?"),
    a: getCopyText(
      "marketing.faq.4.a",
      "Напишите в поддержку: Telegram остаётся быстрым резервным каналом, чтобы не оставлять человека один на один с ошибкой, оплатой или настройкой.",
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
            Написать в поддержку
          </a>
        </nav>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-kicker">{heroKicker || getCopyText("marketing.hero.kicker", "POKROV VPN • 5 дней бесплатно • Android и Windows")}</div>
          <h1>{heroTitle || getCopyText("marketing.hero.title", "Простой старт, спокойный интернет и никакой путаницы")}</h1>
          <p>
            {heroSubtitle ||
              getCopyText(
                "marketing.hero.subtitle",
                "Основной путь начинается с приложения: устанавливаете POKROV VPN, получаете 5 дней бесплатно и проверяете сервис в своих обычных сценариях.",
              )}
          </p>
          <div className="lp-hero-actions">
            <a href="#downloads" className="lp-btn lp-btn--primary">
              {getCopyText("marketing.hero.primary_cta", "Скачать приложение")}
            </a>
            <a href={config.connectUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
              {getCopyText("marketing.hero.secondary_cta", "Открыть кабинет")}
            </a>
          </div>
          <div className="lp-proof">
            <div>
              <strong>{getCopyText("marketing.hero.proof_1.title", "5 дней")}</strong>
              <span>{getCopyText("marketing.hero.proof_1.text", "бесплатно, чтобы спокойно проверить сервис")}</span>
            </div>
            <div>
              <strong>{getCopyText("marketing.hero.proof_2.title", "Android + Windows")}</strong>
              <span>{getCopyText("marketing.hero.proof_2.text", "главный релиз уже готовим именно для этих устройств")}</span>
            </div>
            <div>
              <strong>{getCopyText("marketing.hero.proof_3.title", "Живой человек рядом")}</strong>
              <span>{getCopyText("marketing.hero.proof_3.text", "если что-то непонятно, можно быстро продолжить через Telegram и поддержку")}</span>
            </div>
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Обещание]</span>
            <h2>{getCopyText("marketing.promise.title", "Что вы получаете на старте")}</h2>
            <p>{getCopyText("marketing.promise.subtitle", "Без квеста из пяти экранов: установка, тест, подключение, продление и помощь находятся в одном понятном маршруте.")}</p>
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
            <h2>{getCopyText("marketing.downloads.title", "С чего начать прямо сейчас")}</h2>
            <p>{getCopyText("marketing.downloads.subtitle", "Основной релиз идёт через Android и Windows. Для iPhone и Mac мы готовим отдельную публикацию и не обещаем её раньше времени.")}</p>
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
            <h2>{getCopyText("marketing.steps.title", "Как выглядит путь без путаницы")}</h2>
            <p>{getCopyText("marketing.steps.subtitle", "POKROV VPN не заставляет сначала читать десяток инструкций. Мы оставляем только шаги, которые реально нужны пользователю.")}</p>
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
            <h2>{getCopyText("marketing.pricing.title", "Планы для тех, кто уже всё проверил")}</h2>
            <p>{getCopyText("marketing.pricing.subtitle", "Публичная страница больше не притворяется кассой. Сначала вход и персональный маршрут, потом честная ссылка на оплату и понятная сумма.")}</p>
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
            <h2>{getCopyText("marketing.reviews.title", "Что пишут пользователи")}</h2>
            <p>{getCopyText("marketing.reviews.subtitle", "На главной показываем только одобренные отзывы. Ники маскируем, чтобы не раскрывать лишние данные.")}</p>
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
            <h2>{getCopyText("marketing.faq.title", "Коротко о важном")}</h2>
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
                  <p>Отдельная страница под конкретный сценарий, чтобы быстрее перейти к нужному маршруту без лишнего поиска.</p>
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
              <h3>{getCopyText("marketing.footer.title", "POKROV VPN для спокойного повседневного использования")}</h3>
              <p>{getCopyText("marketing.footer.body", "Начните с приложения, проверьте сервис на своих задачах и только потом решайте, нужен ли полный доступ.")}</p>
            </div>
            <div className="lp-footer-actions">
              <a href={config.connectUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                Открыть кабинет
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Поддержка
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
