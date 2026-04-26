"use client";

import type { ReactNode } from "react";

import CabinetShell from "@/components/cabinet-shell";
import { PortalSessionProvider } from "@/lib/session";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <PortalSessionProvider>
      <CabinetShell>{children}</CabinetShell>
    </PortalSessionProvider>
  );
}
