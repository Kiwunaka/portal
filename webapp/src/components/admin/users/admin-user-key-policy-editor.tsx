"use client";

import type { Dispatch, SetStateAction } from "react";
import { adminButtonClass, adminCheckboxLabelClass, adminFieldClass, adminInsetPanelClass } from "@/components/admin/admin-shell";
import type { AdminUserKey } from "@/lib/api";
import { fmtTraffic, parseNullableNumber, type KeyPolicyDraft } from "./admin-users-format";

type AdminUserKeyPolicyEditorProps = {
  selectedTgId: number;
  keys: AdminUserKey[];
  policyDrafts: Record<string, KeyPolicyDraft>;
  busy: boolean;
  keyBusy: string;
  policyBusy: string;
  onReload: () => void;
  onRunKeyAction: (key: AdminUserKey, action: "toggle" | "reset" | "resync") => void;
  onSavePolicy: (nodeCode: string) => void;
  setPolicyDrafts: Dispatch<SetStateAction<Record<string, KeyPolicyDraft>>>;
};

export function AdminUserKeyPolicyEditor({
  selectedTgId,
  keys,
  policyDrafts,
  busy,
  keyBusy,
  policyBusy,
  onReload,
  onRunKeyAction,
  onSavePolicy,
  setPolicyDrafts,
}: AdminUserKeyPolicyEditorProps) {
  return (
    <div className={`${adminInsetPanelClass} mt-3 text-sm`}>
      <div className="mb-3 flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-slate-50">Ключи и политика по нодам</p>
          <p className="mt-1 text-xs leading-5 text-slate-400">Управляйте ключами, сбросом трафика, синхронизацией sub ID и лимитами без выхода из аккаунта.</p>
        </div>
        <button className={adminButtonClass("secondary", "xs")} type="button" onClick={onReload} disabled={busy || !!keyBusy || !!policyBusy}>
          Обновить
        </button>
      </div>

      <div className="space-y-3">
        {keys.map((key) => {
          const draft = policyDrafts[key.node_code];
          if (!draft) return null;

          return (
            <div key={key.node_code} className="rounded-xl border border-[#22303c] bg-[#0b1218] p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-semibold text-slate-50">
                    {key.node_name || key.node_code}
                    <span className="ml-2 text-xs text-slate-500">{key.node_code}</span>
                  </p>
                  <p className="text-xs text-slate-400">
                    {key.exists ? "Ключ присутствует" : "Ключ отсутствует"} | {key.enabled ? "включён" : "выключен"} | {key.online ? "online" : "offline"}
                  </p>
                  <p className="text-xs text-slate-400">
                    Трафик: {fmtTraffic(key.total_bytes)} | соединений сейчас: {key.current_connections}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunKeyAction(key, "toggle")} disabled={busy || keyBusy === `${key.node_code}:toggle`}>
                    {key.enabled ? "Выключить" : "Включить"}
                  </button>
                  <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunKeyAction(key, "reset")} disabled={busy || keyBusy === `${key.node_code}:reset`}>
                    Сбросить трафик
                  </button>
                  <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunKeyAction(key, "resync")} disabled={busy || keyBusy === `${key.node_code}:resync`}>
                    Синхронизировать sub ID
                  </button>
                </div>
              </div>

              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                <input
                  value={draft.burst_mbps}
                  onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, burst_mbps: event.target.value } }))}
                  placeholder="Burst-лимит, Мбит/с"
                  className={adminFieldClass}
                />
                <input
                  value={draft.soft_cap_gb}
                  onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, soft_cap_gb: event.target.value } }))}
                  placeholder="Мягкий лимит, ГБ"
                  className={adminFieldClass}
                />
                <input
                  value={draft.hard_cap_gb}
                  onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, hard_cap_gb: event.target.value } }))}
                  placeholder="Жесткий лимит, ГБ"
                  className={adminFieldClass}
                />
              </div>

              <div className="mt-3 flex flex-wrap items-center gap-3">
                <label className={adminCheckboxLabelClass}>
                  <input
                    type="checkbox"
                    checked={draft.notify_soft}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_soft: event.target.checked } }))}
                  />
                  Уведомить на мягком лимите
                </label>
                <label className={adminCheckboxLabelClass}>
                  <input
                    type="checkbox"
                    checked={draft.notify_hard}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_hard: event.target.checked } }))}
                  />
                  Уведомить на жестком лимите
                </label>
                <label className={adminCheckboxLabelClass}>
                  <input
                    type="checkbox"
                    checked={draft.auto_disable_on_hard}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, auto_disable_on_hard: event.target.checked } }))}
                  />
                  Автоотключение на жестком лимите
                </label>
                <label className={adminCheckboxLabelClass}>
                  <input
                    type="checkbox"
                    checked={draft.apply_now}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, apply_now: event.target.checked } }))}
                  />
                  Применить сейчас
                </label>
                <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => onSavePolicy(key.node_code)} disabled={policyBusy === key.node_code}>
                  {policyBusy === key.node_code ? "..." : "Сохранить политику"}
                </button>
              </div>

              <div className="mt-2 text-xs text-slate-400">
                Черновик: burst {parseNullableNumber(draft.burst_mbps) ?? "нет"}, мягкий {parseNullableNumber(draft.soft_cap_gb) ?? "нет"}, жесткий {parseNullableNumber(draft.hard_cap_gb) ?? "нет"}.
              </div>
            </div>
          );
        })}
      </div>

      {!keys.length ? <p className="mt-3 text-xs text-slate-400">Для tg_id {selectedTgId} ключи пока не созданы.</p> : null}
    </div>
  );
}
