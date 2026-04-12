import { Suspense } from "react";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";
import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export const metadata = buildMarketingMetadata(
  "Checkout и продление | POKROV VPN",
  "Публичная страница checkout объясняет следующий шаг и переводит в личный кабинет или Telegram, если нужен персональный маршрут оплаты.",
  {
    path: "/checkout/",
    noIndex: true,
    keywords: ["pokrov vpn checkout", "оплата vpn", "продлить vpn", "vpn checkout"],
  },
);

export default function CheckoutPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: "POKROV VPN", path: "/" },
          { name: "Checkout и продление", path: "/checkout/" },
        ])}
      />
      <Suspense fallback={<CheckoutLoadingFallback />}>
        <CheckoutClient />
      </Suspense>
    </>
  );
}
