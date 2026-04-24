"use client";

import type { AdminObserverState } from "@/lib/api";

export const ACTIVE_USERS_LABEL = "Estimated active users by IP";
export const ACTIVE_USERS_HINT =
  "Based on live IP footprint, capped by unique IPs in the last 24h. It is an estimate, not a billing count.";

export type KeyPolicyDraft = {
  burst_mbps: string;
  soft_cap_gb: string;
  hard_cap_gb: string;
  notify_soft: boolean;
  notify_hard: boolean;
  auto_disable_on_hard: boolean;
  apply_now: boolean;
};

export function emptyPolicyDraft(): KeyPolicyDraft {
  return {
    burst_mbps: "",
    soft_cap_gb: "",
    hard_cap_gb: "",
    notify_soft: true,
    notify_hard: true,
    auto_disable_on_hard: true,
    apply_now: true,
  };
}

export function fmtTraffic(bytes: number): string {
  const gb = Number(bytes || 0) / 1024 ** 3;
  return `${gb.toFixed(2)} GB`;
}

export function fmtOnline(value: boolean | null | undefined): string {
  if (value === true) return "Online";
  if (value === false) return "Offline";
  return "Unknown";
}

export function parseNullableNumber(input: string): number | null {
  const raw = input.trim();
  if (!raw) return null;
  const value = Number(raw);
  return Number.isFinite(value) ? value : null;
}

export function historyBadgeClass(action: string): string {
  const value = String(action || "").toLowerCase();
  if (value.includes("regen") || value.includes("rotate")) return "badge-warning";
  if (value.includes("disable") || value.includes("block")) return "badge-danger";
  if (value.includes("resync") || value.includes("move") || value.includes("node")) return "badge-info";
  if (value.includes("enable") || value.includes("create")) return "badge-success";
  return "badge-violet";
}

export function actionLabel(action: string): string {
  const value = String(action || "").toLowerCase();
  if (!value) return "-";
  if (value.includes("regen") || value.includes("rotate")) return "Token rotation";
  if (value.includes("reset")) return "Traffic reset";
  if (value.includes("resync")) return "Sub ID resync";
  if (value.includes("move") || value.includes("node")) return "Node operation";
  if (value.includes("disable") || value.includes("block")) return "Block / disable";
  if (value.includes("enable") || value.includes("unblock")) return "Unblock / enable";
  if (value.includes("create")) return "Create";
  if (value.includes("delete") || value.includes("remove")) return "Delete";
  if (value.includes("extend")) return "Extend";
  return action;
}

export function riskLevelLabel(level: string): string {
  const value = String(level || "").toLowerCase();
  if (value === "low") return "Low";
  if (value === "medium" || value === "med") return "Medium";
  if (value === "high") return "High";
  if (value === "critical" || value === "crit") return "Critical";
  return value || "Unknown";
}

export function panelStateLabel(state: string): string {
  const value = String(state || "").toLowerCase();
  if (["ok", "healthy", "fresh"].includes(value)) return "Healthy";
  if (["degraded", "stale", "warn", "warning"].includes(value)) return "Degraded";
  if (["error", "down", "offline", "fail"].includes(value)) return "Error";
  return value || "Unknown";
}

export function ticketStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase().replace(/\s+/g, "_");
  if (value === "open") return "Open";
  if (value === "in_progress") return "In progress";
  if (value === "closed") return "Closed";
  return status || "-";
}

export function userStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "active") return "Active";
  if (value === "blocked") return "Blocked";
  if (value === "manual_test") return "Manual/Test";
  return "Expired";
}

export function userStatusBadgeClass(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "active") return "bg-emerald-500/20 text-emerald-300";
  if (value === "blocked") return "bg-amber-500/20 text-amber-300";
  if (value === "manual_test") return "bg-sky-500/20 text-sky-300";
  return "bg-rose-500/20 text-rose-300";
}

export function originLabel(origin: string): string {
  const value = String(origin || "").toLowerCase();
  if (value === "app") return "App";
  if (value === "hybrid") return "App + Telegram";
  if (value === "manual_test") return "Manual/Test";
  return "Telegram";
}

export function observerStateLabel(state: AdminObserverState | string): string {
  const value = String(state || "").toLowerCase();
  if (value === "watch") return "watch";
  if (value === "suspicious") return "suspicious";
  return "ok";
}

export function observerStateBadgeClass(state: AdminObserverState | string): string {
  const value = String(state || "").toLowerCase();
  if (value === "suspicious") return "badge-danger";
  if (value === "watch") return "badge-warning";
  return "badge-success";
}

export function isManualTestUserLike(user: {
  tg_id?: number | null;
  origin?: string | null;
  status?: string | null;
  is_manual?: boolean | null;
} | null | undefined): boolean {
  if (!user) return false;
  return Boolean(
    user.is_manual ||
      String(user.origin || "").toLowerCase() === "manual_test" ||
      String(user.status || "").toLowerCase() === "manual_test" ||
      Number(user.tg_id || 0) < 0,
  );
}

export function observerHasData(observer:
  | {
      observed_ip_count_24h?: number | null;
      observed_ip_count_7d?: number | null;
      observed_ip_count_30d?: number | null;
      observed_node_count_24h?: number | null;
      observed_node_count_7d?: number | null;
      observed_node_count_30d?: number | null;
      overlap_count_24h?: number | null;
      reasons?: string[] | null;
      recent_ips?: Array<unknown> | null;
      recent_nodes?: Array<unknown> | null;
    }
  | null
  | undefined): boolean {
  if (!observer) return false;
  return Boolean(
    observer.observed_ip_count_24h ||
      observer.observed_ip_count_7d ||
      observer.observed_ip_count_30d ||
      observer.observed_node_count_24h ||
      observer.observed_node_count_7d ||
      observer.observed_node_count_30d ||
      observer.overlap_count_24h ||
      observer.reasons?.length ||
      observer.recent_ips?.length ||
      observer.recent_nodes?.length,
  );
}
