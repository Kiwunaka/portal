"use client";

import type { ReactNode } from "react";

import CabinetShell from "@/components/cabinet-shell";
import { PortalSessionProvider } from "@/lib/session";
import { usePathname } from "next/navigation";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAdminRoute = pathname === "/admin" || pathname.startsWith("/admin/");

  return (
    <PortalSessionProvider>
      {isAdminRoute ? children : <CabinetShell>{children}</CabinetShell>}
    </PortalSessionProvider>
  );
}
