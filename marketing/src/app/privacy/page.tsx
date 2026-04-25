import Link from "next/link";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd, MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export const metadata = buildMarketingMetadata(
  "Политика конфиденциальности | POKROV",
  "Какие данные использует POKROV для работы доступа, поддержки и платежей, и как связаться с поддержкой.",
  {
    path: "/privacy/",
    keywords: ["политика конфиденциальности", "privacy pokrov", "данные pokrov"],
  },
);

export default function PrivacyPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: "Политика конфиденциальности", path: "/privacy/" },
        ])}
      />
      <main className="legal-page lp-legal-shell">
        <section className="lp-legal-banner">
          <span className="lp-legal-banner__eyebrow">Данные и поддержка</span>
          <h1>Политика конфиденциальности</h1>
          <p>
            {getCopyText(
              "marketing.legal.privacy.intro",
              "POKROV использует только те данные, которые нужны для работы доступа, поддержки, защиты сервиса и проведения платежей.",
            )}
          </p>
        </section>

        <section className="lp-legal-grid">
          <article className="lp-legal-panel">
            <h2>Какие данные используются</h2>
            <ul className="lp-legal-list">
              <li>Данные аккаунта: идентификатор, срок доступа, активный план и служебные метки для работы продукта.</li>
              <li>Технические события: ошибки оплаты, события авторизации, обращения в поддержку и сигналы стабильности сервиса.</li>
              <li>Платёжные события: номер или статус заказа внутри POKROV, выбранный срок, сумма, провайдерский статус и отметки ручной сверки без хранения карточных данных на стороне POKROV.</li>
              <li>Сообщения и файлы, которые пользователь сам отправляет в службу заботы.</li>
            </ul>
          </article>

          <article className="lp-legal-panel">
            <h2>Как мы с этим обращаемся</h2>
            <p>Мы не продаём персональные данные и используем их только там, где это нужно для работы сервиса и обязательных расчётов.</p>
            <p>Во время оплачиваемой беты часть платёжной обработки выполняет внешний провайдер. Данные передаются ему только в объёме, который нужен для оплаты, возврата, сверки спорного статуса или поддержки пользователя.</p>
            <p className="lp-legal-inline-links">
              Полезные страницы: <Link href="/">главная POKROV</Link>,{" "}
              <Link href={MARKETING_CANONICAL_PATHS.youtube}>YouTube</Link> и{" "}
              <Link href={MARKETING_CANONICAL_PATHS.telegram}>Telegram и служба заботы</Link>.
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
