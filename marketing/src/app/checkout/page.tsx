import { Suspense } from "react";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";
import { getCopyText } from "../../lib/pokrov";
import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export const metadata = buildMarketingMetadata(
  getCopyText("marketing.checkout.meta.title", "Личный маршрут оплаты | POKROV Network"),
  getCopyText(
    "marketing.checkout.meta.description",
    "Публичная страница checkout объясняет следующий шаг, но сама касса открывается только после личного входа в кабинет или по персональной ссылке из Telegram.",
  ),
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
          { name: "POKROV Network", path: "/" },
          { name: getCopyText("marketing.checkout.breadcrumb", "Личный маршрут оплаты"), path: "/checkout/" },
        ])}
      />
      <Suspense fallback={<CheckoutLoadingFallback />}>
        <CheckoutClient />
      </Suspense>
    </>
  );
}
