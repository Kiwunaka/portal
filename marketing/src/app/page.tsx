import { getCopyText, getPortalPublicConfig } from "../lib/portal";
import Link from "next/link";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

const FEATURES = [
  {
    title: "Запуск через Telegram",
    desc: "Вход, оплата и переход к кабинету собраны в один понятный путь без лишних экранов.",
  },
  {
    title: "Прозрачные планы",
    desc: "Срок, лимит устройств и формат поддержки видны сразу, без скрытых условий и технарщины.",
  },
  {
    title: "Спокойный кабинет",
    desc: "Срок, точки подключения, приложения и поддержка собраны в одном аккуратном кабинете.",
  },
];

const PLANS = [
  { code: "start_99", name: "Приветственный", price: "99 ₽", period: "30 дней", note: "1 устройство • можно использовать один раз" },
  { code: "1_month", name: "1 месяц", price: "249 ₽", period: "30 дней", note: "До 5 устройств • базовый понятный срок", highlight: true },
  { code: "3_months", name: "3 месяца", price: "699 ₽", period: "91 день", note: "До 5 устройств • удобнее, чем продлевать каждый месяц" },
  { code: "6_months", name: "6 месяцев", price: "1199 ₽", period: "182 дня", note: "До 5 устройств • хороший баланс срока и цены" },
  { code: "9_months", name: "9 месяцев", price: "1399 ₽", period: "273 дня", note: "До 5 устройств • редкие продления и спокойный запас" },
  { code: "12_months", name: "12 месяцев", price: "1644 ₽", period: "365 дней", note: "До 5 устройств • скидка 45% при длинном сроке" },
];

export default function HomePage() {
  return (
    <>
      <div className="lp-bg-blobs" aria-hidden="true" />

      <header className="lp-nav">
        <a href="#main-content" className="lp-brand">
          <span>◌</span>
          PORTAL
        </a>
        <nav className="lp-menu">
          <a href="#features">Возможности</a>
          <a href="#pricing">Планы</a>
          <a href="#support">Поддержка</a>
          <a href="#faq">FAQ</a>
          <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
            Уже подключены?
          </a>
          <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
            {getCopyText("marketing.hero.primary_cta", "Подключиться в Telegram")}
          </a>
        </nav>
      </header>

      <main id="main-content" className="lp-main">
        <section className="lp-hero">
          <div className="lp-kicker">{getCopyText("marketing.hero.kicker", "PORTAL • запуск через Telegram • оплата в рублях")}</div>
          <h1>{getCopyText("marketing.hero.title", "Подключайтесь быстро и без лишней настройки")}</h1>
          <p>{getCopyText("marketing.hero.subtitle", "Откройте Telegram, выберите план и получите готовый доступ за пару минут — с понятным кабинетом и живой поддержкой.")}</p>
          <div className="lp-hero-actions">
            <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
              {getCopyText("marketing.hero.primary_cta", "Подключиться в Telegram")}
            </a>
            <a href="#pricing" className="lp-btn lp-btn--ghost">
              {getCopyText("marketing.hero.secondary_cta", "Сравнить планы")}
            </a>
          </div>
          <div className="lp-proof">
            <div>
              <strong>1-2 мин</strong>
              <span>средний путь до кабинета</span>
            </div>
            <div>
              <strong>6 тарифов</strong>
              <span>от приветственного до годового</span>
            </div>
            <div>
              <strong>Telegram</strong>
              <span>поддержка и продление в одном месте</span>
            </div>
          </div>
        </section>

        <section id="features" className="lp-section">
          <div className="lp-section-head">
            <span>[Почему PORTAL]</span>
            <h2>Меньше визуального шума, больше понятных действий</h2>
          </div>
          <div className="lp-feature-grid">
            {FEATURES.map((item, idx) => (
              <article className="lp-card" key={item.title}>
                <div className="lp-card-index">0{idx + 1}</div>
                <h3>{item.title}</h3>
                <p>{item.desc}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="pricing" className="lp-section">
          <div className="lp-section-head">
            <span>[Планы]</span>
            <h2>Только актуальные суммы и реальные сроки</h2>
            <p>Если вы только начинаете, удобнее всего продолжить через Telegram. Персональная ссылка оплаты появляется уже внутри бота или кабинета.</p>
          </div>

          <div className="lp-plan-grid">
            {PLANS.map((plan) => (
              <article key={plan.code} className={`lp-card lp-plan ${plan.highlight ? "lp-plan--highlight" : ""}`}>
                <h3>{plan.name}</h3>
                <div className="lp-price">{plan.price}</div>
                <p className="lp-period">{plan.period}</p>
                <p>{plan.note}</p>
                <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary" style={{ marginTop: 20 }}>
                  Выбрать в Telegram
                </a>
              </article>
            ))}
          </div>
        </section>

        <section id="support" className="lp-section">
          <div className="lp-section-head">
            <span>[Поддержка]</span>
            <h2>{getCopyText("marketing.support.title", "Если нужен человек, мы рядом")}</h2>
            <p>{getCopyText("marketing.support.subtitle", "Поддержка в Telegram, понятные ответы и быстрый переход к обращению из любого экрана.")}</p>
          </div>
          <div className="lp-feature-grid">
            <article className="lp-card">
              <h3>Telegram</h3>
              <p>Самый быстрый путь, если нужно продолжить оплату, проверить доступ или быстро задать вопрос.</p>
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                Написать в Telegram
              </a>
            </article>
            <article className="lp-card">
              <h3>Кабинет</h3>
              <p>Внутри уже есть история обращений, раздел загрузок и честная сводка по текущему состоянию доступа.</p>
              <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--ghost">
                Открыть кабинет
              </a>
            </article>
          </div>
        </section>

        <section id="faq" className="lp-section">
          <div className="lp-section-head">
            <span>[FAQ]</span>
            <h2>Коротко о главном</h2>
          </div>
          <div className="lp-feature-grid">
            <article className="lp-card">
              <h3>Как начать?</h3>
              <p>Откройте Telegram, выберите план и переходите в кабинет. Если есть персональная ссылка, оплата продолжится сразу.</p>
            </article>
            <article className="lp-card">
              <h3>Можно ли оплатить в рублях?</h3>
              <p>Да. Основной путь настроен на оплату в рублях, а Telegram остаётся быстрым способом продолжить дальше.</p>
            </article>
            <article className="lp-card">
              <h3>Что видно в кабинете?</h3>
              <p>Статус доступа, срок, лимиты, точки подключения, ссылки на приложения и обращения в поддержку.</p>
            </article>
          </div>
        </section>

        <footer className="lp-section" style={{ paddingTop: 0 }}>
          <div className="lp-card" style={{ display: "flex", justifyContent: "space-between", gap: 24, flexWrap: "wrap" }}>
            <div>
              <h3 style={{ marginBottom: 8 }}>PORTAL</h3>
              <p>Спокойный цифровой доступ без лишних шагов и перегруженных экранов.</p>
            </div>
            <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
              <a href={config.botUrl} target="_blank" rel="noreferrer" className="lp-btn lp-btn--primary">
                Подключиться
              </a>
              <Link href="/offer/" className="lp-btn lp-btn--ghost">Оферта</Link>
              <Link href="/privacy/" className="lp-btn lp-btn--ghost">Политика</Link>
            </div>
          </div>
        </footer>
      </main>
    </>
  );
}
