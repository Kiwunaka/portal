import { Suspense } from "react";

import JsonLd from "../../components/json-ld";
import { buildMarketingMetadata } from "../../components/marketing-landing";
import { buildBreadcrumbJsonLd } from "../../lib/marketing-site";
import { CANONICAL_PLATFORM_BRAND, getCopyText } from "../../lib/pokrov";
import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export const metadata = buildMarketingMetadata(
  getCopyText("marketing.checkout.meta.title", "Статус продления | POKROV"),
  getCopyText(
    "marketing.checkout.meta.description",
    "Страница продления показывает статус платежного маршрута, ключ доступа, ручную помощь при спорных случаях и следующий шаг без сырых технических ссылок.",
  ),
  {
    path: "/checkout/",
    noIndex: false,
    keywords: ["статус продления pokrov", "продление pokrov", "ключ доступа pokrov", "кабинет pokrov"],
  },
);

export default function CheckoutPage() {
  return (
    <>
      <JsonLd
        data={buildBreadcrumbJsonLd([
          { name: CANONICAL_PLATFORM_BRAND, path: "/" },
          { name: getCopyText("marketing.checkout.breadcrumb", "Статус продления"), path: "/checkout/" },
        ])}
      />
      <Suspense fallback={<CheckoutLoadingFallback />}>
        <CheckoutClient />
      </Suspense>
    </>
  );
}
