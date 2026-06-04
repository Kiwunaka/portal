"use client";

import { AdminBadge, AdminEmptyState, adminPanelClass, adminTableShellClass } from "@/components/admin/admin-shell";
import { fmtRuDate } from "@/lib/date-format";
import {
  isManualTestUserLike,
  observerStateLabel,
  originLabel,
  userStatusLabel,
} from "./admin-users-format";
import type { AdminUserRow } from "@/lib/api";

type AdminUsersResultsTableProps = {
  rows: AdminUserRow[];
  loading: boolean;
  error: string;
  selectedTgId: number;
  page: number;
  totalPages: number;
  totalRows: number;
  pageStart: number;
  pageEnd: number;
  onSelect: (tgId: number) => void;
};

function observerTone(row: AdminUserRow): "success" | "warning" | "danger" {
  if (row.observer_state === "suspicious") return "danger";
  if (row.observer_state === "watch") return "warning";
  return "success";
}

function statusTone(row: AdminUserRow): "success" | "warning" | "danger" | "neutral" {
  if (row.status === "active") return "success";
  if (row.status === "expired") return "warning";
  if (row.status === "blocked") return "danger";
  return "neutral";
}

function AdminUsersRowsSkeleton() {
  return (
    <>
      {Array.from({ length: 7 }).map((_, index) => (
        <tr key={`skeleton-${index}`} className="border-t border-[#22303c]">
          <td className="px-3 py-3">
            <div className="h-3 w-16 animate-pulse rounded-full bg-slate-700" />
          </td>
          <td className="px-3 py-3">
            <div className="h-6 w-24 animate-pulse rounded-full bg-slate-800" />
          </td>
          <td className="px-3 py-3">
            <div className="h-3 w-36 animate-pulse rounded-full bg-slate-700" />
            <div className="mt-2 h-3 w-48 animate-pulse rounded-full bg-slate-800" />
          </td>
          <td className="px-3 py-3">
            <div className="h-6 w-20 animate-pulse rounded-full bg-slate-800" />
          </td>
          <td className="px-3 py-3">
            <div className="h-6 w-16 animate-pulse rounded-full bg-slate-800" />
          </td>
          <td className="px-3 py-3">
            <div className="h-3 w-20 animate-pulse rounded-full bg-slate-700" />
          </td>
          <td className="px-3 py-3">
            <div className="h-3 w-24 animate-pulse rounded-full bg-slate-700" />
          </td>
        </tr>
      ))}
    </>
  );
}

export function AdminUsersResultsTable({
  rows,
  loading,
  error,
  selectedTgId,
  page,
  totalPages,
  totalRows,
  pageStart,
  pageEnd,
  onSelect,
}: AdminUsersResultsTableProps) {
  return (
    <article className={adminPanelClass("neutral")}>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Результаты</p>
          <p className="mt-1 text-sm font-semibold text-slate-900" aria-live="polite">
            {loading
              ? "Обновляем список пользователей."
              : rows.length
                ? `Показаны ${pageStart}-${pageEnd} из ${totalRows} пользователей.`
                : "По текущим фильтрам пользователей нет."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <AdminBadge>Список</AdminBadge>
          <AdminBadge tone="warning">Удаление только для тестовых аккаунтов</AdminBadge>
        </div>
      </div>

      {loading ? <p className="mb-3 text-sm text-slate-400">Загружаем список пользователей…</p> : null}
      {error ? <p className="mb-3 text-sm text-rose-500">{error}</p> : null}

      <div className={adminTableShellClass}>
        <div className="max-h-[62vh] overflow-x-auto overflow-y-auto">
          <table className="min-w-[900px] text-sm">
            <thead className="sticky top-0 z-[1]">
              <tr className="border-b border-slate-200 bg-slate-50/90 text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-3 py-3">ID</th>
                <th className="px-3 py-3">Проверка</th>
                <th className="px-3 py-3">Пользователь</th>
                <th className="px-3 py-3">Статус</th>
                <th className="px-3 py-3">Источник</th>
                <th className="px-3 py-3">Тариф</th>
                <th className="px-3 py-3">Срок</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <AdminUsersRowsSkeleton />
              ) : (
                rows.map((row) => (
                  <tr
                    key={`summary-${row.tg_id}`}
                    className={`cursor-pointer border-t border-slate-200 align-top transition hover:bg-emerald-50/45 ${
                      row.tg_id === selectedTgId
                        ? "bg-emerald-50/80 text-emerald-950"
                        : isManualTestUserLike(row)
                          ? "bg-sky-50/80"
                          : ""
                    }`}
                    onClick={() => onSelect(row.tg_id)}
                  >
                    <td className="px-3 py-3 font-mono text-xs">{row.tg_id}</td>
                    <td className="px-3 py-3">
                      <AdminBadge tone={observerTone(row)}>{observerStateLabel(row.observer_state)}</AdminBadge>
                    </td>
                    <td className="px-3 py-3">
                      <div className="font-medium">{row.display_name || row.username || "Без имени"}</div>
                      <div className={`mt-1 text-xs ${row.tg_id === selectedTgId ? "text-emerald-800" : "text-slate-500"}`}>
                        {row.username ? `@${row.username}` : "без username"}
                        {row.linked_telegram_username ? ` · Telegram @${row.linked_telegram_username}` : ""}
                        {row.app_install_id ? ` · приложение ${row.app_install_id}` : ""}
                      </div>
                    </td>
                    <td className="px-3 py-3">
                      <AdminBadge tone={statusTone(row)}>{userStatusLabel(row.status)}</AdminBadge>
                    </td>
                    <td className="px-3 py-3">
                      <AdminBadge>{originLabel(row.origin)}</AdminBadge>
                    </td>
                    <td className="px-3 py-3">{row.sub_type || "-"}</td>
                    <td className={`px-3 py-3 text-xs ${row.tg_id === selectedTgId ? "text-emerald-800" : "text-slate-500"}`}>
                      {fmtRuDate(row.expiry_at)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {!loading && !error && !rows.length ? (
            <AdminEmptyState
              className="m-3 min-h-[180px]"
              title="По текущим фильтрам пользователей нет."
              description="Попробуйте очистить поиск или расширить фильтры по статусу, источнику и проверке."
            />
          ) : null}
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-500">Страница {page} из {totalPages}</p>
    </article>
  );
}
