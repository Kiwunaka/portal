import { Suspense } from "react";

import CheckoutClient, { CheckoutLoadingFallback } from "./checkout-client";

export default function CheckoutPage() {
  return (
    <Suspense fallback={<CheckoutLoadingFallback />}>
      <CheckoutClient />
    </Suspense>
  );
}
