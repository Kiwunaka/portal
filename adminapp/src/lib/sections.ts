export const OPS_GROUPS = [
  { label: "Команда", sections: [{ id: "dashboard", label: "Главная", href: "/" }] },
  {
    label: "Сеть",
    sections: [
      { id: "nodes", label: "Ноды", href: "/nodes" },
      { id: "traffic", label: "Трафик", href: "/traffic" },
      { id: "alerts", label: "Алерты", href: "/alerts" },
      { id: "provider-caps", label: "Лимиты провайдеров", href: "/provider-caps" },
      { id: "emergency-network", label: "Экстренная сеть", href: "/emergency-network" },
      { id: "free-tier", label: "Архив FREE", href: "/free-tier" }
    ]
  },
  {
    label: "Клиенты",
    sections: [
      { id: "users", label: "Пользователи", href: "/users" },
      { id: "online", label: "Сейчас онлайн", href: "/online" },
      { id: "tickets", label: "Тикеты", href: "/tickets" }
    ]
  },
  {
    label: "Деньги и рост",
    sections: [
      { id: "payments", label: "Платежи", href: "/payments" },
      { id: "funnel", label: "Воронка", href: "/funnel" },
      { id: "promos", label: "Промо", href: "/promos" },
      { id: "referrals", label: "Рефералы", href: "/referrals" }
    ]
  },
  {
    label: "Управление",
    sections: [
      { id: "release", label: "Релиз", href: "/release" },
      { id: "broadcast", label: "Рассылка", href: "/broadcast" },
      { id: "news", label: "Новости", href: "/news" }
    ]
  }
] as const;

export type OpsSection = (typeof OPS_GROUPS)[number]["sections"][number];
export const OPS_SECTIONS: readonly OpsSection[] = OPS_GROUPS.flatMap(
  (group): OpsSection[] => [...group.sections]
);

export type OpsSectionId = OpsSection["id"];

export function normalizeOpsSection(section: string): OpsSectionId {
  return OPS_SECTIONS.some((item) => item.id === section) ? (section as OpsSectionId) : "dashboard";
}

export function opsSectionFromPath(pathname: string): OpsSection {
  const raw = pathname.replace(/^\/+|\/+$/g, "");
  const id = normalizeOpsSection(raw || "dashboard");
  return OPS_SECTIONS.find((item) => item.id === id) ?? OPS_SECTIONS[0];
}
