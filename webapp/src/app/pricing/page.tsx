"use client";

import AppRouteLink from "@/components/app-route-link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function PricingPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/subscription/");
  }, [router]);

  return (
    <main className="grid min-h-[60vh] place-items-center px-4">
      <AppRouteLink href="/subscription/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
        Перейти к тарифам
      </AppRouteLink>
    </main>
  );
}
