const TG_FALLBACK = "https://t.me/portal_service_bot";

const TARGET_URL =
  process.env.NEXT_PUBLIC_PAY_CHECKOUT_URL ||
  process.env.PAY_CHECKOUT_URL ||
  process.env.NEXT_PUBLIC_TELEGRAM_BOT_URL ||
  TG_FALLBACK;

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
