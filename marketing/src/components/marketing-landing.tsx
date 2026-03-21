import type { Metadata } from "next";
import Link from "next/link";

import { getPortalPublicConfig } from "../lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export type MarketingReview = {
  name: string;
  role: string;
  text: string;
};

const DEFAULT_REVIEWS: MarketingReview[] = [
  {
    name: "mikh****",
    role: "Android",
    text: "Запустил тест через Telegram, спокойно всё проверил и уже потом перешёл к платному доступу. Путь действительно короткий и без лишней путаницы.",
  },
  {
    name: "anna****",
    role: "iPhone",
    text: "Понравилось, что сначала можно просто попробовать сервис на своих задачах, а потом уже без спешки выбрать подходящий вариант.",
  },
  {
    name: "serg****",
    role: "Windows",
    text: "Подключение оказалось понятным: бот, кабинет, продление и поддержка на своих местах. Не пришлось разбираться в десятке экранов.",
  },
];

const BENEFITS = [
  {
    title: "Понятный старт без сложной настройки",
    desc: "Сначала Telegram-бот, затем тест на 5 дней, потом кабинет и продление, если сервис вам подошёл. Без длинных анкет и лишних развилок.",
  },
  {
    title: "Сначала проверяете сами",
    desc: "POKROV VPN не просит платить вслепую. Сначала вы смотрите, как сервис ведёт себя на ваших устройствах и привычных сайтах.",
  },
  {
    title: "Поддержка рядом, когда она нужна",
    desc: "Если что-то непонятно с оплатой, приложением или подключением, можно сразу написать в поддержку и быстро получить ответ.",
  },
];

const USE_CASES = [
  {
    title: "YouTube и длинные видео",
    desc: "Когда нужен спокойный доступ к роликам, стримам и привычным видеосценариям без долгого старта.",
  },
  {
    title: "TikTok, Instagram и короткие форматы",
    desc: "Подходит для повседневного мобильного сценария, когда важны понятный запуск и быстрый возврат к привычному ритму.",
  },
  {
    title: "Телефон, планшет и ноутбук",
    desc: "Один понятный маршрут для Android, iPhone и Windows, чтобы не осваивать новый процесс на каждом устройстве.",
  },
];

const STEPS = [
  {
    title: "1. Откройте бота",
    desc: "Главный вход в сервис начинается в Telegram. Бот даёт понятный первый шаг и не перегружает лишними действиями.",
  },
  {
    title: "2. Запустите тест на 5 дней",
    desc: "Этого времени хватает, чтобы спокойно проверить доступ, интерфейс и то, как сервис подходит именно под ваш сценарий.",
  },
  {
    title: "3. Перейдите к кабинету и оплате",
    desc: "Если всё подошло, дальше можно открыть кабинет, выбрать срок доступа и продлить подписку без лишних шагов.",
  },
];

const TRIAL_CARDS = [
  {
    title: "Тест на 5 дней",
    price: "0 ₽",
    note: "Спокойный старт для знакомства с сервисом. Сначала проверяете сами, потом уже решаете, нужен ли платный период.",
    cta: "🚀 Начать в Telegram",
    href: config.botUrl,
  },
  {
    title: "Кабинет и управление",
    price: "Без лишней суеты",
    note: "Если вы уже внутри сервиса, кабинет помогает быстро перейти к управлению доступом, оплате и полезным подсказкам.",
    cta: "Открыть кабинет",
    href: config.connectUrl,
  },
];

const PAID_PLANS = [
  { code: "1_month", name: "1 месяц", price: "249 ₽", note: "До 5 устройств • хороший вариант, если хочется начать с короткого периода" },
  { code: "3_months", name: "3 месяца", price: "699 ₽", note: "До 5 устройств • удобный срок, если сервис уже проверен на практике" },
  { code: "6_months", name: "6 месяцев", price: "1199 ₽", note: "До 5 устройств • заметно реже нужно продлевать доступ" },
  { code: "12_months", name: "12 месяцев", price: "1644 ₽", note: "До 5 устройств • самый выгодный вариант по цене на длинной дистанции" },
];

const FAQ = [
  {
    q: "Почему сначала бот, а не сразу оплата?",
    a: "Потому что так проще и честнее. Сначала вы берёте тест на 5 дней и смотрите, подходит ли вам сервис, а потом уже переходите к тарифу.",
  },
  {
    q: "Что входит в тестовый период?",
    a: "Тест даёт доступ к основному пользовательскому сценарию: запуск через Telegram, переход к кабинету и подключение без лишней спешки.",
  },
  {
    q: "Можно ли потом продлить подписку через сайт?",
    a: "Да. После теста и первого входа можно использовать кабинет и публичную страницу оплаты на новом контуре POKROV.",
  },
  {
    q: "Что делать, если нужна помощь?",
    a: "Напишите в поддержку в Telegram. Это самый быстрый маршрут для вопросов по оплате, доступу, приложениям и подключению.",
  },
];

const RELATED_PAGES = [
  { href: "/vpn-dlya-youtube/", label: "VPN для YouTube" },
  { href: "/vpn-telegram-bot/", label: "VPN через Telegram-бота" },
  { href: "/vpn-dlya-tiktok/", label: "VPN для TikTok" },
  { href: "/bystryy-vpn-na-telefon/", label: "Быстрый VPN на телефон" },
  { href: "/vpn-na-iphone-android-windows/", label: "VPN на iPhone, Android и Windows" },
];

function buildCheckoutHref(planCode: string): string {
  const joiner = config.checkoutUrl.includes("?") ? "&" : "?";
  return `${config.checkoutUrl}${joiner}plan=${encodeURIComponent(planCode)}`;
}

export function buildMarketingMetadata(title: string, description: string): Metadata {
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
  heroKicker: string;
  heroTitle: string;
  heroSubtitle: string;
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

  return (
    <>
      <div className="lp-bg-blobs" aria-hidden="true" />
      <header className="lp-nav">
        <a href="#main-content" className="lp-brand">
          <span>●</span>
          POKROV VPN
        </a>
        <nav className="lp-menu">
          <a href="#benefits">Преимущества</a>
          <a href="#trial">Тест</a>
          <a href="#pricing">Тарифы</a>
          <a href="#faq">FAQ</a>
          <a href={config.connectUrl} target="_blank" rel="noreferrer" className="lp-chip">
            Открыть кабинет
          </a>
          <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
            🚀 Начать тест
          </a>
        </nav>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-kicker">{heroKicker}</div>
          <h1>{heroTitle}</h1>
          <p>{heroSubtitle}</p>
          <div className="lp-hero-actions">
            <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
              🚀 Начать в Telegram
            </a>
            <a href="#pricing" className="lp-btn lp-btn--ghost">
              Посмотреть тарифы
            </a>
          </div>
          <div className="lp-proof">
            <div>
              <strong>5 дней</strong>
              <span>тестового доступа, чтобы спокойно всё проверить</span>
            </div>
            <div>
              <strong>Telegram → кабинет</strong>
              <span>один понятный маршрут от первого касания до продления</span>
            </div>
            <div>
              <strong>Поддержка рядом</strong>
              <span>если нужен человек, а не квест из подсказок</span>
            </div>
          </div>
        </section>

        <section id="benefits" className="lp-section">
          <div className="lp-section-head">
            <span>[Преимущества]</span>
            <h2>Свободный интернет без перегруза на старте</h2>
            <p>
              POKROV VPN помогает спокойно перейти к привычным сайтам и сервисам без сложной настройки. Вход остаётся
              простым: бот, тест, кабинет, оплата и поддержка на своих местах.
            </p>
          </div>
          <div className="lp-feature-grid">
            {BENEFITS.map((item, idx) => (
              <article key={item.title} className="lp-card">
                <div className="lp-card-index">0{idx + 1}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Сценарии]</span>
            <h2>Где этот путь особенно удобен</h2>
          </div>
          <div className="lp-feature-grid">
            {USE_CASES.map((item) => (
              <article key={item.title} className="lp-card">
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Как начать]</span>
            <h2>Три коротких шага до подключения</h2>
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

        <section id="trial" className="lp-section">
          <div className="lp-section-head">
            <span>[Тест]</span>
            <h2>Сначала попробуйте, потом принимайте решение</h2>
            <p>Тест на 5 дней помогает понять, подходит ли вам сервис по скорости, удобству и самому сценарию запуска.</p>
          </div>
          <div className="lp-support-grid">
            {TRIAL_CARDS.map((card) => (
              <article key={card.title} className="lp-card">
                <h3>{card.title}</h3>
                <div className="lp-price" style={{ marginTop: 12 }}>
                  {card.price}
                </div>
                <p>{card.note}</p>
                <a href={card.href} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary" style={{ marginTop: 20 }}>
                  {card.cta}
                </a>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>[Тарифы]</span>
            <h2>Планы для тех, кто уже всё проверил</h2>
            <p>Когда тест и сценарий вас устраивают, можно спокойно перейти на страницу оплаты и выбрать подходящий срок доступа.</p>
          </div>
          <div className="lp-plan-grid">
            {PAID_PLANS.map((plan) => (
              <article key={plan.code} className="lp-card lp-plan">
                <h3>{plan.name}</h3>
                <div className="lp-price">{plan.price}</div>
                <p>{plan.note}</p>
                <a href={buildCheckoutHref(plan.code)} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary" style={{ marginTop: 20 }}>
                  Перейти к оплате
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Отзывы]</span>
            <h2>Что пишут пользователи</h2>
            <p>На главную попадают только одобренные отзывы. Ники показываем в маске, чтобы сохранить приватность.</p>
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
            <h2>Коротко о том, как всё устроено</h2>
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
              <span>[Полезные страницы]</span>
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
          <div className="lp-card" style={{ display: "flex", justifyContent: "space-between", gap: 24, flexWrap: "wrap" }}>
            <div>
              <h3 style={{ marginBottom: 8 }}>POKROV VPN</h3>
              <p>
                Начать проще всего с Telegram: запустить тест, спокойно проверить сервис и уже потом перейти к кабинету или оплате, если всё подошло.
              </p>
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                🚀 Запустить тест
              </a>
              <a href={config.connectUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Открыть кабинет
              </a>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                💬 Поддержка
              </a>
              <a href={config.feedbackbotUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                🫶 Оставить отзыв
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
