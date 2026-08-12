import { Suspense } from "react";

import JsonLd from "../../components/json-ld";
import { PageShell } from "../../components/layout/page-shell";
import { buildBreadcrumbJsonLd, buildCheckoutServiceJsonLd, buildMarketingMetadata } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText } from "../../lib/pokrov";
import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export const metadata = buildMarketingMetadata(
  getCopyText("marketing.checkout.meta.title", "Оплата доступа | POKROV"),
  getCopyText(
    "marketing.checkout.meta.description",
    "Страница оплаты показывает доступные планы, сумму до оплаты, получение ключа доступа и помощь при спорных платежах.",
  ),
  {
    path: "/checkout/",
    noIndex: false,
  },
);

export default function CheckoutPage() {
  return (
    <PageShell checkout>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: getCopyText("marketing.checkout.breadcrumb", "Продление доступа"), path: "/checkout/" },
        ])}
      />
      <JsonLd data={buildCheckoutServiceJsonLd()} />
      <Suspense fallback={<CheckoutLoadingFallback />}>
        <CheckoutClient />
      </Suspense>
    </PageShell>
  );
}
