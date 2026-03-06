import { getCopyText, getPortalPublicConfig } from "../../lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <h1>Политика конфиденциальности</h1>
      <p>{getCopyText("marketing.legal.privacy.intro", "PORTAL хранит только те данные, которые действительно нужны для работы аккаунта, поддержки и безопасности сервиса.")}</p>
      <ul>
        <li>Данные аккаунта: идентификатор, статус доступа, срок действия и служебные метки.</li>
        <li>События диагностики и стабильности, которые помогают поддерживать качество сервиса.</li>
        <li>Сообщения поддержки, которые пользователь отправляет добровольно в обращениях.</li>
      </ul>
      <p>Мы не публикуем персональные данные пользователей и не используем их вне задач обслуживания платформы.</p>
      <h2>Контакты</h2>
      <ul>
        <li>Support: <a href={`mailto:${config.contactEmail}`}>{config.contactEmail}</a></li>
        <li>Enterprise: <a href={`mailto:${config.enterpriseEmail}`}>{config.enterpriseEmail}</a></li>
        <li>Telegram: <a href={config.supportTelegramUrl} target="_blank" rel="noreferrer">{config.supportTelegramUrl}</a></li>
        <li>Форма связи: <a href={config.contactFormUrl} target="_blank" rel="noreferrer">{config.contactFormUrl}</a></li>
      </ul>
      <div className="legal-actions">
        <a className="btn btn-ghost" href="/">На главную</a>
        <a className="btn btn-primary" href={config.botUrl} target="_blank" rel="noreferrer">Продолжить в Telegram</a>
      </div>
    </main>
  );
}
