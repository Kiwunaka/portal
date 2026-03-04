"use client";

export type AdminNavItem = {
  href: string;
  label: string;
  icon: string;
  match: (path: string) => boolean;
};

export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  { href: "/admin/dashboard", label: "Dashboard", icon: "space_dashboard", match: (path) => path === "/admin" || path.startsWith("/admin/dashboard") },
  { href: "/admin/users", label: "Users", icon: "groups", match: (path) => path.startsWith("/admin/users") },
  { href: "/admin/nodes", label: "Nodes", icon: "hub", match: (path) => path.startsWith("/admin/nodes") },
  { href: "/admin/tickets", label: "Tickets", icon: "support_agent", match: (path) => path.startsWith("/admin/tickets") },
  { href: "/admin/promos", label: "Promos", icon: "sell", match: (path) => path.startsWith("/admin/promos") },
  { href: "/admin/broadcast", label: "Broadcast", icon: "campaign", match: (path) => path.startsWith("/admin/broadcast") },
  { href: "/admin/referrals", label: "Referrals", icon: "link", match: (path) => path.startsWith("/admin/referrals") },
  { href: "/admin/bonuses", label: "Bonuses", icon: "casino", match: (path) => path.startsWith("/admin/bonuses") },
];

export function fmtRuDate(value?: string | null): string {
  if (!value) return "—";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "—";
  return dt.toLocaleString("ru-RU");
}
