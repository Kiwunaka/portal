"use client";

export type AdminUsersQueryState = {
  q: string;
  status: string;
  origin: string;
  observerState: string;
  sort: string;
  page: number;
};

export type AdminUsersBulkActionState = {
  action: "disable" | "enable" | "reset" | "resync";
  segment: string;
  q: string;
  nodeCodes: string;
  limit: number;
  dryRun: boolean;
  force: boolean;
};

export const ADMIN_USERS_PAGE_SIZE = 80;

export const DEFAULT_ADMIN_USERS_QUERY_STATE: AdminUsersQueryState = {
  q: "",
  status: "all",
  origin: "all",
  observerState: "all",
  sort: "created_desc",
  page: 1,
};

export const ADMIN_USERS_STATUS_OPTIONS = [
  { value: "all", label: "Все статусы" },
  { value: "active", label: "Активные" },
  { value: "expired", label: "Истёкшие" },
  { value: "blocked", label: "Заблокированные" },
  { value: "manual_test", label: "Тестовые" },
];

export const ADMIN_USERS_ORIGIN_OPTIONS = [
  { value: "all", label: "Все источники" },
  { value: "telegram", label: "Telegram" },
  { value: "app", label: "Приложение" },
  { value: "hybrid", label: "Приложение + Telegram" },
  { value: "manual_test", label: "Тестовые" },
];

export const ADMIN_USERS_OBSERVER_OPTIONS = [
  { value: "all", label: "Проверка: все" },
  { value: "ok", label: "Проверка: норма" },
  { value: "watch", label: "Проверка: наблюдать" },
  { value: "suspicious", label: "Проверка: проверить" },
];

export const ADMIN_USERS_SORT_OPTIONS = [
  { value: "created_desc", label: "Сначала новые" },
  { value: "created_asc", label: "Сначала старые" },
  { value: "expiry_asc", label: "Скоро истекают" },
  { value: "expiry_desc", label: "Истекают позже" },
  { value: "name_asc", label: "Имя A-Я" },
];

export const ADMIN_USERS_BULK_ACTION_OPTIONS = [
  { value: "disable", label: "Отключить ключи" },
  { value: "enable", label: "Включить ключи" },
  { value: "reset", label: "Сбросить трафик" },
  { value: "resync", label: "Синхронизировать подписку" },
] as const;

export const ADMIN_USERS_BULK_SEGMENT_OPTIONS = [
  { value: "all", label: "Все пользователи" },
  { value: "active", label: "Активные" },
  { value: "inactive", label: "Неактивные" },
  { value: "expired", label: "Истёкшие" },
  { value: "blocked", label: "Заблокированные" },
  { value: "paid", label: "Платные" },
  { value: "free", label: "Бесплатные" },
  { value: "manual_test", label: "Тестовые" },
] as const;

export function createDefaultBulkActionState(): AdminUsersBulkActionState {
  return {
    action: "disable",
    segment: "active",
    q: "",
    nodeCodes: "",
    limit: 50,
    dryRun: true,
    force: false,
  };
}

function normalizePage(value: string | null | undefined): number {
  const page = Number(value || 1);
  return Number.isFinite(page) && page > 0 ? Math.floor(page) : 1;
}

function normalizeFilterValue(value: string | null | undefined, fallback: string): string {
  const raw = String(value || "").trim();
  return raw || fallback;
}

export function readAdminUsersQueryState(searchParams: { get(name: string): string | null }): AdminUsersQueryState {
  return {
    q: String(searchParams.get("q") || ""),
    status: normalizeFilterValue(searchParams.get("status"), "all"),
    origin: normalizeFilterValue(searchParams.get("origin"), "all"),
    observerState: normalizeFilterValue(searchParams.get("observer_state"), "all"),
    sort: normalizeFilterValue(searchParams.get("sort"), "created_desc"),
    page: normalizePage(searchParams.get("page")),
  };
}

export function serializeAdminUsersQueryState(state: AdminUsersQueryState): string {
  const next = new URLSearchParams();
  const q = state.q.trim();
  if (q) next.set("q", q);
  next.set("status", state.status || "all");
  next.set("origin", state.origin || "all");
  next.set("observer_state", state.observerState || "all");
  next.set("sort", state.sort || "created_desc");
  next.set("page", String(Math.max(1, Math.floor(state.page || 1))));
  return next.toString();
}
