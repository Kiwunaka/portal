import { getPortalPublicConfig } from "../../lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export default function OfferPage() {
  return (
    <main className="legal-page">
      <h1>Публичная оферта</h1>
      <p>Этот документ описывает базовые условия доступа к цифровым услугам POKROV VPN, порядок продления и основные правила использования сервиса.</p>
      <ul>
        <li>Сервис предоставляется в формате цифровой подписки на выбранный срок.</li>
        <li>Тестовый период и отдельные сценарии доступа могут иметь свои ограничения по устройствам и функциям.</li>
        <li>Продление и оплата запускаются через интерфейсы POKROV VPN или через Telegram-бота, если это предусмотрено текущим маршрутом.</li>
        <li>Возвраты и спорные случаи рассматриваются индивидуально через поддержку.</li>
      </ul>
      <p>Актуальные версии документов доступны на сайте, в кабинете и по запросу в поддержку.</p>
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
          Форма связи:{" "}
          <a href={config.contactFormUrl} target="_blank" rel="noreferrer">
            {config.contactFormUrl}
          </a>
        </li>
      </ul>
      <div className="legal-actions">
        <a className="btn btn-ghost" href="/">
          На главную
        </a>
        <a className="btn btn-primary" href={config.botUrl} target="_blank" rel="noreferrer">
          Открыть Telegram-бота
        </a>
      </div>
    </main>
  );
}
