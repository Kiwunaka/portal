"use client";

export type AdminNavItem = {
  href: string;
  label: string;
  icon: string;
  match: (path: string) => boolean;
};

export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  { href: "/admin/dashboard", label: "Сводка", icon: "space_dashboard", match: (path) => path === "/admin" || path.startsWith("/admin/dashboard") },
  { href: "/admin/users", label: "Пользователи", icon: "groups", match: (path) => path.startsWith("/admin/users") },
  { href: "/admin/nodes", label: "Ноды", icon: "hub", match: (path) => path.startsWith("/admin/nodes") },
  { href: "/admin/network", label: "Сеть", icon: "lan", match: (path) => path.startsWith("/admin/network") },
  { href: "/admin/tickets", label: "Обращения", icon: "support_agent", match: (path) => path.startsWith("/admin/tickets") },
  { href: "/admin/promos", label: "Промо", icon: "sell", match: (path) => path.startsWith("/admin/promos") },
  { href: "/admin/broadcast", label: "Рассылки", icon: "campaign", match: (path) => path.startsWith("/admin/broadcast") },
  { href: "/admin/referrals", label: "Рефералы", icon: "link", match: (path) => path.startsWith("/admin/referrals") },
  { href: "/admin/bonuses", label: "Бонусы", icon: "casino", match: (path) => path.startsWith("/admin/bonuses") },
];

export function fmtRuDate(value?: string | null): string {
  if (!value) return "-";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "-";
  return dt.toLocaleString("ru-RU");
}
