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
    "Страница оплаты показывает доступные планы, сумму до оплаты, получение ключа доступа и помощь при спорных платежах.",
  ),
  {
    path: "/checkout/",
    noIndex: false,
    keywords: ["оплата pokrov", "продление pokrov", "тарифы pokrov", "checkout pokrov"],
  },
);

export default function CheckoutPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: getCopyText("marketing.checkout.breadcrumb", "Продление доступа"), path: "/checkout/" },
        ])}
      />
      <Suspense fallback={<CheckoutLoadingFallback />}>
        <CheckoutClient />
      </Suspense>
    </>
  );
}
