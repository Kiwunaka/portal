import Link from "next/link";
import { FadeUp } from "../ui/fade-up";

import JsonLd from "../json-ld";
import styles from "./homepage.module.css";
import { buildSoftwareApplicationJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import {
  CANONICAL_PUBLIC_DEFAULT_ROUTE_MODE,
  CANONICAL_PUBLIC_PLATFORM_SCOPE,
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

const HERO_FACTS = [
  { value: "5 дней", label: "бесплатно, без карты, с полным доступом" },
  { value: "Android + Windows", label: "приложения для ваших устройств" },
  { value: "До 5 устройств", label: "один доступ на всю семью" },
  { value: "Без лишней рутины", label: "приложение, кабинет и поддержка в одном пути" },
];

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Откройте маршрут установки",
    text: "Проверьте бета-доступ для Android или Windows. Если файл доступен вашему аккаунту, кабинет покажет правильную ссылку.",
  },
  {
    step: "2",
    title: "Попробуйте 5 дней бесплатно",
    text: "Доступ ко всем доступным серверам на время пробы. Достаточно, чтобы понять, подходит ли вам сервис.",
  },
  {
    step: "3",
    title: "Пользуйтесь интернетом",
    text: "Безопасное соединение из любой точки мира. Смотрите, работайте, общайтесь — всё работает как обычно, только защищённее.",
  },
  {
    step: "4",
    title: "Продлите если понравилось",
    text: "Выберите удобный срок и продолжайте пользоваться тем же доступом. Никаких новых настроек.",
  },
];

const SURFACE_PANELS = [
  {
    eyebrow: "Устройства",
    title: "Один доступ — все экраны",
    text: "Установите POKROV на телефон, ноутбук и планшет. Все устройства работают под одним доступом без дополнительной платы.",
    bullets: ["Android и Windows в одном приложении", "До 5 устройств одновременно", "Переключайтесь мгновенно"],
    tone: "devices" as const,
  },
  {
    eyebrow: "Маршрут",
    title: "Вы сами решаете, что защищать",
    text: "Можно включить защиту для всего устройства или оставить только выбранные приложения. Сценарий меняется без ручных конфигов.",
    bullets: ["Режим для всего устройства", "Выбор отдельных приложений", "Переключение без ручных настроек"],
    tone: "routing" as const,
  },
  {
    eyebrow: "Поддержка",
    title: "Если что-то не так — мы рядом",
    text: "Напишите в поддержку прямо из приложения или кабинета. Один тикет, полная история, не нужно объяснять всё заново.",
    bullets: ["Без декоративного SLA", "Видна история обращений", "Telegram-канал с обновлениями"],
    tone: "support" as const,
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
    .slice(0, 3)
    .map((plan) => ({
      code: plan.code,
      label: plan.label,
      price: `${Number(plan.amount_rub || 0)} ₽`,
      duration: `${Number(plan.duration_days || 0)} дней`,
      devices: `До ${Number(plan.device_limit || 1)} устройств`,
      note:
        plan.marketing_note ||
        plan.cabinet_note ||
        "Продление продолжается поверх того же доступа, без ручного перезапуска.",
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
  return (
    <FadeUp delay={0.1} as="section" className={styles.container}>
      <div className={styles.hero}>
        <div className={styles.heroGrid}>
          <div className={styles.heroCopy}>
            <div className={styles.eyebrow}>
              <UiIcon name="verified_user" size={18} />
              Премиум-доступ
            </div>
            <h1 className={styles.heroTitle}>
              Интернет
              <br />
              без границ
            </h1>
            <p className={styles.heroSubtitle}>
              Спокойный защищенный маршрут для Android и Windows. 5 дней бесплатно, без привязки карты и без технической рутины на старте.
            </p>
            <div className={styles.heroActions}>
              <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}>
                <UiIcon name="shield_lock" size={22} />
                Попробовать бесплатно
              </Link>
              <a href="#how-it-works" className={`${styles.btnSecondary} ${styles.btnPill}`}>
                <UiIcon name="play_circle" size={20} />
                Как это работает
              </a>
            </div>
            <ul className={styles.heroNotes}>
              {HERO_FACTS.map((f) => (
                <li key={f.value}>
                  <strong>{f.value}</strong> — {f.label}
                </li>
              ))}
            </ul>
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

function ProofStrip() {
  const items = [
    { icon: "event_available", value: "5 дней", label: "бесплатного доступа без карты" },
    { icon: "phone_android", value: buildPlatformLabel(), label: "приложения для ваших устройств" },
    { icon: "devices", value: "До 5", label: "устройств одновременно" },
    { icon: "security", value: "Старт в приложении", label: "кабинет остается рядом" },
    { icon: "route", value: buildRouteLabel(), label: "публичный режим маршрута по умолчанию" },
  ];

  return (
    <FadeUp delay={0.2} as="section" className={styles.container}>
      <div className={styles.proofStrip}>
        {items.map((item) => (
          <div key={item.value} className={styles.proofCard}>
            <div className={styles.proofIcon}>
              <UiIcon name={item.icon} size={22} />
            </div>
            <div>
              <span className={styles.proofValue}>{item.value}</span>
              <span className={styles.proofLabel}>{item.label}</span>
            </div>
          </div>
        ))}
      </div>
      <div className={styles.proofFooter}>
        <UiIcon name="lock" size={16} />
        Ваши данные под защитой. Конфиденциально. С понятными условиями. Всегда на вашей стороне.
      </div>
    </FadeUp>
  );
}

function HowItWorks() {
  return (
    <FadeUp delay={0.3} as="section" className={styles.container}>
      <div className={styles.section} id="how-it-works">
        <div className={styles.sectionHead}>
          <span className={styles.eyebrow}>как это работает</span>
          <h2>Четыре шага до безопасного интернета</h2>
          <p>Никаких сложных настроек и технических терминов. Откройте — подключите — пользуйтесь.</p>
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
              <strong>Полный туннель</strong>
              <span>Весь трафик защищён</span>
            </div>
            <div className={styles.modeCard}>
              <strong>Разделённый</strong>
              <span>Только выбранные приложения</span>
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
          <h2>Всё, что нужно для безопасного интернета</h2>
          <p>POKROV работает тихо и незаметно. Вы даже не почувствуете разницы — просто интернет станет безопаснее.</p>
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
  const featuredCode = planCards[1]?.code || defaultPlanCode;

  const freeFeatures = [
    "Полный доступ на 5 дней",
    "Все доступные серверы в пробе",
    "Высокая скорость",
    "Без привязки карты",
  ];

  const paidFeatures = [
    "Доступ без счетчика трафика",
    "Высокая скорость на всех серверах",
    "Поддержка без повторного старта",
    "До 5 устройств",
  ];

  return (
    <FadeUp delay={0.5} as="section" className={styles.container} id="pricing">
      <div className={styles.section}>
        <div className={styles.sectionHead}>
          <span className={styles.eyebrow}>тарифы</span>
          <h2>Сначала проба, потом — ваш выбор</h2>
          <p>5 дней бесплатно, чтобы понять, подходит ли вам сервис. Потом выберите удобный срок.</p>
        </div>

        <div className={styles.pricingLayout}>
          <div className={styles.pricingIntro}>
            <div className={`${styles.badge} ${styles.badgeEmerald}`}>старт</div>
            <h3>5 дней бесплатно</h3>
            <p>
              Достаточно, чтобы проверить скорость, стабильность и удобство. Серверы премиум-пула, без карты.
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
              Начать бесплатно
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
                    {isFeatured ? "Выбрать этот" : "Выбрать"}
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
            готовы начать?
          </span>
          <h2>Попробуйте 5 дней бесплатно</h2>
          <p>
            Никаких обязательств. Откройте маршрут установки, войдите в тот же аккаунт и проверьте, доступна ли бета для вашего устройства.
          </p>
        </div>
        <div className={styles.finalActions}>
          <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}>
            Проверить бета-доступ
          </Link>
          <Link href={links.checkoutHref} className={styles.btnOutline}>
            Выбрать тариф
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

/* ── Main Page ── */

export default function MarketingHomePage() {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards.find((plan) => plan.code === "start_99")?.code || planCards[0]?.code || "start_99";
  const links = buildLinks(defaultPlanCode);

  return (
    <>
      <JsonLd data={buildSoftwareApplicationJsonLd({ pagePath: "/" })} />

      <div className={styles.page}>
        <header className={styles.topbar}>
          <Link href="/" className={styles.brand}>
            <img className={styles.brandMark} src="/pokrov-logo.svg" alt="" aria-hidden="true" />
            <span className={styles.brandText}>
              <strong>POKROV</strong>
              <small>спокойный цифровой маршрут</small>
            </span>
          </Link>

          <nav className={styles.nav} aria-label="Навигация по главной">
            <a href="#proof">Преимущества</a>
            <a href="#how-it-works">Как работает</a>
            <a href="#pricing">Тарифы</a>
            <a href="#final-cta">Начать</a>
          </nav>

          <div className={styles.topbarActions}>
            <a href={links.cabinetHref} className={styles.btnGhost}>
              Кабинет
            </a>
            <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}>
              Установить
            </Link>
          </div>
        </header>

        <main id="main-content">
          <Hero links={links} />
          <ProofStrip />
          <HowItWorks />
          <Features />
          <Pricing links={links} />
          <FinalCta links={links} />
        </main>
      </div>
    </>
  );
}
