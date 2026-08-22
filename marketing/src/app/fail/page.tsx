import { Suspense } from "react";

import { PaymentReturnRedirect } from "../payment-return-redirect";

export default function PaymentFailPage() {
  return (
    <Suspense>
      <PaymentReturnRedirect hint="fail" />
    </Suspense>
  );
}
