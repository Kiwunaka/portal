import Link from "next/link";

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
  {
    value: "5 дней",
    label: "чтобы спокойно проверить сервис в обычной жизни",
  },
  {
    value: "Android + Windows",
    label: "основной путь уже собран без лишних развилок",
  },
  {
    value: "До 5 устройств",
    label: "один доступ для телефона, ноутбука и домашнего ритма",
  },
  {
    value: "Без SLA",
    label: "поддержка отвечает без декоративных обещаний",
  },
];

const HOW_IT_WORKS = [
  {
    step: "1",
    title: "Открываете приложение",
    text: "Старт начинается с нормального экрана, а не с набора технических решений.",
  },
  {
    step: "2",
    title: "Проверяете в своём ритме",
    text: "Пять дней хватает, чтобы понять ощущение дома, в поездках и на рабочем ноутбуке.",
  },
  {
    step: "3",
    title: "Оставляете нужный режим",
    text: "Более полный маршрут можно включить позже, не ломая привычный сценарий.",
  },
  {
    step: "4",
    title: "Продолжаете тем же доступом",
    text: "Если всё подошло после пробного подключения, выбираете срок и продолжаете тот же доступ без нового старта.",
  },
];

const SURFACE_PANELS = [
  {
    eyebrow: "Устройства",
    title: "Один спокойный вход для телефона и компьютера",
    text: "Сайт подводит к установке, приложение становится главным опытом, а кабинет продолжает ту же историю.",
    bullets: ["Android и Windows в одном понятном пути", "Тот же доступ на нескольких устройствах", "Кабинет для срока и списка устройств"],
    tone: "devices" as const,
  },
  {
    eyebrow: "Маршрут",
    title: "По умолчанию всё выглядит мягко и понятно",
    text: "Сначала остаётся режим на каждый день. Более полный вариант подключается только тогда, когда он правда нужен.",
    bullets: ["Спокойный маршрут на старте", "Отдельный переключатель для более полного сценария", "Без технического шума на первом экране"],
    tone: "routing" as const,
  },
  {
    eyebrow: "Поддержка",
    title: "Если что-то не срослось, разговор не начинается заново",
    text: "Поддержка, кабинет и канал остаются рядом как одна связная система, а не как разбросанные ссылки.",
    bullets: ["Ответ в бете: без декоративного SLA", "Видно срок и устройства", "Telegram остается как бонус и запасной путь"],
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

function ProductVisual() {
  return (
    <div className={styles.visual} aria-hidden="true">
      <div className={styles.atlasDeck}>
        <article className={styles.atlasPanelPrimary}>
          <div className={styles.atlasPanelHeader}>
            <div className={styles.brandMini}>
              <img className={styles.brandMarkMini} src="/pokrov-logo.svg" alt="" aria-hidden="true" />
              <div>
                <strong>POKROV</strong>
                <small>приложение сначала</small>
              </div>
            </div>
            <span className={styles.workspaceBadge}>5 дней</span>
          </div>
          <h2>Установите приложение, запустите пробный доступ и сделайте первое подключение.</h2>
          <div className={styles.atlasFlow}>
            <span>Установка</span>
            <span>Пробный доступ</span>
            <span>Первое подключение</span>
          </div>
          <div className={styles.atlasConnection}>
            <div>
              <small>Маршрут</small>
              <strong>{buildRouteLabel()}</strong>
            </div>
            <div>
              <small>Платформы</small>
              <strong>{buildPlatformLabel()}</strong>
            </div>
          </div>
        </article>

        <article className={styles.atlasPanel}>
          <span className={styles.surfaceEyebrow}>после проверки</span>
          <strong>Продление через ключ доступа</strong>
          <p>Оплата нужна только после личной проверки. Ключ погашается в приложении или кабинете.</p>
        </article>

        <article className={styles.atlasPanel}>
          <span className={styles.surfaceEyebrow}>рядом</span>
          <strong>Кабинет и поддержка</strong>
          <p>Срок, устройства, восстановление и помощь остаются в одном понятном маршруте.</p>
        </article>
      </div>
    </div>
  );
}

function SurfaceMock({ tone }: { tone: (typeof SURFACE_PANELS)[number]["tone"] }) {
  if (tone === "devices") {
    return (
      <div className={styles.mockDevices} aria-hidden="true">
        <div className={styles.deviceLaptop} />
        <div className={styles.deviceTablet} />
        <div className={styles.devicePhone} />
      </div>
    );
  }

  if (tone === "routing") {
    return (
      <div className={styles.mockRouting} aria-hidden="true">
        <div className={styles.mockRoutingModes}>
          <article className={styles.modeCardActive}>
            <strong>Весь трафик</strong>
            <span>спокойный режим на каждый день</span>
          </article>
          <article className={styles.modeCard}>
            <strong>Только нужные приложения</strong>
            <span>включается позже, когда это правда нужно</span>
          </article>
        </div>
        <div className={styles.mockRoutingMap} />
      </div>
    );
  }

  return (
    <div className={styles.mockSupport} aria-hidden="true">
      <div className={styles.mockSupportRail}>
        <span className={styles.mockSupportRailActive}>Поддержка</span>
        <span>История</span>
        <span>База знаний</span>
      </div>
      <div className={styles.mockSupportBody}>
        <div className={styles.searchBar} />
        <div className={styles.supportQuickRow}>
          <span />
          <span />
          <span />
        </div>
        <div className={styles.supportList}>
          <div />
          <div />
          <div />
        </div>
      </div>
    </div>
  );
}

export default function MarketingHomePage() {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards[1]?.code || planCards[0]?.code || "1_month";
  const featuredCode = planCards[1]?.code || defaultPlanCode;
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
              <small>спокойный цифровой маршрут на каждый день</small>
            </span>
          </Link>

          <nav className={styles.nav} aria-label="Навигация по главной">
            <a href="#proof">Почему это спокойно</a>
            <a href="#how-it-works">Как это работает</a>
            <a href="#pricing">Сроки и цены</a>
            <a href="#final-cta">Следующий шаг</a>
          </nav>

          <div className={styles.topbarActions}>
            <a href={links.cabinetHref} className={styles.ghostButton}>
              Кабинет
            </a>
            <Link href={links.installHref} className={styles.primaryButton}>
              Установить приложение
            </Link>
          </div>
        </header>

        <main id="main-content" className={styles.main}>
          <section className={styles.hero}>
            <div className={styles.heroCopy}>
              <span className={styles.eyebrow}>спокойный старт без нового квеста</span>
              <h1 className={styles.heroTitle}>Сначала приложение и пробное подключение. Потом спокойное продление.</h1>
              <p className={styles.heroText}>
                POKROV нужен не для того, чтобы заставлять разбираться в настройках. Он нужен, чтобы открыть
                приложение, пожить с ним несколько дней на своих устройствах и только потом решить, хочется ли
                продолжать доступ дальше.
              </p>

              <div className={styles.heroActions}>
                <Link href={links.installHref} className={styles.primaryButton}>
                  Установить приложение
                </Link>
                <Link href={links.checkoutHref} className={styles.secondaryButton}>
                  Выбрать срок
                </Link>
              </div>

              <ul className={styles.heroNotes}>
                <li>Бета-путь уже собран вокруг {buildPlatformLabel()} без лишних развилок.</li>
                <li>Более полный маршрут можно включить позже, когда он действительно нужен.</li>
                <li>Кабинет и поддержка продолжают ту же историю, а не отправляют начинать заново.</li>
              </ul>
            </div>

            <ProductVisual />
          </section>

          <section id="proof" className={styles.proofStrip} aria-label="Ключевые факты">
            {HERO_FACTS.map((fact) => (
              <article key={fact.value} className={styles.proofItem}>
                <strong>{fact.value}</strong>
                <span>{fact.label}</span>
              </article>
            ))}
          </section>

          <section id="how-it-works" className={styles.section}>
            <div className={styles.sectionHead}>
              <span className={styles.eyebrow}>как это работает</span>
              <h2>Короткий путь без рекламного шума и без технической тяжести.</h2>
              <p>Всё построено вокруг нескольких ясных шагов: открыть, проверить, оставить нужный режим и продолжить тем же доступом.</p>
            </div>

            <div className={styles.steps}>
              {HOW_IT_WORKS.map((item, index) => (
                <article key={item.step} className={styles.stepCard}>
                  <div className={styles.stepTop}>
                    <span className={styles.stepIndex}>{item.step}</span>
                    {index < HOW_IT_WORKS.length - 1 ? <span className={styles.stepLine} aria-hidden="true" /> : null}
                  </div>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <span className={styles.eyebrow}>устройства, маршрут и поддержка</span>
              <h2>Все важные поверхности говорят об одном и мягко ведут к следующему шагу.</h2>
              <p>Сайт помогает начать, приложение становится главным опытом, кабинет продолжает историю, а поддержка не ломает ритм.</p>
            </div>

            <div className={styles.surfaceGrid}>
              {SURFACE_PANELS.map((panel) => (
                <article key={panel.title} className={styles.surfaceCard}>
                  <div className={styles.surfaceCardTop}>
                    <div>
                      <span className={styles.surfaceEyebrow}>{panel.eyebrow}</span>
                      <h3>{panel.title}</h3>
                    </div>
                    <SurfaceMock tone={panel.tone} />
                  </div>
                  <p>{panel.text}</p>
                  <ul className={styles.surfaceBullets}>
                    {panel.bullets.map((bullet) => (
                      <li key={bullet}>{bullet}</li>
                    ))}
                  </ul>
                </article>
              ))}
            </div>

            <div className={styles.inlineActions}>
              <Link href={links.installHref} className={styles.inlineLink}>
                Открыть установку
              </Link>
              <a href={links.supportHref} className={styles.inlineLink}>
                Поддержка
              </a>
              <a href={links.channelHref} className={styles.inlineLink}>
                Канал POKROV
              </a>
            </div>
          </section>

          <section id="pricing" className={styles.section}>
            <div className={styles.sectionHead}>
              <span className={styles.eyebrow}>сроки и цены</span>
              <h2>Сначала проба, потом короткий выбор срока без нового старта.</h2>
              <p>Оплата остаётся простой: выбрать срок, перейти к checkout и продолжить тем же доступом.</p>
            </div>

            <div className={styles.pricingLayout}>
              <article className={styles.pricingIntro}>
                <span className={styles.pricingBadge}>старт</span>
                <h3>Первые 5 дней бесплатно</h3>
                <p>
                  Этого хватает, чтобы понять, подходит ли сервис в обычной жизни. Если да, дальше нужен только спокойный
                  checkout без нового круга действий.
                </p>
                <Link href={links.checkoutHref} className={styles.primaryButton}>
                  Выбрать срок
                </Link>
              </article>

              <div className={styles.planGrid}>
                {planCards.map((plan) => {
                  const isFeatured = plan.code === featuredCode;

                  return (
                    <article key={plan.code} className={`${styles.planCard} ${isFeatured ? styles.planCardFeatured : ""}`.trim()}>
                      <span className={styles.planBadge}>{plan.badge || (isFeatured ? "выгодно" : "продление")}</span>
                      <h3>{plan.label}</h3>
                      <div className={styles.planPrice}>{plan.price}</div>
                      <div className={styles.planMeta}>
                        <span>{plan.duration}</span>
                        <span>{plan.devices}</span>
                      </div>
                      <p>{plan.note}</p>
                      <Link
                        href={buildCheckoutHref(plan.code)}
                        className={isFeatured ? styles.primaryButton : styles.secondaryButton}
                      >
                        Выбрать срок
                      </Link>
                    </article>
                  );
                })}
              </div>
            </div>
          </section>

          <section id="final-cta" className={styles.finalCta}>
            <div className={styles.finalCopy}>
              <span className={styles.finalEyebrow}>следующий шаг</span>
              <h2>Если уже хочется продолжить, дальше нужен только спокойный checkout.</h2>
              <p>
                Приложение остаётся главным опытом. Сайт помогает выбрать срок и перейти к оплате, кабинет остаётся для
                устройств и срока, а поддержка помогает, если что-то пошло не так.
              </p>
            </div>

            <div className={styles.finalActions}>
              <Link href={links.checkoutHref} className={styles.lightButton}>
                Выбрать срок
              </Link>
              <Link href={links.installHref} className={styles.outlineButton}>
                Установить приложение
              </Link>
              <a href={links.cabinetHref} className={styles.outlineButton}>
                Кабинет
              </a>
              <a href={links.supportHref} className={styles.outlineButton}>
                Поддержка
              </a>
            </div>
          </section>
        </main>
      </div>
    </>
  );
}
