const TG_FALLBACK = "https://t.me/portal_service_bot";

const TARGET_URL =
  process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL ||
  process.env.PAY_CHECKOUT_URL ||
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ||
  TG_FALLBACK;
const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "support@kiwunaka.space";
const CONTACT_TG_URL = process.env.NEXT_PUBLIC_CONTACT_TG_URL || "https://t.me/portal_privacy_helpbot";
const CONTACT_FORM_URL = process.env.NEXT_PUBLIC_CONTACT_FORM_URL || "https://t.me/portal_privacy_helpbot";

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <h1>Политика конфиденциальности</h1>
      <p>
        PORTAL придерживается принципа минимизации данных: хранятся только сведения, необходимые для предоставления
        доступа, поддержки и предотвращения злоупотреблений.
      </p>
      <ul>
        <li>Идентификатор аккаунта, дата активации и срок действия доступа.</li>
        <li>Служебные события для диагностики и улучшения качества сервиса.</li>
        <li>Данные тикетов поддержки, отправленные пользователем добровольно.</li>
      </ul>
      <p>
        Мы не публикуем персональные данные пользователей и не используем их вне задач обслуживания платформы.
      </p>
      <h2>Контакты</h2>
      <ul>
        <li>Email: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a></li>
        <li>Telegram: <a href={CONTACT_TG_URL} target="_blank" rel="noreferrer">{CONTACT_TG_URL}</a></li>
        <li>Форма связи: <a href={CONTACT_FORM_URL} target="_blank" rel="noreferrer">{CONTACT_FORM_URL}</a></li>
      </ul>
      <div className="legal-actions">
        <a className="btn btn-ghost" href="/">
          На главную
        </a>
        <a className="btn btn-primary" href={TARGET_URL} target="_blank" rel="noreferrer">
          Подключить доступ
        </a>
      </div>
    </main>
  );
}
