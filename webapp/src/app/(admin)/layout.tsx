"use client";

import type { ReactNode } from "react";

import { PortalSessionProvider } from "@/lib/session";

export default function AdminRouteGroupLayout({ children }: { children: ReactNode }) {
  return <PortalSessionProvider>{children}</PortalSessionProvider>;
}
