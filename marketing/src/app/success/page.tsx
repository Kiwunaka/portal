import { Suspense } from "react";

import { PaymentReturnRedirect } from "../payment-return-redirect";

export default function PaymentSuccessPage() {
  return (
    <Suspense>
      <PaymentReturnRedirect hint="success" />
    </Suspense>
  );
}
