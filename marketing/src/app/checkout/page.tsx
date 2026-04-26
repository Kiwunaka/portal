import { Suspense } from "react";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText } from "../../lib/pokrov";
import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export const metadata = buildMarketingMetadata(
  getCopyText("marketing.checkout.meta.title", "Оплата бета-доступа | POKROV"),
  getCopyText(
    "marketing.checkout.meta.description",
    "Страница checkout объясняет оплату бета-доступа, покупку activation key, ручную помощь при спорных платежах и следующий шаг без сырых технических ссылок.",
  ),
  {
    path: "/checkout/",
    noIndex: false,
    keywords: ["оплата pokrov", "продление pokrov", "личный маршрут оплаты", "checkout pokrov"],
  },
);

export default function CheckoutPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: getCopyText("marketing.checkout.breadcrumb", "Личный маршрут оплаты"), path: "/checkout/" },
        ])}
      />
      <Suspense fallback={<CheckoutLoadingFallback />}>
        <CheckoutClient />
      </Suspense>
    </>
  );
}
