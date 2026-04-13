"use client";

import type { Dispatch, SetStateAction } from "react";
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
    <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
      <div className="mb-2 flex items-center justify-between gap-2">
        <p className="font-semibold">Ключи и лимиты</p>
        <button className="outline-btn rounded-xl px-3 py-1.5 text-xs font-semibold" type="button" onClick={onReload} disabled={busy || !!keyBusy || !!policyBusy}>
          Обновить
        </button>
      </div>
      <p className="mb-3 text-xs text-slate-500">
        Ключи на каждой ноде можно включать, отключать, синхронизировать и отдельно настраивать политику трафика.
      </p>
      <div className="space-y-3">
        {keys.map((key) => {
          const draft = policyDrafts[key.node_code];
          if (!draft) return null;

          return (
            <div key={key.node_code} className="rounded-xl border border-white/40 bg-white/70 p-3 dark:border-white/10 dark:bg-white/5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-semibold">
                    {key.node_name || key.node_code}
                    <span className="ml-2 text-xs text-slate-500">{key.node_code}</span>
                  </p>
                  <p className="text-xs text-slate-500">
                    {key.exists ? "Ключ присутствует" : "Ключ отсутствует"} | {key.enabled ? "включён" : "выключен"} | {key.online ? "online" : "offline"}
                  </p>
                  <p className="text-xs text-slate-500">
                    Трафик: {fmtTraffic(key.total_bytes)} | current connections: {key.current_connections}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button className="outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" onClick={() => onRunKeyAction(key, "toggle")} disabled={busy || keyBusy === `${key.node_code}:toggle`}>
                    {key.enabled ? "Выключить" : "Включить"}
                  </button>
                  <button className="outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" onClick={() => onRunKeyAction(key, "reset")} disabled={busy || keyBusy === `${key.node_code}:reset`}>
                    Сбросить трафик
                  </button>
                  <button className="outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" onClick={() => onRunKeyAction(key, "resync")} disabled={busy || keyBusy === `${key.node_code}:resync`}>
                    Resync sub ID
                  </button>
                </div>
              </div>

              <div className="mt-3 grid gap-2 sm:grid-cols-3">
                <input
                  value={draft.burst_mbps}
                  onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, burst_mbps: event.target.value } }))}
                  placeholder="Burst-лимит (Mbps)"
                  className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <input
                  value={draft.soft_cap_gb}
                  onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, soft_cap_gb: event.target.value } }))}
                  placeholder="Soft cap (ГБ)"
                  className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
                <input
                  value={draft.hard_cap_gb}
                  onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, hard_cap_gb: event.target.value } }))}
                  placeholder="Hard cap (ГБ)"
                  className="rounded-lg border border-violet-200/50 bg-white px-2 py-1 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
                />
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-3">
                <label className="inline-flex items-center gap-1 text-[11px]">
                  <input
                    type="checkbox"
                    checked={draft.notify_soft}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_soft: event.target.checked } }))}
                  />
                  Уведомлять на soft cap
                </label>
                <label className="inline-flex items-center gap-1 text-[11px]">
                  <input
                    type="checkbox"
                    checked={draft.notify_hard}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, notify_hard: event.target.checked } }))}
                  />
                  Уведомлять на hard cap
                </label>
                <label className="inline-flex items-center gap-1 text-[11px]">
                  <input
                    type="checkbox"
                    checked={draft.auto_disable_on_hard}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, auto_disable_on_hard: event.target.checked } }))}
                  />
                  Автоотключение на hard cap
                </label>
                <label className="inline-flex items-center gap-1 text-[11px]">
                  <input
                    type="checkbox"
                    checked={draft.apply_now}
                    onChange={(event) => setPolicyDrafts((prev) => ({ ...prev, [key.node_code]: { ...draft, apply_now: event.target.checked } }))}
                  />
                  Применить сразу
                </label>
                <button className="outline-btn rounded-lg px-2 py-1 text-[11px] font-semibold" type="button" onClick={() => onSavePolicy(key.node_code)} disabled={policyBusy === key.node_code}>
                  {policyBusy === key.node_code ? "..." : "Сохранить политику"}
                </button>
              </div>

              <div className="mt-2 text-xs text-slate-500">
                <span className="font-semibold text-slate-600 dark:text-slate-300">Текущие policy-значения:</span>{" "}
                burst {parseNullableNumber(draft.burst_mbps) ?? "—"}, soft {parseNullableNumber(draft.soft_cap_gb) ?? "—"}, hard{" "}
                {parseNullableNumber(draft.hard_cap_gb) ?? "—"}
              </div>
            </div>
          );
        })}
      </div>
      {!keys.length ? <p className="text-xs text-slate-500">Ключи для этого пользователя пока не созданы.</p> : null}
    </div>
  );
}
