"use client";

import { adminPanelClass } from "@/components/admin/admin-shell";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminHomePage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/admin/dashboard/");
  }, [router]);

  return (
    <section className={adminPanelClass("neutral")} aria-live="polite">
      <p className="text-sm font-semibold text-slate-950">Переходим в сводку оператора...</p>
      <p className="mt-1 text-xs leading-5 text-slate-600">/admin теперь ведет в рабочий обзор без отдельной промо-страницы.</p>
    </section>
  );
}
