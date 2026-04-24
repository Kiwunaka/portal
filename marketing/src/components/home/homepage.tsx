import Link from "next/link";

import JsonLd from "../json-ld";
import styles from "./homepage.module.css";
import { buildSoftwareApplicationJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { getPokrovPublicConfig, getTariffPlans } from "../../lib/pokrov";

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

const NAV_ITEMS = [
  { href: "#features", label: "Возможности" },
  { href: "#steps", label: "Как начать" },
  { href: "#platforms", label: "Платформы" },
  { href: "#pricing", label: "Тарифы" },
  { href: "#support", label: "Поддержка" },
];

const PROOF_ITEMS = [
  { value: "5 дней", label: "ключ доступа выдается в приложении" },
  { value: "Android и Windows", label: "основные платформы текущего запуска" },
  { value: "+10 дней", label: "после связи с Telegram-каналом" },
  { value: "До 5 устройств", label: "после продления на платном сроке" },
];

const PRODUCT_STATUS_ITEMS = [
  { label: "Ключ", value: "5 дней для проверки" },
  { label: "После ключа", value: "скачать и активировать" },
  { label: "Помощь", value: "кабинет и Telegram" },
];

const FEATURES = [
  {
    eyebrow: "Приложение",
    title: "Ключ появляется там, где он нужен",
    text: "Открываете приложение, получаете 5 дней доступа и видите понятный статус подключения.",
  },
  {
    eyebrow: "Кабинет",
    title: "Срок и устройства под рукой",
    text: "Кабинет помогает проверить доступ, скачать сборки и продлить срок без новой настройки.",
  },
  {
    eyebrow: "Правила",
    title: "Настройки остаются понятными",
    text: "Повседневный режим включается быстро, а дополнительные параметры не мешают первому запуску.",
  },
];

const USE_CASES = [
  {
    title: "Для телефона",
    text: "Быстро включить доступ перед поездкой, сменой сети или обычным рабочим днем.",
  },
  {
    title: "Для ноутбука",
    text: "Оставить стабильное подключение на Windows и управлять сроком из кабинета.",
  },
  {
    title: "Для семьи",
    text: "Держать несколько устройств на одном доступе и не объяснять каждый шаг заново.",
  },
];

const STEPS = [
  {
    title: "Получите ключ на 5 дней",
    text: "Первый ключ выдается в приложении для нового устройства. Регистрация в Telegram для этого не обязательна.",
  },
  {
    title: "Скачайте приложение",
    text: "Установите POKROV на Android или Windows и активируйте ключ без сложных режимов на первом экране.",
  },
  {
    title: "Продлите, если подходит",
    text: "После проверки выберите срок и управляйте доступом в кабинете. Лишних действий с подключением не потребуется.",
  },
];

const PLATFORMS = [
  {
    name: "Android",
    status: "Основной запуск",
    text: "Главная мобильная платформа для старта, проверки и обычного ежедневного подключения.",
    action: "Установить приложение",
    primary: true,
  },
  {
    name: "Windows",
    status: "Основной запуск",
    text: "Рабочий и домашний компьютер остаются в том же понятном контуре POKROV.",
    action: "Скачать для Windows",
    primary: true,
  },
  {
    name: "Apple",
    status: "Готовится",
    text: "Показываем честный статус без дат и без обещаний раньше готовности.",
    action: "Готовится",
    primary: false,
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
        "Продление добавляется к текущему доступу, без ручной пересборки и лишних шагов.",
      badge: plan.badge || null,
    }));
}

export default function MarketingHomePage() {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards[1]?.code || planCards[0]?.code || "1_month";
  const featuredCode = planCards[1]?.code || defaultPlanCode;
  const installHref = MARKETING_CANONICAL_PATHS.install;
  const supportHref = config.contactFormUrl || config.supportTelegramUrl || config.helpbotUrl;
  const channelHref = config.newsChannelUrl;
  const cabinetHref = config.webappUrl;

  return (
    <>
      <JsonLd data={buildSoftwareApplicationJsonLd({ pagePath: "/" })} />

      <div className={styles.page}>
        <header className={styles.header}>
          <Link href="/" className={styles.brand} aria-label="POKROV">
            <img src="/pokrov-logo.svg" alt="" className={styles.logoMark} aria-hidden="true" />
            <span className={styles.logoText}>POKROV</span>
          </Link>

          <nav className={styles.nav} aria-label="Навигация по главной странице">
            {NAV_ITEMS.map((item) => (
              <a key={item.href} href={item.href}>
                {item.label}
              </a>
            ))}
          </nav>

          <div className={styles.headerActions}>
            <a href={cabinetHref} className={styles.linkButton}>
              Кабинет
            </a>
            <Link href={installHref} className={styles.primaryButton}>
              Получить ключ на 5 дней
            </Link>
          </div>
        </header>

        <main id="main-content" className={styles.main}>
          <section className={styles.hero}>
            <div className={styles.heroCopy}>
              <span className={styles.kicker}>ключ доступа, приложение и поддержка рядом</span>
              <h1>POKROV: сначала 5-дневный ключ, потом приложение и активация.</h1>
              <p>
                Получите ключ для проверки, скачайте POKROV на Android или Windows и включите доступ в приложении.
                Если всё подходит, продлите срок в кабинете или на странице тарифов.
              </p>
              <div className={styles.heroActions}>
                <Link href={installHref} className={styles.primaryButton}>
                  Получить ключ на 5 дней
                </Link>
                <Link href={installHref} className={styles.secondaryButton}>
                  Скачать приложение
                </Link>
              </div>
            </div>

            <div className={styles.heroMedia} aria-label="Визуальный обзор POKROV">
              <img
                src="/redesign/pokrov-hero-product.png"
                alt="Экраны POKROV с приложением, кабинетом и подключением"
                className={styles.heroImage}
              />
              <div className={styles.productStatusRail} aria-hidden="true">
                {PRODUCT_STATUS_ITEMS.map((item) => (
                  <div key={item.label} className={styles.productStatusItem}>
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className={styles.proofStrip} aria-label="Ключевые факты">
            {PROOF_ITEMS.map((item) => (
              <article key={item.value} className={styles.proofItem}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </article>
            ))}
          </section>

          <section id="features" className={styles.section}>
            <div className={styles.sectionHead}>
              <span>возможности</span>
              <h2>Не нужно разбираться в сетевых деталях, чтобы начать пользоваться.</h2>
              <p>
                В публичной части POKROV говорит простым языком: где получить ключ, как скачать, где продлить и куда
                написать, если нужна помощь.
              </p>
            </div>

            <div className={styles.featureGrid}>
              {FEATURES.map((feature) => (
                <article key={feature.title} className={styles.featureCard}>
                  <span>{feature.eyebrow}</span>
                  <h3>{feature.title}</h3>
                  <p>{feature.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.section}>
            <div className={styles.sectionHead}>
              <span>сценарии</span>
              <h2>Подходит для обычных ситуаций, где важны ясность и предсказуемость.</h2>
            </div>

            <div className={styles.useCaseGrid}>
              {USE_CASES.map((item) => (
                <article key={item.title} className={styles.useCaseCard}>
                  <h3>{item.title}</h3>
                  <p>{item.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="steps" className={styles.section}>
            <div className={styles.sectionHead}>
              <span>как начать</span>
              <h2>Три шага: получить ключ, скачать приложение, активировать.</h2>
            </div>

            <div className={styles.stepsGrid}>
              {STEPS.map((step, index) => (
                <article key={step.title} className={styles.stepCard}>
                  <span className={styles.stepIndex}>{index + 1}</span>
                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="platforms" className={styles.section}>
            <div className={styles.sectionHead}>
              <span>платформы</span>
              <h2>Сначала Android и Windows. Apple — честно в подготовке.</h2>
            </div>

            <div className={styles.platformGrid}>
              {PLATFORMS.map((platform) => (
                <article key={platform.name} className={styles.platformCard}>
                  <div>
                    <span className={platform.primary ? styles.statusPrimary : styles.statusMuted}>{platform.status}</span>
                    <h3>{platform.name}</h3>
                    <p>{platform.text}</p>
                  </div>
                  {platform.primary ? (
                    <Link href={installHref} className={styles.secondaryButton}>
                      {platform.action}
                    </Link>
                  ) : (
                    <span className={styles.disabledAction}>{platform.action}</span>
                  )}
                </article>
              ))}
            </div>
          </section>

          <section id="support" className={styles.supportBand}>
            <div>
              <span className={styles.kicker}>поддержка и бонус</span>
              <h2>Telegram остаётся рядом: новости, помощь и +10 дней за подписку.</h2>
              <p>
                Канал помогает не пропускать важные обновления, а поддержка отвечает, если установка, кабинет или
                продление пошли не по плану.
              </p>
            </div>
            <div className={styles.supportActions}>
              <a href={channelHref} className={styles.lightButton}>
                Открыть канал
              </a>
              <a href={supportHref} className={styles.secondaryButton}>
                Написать в поддержку
              </a>
            </div>
          </section>

          <section id="pricing" className={styles.section}>
            <div className={styles.sectionHead}>
              <span>тарифы</span>
              <h2>После пробного периода можно выбрать срок без нового старта.</h2>
              <p>Тарифы нужны только после проверки. Доступ продолжает тот же порядок: приложение, кабинет, поддержка.</p>
            </div>

            <div className={styles.pricingGrid}>
              {planCards.map((plan) => {
                const featured = plan.code === featuredCode;

                return (
                  <article key={plan.code} className={`${styles.planCard} ${featured ? styles.planCardFeatured : ""}`.trim()}>
                    <span className={styles.planBadge}>{plan.badge || (featured ? "частый выбор" : "продление")}</span>
                    <h3>{plan.label}</h3>
                    <strong>{plan.price}</strong>
                    <div className={styles.planMeta}>
                      <span>{plan.duration}</span>
                      <span>{plan.devices}</span>
                    </div>
                    <p>{plan.note}</p>
                    <Link href={buildCheckoutHref(plan.code)} className={featured ? styles.primaryButton : styles.secondaryButton}>
                      Выбрать срок
                    </Link>
                  </article>
                );
              })}
            </div>
          </section>

          <section id="final-cta" className={styles.finalCta}>
            <div>
              <span className={styles.kicker}>готовы начать?</span>
              <h2>Получите ключ на 5 дней и активируйте его в приложении.</h2>
              <p>
                Первый шаг не ведет к покупке. Сначала проверьте POKROV на своем устройстве, а продление оставьте на потом.
              </p>
            </div>
            <div className={styles.finalActions}>
              <Link href={installHref} className={styles.lightButton}>
                Получить ключ на 5 дней
              </Link>
              <Link href={installHref} className={styles.outlineButton}>
                Скачать приложение
              </Link>
            </div>
          </section>
        </main>
      </div>
    </>
  );
}
