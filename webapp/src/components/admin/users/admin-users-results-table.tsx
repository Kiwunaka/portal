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

function AdminUsersCardsSkeleton() {
  return (
    <div className="space-y-3 lg:hidden">
      {Array.from({ length: 4 }).map((_, index) => (
        <article key={`mobile-skeleton-${index}`} className="rounded-[var(--pokrov-radius-card)] border border-slate-200/60 bg-white/70 p-4">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <div className="h-3 w-24 animate-pulse rounded-full bg-slate-200" />
              <div className="mt-3 h-5 w-40 animate-pulse rounded-full bg-slate-100" />
            </div>
            <div className="h-7 w-20 animate-pulse rounded-full bg-slate-100" />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-2">
            {Array.from({ length: 4 }).map((_, itemIndex) => (
              <div key={itemIndex} className="rounded-2xl border border-slate-100 bg-slate-50/80 p-3">
                <div className="h-2.5 w-14 animate-pulse rounded-full bg-slate-200" />
                <div className="mt-2 h-3 w-20 animate-pulse rounded-full bg-slate-100" />
              </div>
            ))}
          </div>
        </article>
      ))}
    </div>
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

      {loading ? <AdminUsersCardsSkeleton /> : null}
      {!loading && rows.length ? (
        <div className="space-y-3 lg:hidden">
          {rows.map((row) => (
            <button
              key={`mobile-${row.tg_id}`}
              type="button"
              className={`w-full rounded-[var(--pokrov-radius-card)] border p-4 text-left transition ${
                row.tg_id === selectedTgId
                  ? "border-emerald-300 bg-emerald-50/90 text-emerald-950"
                  : isManualTestUserLike(row)
                    ? "border-sky-200 bg-sky-50/80"
                    : "border-slate-200/70 bg-white/80 hover:border-emerald-200 hover:bg-emerald-50/35"
              }`}
              onClick={() => onSelect(row.tg_id)}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-mono text-xs text-slate-500">ID {row.tg_id}</p>
                  <p className="mt-1 truncate text-base font-semibold">{row.display_name || row.username || "Без имени"}</p>
                  <p className="mt-1 truncate text-xs text-slate-500">
                    {row.username ? `@${row.username}` : "без username"}
                    {row.linked_telegram_username ? ` · tg @${row.linked_telegram_username}` : ""}
                  </p>
                </div>
                <AdminBadge tone={statusTone(row)}>{userStatusLabel(row.status)}</AdminBadge>
              </div>
              <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
                <div className="rounded-2xl border border-slate-200/60 bg-white/70 p-3">
                  <p className="text-slate-500">Проверка</p>
                  <div className="mt-2">
                    <AdminBadge tone={observerTone(row)}>{observerStateLabel(row.observer_state)}</AdminBadge>
                  </div>
                </div>
                <div className="rounded-2xl border border-slate-200/60 bg-white/70 p-3">
                  <p className="text-slate-500">Источник</p>
                  <p className="mt-2 font-semibold text-slate-800">{originLabel(row.origin)}</p>
                </div>
                <div className="rounded-2xl border border-slate-200/60 bg-white/70 p-3">
                  <p className="text-slate-500">Тариф</p>
                  <p className="mt-2 font-semibold text-slate-800">{row.sub_type || "-"}</p>
                </div>
                <div className="rounded-2xl border border-slate-200/60 bg-white/70 p-3">
                  <p className="text-slate-500">Срок</p>
                  <p className="mt-2 font-semibold text-slate-800">{fmtRuDate(row.expiry_at)}</p>
                </div>
              </div>
            </button>
          ))}
        </div>
      ) : null}
      {!loading && !error && !rows.length ? (
        <AdminEmptyState
          className="min-h-[180px] lg:hidden"
          title="По текущим фильтрам пользователей нет."
          description="Очистите поиск или расширьте фильтры по статусу, источнику и проверке."
        />
      ) : null}

      <div className={`${adminTableShellClass} hidden lg:block`}>
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
