import { getPortalPublicConfig } from "../../lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export default function OfferPage() {
  return (
    <main className="legal-page">
      <h1>Публичная оферта</h1>
      <p>Этот документ описывает общие условия доступа к цифровым услугам PORTAL, порядок продления и базовые правила использования сервиса.</p>
      <ul>
        <li>Сервис предоставляется в формате цифровой подписки с доступом на выбранный срок.</li>
        <li>Тестовый период и бесплатные fallback-сценарии могут иметь отдельные ограничения по устройствам, трафику и доступным возможностям.</li>
        <li>Продление и оплата запускаются в интерфейсах PORTAL или через Telegram-бота, если это предусмотрено текущим сценарием.</li>
        <li>Возврат средств и спорные случаи рассматриваются индивидуально через поддержку.</li>
      </ul>
      <p>Актуальные редакции документов доступны на сайте, в кабинете и по запросу в поддержку.</p>
      <h2>Контакты</h2>
      <ul>
        <li>Support: <a href={`mailto:${config.contactEmail}`}>{config.contactEmail}</a></li>
        <li>Enterprise: <a href={`mailto:${config.enterpriseEmail}`}>{config.enterpriseEmail}</a></li>
        <li>Telegram: <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer">{config.supportTelegramUrl}</a></li>
        <li>Форма связи: <a href={config.contactFormUrl} target="_blank" rel="noreferrer">{config.contactFormUrl}</a></li>
      </ul>
      <div className="legal-actions">
        <a className="btn btn-ghost" href="/">На главную</a>
        <a className="btn btn-primary" href={config.botUrl} target="_blank" rel="noreferrer">Открыть Telegram-бота</a>
      </div>
    </main>
  );
}
