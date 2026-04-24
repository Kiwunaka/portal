"use client";

import AppRouteLink from "@/components/app-route-link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function StatisticsPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard/");
  }, [router]);

  return (
    <main className="grid min-h-[50vh] place-items-center">
      <AppRouteLink href="/dashboard/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
        Вернуться на главную
      </AppRouteLink>
    </main>
  );
}
