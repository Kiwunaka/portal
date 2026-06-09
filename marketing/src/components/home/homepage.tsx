import Link from "next/link";

import JsonLd from "../json-ld";
import { MarketingBrandLogo } from "../marketing-brand-logo";
import styles from "./homepage.module.css";
import { buildFaqJsonLd, buildSoftwareApplicationJsonLd, MARKETING_CANONICAL_PATHS, MARKETING_FAQ } from "../../lib/marketing-site";
import {
  getCopyText,
  getPokrovPublicConfig,
  getTariffPlans,
} from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);
const CHECKOUT_READY_PLAN_CODES = new Set(["start_99"]);

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
};

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Скачайте приложение",
    text: "Выберите Android или Windows. Если файл доступен вашему аккаунту, кабинет покажет его и шаги установки.",
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

const HERO_HOOKS = [
  { value: "от 99 ₽", label: "за 30 дней после теста" },
  { value: "Android + Windows", label: "приложение POKROV" },
  { value: "до 5 устройств", label: "в платном доступе" },
];

function buildCheckoutHref(planCode: string): string {
  return `${MARKETING_CANONICAL_PATHS.checkout}?plan=${encodeURIComponent(planCode)}`;
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
  const heroTitle = getCopyText("marketing.hero.title", "POKROV открывает YouTube, TikTok и другие сервисы");
  const heroSubtitle = getCopyText(
    "marketing.hero.subtitle",
    "Установите приложение на Android или Windows, нажмите «Подключить» и проверьте свои сервисы. 5 дней бесплатно, карту не просим.",
  );
  const primaryCta = getCopyText("marketing.hero.primary_cta", "Попробовать 5 дней бесплатно");

  return (
    <section className={styles.container}>
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
                <div className={styles.appPreview}>
                  <div className={styles.appPreviewTop}>
                    <MarketingBrandLogo className={styles.heroScreenLogo} width={72} height={72} priority />
                    <span>Готово</span>
                  </div>
                  <div className={styles.connectPreviewRing}>
                    <span>Подключить</span>
                  </div>
              <div className={styles.previewPills} aria-label="Короткий статус приложения">
                    <span>Telegram +10</span>
                    <span>Android · Windows</span>
                  </div>
                </div>
              </div>
              <div className={styles.phone}>
                <div className={styles.phoneNotch} />
                <div className={styles.phoneScreen}>
                  <div className={styles.phoneMiniApp}>
                    <UiIcon name="shield" size={24} />
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className={styles.container}>
      <div className={styles.section} id="how-it-works">
        <div className={styles.sectionHead}>
          <span className={styles.eyebrow}>как начать</span>
          <h2>Скачали, включили, проверили</h2>
          <p>Один короткий путь: приложение, бесплатный период, подключение и продление в том же аккаунте.</p>
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
    </section>
  );
}

function Pricing({ links }: { links: HomeLinks }) {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards.find((plan) => plan.code === "start_99")?.code || planCards[0]?.code || "start_99";
  const featuredCode = defaultPlanCode;

  const freeFeatures = [
    "5 дней без карты",
    "Доступ активируется в приложении",
    "Android и Windows",
    "Telegram не нужен для первого старта",
  ];

  const paidFeatures = [
    "Больше направлений для подключения",
    "До 5 личных устройств",
    "Тот же аккаунт и кабинет",
    "Кабинет и поддержка",
  ];

  return (
    <section className={styles.container} id="pricing">
      <div className={styles.section}>
        <div className={styles.sectionHead}>
          <span className={styles.eyebrow}>сколько стоит</span>
          <h2>Сначала попробуйте, потом платите</h2>
          <p>Получите 5 дней в приложении без карты. Если POKROV подходит, стартовое продление на 30 дней стоит 99 ₽.</p>
        </div>

        <div className={styles.pricingLayout}>
          <div className={styles.pricingIntro}>
            <div className={`${styles.badge} ${styles.badgeEmerald}`}>старт</div>
            <h3>5 дней бесплатно без карты</h3>
            <p>
              Проверьте POKROV на YouTube, TikTok и других сервисах. Если нужен платный срок, стартовое продление на 30 дней стоит 99 ₽.
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
                    {plan.badge || (isFeatured ? "beta" : "продление")}
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
                    {isFeatured ? "Выбрать 30 дней" : "Выбрать срок"}
                  </Link>
                </article>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

function FinalCta({ links }: { links: HomeLinks }) {
  return (
    <section className={styles.container} id="final-cta">
      <div className={styles.finalCta}>
        <div className={styles.finalCopy}>
          <h2>Получите 5 дней бесплатно. Дальше решите сами</h2>
        </div>
        <div className={styles.finalActions}>
          <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnPill}`}>
            Попробовать 5 дней бесплатно
          </Link>
          <Link href={links.checkoutHref} className={styles.btnOutline}>
            Выбрать срок
          </Link>
        </div>
      </div>
    </section>
  );
}

function FaqSection() {
  return (
    <section className={styles.container} id="faq">
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
    </section>
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
            <MarketingBrandLogo className={styles.brandMark} priority />
            <span className={styles.brandText}>
              <strong>POKROV</strong>
              <small>Android и Windows · бета</small>
            </span>
          </Link>

          <nav className={styles.nav} aria-label="Навигация по главной">
            <a href="#how-it-works">Как начать</a>
            <a href="#pricing">Тарифы</a>
            <a href="#faq">FAQ</a>
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
          <Pricing links={links} />
          <HowItWorks />
          <FaqSection />
          <FinalCta links={links} />
        </main>
      </div>
    </>
  );
}
