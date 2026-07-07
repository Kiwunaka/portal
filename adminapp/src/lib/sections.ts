export const OPS_SECTIONS = [
  { id: "dashboard", label: "Dashboard", href: "/" },
  { id: "nodes", label: "Nodes", href: "/nodes" },
  { id: "traffic", label: "Traffic", href: "/traffic" },
  { id: "free-tier", label: "Free tier", href: "/free-tier" },
  { id: "provider-caps", label: "Provider caps", href: "/provider-caps" },
  { id: "alerts", label: "Alerts", href: "/alerts" },
  { id: "users", label: "Users", href: "/users" },
  { id: "tickets", label: "Tickets", href: "/tickets" },
  { id: "payments", label: "Payments", href: "/payments" },
  { id: "promos", label: "Promos", href: "/promos" },
  { id: "referrals", label: "Referrals", href: "/referrals" },
  { id: "release", label: "Release", href: "/release" },
  { id: "broadcast", label: "Broadcast", href: "/broadcast" },
  { id: "funnel", label: "Funnel", href: "/funnel" }
] as const;

export type OpsSectionId = (typeof OPS_SECTIONS)[number]["id"];

export function normalizeOpsSection(section: string): OpsSectionId {
  return OPS_SECTIONS.some((item) => item.id === section) ? (section as OpsSectionId) : "dashboard";
}
