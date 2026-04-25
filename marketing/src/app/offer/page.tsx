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
      <main className="legal-page lp-legal-shell">
        <section className="lp-legal-banner">
          <span className="lp-legal-banner__eyebrow">Юридическая информация</span>
          <h1>Публичная оферта</h1>
          <p>
            Здесь собраны базовые условия доступа к цифровым услугам POKROV, порядок продления и спокойный способ
            связаться с командой, если нужен разбор спорной ситуации.
          </p>
        </section>

        <section className="lp-legal-grid">
          <article className="lp-legal-panel">
            <h2>Основные условия</h2>
            <ul className="lp-legal-list">
              <li>Текущая волна — оплачиваемая бета с ограниченным доступом по приглашениям, а не публичный стабильный запуск.</li>
              <li>Сервис предоставляется как цифровой доступ на выбранный срок; автоматическое списание не включается без отдельного явного согласия пользователя.</li>
              <li>Бесплатный тест длится 5 дней, а отдельные сценарии доступа могут иметь ограничения по устройствам, функциям и доступным сборкам.</li>
              <li>Оплата продаёт activation key. Ключ нужно погасить в приложении или кабинете, чтобы продлить managed-доступ на том же app-first аккаунте.</li>
              <li>Возвраты, отмены, спорные статусы провайдера и ручная сверка рассматриваются через поддержку; итог зависит от фактического статуса платежа и уже выданного доступа.</li>
            </ul>
          </article>

          <article className="lp-legal-panel">
            <h2>Бета-ограничения</h2>
            <ul className="lp-legal-list">
              <li>Android APK выдаётся только как внутренняя бета до завершения signing, handoff и физического localhost/control-surface аудита.</li>
              <li>Windows-сборка в бете может быть неподписанной; перед установкой пользователь должен учитывать предупреждение о неизвестном издателе.</li>
              <li>Поддержка работает в формате best-effort с целевым ответом до 24 часов, без production SLA и без обещания круглосуточного ответа.</li>
              <li>Если checkout, download или redeem временно остановлены, команда показывает доступный следующий шаг вместо имитации успешной загрузки или оплаты.</li>
            </ul>
          </article>

          <article className="lp-legal-panel">
            <h2>Где смотреть актуальную версию</h2>
            <p>Актуальные версии документов доступны на сайте, в кабинете и по запросу в службу заботы.</p>
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
            <Link className="btn btn-ghost" href="/">
              На главную POKROV
            </Link>
            <a className="btn btn-primary" href={config.botUrl} target="_blank" rel="noreferrer">
              Открыть Telegram-бота
            </a>
          </div>
        </section>
      </main>
    </>
  );
}
