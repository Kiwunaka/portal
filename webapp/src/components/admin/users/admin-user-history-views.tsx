"use client";

import { adminButtonClass, adminInsetPanelClass, adminTableShellClass } from "@/components/admin/admin-shell";
import { fmtRuDate } from "@/lib/date-format";
import type { AdminAuditRow, AdminUserKeyHistoryRow } from "@/lib/api";
import { actionLabel, historyBadgeClass } from "./admin-users-format";

type AdminUserKeyHistoryViewProps = {
  rows: AdminUserKeyHistoryRow[];
  busy: boolean;
  onReload: () => void;
};

type AdminUserAuditViewProps = {
  rows: AdminAuditRow[];
  busy: boolean;
  onReload: () => void;
};

export function AdminUserKeyHistoryView({ rows, busy, onReload }: AdminUserKeyHistoryViewProps) {
  return (
    <div className={`${adminInsetPanelClass} mt-3 text-sm`}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-[color:var(--atlas-text)]">История ключей</p>
          <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-muted)]">Сбросы, обновления и синхронизация ключей по нодам.</p>
        </div>
        <button className={adminButtonClass("secondary", "xs")} type="button" onClick={onReload} disabled={busy}>
          Обновить
        </button>
      </div>

      <div className={adminTableShellClass}>
        <div className="max-h-[44vh] overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--atlas-text-soft)]">
                <th className="px-3 py-3">Дата</th>
                <th className="px-3 py-3">Действие</th>
                <th className="px-3 py-3">Нода</th>
                <th className="px-3 py-3">Кто сделал</th>
                <th className="px-3 py-3">Детали</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-[color:var(--atlas-border)]">
                  <td className="px-3 py-3 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                  <td className="px-3 py-3">
                    <span className={`badge ${historyBadgeClass(row.action)}`}>{actionLabel(row.action)}</span>
                  </td>
                  <td className="px-3 py-3">{row.node_code || "-"}</td>
                  <td className="px-3 py-3">{row.actor_tg_id || "-"}</td>
                  <td className="max-w-[260px] truncate px-3 py-3">{row.meta ? JSON.stringify(row.meta) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length ? <p className="px-3 py-4 text-xs text-[color:var(--atlas-text-muted)]">Истории по ключам пока нет.</p> : null}
        </div>
      </div>
    </div>
  );
}

export function AdminUserAuditView({ rows, busy, onReload }: AdminUserAuditViewProps) {
  return (
    <div className={`${adminInsetPanelClass} mt-3 text-sm`}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-[color:var(--atlas-text)]">Действия операторов</p>
          <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-muted)]">Кто и что менял в выбранном аккаунте.</p>
        </div>
        <button className={adminButtonClass("secondary", "xs")} type="button" onClick={onReload} disabled={busy}>
          Обновить
        </button>
      </div>

      <div className={adminTableShellClass}>
        <div className="max-h-[44vh] overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-[color:var(--atlas-text-soft)]">
                <th className="px-3 py-3">Дата</th>
                <th className="px-3 py-3">Кто сделал</th>
                <th className="px-3 py-3">Действие</th>
                <th className="px-3 py-3">Детали</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-[color:var(--atlas-border)]">
                  <td className="px-3 py-3 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                  <td className="px-3 py-3">{row.actor_tg_id}</td>
                  <td className="px-3 py-3">
                    <span className="badge badge-violet">{actionLabel(row.action)}</span>
                  </td>
                  <td className="max-w-[280px] truncate px-3 py-3">{row.meta ? JSON.stringify(row.meta) : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!rows.length ? <p className="px-3 py-4 text-xs text-[color:var(--atlas-text-muted)]">Действий пока нет.</p> : null}
        </div>
      </div>
    </div>
  );
}
