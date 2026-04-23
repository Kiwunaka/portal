"use client";

import type { Dispatch, SetStateAction } from "react";
import {
  AdminBadge,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
} from "@/components/admin/admin-shell";
import {
  ADMIN_USERS_BULK_ACTION_OPTIONS,
  ADMIN_USERS_BULK_SEGMENT_OPTIONS,
  ADMIN_USERS_OBSERVER_OPTIONS,
  ADMIN_USERS_ORIGIN_OPTIONS,
  ADMIN_USERS_SORT_OPTIONS,
  ADMIN_USERS_STATUS_OPTIONS,
  type AdminUsersBulkActionState,
  type AdminUsersQueryState,
} from "./admin-users-query-state";

type AdminUsersQueryPanelProps = {
  filters: AdminUsersQueryState;
  bulkAction: AdminUsersBulkActionState;
  busy: boolean;
  loading: boolean;
  okMessage: string;
  bulkResult: string;
  pageStart: number;
  pageEnd: number;
  totalRows: number;
  page: number;
  totalPages: number;
  onQueryChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onOriginChange: (value: string) => void;
  onObserverChange: (value: string) => void;
  onSortChange: (value: string) => void;
  onRefresh: () => void;
  onCreateManual: () => void;
  onPrevPage: () => void;
  onNextPage: () => void;
  onRunBulkAction: () => void;
  setBulkAction: Dispatch<SetStateAction<AdminUsersBulkActionState>>;
};

export function AdminUsersQueryPanel({
  filters,
  bulkAction,
  busy,
  loading,
  okMessage,
  bulkResult,
  pageStart,
  pageEnd,
  totalRows,
  page,
  totalPages,
  onQueryChange,
  onStatusChange,
  onOriginChange,
  onObserverChange,
  onSortChange,
  onRefresh,
  onCreateManual,
  onPrevPage,
  onNextPage,
  onRunBulkAction,
  setBulkAction,
}: AdminUsersQueryPanelProps) {
  return (
    <article className={adminPanelClass("neutral")}>
      <div className="mb-4 flex flex-col gap-3 xl:flex-row xl:items-end xl:justify-between">
        <div className="min-w-0">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Раздел пользователей</p>
          <h2 className="mt-1 text-lg font-semibold text-slate-50">Поиск аккаунтов и операторские действия</h2>
          <p className="mt-1 text-sm leading-6 text-slate-400">
            Держите список плотным: фильтры сверху, таблица слева, карточка пользователя справа. Удаление оставляйте только для явных manual/test аккаунтов.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <AdminBadge tone="accent">Показаны {pageStart}-{pageEnd || 0} из {totalRows}</AdminBadge>
            <AdminBadge>Страница {page} / {totalPages}</AdminBadge>
            <AdminBadge tone="warning">Bulk actions запускайте через dry run</AdminBadge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onRefresh} disabled={loading || busy}>
            Обновить
          </button>
          <button className={adminButtonClass("primary", "sm")} type="button" onClick={onCreateManual} disabled={busy}>
            Создать manual/test пользователя
          </button>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 2xl:grid-cols-[minmax(0,1.8fr),repeat(4,minmax(0,0.88fr))]">
        <input
          value={filters.q}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Поиск по username, Telegram ID, имени или app install ID"
          className={adminFieldClass}
        />
        <select value={filters.status} onChange={(event) => onStatusChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select value={filters.origin} onChange={(event) => onOriginChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_ORIGIN_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select value={filters.observerState} onChange={(event) => onObserverChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_OBSERVER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select value={filters.sort} onChange={(event) => onSortChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      <div className={`${adminInsetPanelClass} mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400`}>
        <div>Показаны {pageStart}-{pageEnd || 0} из {totalRows} пользователей. Эффективный статус общий для web и bot admin.</div>
        <div className="flex items-center gap-2">
          <button className={adminButtonClass("ghost", "xs")} type="button" disabled={page <= 1 || loading} onClick={onPrevPage}>
            Назад
          </button>
          <span>Страница {page} / {totalPages}</span>
          <button className={adminButtonClass("ghost", "xs")} type="button" disabled={page >= totalPages || loading} onClick={onNextPage}>
            Дальше
          </button>
        </div>
      </div>

      <div className={`${adminInsetPanelClass} mt-3`}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Массовое действие</p>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              Начинайте с dry run, если изменение затрагивает широкий сегмент или сразу несколько нод.
            </p>
          </div>
          <AdminBadge tone="warning">Bulk</AdminBadge>
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <select
            value={bulkAction.action}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, action: event.target.value as AdminUsersBulkActionState["action"] }))}
            className={adminFieldClass}
          >
            {ADMIN_USERS_BULK_ACTION_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <select
            value={bulkAction.segment}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, segment: event.target.value }))}
            className={adminFieldClass}
          >
            {ADMIN_USERS_BULK_SEGMENT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <input
            value={bulkAction.q}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, q: event.target.value }))}
            placeholder="Дополнительный фильтр внутри выбранного сегмента"
            className={adminFieldClass}
          />
          <input
            value={bulkAction.nodeCodes}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, nodeCodes: event.target.value }))}
            placeholder="Коды нод через запятую"
            className={adminFieldClass}
          />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="text-xs text-slate-400">
            Лимит:
            <input
              type="number"
              min={1}
              max={500}
              value={bulkAction.limit}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, limit: Number(event.target.value || 50) }))}
              className="ml-2 h-8 w-20 rounded-lg border border-[#24313d] bg-[#0a1117] px-2 text-xs text-slate-100 outline-none"
            />
          </label>
          <label className="inline-flex items-center gap-2 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={bulkAction.dryRun}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, dryRun: event.target.checked }))}
            />
            Dry run
          </label>
          <label className="inline-flex items-center gap-2 text-xs text-slate-400">
            <input
              type="checkbox"
              checked={bulkAction.force}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, force: event.target.checked }))}
            />
            Force
          </label>
          <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onRunBulkAction} disabled={busy}>
            Запустить
          </button>
        </div>

        {bulkResult ? <p className="mt-3 text-xs text-emerald-300">{bulkResult}</p> : null}
      </div>

      {okMessage ? <p className="mt-3 text-sm text-emerald-300">{okMessage}</p> : null}
    </article>
  );
}
