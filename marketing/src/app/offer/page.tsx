import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export const metadata = buildMarketingMetadata(
  "Публичная оферта | POKROV",
  "Базовые условия цифровой подписки POKROV, порядок продления и контакты поддержки.",
  {
    path: "/offer/",
    keywords: ["оферта pokrov", "условия подписки", "pokrov offer"],
  },
);

export default function OfferPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Публичная оферта", path: "/offer/" },
        ])}
      />
      <div className="lp-route-shell lp-route-shell--legal">
        <header className="lp-nav">
          <div className="lp-nav-shell">
            <Link href="/" className="lp-brand">
              <img src="/pokrov-logo.svg" alt="" aria-hidden="true" className="lp-brand-logo" />
              <span>{CANONICAL_PLATFORM_BRAND}</span>
            </Link>
            <nav className="lp-menu" aria-label="Навигация по юридическим страницам">
              <div className="lp-nav-links">
                <Link href="/">Главная</Link>
                <Link href={MARKETING_CANONICAL_PATHS.install}>Установка</Link>
                <Link href={MARKETING_CANONICAL_PATHS.privacy}>Политика</Link>
              </div>
              <div className="lp-nav-actions">
                <a href={config.webappUrl} target="_blank" rel="noreferrer" className="lp-chip">
                  Кабинет
                </a>
                <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer" className="lp-chip lp-chip--primary">
                  Поддержка
                </a>
              </div>
            </nav>
          </div>
        </header>

        <main id="main-content" className="legal-page lp-legal-shell">
          <section className="lp-legal-banner">
            <span className="lp-legal-banner__eyebrow">Юридическая информация</span>
            <h1>Публичная оферта</h1>
            <p>
              Здесь собраны базовые условия доступа к цифровым услугам POKROV, порядок продления и рабочий способ
              связаться с командой, если нужен разбор спорной ситуации.
            </p>
          </section>

        <section className="lp-legal-grid">
          <article className="lp-legal-panel">
            <h2>Основные условия</h2>
            <ul className="lp-legal-list">
              <li>Текущая волна — бета-контур с честными ограничениями, а не обещание широкого стабильного запуска.</li>
              <li>Сервис предоставляется как цифровой доступ на выбранный срок; автоматическое списание не включается без отдельного явного согласия пользователя.</li>
              <li>Бесплатный тест длится 5 дней, а отдельные режимы доступа могут иметь ограничения по устройствам, функциям и доступным сборкам.</li>
              <li>Продление должно заканчиваться ключом доступа. Ключ нужно погасить в приложении или кабинете, чтобы продолжить тот же аккаунт без ручной настройки.</li>
              <li>Возвраты, отмены, спорные статусы провайдера и ручная сверка рассматриваются через поддержку; итог зависит от фактического статуса платежа и уже выданного доступа.</li>
            </ul>
          </article>

          <article className="lp-legal-panel">
            <h2>Бета-ограничения</h2>
            <ul className="lp-legal-list">
              <li>Android-сборка может быть доступна как бета-установка до завершения публикации и финальной проверки.</li>
              <li>Windows-сборка в бете может быть неподписанной; перед установкой пользователь должен учитывать предупреждение о неизвестном издателе.</li>
              <li>Поддержка отвечает по мере возможности без обещания круглосуточного ответа или фиксированного SLA.</li>
              <li>Если оплата, загрузка или погашение ключа временно остановлены, команда показывает доступное действие вместо имитации успешной загрузки или оплаты.</li>
            </ul>
          </article>

          <article className="lp-legal-panel">
            <h2>Где смотреть актуальную версию</h2>
            <p>Актуальные версии документов доступны на сайте, в кабинете и по запросу в поддержку.</p>
            <p className="lp-legal-inline-links">
              Полезные страницы: <Link href="/">главная POKROV</Link>,{" "}
              <Link href={MARKETING_CANONICAL_PATHS.mobile}>мобильный старт</Link> и{" "}
              <Link href={MARKETING_CANONICAL_PATHS.devices}>Android и Windows</Link>.
            </p>
          </article>
        </section>

        <section className="lp-legal-panel">
          <h2>Контакты</h2>
          <ul className="lp-legal-list lp-legal-list--contacts">
            <li>
              Support: <a href={`mailto:${config.contactEmail}`}>{config.contactEmail}</a>
            </li>
            <li>
              Enterprise: <a href={`mailto:${config.enterpriseEmail}`}>{config.enterpriseEmail}</a>
            </li>
            <li>
              Telegram:{" "}
              <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer">
                {config.supportTelegramUrl}
              </a>
            </li>
            <li>
              Канал новостей:{" "}
              <a href={config.newsChannelUrl} target="_blank" rel="noreferrer">
                {config.newsChannelUrl}
              </a>
            </li>
          </ul>
          <div className="legal-actions">
            <Link className="lp-btn lp-btn--ghost" href="/">
              На главную POKROV
            </Link>
            <a className="lp-btn lp-btn--primary" href={config.botUrl} target="_blank" rel="noreferrer">
              Открыть Telegram-бота
            </a>
          </div>
        </section>
        </main>
      </div>
    </>
  );
}
