import { getCopyText, getPokrovPublicConfig } from "../../lib/pokrov";

const config = getPokrovPublicConfig(process.env as Record<string, string | undefined>);

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <h1>Политика конфиденциальности</h1>
      <p>{getCopyText("marketing.legal.privacy.intro", "POKROV VPN собирает только те данные, которые нужны для работы аккаунта, поддержки, защиты сервиса и проведения платежей.")}</p>
      <ul>
        <li>Данные аккаунта: идентификатор, срок доступа, активный план и служебные метки для работы продукта.</li>
        <li>Технические события: ошибки оплаты, события авторизации, обращения в поддержку и сигналы стабильности сервиса.</li>
        <li>Сообщения и файлы, которые пользователь сам отправляет в поддержку.</li>
      </ul>
      <p>Мы не продаём персональные данные и используем их только там, где это нужно для работы сервиса, поддержки и обязательных расчётов.</p>
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
