"use client";

import { fmtRuDate } from "@/app/(dashboard)/admin/nav";
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
    <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="font-semibold">История ключей (сбросы / ротации / ресинк)</p>
        <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={onReload} disabled={busy}>
          Обновить
        </button>
      </div>
      <p className="mb-3 text-xs text-slate-500">
        Здесь видны низкоуровневые операции с ключами, чтобы быстро понять, когда доступ ротировали, сбрасывали, синхронизировали или переносили между нодами.
      </p>
      <div className="max-h-[44vh] overflow-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="px-2 py-2">Дата</th>
              <th className="px-2 py-2">Действие</th>
              <th className="px-2 py-2">Нода</th>
              <th className="px-2 py-2">Актор</th>
              <th className="px-2 py-2">Метаданные</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                <td className="px-2 py-2 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                <td className="px-2 py-2">
                  <span className={`badge ${historyBadgeClass(row.action)}`}>{actionLabel(row.action)}</span>
                </td>
                <td className="px-2 py-2">{row.node_code || "-"}</td>
                <td className="px-2 py-2">{row.actor_tg_id || "-"}</td>
                <td className="px-2 py-2 max-w-[260px] truncate">{row.meta ? JSON.stringify(row.meta) : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length ? <p className="px-2 py-3 text-xs text-slate-500">История ключей пока пуста.</p> : null}
      </div>
    </div>
  );
}

export function AdminUserAuditView({ rows, busy, onReload }: AdminUserAuditViewProps) {
  return (
    <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="font-semibold">Админ-аудит</p>
        <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={onReload} disabled={busy}>
          Обновить
        </button>
      </div>
      <p className="mb-3 text-xs text-slate-500">
        В этой таблице записаны более высокоуровневые действия оператора над пользователем из admin-поверхностей.
      </p>
      <div className="max-h-[44vh] overflow-auto">
        <table className="min-w-full text-xs">
          <thead>
            <tr className="text-left text-slate-500">
              <th className="px-2 py-2">Дата</th>
              <th className="px-2 py-2">Актор</th>
              <th className="px-2 py-2">Действие</th>
              <th className="px-2 py-2">Метаданные</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id} className="border-t border-white/30 dark:border-white/10">
                <td className="px-2 py-2 whitespace-nowrap">{fmtRuDate(row.created_at)}</td>
                <td className="px-2 py-2">{row.actor_tg_id}</td>
                <td className="px-2 py-2">
                  <span className="badge badge-violet">{actionLabel(row.action)}</span>
                </td>
                <td className="px-2 py-2 max-w-[280px] truncate">{row.meta ? JSON.stringify(row.meta) : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!rows.length ? <p className="px-2 py-3 text-xs text-slate-500">Записей аудита пока нет.</p> : null}
      </div>
    </div>
  );
}
