export const OPS_SECTIONS = [
  { id: "dashboard", label: "Главная", href: "/" },
  { id: "users", label: "Пользователи", href: "/users" },
  { id: "online", label: "Сейчас онлайн", href: "/online" },
  { id: "nodes", label: "Ноды", href: "/nodes" },
  { id: "payments", label: "Платежи", href: "/payments" },
  { id: "funnel", label: "Воронка", href: "/funnel" },
  { id: "tickets", label: "Тикеты", href: "/tickets" },
  { id: "alerts", label: "Алерты", href: "/alerts" },
  { id: "traffic", label: "Трафик", href: "/traffic" },
  { id: "free-tier", label: "Free tier", href: "/free-tier" },
  { id: "provider-caps", label: "Лимиты провайдеров", href: "/provider-caps" },
  { id: "promos", label: "Промо", href: "/promos" },
  { id: "referrals", label: "Рефералы", href: "/referrals" },
  { id: "release", label: "Релиз", href: "/release" },
  { id: "broadcast", label: "Рассылка", href: "/broadcast" }
] as const;

export type OpsSectionId = (typeof OPS_SECTIONS)[number]["id"];

export function normalizeOpsSection(section: string): OpsSectionId {
  return OPS_SECTIONS.some((item) => item.id === section) ? (section as OpsSectionId) : "dashboard";
}
