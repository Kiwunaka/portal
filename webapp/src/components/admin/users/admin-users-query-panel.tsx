"use client";

import { useEffect, useState, type Dispatch, type SetStateAction } from "react";
import {
  AdminBadge,
  AdminPanelHeader,
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

const ADMIN_USERS_SEARCH_DEBOUNCE_MS = 350;

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
  const [draftQuery, setDraftQuery] = useState(filters.q);

  useEffect(() => {
    setDraftQuery(filters.q);
  }, [filters.q]);

  useEffect(() => {
    if (draftQuery === filters.q) return;
    const timer = window.setTimeout(() => {
      onQueryChange(draftQuery);
    }, ADMIN_USERS_SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [draftQuery, filters.q, onQueryChange]);

  return (
    <article className={adminPanelClass("neutral")}>
      <AdminPanelHeader
        eyebrow="people"
        title="User search and access operations"
        description="Filters stay at the top, results stay left, and the selected account opens in the right detail panel."
        actions={
          <>
            <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onRefresh} disabled={loading || busy}>
              Обновить
            </button>
            <button className={adminButtonClass("primary", "sm")} type="button" onClick={onCreateManual} disabled={busy}>
              Создать manual/test пользователя
            </button>
          </>
        }
      />

      <div className="mb-3 flex flex-wrap gap-2">
        <AdminBadge tone="accent">Диапазон {pageStart}-{pageEnd || 0} / {totalRows}</AdminBadge>
        <AdminBadge>Страница {page} / {totalPages}</AdminBadge>
        <AdminBadge tone="warning">bulk actions default to dry run</AdminBadge>
      </div>

      <div className="grid gap-2 sm:grid-cols-2 2xl:grid-cols-[minmax(0,1.8fr),repeat(4,minmax(0,0.88fr))]">
        <input
          value={draftQuery}
          onChange={(event) => setDraftQuery(event.target.value)}
          placeholder="Поиск по username, Telegram ID, имени или app install ID"
          className={adminFieldClass}
        />
        <select value={filters.status} onChange={(event) => onStatusChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select value={filters.origin} onChange={(event) => onOriginChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_ORIGIN_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select value={filters.observerState} onChange={(event) => onObserverChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_OBSERVER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
        <select value={filters.sort} onChange={(event) => onSortChange(event.target.value)} className={adminFieldClass}>
          {ADMIN_USERS_SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>
      </div>

      <div className={`${adminInsetPanelClass} mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400`}>
        <div>Effective status is shared by web admin and bot admin. Deletion remains limited to explicit manual/test accounts.</div>
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
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">bulk key action</p>
            <p className="mt-1 text-xs leading-5 text-slate-400">
              Use dry run first for any segment wider than one account. Turn off dry run only after reviewing matched and changed counts.
            </p>
          </div>
          <AdminBadge tone={bulkAction.dryRun ? "success" : "warning"}>{bulkAction.dryRun ? "dry run" : "live action"}</AdminBadge>
        </div>

        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          <select
            value={bulkAction.action}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, action: event.target.value as AdminUsersBulkActionState["action"] }))}
            className={adminFieldClass}
          >
            {ADMIN_USERS_BULK_ACTION_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <select
            value={bulkAction.segment}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, segment: event.target.value }))}
            className={adminFieldClass}
          >
            {ADMIN_USERS_BULK_SEGMENT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          <input
            value={bulkAction.q}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, q: event.target.value }))}
            placeholder="Optional filter inside selected segment"
            className={adminFieldClass}
          />
          <input
            value={bulkAction.nodeCodes}
            onChange={(event) => setBulkAction((prev) => ({ ...prev, nodeCodes: event.target.value }))}
            placeholder="Node codes, comma-separated"
            className={adminFieldClass}
          />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="text-xs text-slate-400">
            Limit
            <input
              type="number"
              min={1}
              max={500}
              value={bulkAction.limit}
              onChange={(event) => setBulkAction((prev) => ({ ...prev, limit: Number(event.target.value || 50) }))}
              className="ml-2 h-8 w-20 rounded-lg border border-[#c6e6db] bg-[#ffffff] px-2 text-xs text-slate-100 outline-none"
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
            Run bulk action
          </button>
        </div>

        {bulkResult ? <p className="mt-3 text-xs text-emerald-300">{bulkResult}</p> : null}
      </div>

      {okMessage ? <p className="mt-3 text-sm text-emerald-300">{okMessage}</p> : null}
    </article>
  );
}
