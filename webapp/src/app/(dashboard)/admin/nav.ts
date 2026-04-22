"use client";

export type AdminNavCategoryId =
  | "diagnostics"
  | "people"
  | "access"
  | "payments"
  | "network"
  | "messaging"
  | "feedback";

export type AdminNavItem = {
  href: string;
  label: string;
  icon: string;
  summary: string;
  categoryId: AdminNavCategoryId;
  match: (path: string) => boolean;
};

export type AdminNavCategory = {
  id: AdminNavCategoryId;
  label: string;
  icon: string;
  description: string;
  primaryHint: string;
};

export const ADMIN_NAV_CATEGORIES: AdminNavCategory[] = [
  {
    id: "diagnostics",
    label: "Diagnostics",
    icon: "monitoring",
    description: "Сводка по свежести метрик, рискам, очередям и общему состоянию сервиса.",
    primaryHint: "Начинайте отсюда, когда нужно быстро понять, где команде требуется внимание.",
  },
  {
    id: "people",
    label: "People",
    icon: "groups",
    description: "Поиск аккаунтов, ручные кейсы, ключи, лимиты и операторские действия.",
    primaryHint: "Основное место для разборов по пользователям и доступу.",
  },
  {
    id: "access",
    label: "Access",
    icon: "key",
    description: "Лояльность, бонусы и стартовые сценарии, влияющие на выдачу и удержание доступа.",
    primaryHint: "Управляйте бонусами и стартовыми сценариями здесь, а не через Telegram.",
  },
  {
    id: "payments",
    label: "Payments",
    icon: "payments",
    description: "Access keys, tariff catalog, hosted checkout guardrails и first-party promo slots.",
    primaryHint: "Платёжная логика должна жить в key-first commerce, а не в legacy gift-code сценариях.",
  },
  {
    id: "network",
    label: "Network",
    icon: "lan",
    description: "Ноды, rollout, таргетинг, drift и транспортная политика.",
    primaryHint: "Изменения сети и транспорта вносите только из веб-админки как primary ops surface.",
  },
  {
    id: "messaging",
    label: "Messaging",
    icon: "campaign",
    description: "Рассылки, новости и retention-шаблоны для коммуникаций.",
    primaryHint: "Массовые касания должны быть заметными, воспроизводимыми и легко проверяемыми.",
  },
  {
    id: "feedback",
    label: "Feedback",
    icon: "support_agent",
    description: "Очередь обращений и рабочая переписка с пользователями.",
    primaryHint: "Telegram остаётся fallback-каналом, а рабочая очередь должна жить здесь.",
  },
];

export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  {
    href: "/admin/dashboard",
    label: "Сводка",
    icon: "space_dashboard",
    summary: "Главная сменная сводка по рискам, нагрузке, retention и очередям.",
    categoryId: "diagnostics",
    match: (path) => path === "/admin" || path.startsWith("/admin/dashboard"),
  },
  {
    href: "/admin/users",
    label: "Пользователи",
    icon: "manage_accounts",
    summary: "Поиск, фильтры, ручные действия, observer watch и политика ключей.",
    categoryId: "people",
    match: (path) => path.startsWith("/admin/users"),
  },
  {
    href: "/admin/bonuses",
    label: "Бонусы",
    icon: "workspace_premium",
    summary: "Лояльность, wheel-конфиг и ручная выдача уровней.",
    categoryId: "access",
    match: (path) => path.startsWith("/admin/bonuses"),
  },
  {
    href: "/admin/referrals",
    label: "Рефералы",
    icon: "link",
    summary: "Стартовые ссылки, referral-очередь и кампании входа.",
    categoryId: "access",
    match: (path) => path.startsWith("/admin/referrals"),
  },
  {
    href: "/admin/promos",
    label: "Ключи и промо",
    icon: "sell",
    summary: "Access keys, tariff catalog, promo-slot scheduling и recovery lookup без public pricing drift.",
    categoryId: "payments",
    match: (path) => path.startsWith("/admin/promos"),
  },
  {
    href: "/admin/nodes",
    label: "Ноды",
    icon: "hub",
    summary: "Health, alerts, drift и ручные действия по инфраструктуре.",
    categoryId: "network",
    match: (path) => path.startsWith("/admin/nodes"),
  },
  {
    href: "/admin/network",
    label: "Rollout",
    icon: "route",
    summary: "Rollout policy, targeting selectors, feeds и recovery order.",
    categoryId: "network",
    match: (path) => path.startsWith("/admin/network"),
  },
  {
    href: "/admin/broadcast",
    label: "Рассылки",
    icon: "campaign",
    summary: "Операционные рассылки, новости и retention templates.",
    categoryId: "messaging",
    match: (path) => path.startsWith("/admin/broadcast"),
  },
  {
    href: "/admin/tickets",
    label: "Обращения",
    icon: "support",
    summary: "Очередь поддержки, triage и ответы оператора.",
    categoryId: "feedback",
    match: (path) => path.startsWith("/admin/tickets"),
  },
];

export const ADMIN_NAV_GROUPS = ADMIN_NAV_CATEGORIES.map((category) => ({
  ...category,
  items: ADMIN_NAV_ITEMS.filter((item) => item.categoryId === category.id),
}));

export function findAdminNavItem(path: string): AdminNavItem {
  return ADMIN_NAV_ITEMS.find((item) => item.match(path)) || ADMIN_NAV_ITEMS[0];
}

export function findAdminNavCategory(path: string) {
  const activeItem = findAdminNavItem(path);
  return ADMIN_NAV_GROUPS.find((group) => group.id === activeItem.categoryId) || ADMIN_NAV_GROUPS[0];
}

export function fmtRuDate(value?: string | null): string {
  if (!value) return "-";
  const dt = new Date(value);
  if (Number.isNaN(dt.getTime())) return "-";
  return dt.toLocaleString("ru-RU");
}
