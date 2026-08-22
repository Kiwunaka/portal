export const OPS_WORKSPACES = [
  {
    id: "shift",
    label: "Моя смена",
    shortLabel: "Смена",
    href: "/shift",
    sections: [{ id: "dashboard", label: "Главная", href: "/" }]
  },
  {
    id: "support",
    label: "Пользователи и поддержка",
    shortLabel: "Поддержка",
    href: "/support",
    sections: [
      { id: "users", label: "Пользователи", href: "/users" },
      { id: "online", label: "Сейчас онлайн", href: "/online" },
      { id: "tickets", label: "Тикеты", href: "/tickets" }
    ]
  },
  {
    id: "network",
    label: "Сеть и инциденты",
    shortLabel: "Сеть",
    href: "/network",
    sections: [
      { id: "nodes", label: "Ноды", href: "/nodes" },
      { id: "traffic", label: "Трафик", href: "/traffic" },
      { id: "alerts", label: "Алерты", href: "/alerts" },
      { id: "incidents", label: "Incident Room", href: "/incidents" },
      { id: "provider-caps", label: "Лимиты провайдеров", href: "/provider-caps" },
      { id: "emergency-network", label: "Экстренная сеть", href: "/emergency-network" }
    ]
  },
  {
    id: "money",
    label: "Деньги и доступ",
    shortLabel: "Деньги",
    href: "/money",
    sections: [
      { id: "payments", label: "Платежи", href: "/payments" },
      { id: "access", label: "Доступ", href: "/access" },
      { id: "free-tier", label: "Архив FREE", href: "/free-tier" },
      { id: "promos", label: "Промокоды", href: "/promos" }
    ]
  },
  {
    id: "growth",
    label: "Рост и коммуникации",
    shortLabel: "Рост",
    href: "/growth",
    sections: [
      { id: "funnel", label: "Воронка", href: "/funnel" },
      { id: "bonuses", label: "Бонусы", href: "/bonuses" },
      { id: "programs", label: "Программы", href: "/programs" },
      { id: "referrals", label: "Рефералы", href: "/referrals" },
      { id: "broadcast", label: "Рассылка", href: "/broadcast" },
      { id: "news", label: "Новости", href: "/news" }
    ]
  },
  {
    id: "releases",
    label: "Релизы и клиенты",
    shortLabel: "Релизы",
    href: "/releases",
    sections: [{ id: "release", label: "Релиз", href: "/release" }]
  },
  {
    id: "governance",
    label: "Управление системой",
    shortLabel: "Система",
    href: "/governance",
    sections: []
  }
] as const;

export type OpsWorkspace = (typeof OPS_WORKSPACES)[number];
export type OpsWorkspaceId = OpsWorkspace["id"];
export type OpsCapabilitySection = OpsWorkspace["sections"][number];
export type OpsSectionId = OpsWorkspaceId | OpsCapabilitySection["id"];
export type OpsSection = { id: OpsSectionId; label: string; href: string; workspace: OpsWorkspaceId };

export const OPS_SECTIONS: readonly OpsSection[] = OPS_WORKSPACES.flatMap((workspace) => [
  {
    id: workspace.id,
    label: workspace.label,
    href: workspace.href,
    workspace: workspace.id
  },
  ...workspace.sections.map((section) => ({
    ...section,
    workspace: workspace.id
  }))
]);

// Compatibility alias for callers that still speak in navigation groups.
export const OPS_GROUPS = OPS_WORKSPACES;

export function normalizeOpsSection(section: string): OpsSectionId {
  return OPS_SECTIONS.some((item) => item.id === section) ? (section as OpsSectionId) : "dashboard";
}

export function opsSectionFromPath(pathname: string): OpsSection {
  const normalizedPath = pathname === "/" ? "/" : pathname.replace(/\/+$/, "");
  return OPS_SECTIONS.find((item) => item.href === normalizedPath) ?? OPS_SECTIONS.find((item) => item.id === "dashboard")!;
}

export function opsWorkspaceForSection(section: OpsSectionId): OpsWorkspace {
  const workspaceId = OPS_SECTIONS.find((item) => item.id === section)?.workspace ?? "shift";
  return OPS_WORKSPACES.find((workspace) => workspace.id === workspaceId) ?? OPS_WORKSPACES[0];
}
