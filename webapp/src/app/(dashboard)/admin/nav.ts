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
    label: "Рабочий стол",
    icon: "monitoring",
    description: "Сводка смены, релизные gates, метрики и риски.",
    primaryHint: "Начинайте отсюда: сначала очередь, свежесть данных и критичные сигналы.",
  },
  {
    id: "people",
    label: "Люди",
    icon: "groups",
    description: "Поиск аккаунтов, статусы доступа и ручные действия.",
    primaryHint: "Основное место для разборов по пользователям и подпискам.",
  },
  {
    id: "access",
    label: "Доступ и промо",
    icon: "key",
    description: "Бонусы, рефералы и стартовые воронки доступа.",
    primaryHint: "Здесь настраиваются бонусы и стартовые предложения без ручной беготни.",
  },
  {
    id: "payments",
    label: "Оплата",
    icon: "payments",
    description: "Тарифы, оплаты, промокоды и правила выдачи.",
    primaryHint: "Здесь контролируются деньги, тарифы и промо-механики.",
  },
  {
    id: "network",
    label: "Сеть",
    icon: "lan",
    description: "Ноды, точки доступа и текущее состояние сети.",
    primaryHint: "Все изменения по сети лучше делать из веб-админки, а не через обходные пути.",
  },
  {
    id: "messaging",
    label: "Сообщения",
    icon: "campaign",
    description: "Рассылки, новости и шаблоны сообщений.",
    primaryHint: "Массовые сообщения должны запускаться и проверяться из одного места.",
  },
  {
    id: "feedback",
    label: "Поддержка",
    icon: "support_agent",
    description: "Очередь обращений и рабочая переписка с пользователями.",
    primaryHint: "Рабочая очередь поддержки должна жить здесь, а не расползаться по чатам.",
  },
];

export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  {
    href: "/admin/dashboard",
    label: "Сводка",
    icon: "space_dashboard",
    summary: "Главный экран со сводкой по сервису и очередям.",
    categoryId: "diagnostics",
    match: (path) => path === "/admin" || path.startsWith("/admin/dashboard"),
  },
  {
    href: "/admin/release",
    label: "Релиз",
    icon: "rocket_launch",
    summary: "Beta GO, runtime-ссылки, оплата, email и ручные внешние gates.",
    categoryId: "diagnostics",
    match: (path) => path.startsWith("/admin/release"),
  },
  {
    href: "/admin/users",
    label: "Пользователи",
    icon: "manage_accounts",
    summary: "Поиск пользователей, фильтры и ручные действия.",
    categoryId: "people",
    match: (path) => path.startsWith("/admin/users"),
  },
  {
    href: "/admin/bonuses",
    label: "Бонусы",
    icon: "workspace_premium",
    summary: "Бонусы, уровни и ручная выдача доступа.",
    categoryId: "access",
    match: (path) => path.startsWith("/admin/bonuses"),
  },
  {
    href: "/admin/referrals",
    label: "Рефералы",
    icon: "link",
    summary: "Реферальные ссылки и стартовые воронки.",
    categoryId: "access",
    match: (path) => path.startsWith("/admin/referrals"),
  },
  {
    href: "/admin/promos",
    label: "Ключи и промо",
    icon: "sell",
    summary: "Промокоды, тарифы и правила для оплаты.",
    categoryId: "payments",
    match: (path) => path.startsWith("/admin/promos"),
  },
  {
    href: "/admin/payments",
    label: "Платёжный журнал",
    icon: "receipt_long",
    summary: "Заказы, callback провайдера, ручная проверка и сверка.",
    categoryId: "payments",
    match: (path) => path.startsWith("/admin/payments"),
  },
  {
    href: "/admin/nodes",
    label: "Ноды",
    icon: "hub",
    summary: "Состояние нод, тревоги и действия по инфраструктуре.",
    categoryId: "network",
    match: (path) => path.startsWith("/admin/nodes"),
  },
  {
    href: "/admin/network",
    label: "Маршруты",
    icon: "route",
    summary: "Маршруты, правила трафика и порядок переключения.",
    categoryId: "network",
    match: (path) => path.startsWith("/admin/network"),
  },
  {
    href: "/admin/broadcast",
    label: "Рассылки",
    icon: "campaign",
    summary: "Рассылки, новости и готовые шаблоны.",
    categoryId: "messaging",
    match: (path) => path.startsWith("/admin/broadcast"),
  },
  {
    href: "/admin/tickets",
    label: "Обращения",
    icon: "support",
    summary: "Очередь поддержки и ответы оператора.",
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
