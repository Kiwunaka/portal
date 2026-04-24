import { Suspense } from "react";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText } from "../../lib/pokrov";
import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export const metadata = buildMarketingMetadata(
  getCopyText("marketing.checkout.meta.title", "Ключ доступа | POKROV"),
  getCopyText(
    "marketing.checkout.meta.description",
    "Выберите срок, оплатите ключ доступа и активируйте его в приложении или кабинете POKROV.",
  ),
  {
    path: "/checkout/",
    noIndex: true,
    keywords: ["оплата pokrov", "ключ доступа pokrov", "продление pokrov", "кабинет pokrov"],
  },
);

export default function CheckoutPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: getCopyText("marketing.checkout.breadcrumb", "Ключ доступа"), path: "/checkout/" },
        ])}
      />
      <Suspense fallback={<CheckoutLoadingFallback />}>
        <CheckoutClient />
      </Suspense>
    </>
  );
}
