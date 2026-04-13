"use client";

import { fmtRuDate } from "@/app/(dashboard)/admin/nav";
import {
  isManualTestUserLike,
  observerStateBadgeClass,
  observerStateLabel,
  originLabel,
  userStatusBadgeClass,
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
    <article className="glass-card min-w-0 p-4">
      {loading ? <p className="text-sm text-slate-500">Загружаю список пользователей...</p> : null}
      {error ? <p className="mb-2 text-sm text-rose-500">{error}</p> : null}

      <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
        <span>{rows.length ? `Показаны ${pageStart}-${pageEnd} из ${totalRows} пользователей.` : "По текущим фильтрам пользователей нет."}</span>
        <span>Безопасное удаление доступно только для явных manual/test пользователей.</span>
      </div>

      <div className="max-h-[58vh] overflow-x-auto overflow-y-auto rounded-xl border border-white/20">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="px-2 py-2">ID</th>
              <th className="px-2 py-2">Observer</th>
              <th className="px-2 py-2">Пользователь</th>
              <th className="px-2 py-2">Статус</th>
              <th className="px-2 py-2">Источник</th>
              <th className="px-2 py-2">Тариф</th>
              <th className="px-2 py-2">Истекает</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={`summary-${row.tg_id}`}
                className={`cursor-pointer border-t border-white/30 dark:border-white/10 ${
                  row.tg_id === selectedTgId ? "bg-violet-500/10" : isManualTestUserLike(row) ? "bg-violet-500/5" : ""
                }`}
                onClick={() => onSelect(row.tg_id)}
              >
                <td className="px-2 py-2 font-mono text-xs">{row.tg_id}</td>
                <td className="px-2 py-2">
                  <span className={`badge ${observerStateBadgeClass(row.observer_state)}`}>{observerStateLabel(row.observer_state)}</span>
                </td>
                <td className="px-2 py-2">
                  <div className="font-medium">{row.display_name || row.username || "Без имени"}</div>
                  <div className="text-xs text-slate-500">
                    {row.username ? `@${row.username}` : "без username"}
                    {row.linked_telegram_username ? ` | linked @${row.linked_telegram_username}` : ""}
                    {row.app_install_id ? ` | app ${row.app_install_id}` : ""}
                  </div>
                </td>
                <td className="px-2 py-2">
                  <span className={`rounded-full px-2 py-1 text-xs ${userStatusBadgeClass(row.status)}`}>{userStatusLabel(row.status)}</span>
                </td>
                <td className="px-2 py-2">
                  <span className="rounded-full bg-slate-500/10 px-2 py-1 text-xs font-semibold text-slate-600 dark:text-slate-200">
                    {originLabel(row.origin)}
                  </span>
                </td>
                <td className="px-2 py-2">{row.sub_type || "-"}</td>
                <td className="px-2 py-2 text-xs text-slate-600 dark:text-slate-300">{fmtRuDate(row.expiry_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && !error && !rows.length ? (
          <div className="empty-state p-5 text-sm text-slate-500">
            <p>Пользователи не найдены по текущим фильтрам.</p>
            <p className="mt-1 text-xs">Попробуйте очистить поиск или переключить статус, источник и observer-фильтр.</p>
          </div>
        ) : null}
      </div>

      <p className="mt-3 text-xs text-slate-500">Страница {page} из {totalPages}</p>
    </article>
  );
}
