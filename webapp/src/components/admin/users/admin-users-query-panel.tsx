"use client";

import { Loader2, Search, X } from "lucide-react";
import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
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

type AdminUsersSearchFieldProps = {
  initialQuery: string;
  loading: boolean;
  onQueryChange: (value: string) => void;
};

function AdminUsersSearchField({ initialQuery, loading, onQueryChange }: AdminUsersSearchFieldProps) {
  const [queryDraft, setQueryDraft] = useState(initialQuery);

  useEffect(() => {
    if (queryDraft === initialQuery) return;
    const timer = window.setTimeout(() => onQueryChange(queryDraft), 300);
    return () => window.clearTimeout(timer);
  }, [initialQuery, onQueryChange, queryDraft]);

  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
        {loading ? <Loader2 aria-hidden className="h-4 w-4 animate-spin" /> : <Search aria-hidden className="h-4 w-4" />}
      </span>
      <input
        value={queryDraft}
        onChange={(event) => setQueryDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") onQueryChange(queryDraft);
        }}
        placeholder="Поиск по username, Telegram ID, имени или app install ID"
        className={`${adminFieldClass} pl-9 pr-10 shadow-sm`}
        aria-label="Поиск пользователей"
      />
      {queryDraft ? (
        <button
          type="button"
          className="absolute right-2 top-1/2 inline-flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
          onClick={() => {
            setQueryDraft("");
            onQueryChange("");
          }}
          aria-label="Очистить поиск"
        >
          <X aria-hidden className="h-4 w-4" />
        </button>
      ) : null}
    </div>
  );
}

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
          <h2 className="mt-1 text-lg font-semibold text-slate-900">Поиск аккаунтов и операторские действия</h2>
          <p className="mt-1 text-sm leading-6 text-slate-600">
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
        <AdminUsersSearchField key={filters.q} initialQuery={filters.q} loading={loading} onQueryChange={onQueryChange} />
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

      <div className={`${adminInsetPanelClass} mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600`}>
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
            <p className="mt-1 text-xs leading-5 text-slate-600">
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
          <label className="text-xs text-slate-600">
            Лимит:
            <input
              type="number"
              min={1}
              max={500}
              value={bulkAction.limit}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, limit: Number(event.target.value || 50) }))}
              className={`${adminFieldClass} ml-2 h-8 min-h-8 w-20 rounded-lg px-2 py-1 text-xs`}
            />
          </label>
          <label className="inline-flex items-center gap-2 text-xs text-slate-600">
            <input
              type="checkbox"
              checked={bulkAction.dryRun}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, dryRun: event.target.checked }))}
            />
            Dry run
          </label>
          <label className="inline-flex items-center gap-2 text-xs text-slate-600">
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

        {bulkResult ? <p className="mt-3 text-xs font-medium text-emerald-700">{bulkResult}</p> : null}
      </div>

      {okMessage ? <p className="mt-3 text-sm font-medium text-emerald-700">{okMessage}</p> : null}
    </article>
  );
}
