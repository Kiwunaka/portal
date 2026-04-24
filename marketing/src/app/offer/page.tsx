import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export const metadata = buildMarketingMetadata(
  "Публичная оферта | POKROV",
  "Понятные условия POKROV: доступ, 5 дней проверки, ключи доступа, продление и контакты поддержки.",
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
      <main className="legal-page lp-legal-shell">
        <section className="lp-legal-banner">
          <span className="lp-legal-banner__eyebrow">Юридическая информация</span>
          <h1>Публичная оферта</h1>
          <p>
            {getCopyText(
              "marketing.legal.offer.intro",
              "Понятные условия POKROV: доступ, 5 дней проверки, ключи доступа, продление и контакты поддержки.",
            )}
          </p>
        </section>

        <section className="lp-legal-grid">
          <article className="lp-legal-panel">
            <h2>Основные условия простыми словами</h2>
            <ul className="lp-legal-list">
              <li>POKROV предоставляет доступ на выбранный срок.</li>
              <li>Новая установка может начать с 5 дней проверки в приложении.</li>
              <li>Продление и оплата проходят через сайт, приложение, кабинет или Telegram-бота, если такой путь доступен пользователю.</li>
              <li>После оплаты пользователь получает ключ доступа и активирует его в приложении или кабинете.</li>
              <li>Возвраты и спорные случаи разбираются индивидуально через поддержку.</li>
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
              Поддержка: <a href={`mailto:${config.contactEmail}`}>{config.contactEmail}</a>
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
            <Link className="btn btn-ghost" href="/">
              На главную POKROV
            </Link>
            <Link className="btn btn-primary" href={MARKETING_CANONICAL_PATHS.install}>
              Попробовать 5 дней
            </Link>
            <a className="btn btn-ghost" href={config.botUrl} target="_blank" rel="noreferrer">
              Открыть Telegram-бота
            </a>
          </div>
        </section>
      </main>
    </>
  );
}
