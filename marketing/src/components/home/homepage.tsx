import Link from "next/link";

import HomepageTopbar from "./homepage-topbar";
import JsonLd from "../json-ld";
import { MarketingBrandLogo } from "../marketing-brand-logo";
import { Reveal } from "./reveal";
import styles from "./homepage.module.css";
import { buildFaqJsonLd, buildSoftwareApplicationJsonLd, MARKETING_CANONICAL_PATHS, MARKETING_FAQ } from "../../lib/marketing-site";
import { getCopyText, getPokrovPublicConfig, getTariffPlans } from "../../lib/pokrov";

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

type HomeLinks = { checkoutHref: string; installHref: string; cabinetHref: string };

const HOW_IT_WORKS = [
  { step: "1", title: "Скачайте приложение", text: "Android или Windows. Один файл, без долгой регистрации и настройки вручную." },
  { step: "2", title: "Запустите 5 дней бесплатно", text: "Первый период включается прямо в приложении — без карты и автосписаний." },
  { step: "3", title: "Нажмите «Подключить»", text: "POKROV сам подберёт параметры. Никаких серверных списков и ручных настроек." },
  { step: "4", title: "Продлите, если подходит", text: "Цена и срок видны до оплаты. Дальше — тот же аккаунт и кабинет." },
];

const FEATURES = [
  { icon: "globe", title: "Открывает нужные сервисы", text: "YouTube, TikTok, мессенджеры и привычные сайты снова открываются — на телефоне и компьютере." },
  { icon: "bolt", title: "Подключение в один тап", text: "Без выбора сервера и копирования конфигов. Нажали «Подключить» — и всё работает." },
  { icon: "devices", title: "Android, Windows и кабинет", text: "До 5 устройств на одном аккаунте. Срок, устройства и оплата — в личном кабинете." },
  { icon: "headset", title: "Поддержка рядом", text: "Живой ответ в Telegram и в кабинете. Бонус +10 дней за подписку на канал." },
];

const TRUST = [
  { value: "5 дней", label: "бесплатно, без карты" },
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
      note: plan.marketing_note || plan.cabinet_note || "Продление добавляет срок к тому же аккаунту POKROV.",
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

/* ── Icons (ultra-light line set) ── */
function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className={styles.check} aria-hidden="true">
      <path d="M3 8.2 6.4 11.6 13 4.6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function UiIcon({ name, size = 22 }: { name: string; size?: number }) {
  const c = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", "aria-hidden": true, className: styles.uiIcon } as const;
  const s = { stroke: "currentColor", strokeWidth: 1.7, strokeLinecap: "round", strokeLinejoin: "round" } as const;
  if (name === "shield")
    return (<svg {...c}><path d="M12 3.5 18.5 6v5.6c0 4.3-2.5 7.7-6.5 8.9-4-1.2-6.5-4.6-6.5-8.9V6L12 3.5Z" {...s} /><path d="m9.3 12 1.8 1.9 3.6-4.1" {...s} /></svg>);
  if (name === "bolt")
    return (<svg {...c}><path d="M13 3 5 13.5h6L11 21l8-10.5h-6L13 3Z" {...s} /></svg>);
  if (name === "globe")
    return (<svg {...c}><circle cx="12" cy="12" r="8.4" {...s} /><path d="M3.6 12h16.8M12 3.6c2.3 2.3 3.5 5.3 3.5 8.4s-1.2 6.1-3.5 8.4c-2.3-2.3-3.5-5.3-3.5-8.4S9.7 5.9 12 3.6Z" {...s} /></svg>);
  if (name === "devices")
    return (<svg {...c}><rect x="3.3" y="5" width="12.6" height="9" rx="2" {...s} /><rect x="15.2" y="9.4" width="5.5" height="9.6" rx="1.6" {...s} /><path d="M7.8 18h5" {...s} /></svg>);
  if (name === "headset")
    return (<svg {...c}><path d="M5 13v-1a7 7 0 0 1 14 0v1" {...s} /><rect x="3.4" y="12.6" width="3.4" height="6" rx="1.5" {...s} /><rect x="17.2" y="12.6" width="3.4" height="6" rx="1.5" {...s} /><path d="M19 18.6c0 1.6-1.7 2.6-3.5 2.6" {...s} /></svg>);
  if (name === "play")
    return (<svg {...c}><circle cx="12" cy="12" r="8.4" {...s} /><path d="M10.2 8.8 15 12l-4.8 3.2V8.8Z" fill="currentColor" /></svg>);
  if (name === "lock")
    return (<svg {...c}><rect x="5" y="10.4" width="14" height="9.4" rx="2.4" {...s} /><path d="M8.4 10.4V8c0-2 1.5-3.6 3.6-3.6S15.6 6 15.6 8v2.4" {...s} /></svg>);
  if (name === "arrow")
    return (<svg {...c}><path d="M5 12h13M13 6.5 18.5 12 13 17.5" {...s} /></svg>);
  return (<svg {...c}><circle cx="12" cy="12" r="8.4" {...s} /></svg>);
}

/* ── Hero app preview (faithful POKROV connect screen) ── */
function HeroAppPreview() {
  return (
    <div className={styles.heroStage} aria-hidden="true">
      <div className={styles.stageGlow} />
      <div className={styles.stageArc} />
      <div className={styles.phone}>
        <div className={styles.phoneNotch} />
        <div className={styles.phoneScreen}>
          <div className={styles.appTop}>
            <span className={styles.appBrand}>
              <MarketingBrandLogo className={styles.appLogo} width={22} height={22} />
              POKROV
            </span>
            <span className={styles.appStatus}>
              <span className={styles.appDot} />
              Защищено
            </span>
          </div>
          <div className={styles.connectWrap}>
            <div className={styles.connectRing} />
            <div className={styles.connectInner}>
              <UiIcon name="shield" size={26} />
              <strong>Подключено</strong>
              <small>нажмите, чтобы отключить</small>
            </div>
          </div>
          <div className={styles.locationRow}>
            <span className={styles.flag}>🌍</span>
            <span className={styles.locName}>
              <strong>Авто · лучший маршрут</strong>
              <small>выбирается автоматически</small>
            </span>
            <UiIcon name="arrow" size={18} />
          </div>
          <div className={styles.appChips}>
            <span>Android · Windows</span>
            <span>5 дней бесплатно</span>
          </div>
        </div>
      </div>
      <div className={styles.floatCard} style={{ top: "12%", left: "-4%" }}>
        <UiIcon name="bolt" size={18} />
        <span>1 тап — и работает</span>
      </div>
      <div className={styles.floatCard} style={{ bottom: "14%", right: "-2%" }}>
        <UiIcon name="globe" size={18} />
        <span>YouTube · TikTok снова открыты</span>
      </div>
    </div>
  );
}

/* ── Sections ── */
function Hero({ links }: { links: HomeLinks }) {
  const heroTitle = getCopyText("marketing.hero.title", "Открывайте интернет без границ — в одном приложении");
  const heroSubtitle = getCopyText(
    "marketing.hero.subtitle",
    "POKROV возвращает доступ к YouTube, TikTok и привычным сервисам на Android и Windows. Установите, нажмите «Подключить» — и всё работает. 5 дней бесплатно, карту не просим.",
  );
  const primaryCta = getCopyText("marketing.hero.primary_cta", "Попробовать 5 дней бесплатно");
  return (
    <section className={styles.container}>
      <div className={styles.hero}>
        <div className={styles.heroCopy}>
          <span className={styles.eyebrow}>
            <UiIcon name="shield" size={15} />
            {getCopyText("marketing.hero.kicker", "5 дней бесплатно · без карты")}
          </span>
          <h1 className={styles.heroTitle}>{heroTitle}</h1>
          <p className={styles.heroSubtitle}>{heroSubtitle}</p>
          <div className={styles.heroActions}>
            <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnLg} ${styles.btnMagnet}`}>
              {primaryCta}
              <span className={styles.btnArrow}><UiIcon name="arrow" size={18} /></span>
            </Link>
            <a href="#how-it-works" className={`${styles.btnSecondary} ${styles.btnLg}`}>
              <UiIcon name="play" size={20} />
              Как это работает
            </a>
          </div>
          <div className={styles.heroTrust}>
            {TRUST.map((item) => (
              <div key={item.value} className={styles.heroTrustItem}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
        <HeroAppPreview />
      </div>
    </section>
  );
}

function Features() {
  return (
    <section className={styles.container} id="features">
      <div className={styles.sectionHead}>
        <span className={styles.eyebrowFlat}>возможности</span>
        <h2>Просто работает — без сложных настроек</h2>
        <p>POKROV берёт техническую часть на себя. Вам остаётся открыть приложение и нажать одну кнопку.</p>
      </div>
      <div className={styles.featureGrid}>
        {FEATURES.map((f) => (
          <article key={f.title} className={styles.featureCard}>
            <span className={styles.featureIcon}><UiIcon name={f.icon} size={24} /></span>
            <h3>{f.title}</h3>
            <p>{f.text}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

const SHOWCASE_LOCATIONS = [
  { flag: "🇳🇱", name: "Нидерланды", meta: "лучший маршрут", active: true },
  { flag: "🇩🇪", name: "Германия", meta: "24 мс", active: false },
  { flag: "🇫🇮", name: "Финляндия", meta: "18 мс", active: false },
  { flag: "🇺🇸", name: "США", meta: "48 мс", active: false },
];

function Showcase() {
  return (
    <section className={styles.container} id="showcase">
      <div className={styles.sectionHead}>
        <span className={styles.eyebrowFlat}>как выглядит</span>
        <h2>Приложение, в котором всё понятно</h2>
        <p>Одна большая кнопка, список стран без ручных настроек и понятный аккаунт — на Android и Windows.</p>
      </div>
      <div className={styles.showGrid}>
        <article className={styles.showItem}>
          <div className={styles.showPhone}>
            <div className={styles.showScreen}>
              <div className={styles.showTop}>
                <span className={styles.appBrand}><MarketingBrandLogo className={styles.appLogo} width={20} height={20} />POKROV</span>
                <span className={styles.appStatus}><span className={styles.appDot} />Защищено</span>
              </div>
              <div className={styles.showRingWrap}>
                <div className={styles.showRing} />
                <div className={styles.showRingInner}>
                  <UiIcon name="shield" size={22} />
                  <strong>Подключено</strong>
                </div>
              </div>
              <div className={styles.showPill}><span className={styles.flag}>🌍</span>Авто · лучший маршрут</div>
            </div>
          </div>
          <p className={styles.showCaption}>Одна кнопка — и защита включена</p>
        </article>

        <article className={styles.showItem}>
          <div className={styles.showPhone}>
            <div className={styles.showScreen}>
              <div className={styles.showTop}>
                <strong className={styles.showTitle}>Локации</strong>
                <span className={styles.showMuted}>12 стран</span>
              </div>
              <div className={styles.showList}>
                {SHOWCASE_LOCATIONS.map((loc) => (
                  <div key={loc.name} className={styles.showLoc} data-active={loc.active}>
                    <span className={styles.flag}>{loc.flag}</span>
                    <span className={styles.showLocName}>
                      <strong>{loc.name}</strong>
                      <small>{loc.meta}</small>
                    </span>
                    {loc.active ? <span className={styles.showCheck}><UiIcon name="shield" size={13} /></span> : <span className={styles.showRadio} />}
                  </div>
                ))}
              </div>
            </div>
          </div>
          <p className={styles.showCaption}>Локации без ручных настроек</p>
        </article>

        <article className={styles.showItem}>
          <div className={styles.showPhone}>
            <div className={styles.showScreen}>
              <div className={styles.showTop}>
                <span className={styles.appBrand}><MarketingBrandLogo className={styles.appLogo} width={20} height={20} />POKROV</span>
              </div>
              <div className={styles.showAccess}>
                <span className={styles.appDot} />
                <span>
                  <strong>Доступ активен</strong>
                  <small>до 1 января</small>
                </span>
              </div>
              <div className={styles.showList}>
                <div className={styles.showStat}><span>Трафик</span><strong>Безлимит</strong></div>
                <div className={styles.showStat}><span>Устройства</span><strong>2 из 5</strong></div>
                <div className={styles.showStat}><span>Бонус</span><strong>+10 дней</strong></div>
              </div>
            </div>
          </div>
          <p className={styles.showCaption}>Срок, устройства и бонусы под рукой</p>
        </article>
      </div>
    </section>
  );
}

function HowItWorks() {
  return (
    <section className={styles.container}>
      <div className={styles.section} id="how-it-works">
        <div className={styles.sectionHead}>
          <span className={styles.eyebrowFlat}>как начать</span>
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
  const featuredCode = planCards.find((plan) => plan.code === "start_99")?.code || planCards[0]?.code || "start_99";
  const paidFeatures = ["Больше направлений для подключения", "До 5 личных устройств", "Тот же аккаунт и кабинет", "Поддержка рядом"];
  return (
    <section className={styles.container} id="pricing">
      <div className={styles.section}>
        <div className={styles.sectionHead}>
          <span className={styles.eyebrowFlat}>сколько стоит</span>
          <h2>Сначала попробуйте, потом платите</h2>
          <p>Получите 5 дней в приложении без карты. Если POKROV подходит, стартовое продление на 30 дней стоит 99 ₽.</p>
        </div>
        <div className={styles.pricingLayout}>
          <div className={styles.pricingIntro}>
            <div className={`${styles.badge} ${styles.badgeEmerald}`}>старт</div>
            <h3>5 дней бесплатно, без карты</h3>
            <p>Проверьте POKROV на своих сервисах. Если нужен платный срок — стартовое продление на 30 дней стоит 99 ₽.</p>
            <ul className={styles.planFeatures}>
              {["5 дней без карты", "Доступ активируется в приложении", "Android и Windows", "Telegram не нужен для старта"].map((f) => (
                <li key={f}><CheckIcon />{f}</li>
              ))}
            </ul>
            <Link href={links.installHref} className={`${styles.btnPrimary} ${styles.btnMagnet}`} style={{ marginTop: "auto" }}>
              Попробовать 5 дней бесплатно
              <span className={styles.btnArrow}><UiIcon name="arrow" size={16} /></span>
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
                  <div className={styles.planPrice}>{plan.price} <span>/ {plan.duration.replace(/\d+\s*/, "")}</span></div>
                  <div className={styles.planMeta}><span>{plan.duration}</span><span>{plan.devices}</span></div>
                  <p>{plan.note}</p>
                  <ul className={styles.planFeatures}>
                    {paidFeatures.map((f) => (<li key={f}><CheckIcon />{f}</li>))}
                  </ul>
                  <Link href={buildCheckoutHref(plan.code)} className={`${isFeatured ? styles.btnPrimary : styles.btnSecondary} ${styles.btnMagnet}`} style={{ marginTop: "auto" }}>
                    {isFeatured ? "Выбрать 30 дней" : "Выбрать срок"}
                    {isFeatured ? <span className={styles.btnArrow}><UiIcon name="arrow" size={16} /></span> : null}
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

function FaqSection() {
  return (
    <section className={styles.container} id="faq">
      <div className={styles.section}>
        <div className={styles.sectionHead}>
          <span className={styles.eyebrowFlat}>FAQ</span>
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

function FinalCta({ links }: { links: HomeLinks }) {
  return (
    <section className={styles.container}>
      <div className={styles.finalCta}>
        <div className={styles.finalGlow} aria-hidden="true" />
        <div className={styles.finalCopy}>
          <span className={styles.eyebrowOnDark}>пора начать</span>
          <h2>Получите 5 дней бесплатно. Дальше решите сами</h2>
          <p>Без карты на старте. Установите приложение, проверьте свои сервисы и продлите только если подходит.</p>
        </div>
        <div className={styles.finalActions}>
          <Link href={links.installHref} className={`${styles.btnLight} ${styles.btnLg} ${styles.btnMagnet}`}>
            Попробовать 5 дней бесплатно
            <span className={styles.btnArrowDark}><UiIcon name="arrow" size={18} /></span>
          </Link>
          <Link href={links.checkoutHref} className={`${styles.btnOutline} ${styles.btnLg}`}>Выбрать срок</Link>
        </div>
      </div>
    </section>
  );
}

function Footer({ links }: { links: HomeLinks }) {
  return (
    <footer className={styles.container}>
      <div className={styles.footer}>
        <div className={styles.footerBrand}>
          <Link href="/" className={styles.brand}>
            <MarketingBrandLogo className={styles.brandMark} />
            <span className={styles.brandText}><strong>POKROV</strong><small>Android и Windows · бета</small></span>
          </Link>
          <p>Приложение для доступа к привычным сервисам. Сначала приложение и бесплатный период, дальше — кабинет для продления и поддержки.</p>
        </div>
        <nav className={styles.footerCol} aria-label="Продукт">
          <p className={styles.footerTitle}>Продукт</p>
          <Link href={links.installHref}>Скачать</Link>
          <a href="#features">Возможности</a>
          <a href="#pricing">Тарифы</a>
          <a href={links.cabinetHref}>Кабинет</a>
        </nav>
        <nav className={styles.footerCol} aria-label="Поддержка">
          <p className={styles.footerTitle}>Поддержка</p>
          <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer">Telegram-поддержка</a>
          <a href={config.newsChannelUrl} target="_blank" rel="noreferrer">Канал новостей</a>
          <Link href={MARKETING_CANONICAL_PATHS.offer}>Оферта</Link>
          <Link href={MARKETING_CANONICAL_PATHS.privacy}>Политика</Link>
        </nav>
      </div>
      <div className={styles.footerBottom}>
        <span>© {new Date().getFullYear()} POKROV</span>
        <span>Android и Windows · публичная бета</span>
      </div>
    </footer>
  );
}

export default function MarketingHomePage() {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards.find((plan) => plan.code === "start_99")?.code || planCards[0]?.code || "start_99";
  const links = buildLinks(defaultPlanCode);
  return (
    <>
      <JsonLd data={buildSoftwareApplicationJsonLd({ pagePath: "/" })} />
      <JsonLd data={buildFaqJsonLd(MARKETING_FAQ)} />
      <div className={styles.page}>
        <HomepageTopbar cabinetHref={links.cabinetHref} installHref={links.installHref} />
        <main id="main-content">
          <Hero links={links} />
          <Reveal><Features /></Reveal>
          <Reveal><Showcase /></Reveal>
          <Reveal><HowItWorks /></Reveal>
          <Reveal><Pricing links={links} /></Reveal>
          <Reveal><FaqSection /></Reveal>
          <Reveal><FinalCta links={links} /></Reveal>
          <Reveal><Footer links={links} /></Reveal>
        </main>
      </div>
    </>
  );
}
