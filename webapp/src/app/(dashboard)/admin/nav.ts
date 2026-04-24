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
    label: "Диагностика",
    icon: "monitoring",
    description: "Состояние сервиса, очереди, свежесть метрик и предупреждения.",
    primaryHint: "Начинайте смену здесь, чтобы быстро увидеть здоровье и инциденты.",
  },
  {
    id: "people",
    label: "Пользователи",
    icon: "groups",
    description: "Поиск людей, состояние доступа, привязки и ручные действия.",
    primaryHint: "Основной раздел для разбора учетной записи и передачи в поддержку.",
  },
  {
    id: "access",
    label: "Доступ",
    icon: "key",
    description: "Бонусы, приглашения, лояльность и жизненный цикл доступа.",
    primaryHint: "Используйте для начислений и управляемых изменений доступа.",
  },
  {
    id: "payments",
    label: "Оплата",
    icon: "payments",
    description: "Ключи доступа, промо-правила, оплата и слоты предложений.",
    primaryHint: "Выдача платного доступа и промо-механики должны оставаться проверяемыми.",
  },
  {
    id: "network",
    label: "Сеть",
    icon: "lan",
    description: "Ноды, маршруты, правила трафика и состояние инфраструктуры.",
    primaryHint: "Сетевые изменения сначала оформляйте в web admin; Telegram только резервный канал.",
  },
  {
    id: "messaging",
    label: "Сообщения",
    icon: "campaign",
    description: "Рассылки, шаблоны, предпросмотр доставки и live-обновления.",
    primaryHint: "Массовые сообщения требуют предпросмотра, выбора аудитории и подтверждения.",
  },
  {
    id: "feedback",
    label: "Обращения",
    icon: "support_agent",
    description: "Очередь поддержки, модерация отзывов и ответы оператора.",
    primaryHint: "Держите поддержку в отслеживаемом разделе, а не в разрозненных чатах.",
  },
];

export const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  {
    href: "/admin/dashboard",
    label: "Сводка",
    icon: "space_dashboard",
    summary: "Короткая сводка здоровья, очередей и последних сигналов.",
    categoryId: "diagnostics",
    match: (path) => path === "/admin" || path.startsWith("/admin/dashboard"),
  },
  {
    href: "/admin/users",
    label: "Пользователи",
    icon: "manage_accounts",
    summary: "Поиск людей, проверка доступа и точечные ручные операции.",
    categoryId: "people",
    match: (path) => path.startsWith("/admin/users"),
  },
  {
    href: "/admin/bonuses",
    label: "Бонусы",
    icon: "workspace_premium",
    summary: "Колесо, уровни лояльности, ручные начисления и правила наград.",
    categoryId: "access",
    match: (path) => path.startsWith("/admin/bonuses"),
  },
  {
    href: "/admin/referrals",
    label: "Приглашения",
    icon: "link",
    summary: "Стартовые ссылки, кампании, очередь атрибуции и начисления.",
    categoryId: "access",
    match: (path) => path.startsWith("/admin/referrals"),
  },
  {
    href: "/admin/promos",
    label: "Ключи и промо",
    icon: "sell",
    summary: "Выдача ключей доступа, промо-слоты и совместимость.",
    categoryId: "payments",
    match: (path) => path.startsWith("/admin/promos"),
  },
  {
    href: "/admin/nodes",
    label: "Ноды",
    icon: "hub",
    summary: "Здоровье нод, предупреждения и инфраструктурные действия.",
    categoryId: "network",
    match: (path) => path.startsWith("/admin/nodes"),
  },
  {
    href: "/admin/network",
    label: "Маршруты",
    icon: "route",
    summary: "Маршруты трафика, правила и порядок переключений.",
    categoryId: "network",
    match: (path) => path.startsWith("/admin/network"),
  },
  {
    href: "/admin/broadcast",
    label: "Рассылки",
    icon: "campaign",
    summary: "Отправка обновлений с предпросмотром и счетчиками доставки.",
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
