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
  { href: "#path", label: "Путь" },
  { href: "#surface", label: "Приложение" },
  { href: "#pricing", label: "Тарифы" },
  { href: "#support", label: "Поддержка" },
];

const STATUS_RAIL = [
  { value: "5 дней", label: "проверка в приложении" },
  { value: "Android + Windows", label: "публичный запуск" },
  { value: "+10 дней", label: "за связь с Telegram" },
  { value: "до 5 устройств", label: "после продления" },
];

const PATH_STEPS = [
  {
    index: "01",
    title: "5 дней",
    text: "Получите первый ключ для нового устройства.",
  },
  {
    index: "02",
    title: "Приложение",
    text: "Откройте POKROV на Android или Windows.",
  },
  {
    index: "03",
    title: "Активация",
    text: "Включите доступ без сетевых деталей на первом экране.",
  },
  {
    index: "04",
    title: "Кабинет",
    text: "Продлевайте срок и обращайтесь в поддержку там же.",
  },
];

const SURFACE_ROWS = [
  {
    icon: "5",
    title: "Старт без лишней регистрации",
    text: "Первый шаг идет через приложение. Telegram остается рядом для бонуса, восстановления и помощи.",
  },
  {
    icon: "A",
    title: "Один понятный статус доступа",
    text: "Пользователь видит срок, устройство и следующий шаг, а технические детали не мешают ежедневному подключению.",
  },
  {
    icon: "K",
    title: "Ключ доступа вместо ручной возни",
    text: "После оплаты ключ активируется в приложении или кабинете и продолжает тот же аккаунт.",
  },
];

const PLATFORM_ROWS = [
  {
    title: "Android",
    status: "основной запуск",
    text: "Мобильный старт, проверка 5 дней и обычное ежедневное подключение.",
  },
  {
    title: "Windows",
    status: "основной запуск",
    text: "Тот же доступ на рабочем или домашнем компьютере.",
  },
  {
    title: "Apple",
    status: "готовится",
    text: "Показываем честный статус без дат и обещаний раньше готовности.",
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
        "Продление добавляется к текущему доступу без новой настройки и лишних шагов.",
      badge: plan.badge || null,
    }));
}

export default function MarketingHomePage() {
  const planCards = buildPlanCards();
  const defaultPlanCode = planCards[1]?.code || planCards[0]?.code || "1_month";
  const featuredCode = planCards[1]?.code || defaultPlanCode;
  const checkoutHref = buildCheckoutHref(defaultPlanCode);
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
            <img src="/redesign/brand/pokrov-mark.svg" alt="" className={styles.logoMark} aria-hidden="true" />
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
              Попробовать 5 дней
            </Link>
          </div>
        </header>

        <main id="main-content" className={styles.main}>
          <section className={styles.hero}>
            <div className={styles.heroCopy}>
              <div className={styles.heroBrand} aria-hidden="true">
                <img src="/redesign/brand/pokrov-mark.svg" alt="" />
                <span>POKROV</span>
              </div>
              <span className={styles.kicker}>спокойный доступ для Android и Windows</span>
              <h1>5 дней в приложении, ключ доступа и кабинет рядом.</h1>
              <p>
                POKROV ведет по одному понятному пути: сначала проверка на устройстве, затем активация ключа,
                продление в кабинете и поддержка без лишней сетевой терминологии.
              </p>
              <div className={styles.heroActions}>
                <Link href={installHref} className={styles.primaryButton}>
                  Попробовать 5 дней
                </Link>
                <Link href={checkoutHref} className={styles.secondaryButton}>
                  Купить ключ доступа
                </Link>
                <a href={cabinetHref} className={styles.textButton}>
                  Открыть кабинет
                </a>
              </div>
            </div>

            <div className={styles.heroScene} aria-label="Визуальный обзор POKROV">
              <div className={styles.sceneStatus} aria-hidden="true">
                <span>Статус</span>
                <strong>Готово к проверке</strong>
              </div>
              <img
                src="/redesign/pokrov-hero-product.png"
                alt="Экраны POKROV с приложением, кабинетом и подключением"
                className={styles.heroImage}
              />
              <div className={styles.sceneRail} aria-hidden="true">
                <span>5 дней</span>
                <span>Приложение</span>
                <span>Ключ</span>
                <span>Поддержка</span>
              </div>
            </div>
          </section>

          <section className={styles.statusRail} aria-label="Ключевые факты">
            {STATUS_RAIL.map((item) => (
              <article key={item.value} className={styles.statusItem}>
                <strong>{item.value}</strong>
                <span>{item.label}</span>
              </article>
            ))}
          </section>

          <section id="path" className={styles.pathBand}>
            <div className={styles.sectionHead}>
              <span>путь</span>
              <h2>Один понятный путь: 5 дней → приложение → активировать ключ → кабинет и поддержка.</h2>
            </div>

            <div className={styles.pathLine}>
              {PATH_STEPS.map((step) => (
                <article key={step.index} className={styles.pathStep}>
                  <span>{step.index}</span>
                  <h3>{step.title}</h3>
                  <p>{step.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="surface" className={styles.surfaceSection}>
            <div className={styles.surfaceIntro}>
              <span className={styles.kicker}>повседневный контур</span>
              <h2>Главная говорит как продукт, а не как витрина с карточками.</h2>
              <p>
                Акцент остается на уверенном первом запуске, понятном сроке доступа и живой поддержке. Технические
                режимы остаются там, где они действительно нужны.
              </p>
            </div>

            <div className={styles.surfaceRows}>
              {SURFACE_ROWS.map((row) => (
                <article key={row.title} className={styles.surfaceRow}>
                  <span className={styles.rowIcon}>{row.icon}</span>
                  <div>
                    <h3>{row.title}</h3>
                    <p>{row.text}</p>
                  </div>
                </article>
              ))}
            </div>
          </section>

          <section className={styles.platformBand}>
            <div className={styles.platformCopy}>
              <span className={styles.kicker}>платформы</span>
              <h2>Сейчас публично: Android и Windows. Apple аккуратно готовится.</h2>
            </div>
            <div className={styles.platformRows}>
              {PLATFORM_ROWS.map((platform) => (
                <article key={platform.title} className={styles.platformRow}>
                  <strong>{platform.title}</strong>
                  <span>{platform.status}</span>
                  <p>{platform.text}</p>
                </article>
              ))}
            </div>
          </section>

          <section id="pricing" className={styles.pricingSection}>
            <div className={styles.pricingIntro}>
              <span className={styles.kicker}>тарифы</span>
              <h2>После проверки выберите срок и активируйте ключ в том же аккаунте.</h2>
              <p>
                Тарифы не создают новый путь. Они продолжают тот же порядок: приложение, ключ доступа, кабинет и
                поддержка.
              </p>
              <Link href={checkoutHref} className={styles.primaryButton}>
                Перейти к тарифам
              </Link>
            </div>

            <div className={styles.planRows}>
              {planCards.map((plan) => {
                const featured = plan.code === featuredCode;

                return (
                  <article key={plan.code} className={`${styles.planRow} ${featured ? styles.planRowFeatured : ""}`.trim()}>
                    <div>
                      <span>{plan.badge || (featured ? "частый выбор" : "продление")}</span>
                      <h3>{plan.label}</h3>
                      <p>{plan.note}</p>
                    </div>
                    <div className={styles.planSide}>
                      <strong>{plan.price}</strong>
                      <small>
                        {plan.duration} · {plan.devices}
                      </small>
                      <Link href={buildCheckoutHref(plan.code)} className={featured ? styles.primaryButton : styles.secondaryButton}>
                        Выбрать
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>

          <section id="support" className={styles.supportBand}>
            <div>
              <span className={styles.kicker}>поддержка и бонус</span>
              <h2>Telegram рядом, но не стоит на входе.</h2>
              <p>
                Канал помогает получать новости и бонус +10 дней, а поддержка остается доступной через кабинет,
                приложение и Telegram, если что-то пошло не по плану.
              </p>
            </div>
            <div className={styles.supportActions}>
              <a href={channelHref} className={styles.lightButton}>
                Открыть канал
              </a>
              <a href={supportHref} className={styles.outlineButton}>
                Написать в поддержку
              </a>
            </div>
          </section>
        </main>
      </div>
    </>
  );
}
