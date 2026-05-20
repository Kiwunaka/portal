import Link from "next/link";
import { FadeUp } from "../ui/fade-up";

import JsonLd from "../json-ld";
import styles from "./homepage.module.css";
import { buildFaqJsonLd, buildSoftwareApplicationJsonLd, MARKETING_CANONICAL_PATHS, MARKETING_FAQ } from "../../lib/marketing-site";
import {
  getCopyText,
  getPokrovPublicConfig,
  getTariffPlans,
} from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

type PlanCard = {
  code: string;
  label: string;
  price: string;
  duration: string;
  devices: string;
  note: string;
  badge: string | null;
};

type HomeLinks = {
  checkoutHref: string;
  installHref: string;
  cabinetHref: string;
  supportHref: string;
  channelHref: string;
};

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Скачайте приложение",
    text: "Выберите Android или Windows. Если сборка доступна вашему аккаунту, кабинет покажет файл и шаги установки.",
  },
  {
    step: "2",
    title: "Запустите 5 дней без карты",
    text: "Первый период активируется в приложении: без платежных данных, автосписаний и долгой регистрации.",
  },
  {
    step: "3",
    title: "Нажмите «Подключить»",
    text: "POKROV применит нужные параметры сам. Никаких конфигов, серверных списков и ручных профилей.",
  },
  {
    step: "4",
    title: "Продлите, если подходит",
    text: "Цена, срок и лимит устройств видны до оплаты. После окончания полного доступа останется базовый режим.",
  },
];

const SURFACE_PANELS = [
  {
    eyebrow: "Старт",
    title: "Одна кнопка вместо настроек",
    text: "Не нужно искать ссылку, копировать конфиг или выбирать сервер из списка. Установили приложение, нажали «Подключить» и проверили свои сервисы.",
    bullets: ["Скачайте приложение", "Получите 5 дней", "Нажмите «Подключить»"],
    tone: "routing" as const,
  },
  {
    eyebrow: "Устройства",
    title: "Телефон и компьютер вместе",
    text: "Android и Windows остаются в одном кабинете: там видны загрузки, срок доступа, устройства и продление.",
    bullets: ["Android + Windows", "До 5 устройств в платных планах", "Один кабинет для управления"],
    tone: "devices" as const,
  },
  {
    eyebrow: "Вход",
    title: "Почта и Telegram ведут в один аккаунт",
    text: "Начать можно без Telegram. Почту и Telegram можно привязать позже для входа, бонуса, восстановления и поддержки.",
    bullets: ["Email-вход", "Telegram-бонус +10 дней", "Один профиль POKROV"],
    tone: "support" as const,
  },
];

const HERO_HOOKS = [
  { value: "5 дней", label: "без карты и автосписаний" },
  { value: "от 99 ₽", label: "за 30 дней после теста" },
  { value: "Android + Windows", label: "beta-сборки" },
  { value: "до 5 устройств", label: "в платном доступе" },
];

const VALUE_CARDS = [
  {
    icon: "event_available",
    title: "Карта не нужна",
    text: "5 дней теста без платежных данных и автосписаний. Сначала проверяете POKROV на своих сервисах, потом решаете.",
  },
  {
    icon: "phone_android",
    title: "Одна кнопка вместо настроек",
    text: "POKROV сам применит нужные параметры. Никаких конфигов, ручных профилей и выбора серверов на первом экране.",
  },
  {
    icon: "devices",
    title: "Телефон и компьютер вместе",
    text: "Android и Windows управляются вместе. В платных планах можно подключить до 5 личных устройств.",
  },
  {
    icon: "security",
    title: "Telegram как бонус",
    text: "Начать можно без Telegram. Привяжете позже — получите +10 дней, восстановление и быстрый канал поддержки.",
  },
];

function buildCheckoutHref(planCode: string): string {
  return `${MARKETING_CANONICAL_PATHS.checkout}?plan=${encodeURIComponent(planCode)}`;
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
      duration: `${Number(plan.duration_days || 0)} дней`,
      devices: `До ${Number(plan.device_limit || 1)} устройств`,
      note:
        plan.marketing_note ||
        plan.cabinet_note ||
        "Продление добавляет срок к тому же аккаунту POKROV.",
      badge: plan.badge || null,
    }));
}

function buildLinks(defaultPlanCode: string): HomeLinks {
  return {
    checkoutHref: buildCheckoutHref(defaultPlanCode),
    installHref: MARKETING_CANONICAL_PATHS.install,
    cabinetHref: config.webappUrl,
    supportHref: config.contactFormUrl || config.supportTelegramUrl || config.helpbotUrl,
    channelHref: config.newsChannelUrl,
  };
}

/* ── Icons ── */
function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={styles.check}>
      <path d="M3 8L6.5 11.5L13 4.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M3 9H15M15 9L10 4M15 9L10 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function UiIcon({ name, size = 20 }: { name: string; size?: number }) {
  const common = {
    width: size,
    height: size,
    viewBox: "0 0 24 24",
    fill: "none",
    "aria-hidden": true,
    className: styles.uiIcon,
  };

  if (name === "play_circle") {
    return (
      <svg {...common}>
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.9" />
        <path d="M10 8.8L15.2 12L10 15.2V8.8Z" fill="currentColor" />
      </svg>
    );
  }

  if (name === "event_available") {
    return (
      <svg {...common}>
        <path d="M7 3.8V6.2M17 3.8V6.2M5.5 9.2H18.5" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
        <rect x="4" y="5.5" width="16" height="14.5" rx="3" stroke="currentColor" strokeWidth="1.9" />
        <path d="M8.2 14L10.6 16.3L15.8 11" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  if (name === "phone_android") {
    return (
      <svg {...common}>
        <rect x="7.5" y="3.5" width="9" height="17" rx="2.4" stroke="currentColor" strokeWidth="1.9" />
        <path d="M10.5 17.5H13.5" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
      </svg>
    );
  }

  if (name === "devices") {
    return (
      <svg {...common}>
        <rect x="3.5" y="5" width="12.5" height="9" rx="2" stroke="currentColor" strokeWidth="1.9" />
        <rect x="15" y="9.5" width="5.5" height="9.5" rx="1.7" stroke="currentColor" strokeWidth="1.9" />
        <path d="M8 18H13" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
      </svg>
    );
  }

  if (name === "route") {
    return (
      <svg {...common}>
        <path d="M6.5 6.5H9.5C11.4 6.5 12.5 7.6 12.5 9.2C12.5 10.8 11.4 12 9.6 12H14.5C16.4 12 17.5 13.1 17.5 14.7C17.5 16.3 16.4 17.5 14.5 17.5H12" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
        <circle cx="6.2" cy="6.5" r="2.2" stroke="currentColor" strokeWidth="1.9" />
        <circle cx="17.8" cy="17.5" r="2.2" stroke="currentColor" strokeWidth="1.9" />
      </svg>
    );
  }

  if (name === "lock") {
    return (
      <svg {...common}>
        <rect x="5" y="10" width="14" height="10" rx="2.5" stroke="currentColor" strokeWidth="1.9" />
        <path d="M8.5 10V7.8C8.5 5.7 9.9 4.2 12 4.2C14.1 4.2 15.5 5.7 15.5 7.8V10" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <svg {...common}>
      <path d="M12 3.8L18.3 6.2V11.2C18.3 15.2 15.8 18.5 12 20.2C8.2 18.5 5.7 15.2 5.7 11.2V6.2L12 3.8Z" stroke="currentColor" strokeWidth="1.9" strokeLinejoin="round" />
      {name === "shield_lock" ? (
        <>
          <rect x="9.2" y="10.8" width="5.6" height="4.4" rx="1" stroke="currentColor" strokeWidth="1.6" />
          <path d="M10.5 10.8V9.7C10.5 8.8 11.1 8.2 12 8.2C12.9 8.2 13.5 8.8 13.5 9.7V10.8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
        </>
      ) : name === "verified_user" || name === "security" ? (
        <path d="M8.9 12.2L11 14.2L15.4 9.7" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round" />
      ) : null}
    </svg>
  );
}

/* ── Sections ── */

function Hero({ links }: { links: HomeLinks }) {
  const heroTitle = getCopyText("marketing.hero.title", "POKROV для YouTube, TikTok и нужных вам сайтов");
  const heroSubtitle = getCopyText(
    "marketing.hero.subtitle",
    "Установите приложение на Android или Windows, нажмите «Подключить» и проверьте свои сервисы. 5 дней бесплатно, карту не просим.",
  );
  const primaryCta = getCopyText("marketing.hero.primary_cta", "Попробовать 5 дней бесплатно");

  return (
    <FadeUp delay={0.1} as="section" className={styles.container}>
      <div className={styles.hero}>
        <div className={styles.heroGrid}>
          <div className={styles.heroCopy}>
            <div className={styles.eyebrow}>
              <UiIcon name="verified_user" size={18} />
              {getCopyText("marketing.hero.kicker", "POKROV • 5 дней без карты")}
            </div>
            <h1 className={styles.heroTitle}>{heroTitle}</h1>
            <p className={styles.heroSubtitle}>{heroSubtitle}</p>
            <div className={styles.heroActions}>
              <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}>
                <UiIcon name="shield_lock" size={22} />
                {primaryCta}
              </Link>
              <a href="#pricing" className={`${styles.btnSecondary} ${styles.btnPill}`}>
                <UiIcon name="play_circle" size={20} />
                Посмотреть тарифы
              </a>
            </div>
            <div className={styles.heroHooks} aria-label="Коротко о POKROV">
              {HERO_HOOKS.map((item) => (
                <div key={item.value} className={styles.heroHook}>
                  <span className={styles.heroHookValue}>{item.value}</span>
                  <span className={styles.heroHookLabel}>{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.heroVisual}>
            <div className={`${styles.deviceFrame} ${styles.laptop}`}>
              <div className={styles.laptopTop}>
                <span /><span /><span />
              </div>
              <div className={styles.laptopScreen}>
                <div style={{ textAlign: "center", color: "#0d5c3b" }}>
                  <img className={styles.heroScreenLogo} src="/pokrov-logo.svg" alt="" aria-hidden="true" />
                  <p style={{ margin: "8px 0 0", fontSize: 14, fontWeight: 700 }}>POKROV</p>
                  <p style={{ margin: 0, fontSize: 12, opacity: 0.6 }}>Подключено</p>
                </div>
              </div>
              <div className={styles.phone}>
                <div className={styles.phoneNotch} />
                <div className={styles.phoneScreen}>
                  <UiIcon name="shield" size={30} />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </FadeUp>
  );
}

function ValueCards() {
  return (
    <FadeUp delay={0.25} as="section" className={styles.container} id="why-pokrov">
        <div className={styles.section}>
          <div className={styles.sectionHead}>
            <span className={styles.eyebrow}>почему POKROV</span>
            <h2>Конкретно: пробуете, подключаете, решаете</h2>
            <p>Карта не нужна на старте, Telegram не обязателен, а тарифы видны до оплаты.</p>
          </div>
        <div className={styles.valueGrid}>
          {VALUE_CARDS.map((card) => (
            <article key={card.title} className={styles.valueCard}>
              <div className={styles.valueIcon}>
                <UiIcon name={card.icon} size={22} />
              </div>
              <h3>{card.title}</h3>
              <p>{card.text}</p>
            </article>
          ))}
        </div>
      </div>
    </FadeUp>
  );
}

function HowItWorks() {
  return (
    <FadeUp delay={0.3} as="section" className={styles.container}>
        <div className={styles.section} id="how-it-works">
          <div className={styles.sectionHead}>
            <span className={styles.eyebrow}>как начать</span>
          <h2>Старт за пару минут</h2>
          <p>Сначала приложение и бесплатный период, затем тариф в том же аккаунте. Кабинет показывает срок, устройства, оплату и поддержку.</p>
        </div>
        <div className={styles.stepsGrid}>
          {HOW_IT_WORKS.map((item) => (
            <article key={item.step} className={styles.stepCard}>
              <div className={styles.stepIndex}>{item.step}</div>
              <h3>{item.title}</h3>
              <p>{item.text}</p>
            </article>
          ))}
        </div>
      </div>
    </FadeUp>
  );
}

function SurfaceMock({ tone }: { tone: (typeof SURFACE_PANELS)[number]["tone"] }) {
  if (tone === "devices") {
    return (
      <div className={`${styles.mockVisual} ${styles.mockDevices}`} aria-hidden="true">
        <div className={styles.mockDeviceRow}>
          <div className={`${styles.mockDevice} ${styles.mockDeviceLaptop}`} />
          <div className={`${styles.mockDevice} ${styles.mockDeviceTablet}`} />
          <div className={`${styles.mockDevice} ${styles.mockDevicePhone}`} />
        </div>
      </div>
    );
  }

  if (tone === "routing") {
    return (
      <div className={styles.mockVisual} aria-hidden="true">
        <div className={styles.mockRouting}>
          <div className={styles.mockRoutingModes}>
            <div className={styles.modeCardActive}>
              <strong>Всё устройство</strong>
              <span>Один режим для повседневного старта</span>
            </div>
            <div className={styles.modeCard}>
              <strong>Выбор приложений</strong>
              <span>Для тех, кому нужна точная настройка</span>
            </div>
          </div>
          <div className={styles.mockRoutingMap} />
        </div>
      </div>
    );
  }

  return (
    <div className={styles.mockVisual} aria-hidden="true">
      <div className={`${styles.mockVisual} ${styles.mockSupport}`}>
        <div className={styles.mockSupportRail}>
          <span className={styles.mockSupportRailActive}>Поддержка</span>
          <span>История</span>
          <span>FAQ</span>
        </div>
        <div className={styles.mockSupportBody}>
          <div className={styles.searchBar} />
          <div className={styles.supportQuickRow}>
            <span /><span /><span />
          </div>
          <div className={styles.supportList}>
            <div /><div />
          </div>
        </div>
      </div>
    </div>
  );
}

function Features() {
  return (
    <FadeUp delay={0.4} as="section" className={styles.container}>
        <div className={styles.section}>
          <div className={styles.sectionHead}>
            <span className={styles.eyebrow}>возможности</span>
          <h2>Что видно в POKROV</h2>
          <p>Приложение ведет к подключению, кабинет показывает срок и устройства, поддержка помогает с установкой, входом и продлением.</p>
        </div>
        <div className={styles.surfaceGrid}>
          {SURFACE_PANELS.map((panel) => (
            <article key={panel.title} className={styles.surfaceCard}>
              <div>
                <span className={styles.eyebrow} style={{ marginBottom: 12, fontSize: "0.7rem", padding: "6px 10px" }}>
                  {panel.eyebrow}
                </span>
                <h3>{panel.title}</h3>
                <p>{panel.text}</p>
              </div>
              <SurfaceMock tone={panel.tone} />
              <ul className={styles.surfaceBullets}>
                {panel.bullets.map((bullet) => (
                  <li key={bullet}>{bullet}</li>
                ))}
              </ul>
            </article>
          ))}
        </div>
        <div className={styles.inlineActions}>
          <Link href={MARKETING_CANONICAL_PATHS.install} className={styles.inlineLink}>
            Установить приложение <ArrowRightIcon />
          </Link>
          <a href={config.contactFormUrl || config.supportTelegramUrl || config.helpbotUrl} className={styles.inlineLink}>
            Поддержка <ArrowRightIcon />
          </a>
          <a href={config.newsChannelUrl} className={styles.inlineLink}>
            Канал POKROV <ArrowRightIcon />
          </a>
        </div>
      </div>
    </FadeUp>
  );
}

function Pricing({ links }: { links: HomeLinks }) {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards.find((plan) => plan.code === "start_99")?.code || planCards[0]?.code || "start_99";
  const featuredCode = planCards.find((plan) => plan.code === "12_months")?.code || planCards[1]?.code || defaultPlanCode;

  const freeFeatures = [
    "5 дней без карты",
    "Доступ активируется в приложении",
    "Android и Windows",
    "Telegram не нужен для первого старта",
  ];

  const paidFeatures = [
    "Платный пул доступных узлов",
    "До 5 личных устройств",
    "Тот же аккаунт и кабинет",
    "Кабинет и поддержка",
  ];

  return (
    <FadeUp delay={0.5} as="section" className={styles.container} id="pricing">
        <div className={styles.section}>
          <div className={styles.sectionHead}>
            <span className={styles.eyebrow}>сколько стоит</span>
          <h2>Сначала попробуйте, потом платите</h2>
          <p>Получите 5 дней в приложении без карты. Если всё нравится, выберите срок: цена, лимит устройств и условия видны до оплаты.</p>
        </div>

        <div className={styles.pricingLayout}>
          <div className={styles.pricingIntro}>
            <div className={`${styles.badge} ${styles.badgeEmerald}`}>старт</div>
            <h3>5 дней бесплатно без карты</h3>
            <p>
              Проверьте POKROV на YouTube, TikTok и нужных сайтах. Если нужен платный срок, стартовое продление на 30 дней стоит 99 ₽.
            </p>
            <ul className={styles.planFeatures}>
              {freeFeatures.map((f) => (
                <li key={f}>
                  <CheckIcon />
                  {f}
                </li>
              ))}
            </ul>
              <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`} style={{ marginTop: "auto" }}>
              Попробовать 5 дней бесплатно
            </Link>
          </div>

          <div className={styles.planGrid}>
            {planCards.map((plan) => {
              const isFeatured = plan.code === featuredCode;
              return (
                <article key={plan.code} className={`${styles.planCard} ${isFeatured ? styles.planCardFeatured : ""}`.trim()}>
                  <div className={`${styles.planBadge} ${isFeatured ? styles.badgeAmber : styles.badgeEmerald}`}>
                    {plan.badge || (isFeatured ? "выгодно" : "продление")}
                  </div>
                  <h3>{plan.label}</h3>
                  <div className={styles.planPrice}>
                    {plan.price} <span>/ {plan.duration.replace(/\d+\s*/, "")}</span>
                  </div>
                  <div className={styles.planMeta}>
                    <span>{plan.duration}</span>
                    <span>{plan.devices}</span>
                  </div>
                  <p>{plan.note}</p>
                  <ul className={styles.planFeatures}>
                    {paidFeatures.map((f) => (
                      <li key={f}>
                        <CheckIcon />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <Link
                    href={buildCheckoutHref(plan.code)}
                    className={isFeatured ? styles.btnPrimary : styles.btnSecondary}
                    style={{ marginTop: "auto", borderRadius: "var(--radius-pill)" }}
                  >
                    {isFeatured ? "Выбрать выгодный срок" : "Выбрать срок"}
                  </Link>
                </article>
              );
            })}
          </div>
        </div>
      </div>
    </FadeUp>
  );
}

function FinalCta({ links }: { links: HomeLinks }) {
  return (
    <FadeUp delay={0.6} as="section" className={styles.container} id="final-cta">
      <div className={styles.finalCta}>
        <div className={styles.finalCopy}>
          <span className={styles.eyebrow} style={{ borderColor: "rgba(255,255,255,0.2)", background: "rgba(255,255,255,0.08)", color: "#fff" }}>
            первый шаг
          </span>
          <h2>Получите 5 дней бесплатно. Дальше решите сами</h2>
          <p>
            Android и Windows остаются beta-сборками. Кабинет показывает тарифы, устройства и поддержку, а Telegram добавляет бонус и запасной способ связи.
          </p>
        </div>
        <div className={styles.finalActions}>
          <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}>
            Попробовать 5 дней бесплатно
          </Link>
          <Link href={links.checkoutHref} className={styles.btnOutline}>
            Выбрать срок
          </Link>
          <a href={links.cabinetHref} className={styles.btnOutline}>
            Кабинет
          </a>
          <a href={links.supportHref} className={styles.btnOutline}>
            Поддержка
          </a>
        </div>
      </div>
    </FadeUp>
  );
}

function FaqSection() {
  return (
    <FadeUp delay={0.56} as="section" className={styles.container} id="faq">
      <div className={styles.section}>
        <div className={styles.sectionHead}>
          <span className={styles.eyebrow}>FAQ</span>
          <h2>Ответы перед установкой и оплатой</h2>
          <p>Коротко о бесплатном старте, продлении, Telegram-бонусе и поддержке.</p>
        </div>
        <div className={styles.faqGrid}>
          {MARKETING_FAQ.map((item) => (
            <details key={item.question} className={styles.faqItem}>
              <summary className={styles.faqQuestion}>
                <span>{item.question}</span>
                <span aria-hidden="true" className={styles.faqIcon}>+</span>
              </summary>
              <p>{item.answer}</p>
            </details>
          ))}
        </div>
      </div>
    </FadeUp>
  );
}

/* ── Main Page ── */

export default function MarketingHomePage() {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards.find((plan) => plan.code === "start_99")?.code || planCards[0]?.code || "start_99";
  const links = buildLinks(defaultPlanCode);

  return (
    <>
      <JsonLd data={buildSoftwareApplicationJsonLd({ pagePath: "/" })} />
      <JsonLd data={buildFaqJsonLd(MARKETING_FAQ)} />

      <div className={styles.page}>
        <header className={styles.topbar}>
          <Link href="/" className={styles.brand}>
            <img className={styles.brandMark} src="/pokrov-logo.svg" alt="" aria-hidden="true" />
            <span className={styles.brandText}>
              <strong>POKROV</strong>
              <small>5 дней бесплатно • Android и Windows</small>
            </span>
          </Link>

          <nav className={styles.nav} aria-label="Навигация по главной">
            <a href="#why-pokrov">Преимущества</a>
            <a href="#how-it-works">Как работает</a>
            <a href="#pricing">Планы</a>
            <a href="#final-cta">Начать</a>
          </nav>

          <div className={styles.topbarActions}>
            <a href={links.cabinetHref} className={styles.btnGhost}>
              Кабинет
            </a>
            <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}>
              Попробовать 5 дней бесплатно
            </Link>
          </div>
        </header>

        <main id="main-content">
          <Hero links={links} />
          <ValueCards />
          <Pricing links={links} />
          <HowItWorks />
          <Features />
          <FaqSection />
          <FinalCta links={links} />
        </main>
      </div>
    </>
  );
}
