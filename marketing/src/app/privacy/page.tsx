const TG_FALLBACK = "https://t.me/portal_service_bot";

const TARGET_URL =
  process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL ||
  process.env.PAY_CHECKOUT_URL ||
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ||
  TG_FALLBACK;

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
