import type { Metadata } from "next";
import Link from "next/link";

import { getPortalPublicConfig } from "../lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

const BENEFITS = [
  {
    title: "Свободный интернет без танцев с бубном.",
    desc: "YouTube, TikTok, Instagram и любимые сайты открываются в привычном ритме. Один понятный сценарий подключения без сложных настроек. Справится даже человек, который обычно просит «нажми тут за меня». И главное — вы платите только после того, как сами всё проверите.",
  },
];

const USE_CASES = [
  {
    title: "YouTube и стриминг",
    desc: "Смотреть ролики, прямые эфиры и длинные видео без мучительных переключений между случайными сервисами.",
  },
  {
    title: "TikTok и Instagram",
    desc: "Открывать ленту, Reels и клипы с телефона, не теряя время на повторные настройки.",
  },
  {
    title: "Сайты, мессенджеры и приложения",
    desc: "Один профиль для повседневного доступа на iPhone, Android, Windows и других устройствах.",
  },
];

const STEPS = [
  {
    title: "1. Откройте Telegram-бота",
    desc: "Первый шаг уже внутри бота: без лишних экранов и с одним понятным сценарием запуска.",
  },
  {
    title: "2. Заберите 3 дня бесплатного теста",
    desc: "Тест активируется в один клик, чтобы вы спокойно проверили скорость и удобство без оплаты на входе.",
  },
  {
    title: "3. Подключите устройство за пару минут",
    desc: "Бот и WebApp подскажут, что открыть дальше: ключ, QR и приложение без путаницы и долгой настройки.",
  },
];

const TRIAL_CARDS = [
  {
    title: "Тест 3 дня",
    price: "0 ₽",
    note: "1 устройство • 5 ГБ • удобный старт для проверки сервиса.",
    cta: "🚀 Начать бесплатно",
  },
  {
    title: "Free fallback",
    price: "0 ₽",
    note: "5 ГБ • 1 устройство • базовый доступ, если тест уже завершён.",
    cta: "Открыть бот",
  },
];

const PAID_PLANS = [
  { code: "1_month", name: "1 месяц", price: "249 ₽", note: "До 5 устройств • простой ежемесячный режим" },
  { code: "3_months", name: "3 месяца", price: "699 ₽", note: "До 5 устройств • удобнее, чем продлевать каждый месяц" },
  { code: "6_months", name: "6 месяцев", price: "1199 ₽", note: "До 5 устройств • заметная экономия и редкие продления" },
  { code: "12_months", name: "12 месяцев", price: "1644 ₽", note: "До 5 устройств • лучшая цена на длинной дистанции" },
];

const FAQ = [
  {
    q: "Почему сначала бот, а не сразу оплата?",
    a: "Потому что так честнее. Сначала вы бесплатно проверяете скорость, открываете привычные сервисы и смотрите, всё ли вам подходит. И только потом решаете, нужен ли вам тариф. Без кота в мешке.",
  },
  {
    q: "Что входит в тест?",
    a: "Три дня доступа для быстрой проверки сервиса: один профиль, один сценарий запуска и понятный путь к ключу или QR.",
  },
  {
    q: "Если касса временно не отвечает?",
    a: "Главный путь всё равно остаётся рабочим: бот, тест, подключение и поддержка. Продление можно продолжить через Telegram, когда касса снова доступна.",
  },
  {
    q: "Можно ли подключить несколько устройств?",
    a: "Да. Платные тарифы рассчитаны на несколько устройств, а в кабинете сразу видно лимит и доступные точки подключения.",
  },
];

const REVIEWS = [
  {
    name: "Артем",
    role: "Android",
    text: "Нажал кнопку в Telegram, поднял тест и за пару минут уже смотрел YouTube без поиска новых сервисов.",
  },
  {
    name: "Лена",
    role: "iPhone",
    text: "Понравилось, что сначала дали попробовать, а уже потом аккуратно подвели к тарифам и продлению.",
  },
  {
    name: "Илья",
    role: "Windows + телефон",
    text: "Подключил сразу два устройства и не потерялся: бот, кабинет и поддержка говорят одним языком.",
  },
];

const RELATED_PAGES = [
  { href: "/vpn-dlya-youtube/", label: "VPN для YouTube" },
  { href: "/vpn-telegram-bot/", label: "VPN Telegram bot" },
  { href: "/vpn-dlya-tiktok/", label: "VPN для TikTok" },
  { href: "/bystryy-vpn-na-telefon/", label: "Быстрый VPN на телефон" },
  { href: "/vpn-na-iphone-android-windows/", label: "VPN на iPhone / Android / Windows" },
];

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
};

export default function MarketingLanding({
  heroKicker,
  heroTitle,
  heroSubtitle,
  clusterTitle,
  clusterBody,
}: MarketingLandingProps) {
  return (
    <>
      <div className="lp-bg-blobs" aria-hidden="true" />
      <header className="lp-nav">
        <a href="#main-content" className="lp-brand">
          <span>◌</span>
          PORTAL
        </a>
        <nav className="lp-menu">
          <a href="#benefits">Что получаете</a>
          <a href="#trial">Тест</a>
          <a href="#pricing">Тарифы</a>
          <a href="#faq">FAQ</a>
          <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
            Уже подключены?
          </a>
          <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
            Запустить тест
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
              🚀 Начать бесплатно
            </a>
            <a href="#pricing" className="lp-btn lp-btn--ghost">
              Посмотреть тарифы
            </a>
          </div>
          <div className="lp-proof">
            <div>
              <strong>3 дня</strong>
              <span>lead magnet для холодного трафика</span>
            </div>
            <div>
              <strong>5 ГБ</strong>
              <span>ограниченный тестовый объём</span>
            </div>
            <div>
              <strong>Telegram → WebApp</strong>
              <span>единый путь от клика до подключения</span>
            </div>
          </div>
        </section>

        <section id="benefits" className="lp-section">
          <div className="lp-section-head">
            <span>[Что получаете]</span>
            <h2>Свободный интернет без танцев с бубном.</h2>
            <p>YouTube, TikTok, Instagram и любимые сайты открываются в привычном ритме. Один понятный сценарий подключения без сложных настроек. Справится даже человек, который обычно просит «нажми тут за меня». И главное — вы платите только после того, как сами всё проверите.</p>
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
            <span>[Что работает]</span>
            <h2>Сервисы и сценарии, ради которых люди реально ищут VPN</h2>
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
            <h2>Три шага до свободного интернета:</h2>
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
            <h2>Сначала попробовать, потом продлевать</h2>
            <p>Сначала вы проверяете сервис вживую, а уже потом решаете, нужен ли вам полный доступ. Бесплатный режим остаётся только как базовый запасной сценарий.</p>
          </div>
          <div className="lp-support-grid">
            {TRIAL_CARDS.map((card) => (
              <article key={card.title} className="lp-card">
                <h3>{card.title}</h3>
                <div className="lp-price" style={{ marginTop: 12 }}>{card.price}</div>
                <p>{card.note}</p>
                <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary" style={{ marginTop: 20 }}>
                  {card.cta}
                </a>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>[Тарифы]</span>
            <h2>Платные планы для тех, кто уже проверил сервис</h2>
            <p>Первый публичный CTA ведет в тест, а тарифы остаются следующим шагом для апгрейда и продления без агрессивного давления на оплату.</p>
          </div>
          <div className="lp-plan-grid">
            {PAID_PLANS.map((plan) => (
              <article key={plan.code} className="lp-card lp-plan">
                <h3>{plan.name}</h3>
                <div className="lp-price">{plan.price}</div>
                <p>{plan.note}</p>
                <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary" style={{ marginTop: 20 }}>
                  Открыть в Telegram
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="lp-section">
          <div className="lp-section-head">
            <span>[Отзывы]</span>
            <h2>Социальное доказательство без искусственного шума</h2>
          </div>
          <div className="lp-feature-grid">
            {REVIEWS.map((item) => (
              <article key={item.name} className="lp-card">
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
            <h2>Коротко о том, как устроена новая воронка</h2>
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
              <span>[SEO кластер]</span>
              <h2>{clusterTitle}</h2>
              <p>{clusterBody}</p>
            </div>
            <div className="lp-feature-grid">
              {RELATED_PAGES.map((item) => (
                <article key={item.href} className="lp-card">
                  <h3>{item.label}</h3>
                  <p>Отдельная посадочная страница под высокое намерение и быстрый переход в Telegram-бота.</p>
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
              <h3 style={{ marginBottom: 8 }}>PORTAL VPN</h3>
              <p>Главный путь сейчас простой: откройте бота, запустите тест, подключите приложение и переходите на платный план только после реальной проверки сервиса.</p>
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                Запустить тест
              </a>
              <Link href="/offer/" className="lp-btn lp-btn--ghost">Оферта</Link>
              <Link href="/privacy/" className="lp-btn lp-btn--ghost">Политика</Link>
            </div>
          </div>
        </section>
      </main>
    </>
  );
}
