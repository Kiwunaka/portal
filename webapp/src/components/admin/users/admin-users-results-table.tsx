"use client";

import { AdminBadge, AdminEmptyState, adminPanelClass, adminTableShellClass } from "@/components/admin/admin-shell";
import { fmtRuDate } from "@/app/(dashboard)/admin/nav";
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
          <p className="mt-1 text-sm font-semibold text-slate-50">
            {rows.length ? `Показаны ${pageStart}-${pageEnd} из ${totalRows} пользователей.` : "По текущим фильтрам пользователей нет."}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <AdminBadge>Список</AdminBadge>
          <AdminBadge tone="warning">Удаление только для manual/test</AdminBadge>
        </div>
      </div>

      {loading ? <p className="mb-3 text-sm text-slate-400">Загружаем список пользователей…</p> : null}
      {error ? <p className="mb-3 text-sm text-rose-500">{error}</p> : null}

      <div className={adminTableShellClass}>
        <div className="max-h-[62vh] overflow-x-auto overflow-y-auto">
          <table className="min-w-full text-sm">
            <thead className="sticky top-0 z-[1]">
              <tr className="border-b border-[#22303c] bg-[#101821] text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-3 py-3">ID</th>
                <th className="px-3 py-3">Observer</th>
                <th className="px-3 py-3">User</th>
                <th className="px-3 py-3">Status</th>
                <th className="px-3 py-3">Origin</th>
                <th className="px-3 py-3">Plan</th>
                <th className="px-3 py-3">Expiry</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr
                  key={`summary-${row.tg_id}`}
                  className={`cursor-pointer border-t border-[#22303c] align-top transition hover:bg-[#111922] ${
                    row.tg_id === selectedTgId
                      ? "bg-[#18222b] text-white"
                      : isManualTestUserLike(row)
                        ? "bg-sky-950/20"
                        : ""
                  }`}
                  onClick={() => onSelect(row.tg_id)}
                >
                  <td className="px-3 py-3 font-mono text-xs">{row.tg_id}</td>
                  <td className="px-3 py-3">
                    <AdminBadge tone={observerTone(row)}>{`Observer ${observerStateLabel(row.observer_state)}`}</AdminBadge>
                  </td>
                  <td className="px-3 py-3">
                    <div className="font-medium">{row.display_name || row.username || "Без имени"}</div>
                    <div className={`mt-1 text-xs ${row.tg_id === selectedTgId ? "text-white/70" : "text-slate-500"}`}>
                      {row.username ? `@${row.username}` : "без username"}
                      {row.linked_telegram_username ? ` · linked @${row.linked_telegram_username}` : ""}
                      {row.app_install_id ? ` · app ${row.app_install_id}` : ""}
                    </div>
                  </td>
                  <td className="px-3 py-3">
                    <AdminBadge tone={statusTone(row)}>{userStatusLabel(row.status)}</AdminBadge>
                  </td>
                  <td className="px-3 py-3">
                    <AdminBadge>{originLabel(row.origin)}</AdminBadge>
                  </td>
                  <td className="px-3 py-3">{row.sub_type || "-"}</td>
                  <td className={`px-3 py-3 text-xs ${row.tg_id === selectedTgId ? "text-white/70" : "text-slate-400"}`}>
                    {fmtRuDate(row.expiry_at)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {!loading && !error && !rows.length ? (
            <AdminEmptyState
              className="m-3 min-h-[180px]"
              title="По текущим фильтрам пользователей нет."
              description="Попробуйте очистить поиск или расширить фильтры по статусу, источнику и observer-состоянию."
            />
          ) : null}
        </div>
      </div>

      <p className="mt-3 text-xs text-slate-500">Страница {page} из {totalPages}</p>
    </article>
  );
}
