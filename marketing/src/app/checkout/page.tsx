const freekassaNotify = "https://kiwunaka.space/api/payments/freekassa/notify";
const paySuccess = "https://kiwunaka.space/pay/success";
const payFail = "https://kiwunaka.space/pay/fail";

const cardlinkResult = "https://kiwunaka.space/api/payments/result/cardlink";
const cardlinkRefund = "https://kiwunaka.space/api/payments/refund/cardlink";
const cardlinkChargeback = "https://kiwunaka.space/api/payments/chargeback/cardlink";

const plans = [
  { code: "1m", label: "1 месяц", rub: 249 },
  { code: "3m", label: "3 месяца", rub: 699 },
  { code: "6m", label: "6 месяцев", rub: 1199 },
  { code: "9m", label: "9 месяцев", rub: 1399 },
  { code: "12m", label: "12 месяцев", rub: 1499 },
];

function netAfterFees(price: number): number {
  return 0.902275 * price - 1.93;
}

export default function CheckoutMockPage() {
  return (
    <main className="legal-page">
      <h1>Mock checkout</h1>
      <p>Эта страница показывает сценарий выбора кассы и тарифа. Реальная API-интеграция будет добавлена на следующем этапе.</p>

      <h2>Тарифы (RUB)</h2>
      <ul>
        {plans.map((plan) => (
          <li key={plan.code}>
            {plan.label}: {plan.rub} ₽ | net после комиссий: {netAfterFees(plan.rub).toFixed(2)} ₽
          </li>
        ))}
      </ul>

      <h2>Freekassa</h2>
      <ul>
        <li>Store URL: https://portal-privacy.online/</li>
        <li>Notify URL (POST): {freekassaNotify}</li>
        <li>Success URL (GET): {paySuccess}</li>
        <li>Fail URL (GET): {payFail}</li>
      </ul>

      <h2>Cardlink</h2>
      <ul>
        <li>Store URL: https://portal-privacy.online/</li>
        <li>Success URL: {paySuccess}</li>
        <li>Fail URL: {payFail}</li>
        <li>Result URL: {cardlinkResult}</li>
        <li>Refund URL: {cardlinkRefund}</li>
        <li>Chargeback URL: {cardlinkChargeback}</li>
      </ul>

      <div className="legal-actions">
        <a className="btn btn-ghost" href="/">
          На главную
        </a>
        <a className="btn btn-primary" href="https://t.me/portal_service_bot" target="_blank" rel="noreferrer">
          Быстрый путь через Telegram
        </a>
      </div>
    </main>
  );
}
