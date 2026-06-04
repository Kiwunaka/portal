"use client";

import type { AdminObserverState } from "@/lib/api";

export const ACTIVE_USERS_LABEL = "Пользователей по IP сейчас";
export const ACTIVE_USERS_HINT =
  "Оценка по живым IP, но не выше уникальных IP за 24 часа. Не точное число людей.";

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
  if (value === true) return "В сети";
  if (value === false) return "Не в сети";
  return "Неизвестно";
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
  if (value.includes("regen") || value.includes("rotate")) return "Ротация токена";
  if (value.includes("reset")) return "Сброс трафика";
  if (value.includes("resync")) return "Синхронизация подписки";
  if (value.includes("move") || value.includes("node")) return "Перенос ноды";
  if (value.includes("disable") || value.includes("block")) return "Блокировка";
  if (value.includes("enable") || value.includes("unblock")) return "Разблокировка";
  if (value.includes("create")) return "Создание";
  if (value.includes("delete") || value.includes("remove")) return "Удаление";
  if (value.includes("extend")) return "Продление";
  return action;
}

export function riskLevelLabel(level: string): string {
  const value = String(level || "").toLowerCase();
  if (value === "low") return "Низкий";
  if (value === "medium" || value === "med") return "Средний";
  if (value === "high") return "Высокий";
  if (value === "critical" || value === "crit") return "Критичный";
  return value || "Неизвестно";
}

export function panelStateLabel(state: string): string {
  const value = String(state || "").toLowerCase();
  if (["ok", "healthy", "fresh"].includes(value)) return "Норма";
  if (["degraded", "stale", "warn", "warning"].includes(value)) return "Деградация";
  if (["error", "down", "offline", "fail"].includes(value)) return "Ошибка";
  return value || "Неизвестно";
}

export function ticketStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase().replace(/\s+/g, "_");
  if (value === "open") return "Открыт";
  if (value === "in_progress") return "В работе";
  if (value === "closed") return "Закрыт";
  return status || "-";
}

export function userStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "active") return "Активен";
  if (value === "blocked") return "Заблокирован";
  if (value === "manual_test") return "Тестовый";
  return "Истёк";
}

export function userStatusBadgeClass(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "active") return "bg-emerald-500/20 text-emerald-600";
  if (value === "blocked") return "bg-amber-500/20 text-amber-600";
  if (value === "manual_test") return "bg-violet-500/20 text-violet-600";
  return "bg-rose-500/20 text-rose-500";
}

export function originLabel(origin: string): string {
  const value = String(origin || "").toLowerCase();
  if (value === "app") return "Приложение";
  if (value === "hybrid") return "Приложение + Telegram";
  if (value === "manual_test") return "Тестовый";
  return "Telegram";
}

export function observerStateLabel(state: AdminObserverState | string): string {
  const value = String(state || "").toLowerCase();
  if (value === "watch") return "под наблюдением";
  if (value === "suspicious") return "проверить";
  return "норма";
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
