"use client";

import AppRouteLink from "@/components/app-route-link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function LegacyDashboardDownloadsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/downloads/");
  }, [router]);

  return (
    <main className="grid min-h-[50vh] place-items-center">
      <AppRouteLink href="/downloads/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
        Открыть загрузки
      </AppRouteLink>
    </main>
  );
}
