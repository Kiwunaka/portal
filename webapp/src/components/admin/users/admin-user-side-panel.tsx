"use client";

import type { Dispatch, SetStateAction } from "react";
import {
  AdminBadge,
  AdminEmptyState,
  adminButtonClass,
  adminFieldClass,
  adminInsetPanelClass,
  adminPanelClass,
} from "@/components/admin/admin-shell";
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
    detailTab === tab ? adminButtonClass("primary", "xs") : adminButtonClass("ghost", "xs");

  if (!selected) {
    return (
      <AdminEmptyState
        className="min-h-[420px]"
        title="Выберите пользователя"
        description="Откройте строку таблицы, чтобы проверить доступ, ключи, сигналы наблюдения и действия оператора."
      />
    );
  }

  const { user, keys = [], key_history = [], admin_actions = [], risk, loyalty, observer } = selected;
  const riskTone =
    String(risk?.level || "").toLowerCase() === "critical" || String(risk?.level || "").toLowerCase() === "high"
      ? "danger"
      : String(risk?.level || "").toLowerCase() === "medium"
        ? "warning"
        : "success";

  return (
    <article className={adminPanelClass("neutral")}>
      <div className={adminInsetPanelClass}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">выбранный пользователь</p>
            <h2 className="mt-1 text-2xl font-semibold text-slate-50">
              {user.display_name || user.username || `User #${user.tg_id}`}
            </h2>
            <div className="mt-2 space-y-1 text-xs text-slate-400">
              <p>Telegram ID: {user.tg_id}</p>
              <p>Создан: {fmtRuDate(user.created_at)}</p>
              <p>Доступ до: {fmtRuDate(user.expiry_at)}</p>
            </div>
          </div>

          <div className="space-y-2 text-right">
            <div className="flex flex-wrap items-center justify-end gap-2">
              <span className={`rounded-full px-2 py-1 text-xs ${userStatusBadgeClass(user.status)}`}>{userStatusLabel(user.status)}</span>
              <span className={`badge ${observerStateBadgeClass(user.observer_state)}`}>Observer {observerStateLabel(user.observer_state)}</span>
              <AdminBadge>{originLabel(user.origin)}</AdminBadge>
            </div>
            <p className="text-xs text-slate-400">
              Telegram привязан: {user.linked_telegram_username ? `@${user.linked_telegram_username}` : user.linked_telegram_id || "нет"}
            </p>
            <p className="text-xs text-slate-400">Установка приложения: {user.app_install_id || "нет"}</p>
          </div>
        </div>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onMessage} disabled={busy}>
          Написать
        </button>
        <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onExtend} disabled={busy}>
          Продлить доступ
        </button>
        <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onRegenerateToken} disabled={busy}>
          Обновить token
        </button>
        <button className={adminButtonClass(user.status === "blocked" ? "primary" : "danger", "sm")} type="button" onClick={onToggleBlock} disabled={busy}>
          {user.status === "blocked" ? "Разблокировать" : "Заблокировать"}
        </button>
      </div>

      {selectedCanDelete ? (
        <div className={`${adminInsetPanelClass} mt-3 border-rose-900/60 bg-rose-950/25`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-rose-200">Удаление только для manual/test</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">
                Удалять можно только явно помеченные manual/test аккаунты. Следующий диалог попросит подтверждение.
              </p>
            </div>
            <button className={adminButtonClass("danger", "sm")} type="button" onClick={onDeleteTestUser} disabled={busy}>
              Удалить manual/test пользователя
            </button>
          </div>
        </div>
      ) : null}

      <div className="mt-3 grid gap-3 xl:grid-cols-3">
        <div className={adminInsetPanelClass}>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">доступ</p>
          <div className="mt-2 space-y-1 text-sm">
            <p>План: <strong>{user.sub_type || "-"}</strong></p>
            <p>Оплачено Stars: <strong>{user.stars_paid ?? 0}</strong></p>
            <p>Приглашения: <strong>{user.referral_count ?? 0}</strong></p>
            <p>Серия: <strong>{loyalty?.streak_days ?? 0} дней</strong></p>
          </div>
        </div>
        <div className={adminInsetPanelClass}>
          <div className="mb-2 flex items-center gap-2">
            <AdminBadge tone={riskTone}>Risk {Math.round(risk?.score || 0)}</AdminBadge>
            <span className="text-xs text-slate-400">{riskLevelLabel(String(risk?.level || ""))}</span>
          </div>
          <div className="space-y-1 text-xs text-slate-400">
            <p>Обновления token: <strong>{risk?.signals?.regen_count ?? 0}</strong></p>
            <p>Операции с ключами: <strong>{risk?.signals?.admin_key_ops ?? 0}</strong></p>
            <p>Unique IPs: <strong>{risk?.signals?.unique_ips ?? 0}</strong></p>
            <p>Traffic: <strong>{Number(risk?.signals?.traffic_gb || 0).toFixed(2)} GB</strong></p>
          </div>
        </div>
        <div className={adminInsetPanelClass}>
          <div className="mb-2 flex items-center gap-2">
            <span className={`badge ${observerStateBadgeClass(observer?.state || user.observer_state)}`}>
              Observer {observerStateLabel(observer?.state || user.observer_state)}
            </span>
          </div>
          <p className="text-xs leading-5 text-slate-400">
            {observer?.reasons?.length ? observer.reasons.join(", ") : "Пока нет причин наблюдения."}
          </p>
          <p className="mt-2 text-xs text-slate-400">
            Состояние панели: <strong>{panelStateLabel(String(selected.summary?.panel_state || ""))}</strong>
          </p>
        </div>
      </div>

      <details className={`${adminInsetPanelClass} mt-3`}>
        <summary className="cursor-pointer text-sm font-semibold text-slate-950">
          Расширенно: ссылка подключения и token
        </summary>
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs leading-5 text-slate-600">Используйте только для recovery или ручной выдачи по запросу.</p>
          <button className={adminButtonClass("ghost", "xs")} type="button" onClick={onReload} disabled={busy}>
            Обновить
          </button>
        </div>
        <div className="mt-3 space-y-2">
          <div className="flex items-start gap-2">
            <input value={String(user.subscription_url || "")} readOnly className={adminFieldClass} />
            <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => onCopyText(String(user.subscription_url || ""))}>
              Copy URL
            </button>
          </div>
          <div className="flex items-start gap-2">
            <input value={String(user.subscription_token || "")} readOnly className={adminFieldClass} />
            <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => onCopyText(String(user.subscription_token || ""))}>
              Copy token
            </button>
          </div>
        </div>
      </details>

      <div className="mt-3 flex flex-wrap gap-2">
        <button className={tabButtonClass("overview")} type="button" onClick={() => setDetailTab("overview")}>Overview</button>
        <button className={tabButtonClass("keys")} type="button" onClick={() => setDetailTab("keys")}>Keys & limits</button>
        <button className={tabButtonClass("history")} type="button" onClick={() => setDetailTab("history")}>Key history</button>
        <button className={tabButtonClass("audit")} type="button" onClick={() => setDetailTab("audit")}>Audit</button>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("reset_key")} disabled={busy}>Preset: reset key</button>
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("rotate_link")} disabled={busy}>Preset: rotate link</button>
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("extend_1d")} disabled={busy}>Preset: +1 day</button>
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("send_guide")} disabled={busy}>Preset: send guide</button>
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
