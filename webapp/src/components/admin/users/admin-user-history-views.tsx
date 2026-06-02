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
          <p className="text-sm font-semibold text-slate-900">Key history</p>
          <p className="mt-1 text-xs leading-5 text-slate-400">Low-level key operations, including resets, rotations, and resync actions across nodes.</p>
        </div>
        <button className={adminButtonClass("secondary", "xs")} type="button" onClick={onReload} disabled={busy}>
          Reload
        </button>
      </div>

      <div className={adminTableShellClass}>
        <div className="max-h-[44vh] overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/90 text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-3 py-3">Date</th>
                <th className="px-3 py-3">Action</th>
                <th className="px-3 py-3">Node</th>
                <th className="px-3 py-3">Actor</th>
                <th className="px-3 py-3">Metadata</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-[#22303c]">
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
          {!rows.length ? <p className="px-3 py-4 text-xs text-slate-400">No key history yet.</p> : null}
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
          <p className="text-sm font-semibold text-slate-900">Admin audit</p>
          <p className="mt-1 text-xs leading-5 text-slate-400">Higher-level operator actions taken against the selected account inside admin surfaces.</p>
        </div>
        <button className={adminButtonClass("secondary", "xs")} type="button" onClick={onReload} disabled={busy}>
          Reload
        </button>
      </div>

      <div className={adminTableShellClass}>
        <div className="max-h-[44vh] overflow-auto">
          <table className="min-w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50/90 text-left text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                <th className="px-3 py-3">Date</th>
                <th className="px-3 py-3">Actor</th>
                <th className="px-3 py-3">Action</th>
                <th className="px-3 py-3">Metadata</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id} className="border-t border-[#22303c]">
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
          {!rows.length ? <p className="px-3 py-4 text-xs text-slate-400">No audit records yet.</p> : null}
        </div>
      </div>
    </div>
  );
}
