const TG_FALLBACK = "https://t.me/portal_service_bot";

const TARGET_URL =
  process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL ||
  process.env.PAY_CHECKOUT_URL ||
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ||
  TG_FALLBACK;
const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "support@portal-privacy.online";
const ENTERPRISE_EMAIL = process.env.NEXT_PUBLIC_ENTERPRISE_EMAIL || "enterprise@portal-privacy.online";
const CONTACT_TG_URL = process.env.NEXT_PUBLIC_CONTACT_TG_URL || "https://t.me/portal_privacy_helpbot";
const CONTACT_FORM_URL = process.env.NEXT_PUBLIC_CONTACT_FORM_URL || "https://t.me/portal_privacy_helpbot";

export default function PrivacyPage() {
  return (
    <main className="legal-page">
      <h1>Политика конфиденциальности</h1>
      <p>
        PORTAL придерживается принципа минимизации данных. Мы обрабатываем только сведения, которые необходимы для работы
        аккаунта, VPN-подключения, поддержки пользователей и предотвращения злоупотреблений.
      </p>
      <ul>
        <li>Технические данные аккаунта: идентификатор, статус доступа, срок действия и служебные метки.</li>
        <li>События диагностики и стабильности, которые помогают поддерживать качество сервиса.</li>
        <li>Сообщения поддержки, которые пользователь отправляет добровольно в тикетах.</li>
      </ul>
      <p>
        Мы не публикуем персональные данные пользователей и не используем их вне задач обслуживания платформы.
      </p>
      <h2>Контакты</h2>
      <ul>
        <li>
          Support: <a href={`mailto:${CONTACT_EMAIL}`}>{CONTACT_EMAIL}</a>
        </li>
        <li>
          Enterprise: <a href={`mailto:${ENTERPRISE_EMAIL}`}>{ENTERPRISE_EMAIL}</a>
        </li>
        <li>
          Telegram: <a href={CONTACT_TG_URL} target="_blank" rel="noreferrer">{CONTACT_TG_URL}</a>
        </li>
        <li>
          Форма связи: <a href={CONTACT_FORM_URL} target="_blank" rel="noreferrer">{CONTACT_FORM_URL}</a>
        </li>
      </ul>
      <div className="legal-actions">
        <a className="btn btn-ghost" href="/">
          На главную
        </a>
        <a className="btn btn-primary" href={TARGET_URL} target="_blank" rel="noreferrer">
          Открыть оплату
        </a>
      </div>
    </main>
  );
}
