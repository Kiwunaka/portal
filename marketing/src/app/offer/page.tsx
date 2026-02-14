const TG_FALLBACK = "https://t.me/portal_service_bot";

const TARGET_URL =
  process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL ||
  process.env.PAY_CHECKOUT_URL ||
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ||
  TG_FALLBACK;
const CONTACT_EMAIL = process.env.NEXT_PUBLIC_CONTACT_EMAIL || "support@kiwunaka.space";
const CONTACT_TG_URL = process.env.NEXT_PUBLIC_CONTACT_TG_URL || "https://t.me/portal_privacy_helpbot";
const CONTACT_FORM_URL = process.env.NEXT_PUBLIC_CONTACT_FORM_URL || "https://t.me/portal_privacy_helpbot";

export default function OfferPage() {
  return (
    <main className="legal-page">
      <h1>Публичная оферта</h1>
      <p>
        Сервис PORTAL предоставляет доступ к цифровой инфраструктуре защищенной маршрутизации. Используя сервис, вы
        подтверждаете, что ознакомлены с условиями и принимаете их.
      </p>
      <ul>
        <li>Доступ предоставляется в формате digital-сервиса без гарантий непрерывности.</li>
        <li>Пользователь самостоятельно соблюдает применимые нормы своей юрисдикции.</li>
        <li>Возврат средств рассматривается индивидуально в рамках действующего регламента.</li>
        <li>Для работы сервиса сохраняется минимум технических данных аккаунта.</li>
      </ul>
      <p>
        Полная версия условий отображается в личном кабинете WebApp внутри Telegram-бота.
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
