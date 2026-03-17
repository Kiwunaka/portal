import { getPortalPublicConfig } from "../../lib/portal";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <h1>Политика конфиденциальности</h1>
      <p>PORTAL хранит только те данные, которые действительно нужны для работы аккаунта, поддержки, защиты сервиса и исполнения платёжных операций.</p>
      <ul>
        <li>Данные аккаунта: идентификатор, срок доступа, активный план и служебные метки для работы продукта.</li>
        <li>Технические события: логи стабильности, ошибки оплаты, события авторизации и обращения в поддержку.</li>
        <li>Сообщения, вложения и файлы, которые пользователь сам отправляет в поддержку.</li>
      </ul>
      <p>Мы не продаём персональные данные пользователей и используем их только в рамках работы сервиса, поддержки и обязательных расчётов.</p>
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
