import { getCopyText, getPortalPublicConfig } from "../../lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export default function OfferPage() {
  return (
    <main className="legal-page">
      <h1>Публичная оферта</h1>
      <p>{getCopyText("marketing.legal.offer.intro", "Этот документ описывает условия доступа к цифровым услугам PORTAL и порядок оплаты выбранного периода.")}</p>
      <ul>
        <li>Сервис предоставляется в формате цифровой услуги по модели best-effort.</li>
        <li>Пользователь самостоятельно соблюдает применимые нормы своей юрисдикции.</li>
        <li>Возврат средств рассматривается индивидуально по действующему регламенту.</li>
        <li>Для работы аккаунта сохраняется только необходимый минимум служебных данных.</li>
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
        <a className="btn btn-primary" href="/checkout/">Открыть оплату</a>
      </div>
    </main>
  );
}
