"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo } from "react";

import { Button } from "../components/ui/button";
import { Card } from "../components/ui/card";
import { getPokrovPublicConfig } from "../lib/pokrov";

type PaymentReturnRedirectProps = {
  hint: "success" | "fail";
};

export function PaymentReturnRedirect({ hint }: PaymentReturnRedirectProps) {
  const searchParams = useSearchParams();
  const surface = searchParams.get("return_surface") === "cabinet" ? "cabinet" : "marketing";
  const destination = useMemo(() => {
    if (typeof window === "undefined") return "/checkout/";
    if (surface === "cabinet") {
      const config = getPokrovPublicConfig({
        NEXT_PUBLIC_WEBAPP_URL: process.env.NEXT_PUBLIC_WEBAPP_URL,
      });
      const url = new URL(config.webappUrl);
      url.pathname = "/subscription/checkout/";
      url.search = "";
      url.searchParams.set("payment_return", hint);
      return url.toString();
    }
    const url = new URL("/checkout/", window.location.origin);
    url.searchParams.set("payment_return", hint);
    return url.toString();
  }, [hint, surface]);

  useEffect(() => {
    window.location.replace(destination);
  }, [destination]);

  return (
    <main className="mx-auto flex min-h-[60vh] max-w-xl items-center px-4 py-12 sm:px-6">
      <Card className="w-full text-center">
        <h1 className="font-display text-2xl font-bold text-ink">Возвращаемся к статусу платежа</h1>
        <p className="mt-3 text-sm leading-relaxed text-ink-soft">
          Подтверждение берём только с сервера. Если переход не сработал, продолжите вручную.
        </p>
        <Button href={destination} className="mt-5">Проверить статус</Button>
      </Card>
    </main>
  );
}
