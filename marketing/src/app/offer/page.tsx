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
      <main className="legal-page">
        <h1>Публичная оферта</h1>
        <p>
          Этот документ описывает базовые условия доступа к цифровым услугам POKROV, порядок продления и
          основные правила использования сервиса.
        </p>
        <ul>
          <li>Сервис предоставляется как цифровая подписка на выбранный срок.</li>
          <li>Бесплатный тест и отдельные сценарии доступа могут иметь свои ограничения по устройствам и функциям.</li>
          <li>Продление и оплата запускаются через интерфейсы POKROV или через Telegram-бота, если это предусмотрено текущим маршрутом.</li>
          <li>Возвраты и спорные случаи рассматриваются индивидуально через службу заботы.</li>
        </ul>
        <p>Актуальные версии документов доступны на сайте, в кабинете и по запросу в службу заботы.</p>
        <p>
          Полезные страницы: <Link href="/">главная POKROV</Link>,{" "}
          <Link href={MARKETING_CANONICAL_PATHS.mobile}>мобильный старт</Link> и{" "}
          <Link href={MARKETING_CANONICAL_PATHS.devices}>Android и Windows</Link>.
        </p>
        <h2>Контакты</h2>
        <ul>
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
          <Link className="btn btn-ghost" href="/">
            На главную POKROV
          </Link>
          <a className="btn btn-primary" href={config.botUrl} target="_blank" rel="noreferrer">
            Открыть Telegram-бота
          </a>
        </div>
      </main>
    </>
  );
}
