"use client";

import type { Dispatch, SetStateAction } from "react";
import { fmtRuDate } from "@/app/(dashboard)/admin/nav";
import type { AdminUserCard, AdminUserKey } from "@/lib/api";
import {
  observerStateBadgeClass,
  observerStateLabel,
  originLabel,
  panelStateLabel,
  riskLevelLabel,
  userStatusBadgeClass,
  userStatusLabel,
} from "./admin-users-format";
import { AdminUserOverviewView } from "./admin-user-overview-view";
import { AdminUserKeyPolicyEditor } from "./admin-user-key-policy-editor";
import { AdminUserAuditView, AdminUserKeyHistoryView } from "./admin-user-history-views";
import type { KeyPolicyDraft } from "./admin-users-format";

type DetailTab = "overview" | "keys" | "history" | "audit";

type AdminUserSidePanelProps = {
  selected: AdminUserCard | null;
  detailTab: DetailTab;
  busy: boolean;
  keyBusy: string;
  policyBusy: string;
  policyDrafts: Record<string, KeyPolicyDraft>;
  selectedCanDelete: boolean;
  onReload: () => void;
  onMessage: () => void;
  onExtend: () => void;
  onToggleBlock: () => void;
  onRegenerateToken: () => void;
  onDeleteTestUser: () => void;
  onRunPreset: (preset: "reset_key" | "rotate_link" | "extend_1d" | "send_guide") => void;
  onGrantLoyalty: (tierDays: number) => void;
  onRunKeyAction: (key: AdminUserKey, action: "toggle" | "reset" | "resync") => void;
  onSavePolicy: (nodeCode: string) => void;
  onCopyText: (text: string) => void;
  setDetailTab: Dispatch<SetStateAction<DetailTab>>;
  setPolicyDrafts: Dispatch<SetStateAction<Record<string, KeyPolicyDraft>>>;
};

export function AdminUserSidePanel({
  selected,
  detailTab,
  busy,
  keyBusy,
  policyBusy,
  policyDrafts,
  selectedCanDelete,
  onReload,
  onMessage,
  onExtend,
  onToggleBlock,
  onRegenerateToken,
  onDeleteTestUser,
  onRunPreset,
  onGrantLoyalty,
  onRunKeyAction,
  onSavePolicy,
  onCopyText,
  setDetailTab,
  setPolicyDrafts,
}: AdminUserSidePanelProps) {
  const tabButtonClass = (tab: DetailTab): string =>
    `rounded-xl px-3 py-2 text-xs font-semibold uppercase tracking-[0.08em] transition ${
      detailTab === tab ? "bg-violet-600 text-white shadow-lg shadow-violet-600/25" : "outline-btn"
    }`;

  if (!selected) {
    return <article className="glass-card min-w-0 p-4 text-sm text-slate-500">Выберите пользователя в таблице, чтобы открыть детали.</article>;
  }

  const { user, keys = [], key_history = [], admin_actions = [], risk, loyalty, observer } = selected;
  const riskClass =
    String(risk?.level || "").toLowerCase() === "critical"
      ? "badge-danger"
      : String(risk?.level || "").toLowerCase() === "high"
        ? "badge-warning"
        : String(risk?.level || "").toLowerCase() === "medium"
          ? "badge-info"
          : "badge-success";

  return (
    <article className="glass-card min-w-0 p-4">
      <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl font-semibold">{user.display_name || user.username || `Пользователь #${user.tg_id}`}</h2>
            <p className="text-xs text-slate-500">tg_id: {user.tg_id}</p>
            <p className="text-xs text-slate-500">Создан: {fmtRuDate(user.created_at)}</p>
            <p className="text-xs text-slate-500">Истекает: {fmtRuDate(user.expiry_at)}</p>
          </div>
          <div className="space-y-2 text-right">
            <div className="flex flex-wrap items-center justify-end gap-2">
              <span className={`rounded-full px-2 py-1 text-xs ${userStatusBadgeClass(user.status)}`}>{userStatusLabel(user.status)}</span>
              <span className={`badge ${observerStateBadgeClass(user.observer_state)}`}>Observer {observerStateLabel(user.observer_state)}</span>
              <span className="badge badge-violet">{originLabel(user.origin)}</span>
            </div>
            <p className="text-xs text-slate-500">
              Связанный Telegram: {user.linked_telegram_username ? `@${user.linked_telegram_username}` : user.linked_telegram_id || "нет"}
            </p>
            <p className="text-xs text-slate-500">ID установки app: {user.app_install_id || "нет"}</p>
          </div>
        </div>
      </div>

      <div className="mb-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
        <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={onMessage} disabled={busy}>
          Написать пользователю
        </button>
        <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={onExtend} disabled={busy}>
          Продлить доступ
        </button>
        <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={onRegenerateToken} disabled={busy}>
          Обновить токен
        </button>
        <button className="outline-btn rounded-xl px-3 py-2 text-sm font-semibold" type="button" onClick={onToggleBlock} disabled={busy}>
          {user.status === "blocked" ? "Разблокировать пользователя" : "Заблокировать пользователя"}
        </button>
        {selectedCanDelete ? (
          <button className="rounded-xl bg-rose-500/15 px-3 py-2 text-sm font-semibold text-rose-500" type="button" onClick={onDeleteTestUser} disabled={busy}>
            Удалить manual/test пользователя
          </button>
        ) : null}
      </div>

      {selectedCanDelete ? (
        <div className="mb-3 rounded-xl border border-rose-200/60 bg-rose-50/70 p-3 dark:border-rose-500/20 dark:bg-rose-500/10">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <p className="text-sm font-semibold text-rose-600">Очистка manual/test</p>
              <p className="text-xs text-slate-500">Из админки можно удалять только явных manual/test пользователей.</p>
            </div>
            <button className="rounded-xl bg-rose-500 px-3 py-2 text-xs font-semibold text-white disabled:opacity-60" type="button" onClick={onDeleteTestUser} disabled={busy}>
              Удалить manual/test пользователя
            </button>
          </div>
        </div>
      ) : null}

      <div className="mb-3 grid gap-2 sm:grid-cols-2">
        <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => onRunPreset("reset_key")} disabled={busy}>
          Пресет: сбросить ключ
        </button>
        <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => onRunPreset("rotate_link")} disabled={busy}>
          Пресет: обновить ссылку
        </button>
        <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => onRunPreset("extend_1d")} disabled={busy}>
          Пресет: +1 день
        </button>
        <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => onRunPreset("send_guide")} disabled={busy}>
          Пресет: отправить инструкцию
        </button>
      </div>

      <div className="mb-3 grid gap-3 xl:grid-cols-3">
        <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
          <p>Тариф: <strong>{user.sub_type || "-"}</strong></p>
          <p>Оплачено stars: <strong>{user.stars_paid}</strong></p>
          <p>Рефералы: <strong>{user.referral_count}</strong></p>
          <p>Серия: <strong>{loyalty?.streak_days ?? 0} дн.</strong></p>
        </div>
        <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
          <div className="mb-1 flex items-center gap-2">
            <span className={`badge ${riskClass}`}>Риск {Math.round(risk?.score || 0)}</span>
            <span className="text-xs text-slate-500">{riskLevelLabel(String(risk?.level || ""))}</span>
          </div>
          <p className="text-xs">Ротации: <strong>{risk?.signals?.regen_count ?? 0}</strong></p>
          <p className="text-xs">Операции админа с ключами: <strong>{risk?.signals?.admin_key_ops ?? 0}</strong></p>
          <p className="text-xs">Уникальные IP: <strong>{risk?.signals?.unique_ips ?? 0}</strong></p>
          <p className="text-xs">Трафик: <strong>{Number(risk?.signals?.traffic_gb || 0).toFixed(2)} GB</strong></p>
        </div>
        <div className="rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
          <div className="mb-1 flex items-center gap-2">
            <span className={`badge ${observerStateBadgeClass(observer?.state || user.observer_state)}`}>
              Observer {observerStateLabel(observer?.state || user.observer_state)}
            </span>
            <span className="text-xs text-slate-500">{observer?.updated_at ? `updated ${fmtRuDate(observer.updated_at)}` : "updated: n/a"}</span>
          </div>
          <p className="text-xs text-slate-500">{observer?.reasons?.length ? observer.reasons.join(", ") : "Observer пока не прислал наблюдений."}</p>
          <p className="mt-1 text-xs text-slate-500">Panel state: <strong>{panelStateLabel(String(selected.summary?.panel_state || ""))}</strong></p>
        </div>
      </div>

      <div className="mb-3 rounded-xl bg-white/70 p-3 text-sm dark:bg-white/10">
        <p className="mb-1 font-semibold">Подписочный доступ</p>
        <div className="flex items-start gap-2">
          <input
            value={String(user.subscription_url || "")}
            readOnly
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => onCopyText(String(user.subscription_url || ""))}>
            Скопировать URL
          </button>
        </div>
        <div className="mt-2 flex items-start gap-2">
          <input
            value={String(user.subscription_token || "")}
            readOnly
            className="w-full rounded-xl border border-violet-200/50 bg-white/80 px-3 py-2 text-xs outline-none dark:border-violet-500/30 dark:bg-slate-900/70"
          />
          <button className="outline-btn rounded-xl px-3 py-2 text-xs font-semibold" type="button" onClick={() => onCopyText(String(user.subscription_token || ""))}>
            Скопировать токен
          </button>
        </div>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <button className={tabButtonClass("overview")} type="button" onClick={() => setDetailTab("overview")}>Обзор</button>
        <button className={tabButtonClass("keys")} type="button" onClick={() => setDetailTab("keys")}>Ключи и лимиты</button>
        <button className={tabButtonClass("history")} type="button" onClick={() => setDetailTab("history")}>История ключей</button>
        <button className={tabButtonClass("audit")} type="button" onClick={() => setDetailTab("audit")}>Аудит</button>
      </div>

      {detailTab === "overview" ? (
        <AdminUserOverviewView selected={selected} busy={busy} onGrantLoyalty={onGrantLoyalty} />
      ) : null}

      {detailTab === "keys" ? (
        <AdminUserKeyPolicyEditor
          selectedTgId={user.tg_id}
          keys={keys}
          policyDrafts={policyDrafts}
          busy={busy}
          keyBusy={keyBusy}
          policyBusy={policyBusy}
          onReload={onReload}
          onRunKeyAction={onRunKeyAction}
          onSavePolicy={onSavePolicy}
          setPolicyDrafts={setPolicyDrafts}
        />
      ) : null}

      {detailTab === "history" ? <AdminUserKeyHistoryView rows={key_history} busy={busy} onReload={onReload} /> : null}

      {detailTab === "audit" ? <AdminUserAuditView rows={admin_actions} busy={busy} onReload={onReload} /> : null}
    </article>
  );
}
