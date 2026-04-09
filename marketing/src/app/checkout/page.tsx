import { Suspense } from "react";

import { buildMarketingMetadata } from "../../components/marketing-landing";
import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export const metadata = buildMarketingMetadata(
  "Checkout и продление | POKROV VPN",
  "Публичная страница checkout объясняет следующий шаг и переводит в личный кабинет или Telegram, если нужен персональный маршрут оплаты.",
  {
    path: "/checkout/",
    keywords: ["pokrov vpn checkout", "оплата vpn", "продлить vpn", "vpn checkout"],
  },
);

export default function CheckoutPage() {
  return (
    <Suspense fallback={<CheckoutLoadingFallback />}>
      <CheckoutClient />
    </Suspense>
  );
}
