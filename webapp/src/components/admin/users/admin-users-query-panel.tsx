"use client";

import type { Dispatch, SetStateAction } from "react";
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
    <article className="glass-card min-w-0 p-4">
      <div className="mb-3 grid gap-2 sm:grid-cols-2 2xl:grid-cols-[minmax(0,1.6fr),repeat(4,minmax(0,0.9fr)),auto,auto]">
        <input
          value={filters.q}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Поиск по username, Telegram ID, имени или app install ID"
          className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
        />
        <select
          value={filters.status}
          onChange={(event) => onStatusChange(event.target.value)}
          className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
        >
          {ADMIN_USERS_STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select
          value={filters.origin}
          onChange={(event) => onOriginChange(event.target.value)}
          className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
        >
          {ADMIN_USERS_ORIGIN_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select
          value={filters.observerState}
          onChange={(event) => onObserverChange(event.target.value)}
          className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
        >
          {ADMIN_USERS_OBSERVER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <select
          value={filters.sort}
          onChange={(event) => onSortChange(event.target.value)}
          className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-sm outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
        >
          {ADMIN_USERS_SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <button className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={onRefresh} disabled={loading || busy}>
          Обновить
        </button>
        <button className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold" type="button" onClick={onCreateManual} disabled={busy}>
          + Создать manual/test пользователя
        </button>
      </div>

      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-violet-200/40 bg-white/70 px-3 py-2 text-xs text-slate-500 dark:border-violet-500/20 dark:bg-white/5">
        <div>
          Показаны {pageStart}-{pageEnd || 0} из {totalRows} пользователей. Эффективный статус общий для web и bot admin.
        </div>
        <div className="flex items-center gap-2">
          <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" disabled={page <= 1 || loading} onClick={onPrevPage}>
            Предыдущая
          </button>
          <span>
            Страница {page} / {totalPages}
          </span>
          <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" disabled={page >= totalPages || loading} onClick={onNextPage}>
            Следующая
          </button>
        </div>
      </div>

      <div className="mb-3 rounded-xl border border-violet-200/40 bg-white/70 p-3 dark:border-violet-500/20 dark:bg-white/5">
        <p className="mb-1 text-xs font-semibold uppercase tracking-[0.08em] text-slate-500">Массовое действие с ключами</p>
        <p className="mb-2 text-xs text-slate-500">Используйте сегменты, выровненные с backend, и начинайте с dry run, если затрагиваете много пользователей.</p>
        <div className="grid gap-2 sm:grid-cols-2">
          <select
            value={bulkAction.action}
            onChange={(event) =>
              setBulkAction((prev) => ({ ...prev, action: event.target.value as AdminUsersBulkActionState["action"] }))
            }
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
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
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
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
            placeholder="Необязательный поиск внутри сегмента"
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <input
            value={bulkAction.nodeCodes}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, nodeCodes: event.target.value }))}
            placeholder="Необязательные коды нод через запятую"
            className="rounded-xl border border-violet-200/50 bg-white/90 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <label className="text-xs text-slate-600 dark:text-slate-300">
            Лимит:
            <input
              type="number"
              min={1}
              max={500}
              value={bulkAction.limit}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, limit: Number(event.target.value || 50) }))}
              className="ml-1 w-20 rounded-lg border border-violet-200/50 bg-white/80 px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
            />
          </label>
          <label className="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={bulkAction.dryRun}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, dryRun: event.target.checked }))}
            />
            Предпросмотр
          </label>
          <label className="inline-flex items-center gap-1 text-xs text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              checked={bulkAction.force}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, force: event.target.checked }))}
            />
            Принудительно
          </label>
          <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={onRunBulkAction} disabled={busy}>
            Запустить массовое действие
          </button>
        </div>
        {bulkResult ? <p className="mt-2 text-xs text-emerald-500">{bulkResult}</p> : null}
      </div>

      {okMessage ? <p className="mb-2 text-sm text-emerald-500">{okMessage}</p> : null}
    </article>
  );
}
