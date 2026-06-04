"use client";

import type { Dispatch, SetStateAction } from "react";
import { AdminEmptyState, adminButtonClass, adminFieldClass, adminInsetPanelClass, adminPanelClass } from "@/components/admin/admin-shell";
import { fmtRuDate } from "@/lib/date-format";
import type { AdminPaymentOrder, AdminUserCard, AdminUserKey } from "@/lib/api";
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

function paymentStatusTone(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "paid") return "badge-success";
  if (["failed", "cancelled", "refunded", "chargeback"].includes(value)) return "badge-danger";
  if (["manual_review", "pending_verification"].includes(value)) return "badge-warning";
  return "badge-info";
}

function formatPaymentAmount(order: AdminPaymentOrder): string {
  return `${Number(order.amount || 0).toLocaleString("ru-RU")} ${order.currency || "RUB"}`;
}

function paymentStatusLabel(status: string): string {
  const value = String(status || "").toLowerCase();
  if (value === "paid") return "Оплачен";
  if (value === "failed") return "Ошибка";
  if (value === "cancelled") return "Отменён";
  if (value === "refunded") return "Возврат";
  if (value === "chargeback") return "Спор";
  if (value === "manual_review") return "Проверить вручную";
  if (value === "pending_verification") return "Ждёт проверки";
  return status || "Неизвестно";
}

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
        description="Откройте строку из таблицы, чтобы посмотреть статус, ключи, проверки и действия операторов."
      />
    );
  }

  const { user, keys = [], key_history = [], admin_actions = [], payment_orders = [], risk, loyalty, observer } = selected;
  const riskClass =
    String(risk?.level || "").toLowerCase() === "critical"
      ? "badge-danger"
      : String(risk?.level || "").toLowerCase() === "high"
        ? "badge-warning"
        : String(risk?.level || "").toLowerCase() === "medium"
          ? "badge-info"
          : "badge-success";

  return (
    <article className={adminPanelClass("neutral")}>
      <div className={adminInsetPanelClass}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Выбранный пользователь</p>
            <h2 className="mt-1 font-display text-2xl font-semibold text-slate-900">
              {user.display_name || user.username || `Пользователь #${user.tg_id}`}
            </h2>
            <div className="mt-2 space-y-1 text-xs text-slate-400">
              <p>tg_id: {user.tg_id}</p>
              <p>Создан: {fmtRuDate(user.created_at)}</p>
              <p>Истекает: {fmtRuDate(user.expiry_at)}</p>
            </div>
          </div>

          <div className="space-y-2 text-right">
            <div className="flex flex-wrap items-center justify-end gap-2">
              <span className={`rounded-full px-2 py-1 text-xs ${userStatusBadgeClass(user.status)}`}>{userStatusLabel(user.status)}</span>
              <span className={`badge ${observerStateBadgeClass(user.observer_state)}`}>Проверка: {observerStateLabel(user.observer_state)}</span>
              <span className="rounded-full border border-slate-200 bg-slate-50 px-2 py-1 text-xs font-semibold text-slate-600">
                {originLabel(user.origin)}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Telegram: {user.linked_telegram_username ? `@${user.linked_telegram_username}` : user.linked_telegram_id || "нет"}
            </p>
            <p className="text-xs text-slate-400">Установка приложения: {user.app_install_id || "нет"}</p>
          </div>
        </div>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onMessage} disabled={busy}>
          Написать пользователю
        </button>
        <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onExtend} disabled={busy}>
          Продлить доступ
        </button>
        <button className={adminButtonClass("secondary", "sm")} type="button" onClick={onRegenerateToken} disabled={busy}>
          Обновить токен
        </button>
        <button className={adminButtonClass(user.status === "blocked" ? "primary" : "danger", "sm")} type="button" onClick={onToggleBlock} disabled={busy}>
          {user.status === "blocked" ? "Разблокировать" : "Заблокировать"}
        </button>
      </div>

      {selectedCanDelete ? (
        <div className={`${adminInsetPanelClass} mt-3 border-rose-200/80 bg-rose-50/88 dark:border-rose-500/20 dark:bg-rose-500/10`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-sm font-semibold text-rose-700 dark:text-rose-200">Удаление только для тестовых аккаунтов</p>
              <p className="mt-1 text-xs leading-5 text-slate-400">
                Удаляйте только служебные аккаунты, созданные для проверки админки или сценариев поддержки.
              </p>
            </div>
            <button className={adminButtonClass("danger", "sm")} type="button" onClick={onDeleteTestUser} disabled={busy}>
              Удалить тестового пользователя
            </button>
          </div>
        </div>
      ) : null}

      <div className="mt-3 grid gap-3 xl:grid-cols-3">
        <div className={adminInsetPanelClass}>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">Доступ</p>
          <div className="mt-2 space-y-1 text-sm">
            <p>Тариф: <strong>{user.sub_type || "-"}</strong></p>
            <p>Оплачено stars: <strong>{user.stars_paid}</strong></p>
            <p>Рефералы: <strong>{user.referral_count}</strong></p>
            <p>Серия: <strong>{loyalty?.streak_days ?? 0} дн.</strong></p>
          </div>
        </div>
        <div className={adminInsetPanelClass}>
          <div className="mb-2 flex items-center gap-2">
            <span className={`badge ${riskClass}`}>Риск {Math.round(risk?.score || 0)}</span>
            <span className="text-xs text-slate-400">{riskLevelLabel(String(risk?.level || ""))}</span>
          </div>
          <div className="space-y-1 text-xs text-slate-400">
            <p>Ротации: <strong>{risk?.signals?.regen_count ?? 0}</strong></p>
            <p>Админ-операции с ключами: <strong>{risk?.signals?.admin_key_ops ?? 0}</strong></p>
            <p>Уникальные IP: <strong>{risk?.signals?.unique_ips ?? 0}</strong></p>
            <p>Трафик: <strong>{Number(risk?.signals?.traffic_gb || 0).toFixed(2)} GB</strong></p>
          </div>
        </div>
        <div className={adminInsetPanelClass}>
          <div className="mb-2 flex items-center gap-2">
            <span className={`badge ${observerStateBadgeClass(observer?.state || user.observer_state)}`}>
              Проверка: {observerStateLabel(observer?.state || user.observer_state)}
            </span>
          </div>
          <p className="text-xs leading-5 text-slate-400">
            {observer?.reasons?.length ? observer.reasons.join(", ") : "Данных для проверки пока нет."}
          </p>
          <p className="mt-2 text-xs text-slate-400">
            Состояние панелей: <strong>{panelStateLabel(String(selected.summary?.panel_state || ""))}</strong>
          </p>
        </div>
      </div>

      <div className="mt-3 grid gap-3 xl:grid-cols-2">
        <div className={adminInsetPanelClass}>
          <p className="text-sm font-semibold text-slate-900">Приложение и Telegram</p>
          <div className="mt-3 space-y-1 text-xs text-slate-400">
            <p>Установка: <strong>{user.app_install_id || "не привязана"}</strong></p>
            <p>Платформа: <strong>{user.app_platform || "неизвестно"}</strong></p>
            <p>Последняя активность: <strong>{fmtRuDate(user.app_last_seen_at)}</strong></p>
            <p>Telegram: <strong>{user.linked_telegram_username ? `@${user.linked_telegram_username}` : user.linked_telegram_id || "не привязан"}</strong></p>
          </div>
        </div>
        <div className={adminInsetPanelClass}>
          <p className="text-sm font-semibold text-slate-900">Последние оплаты</p>
          {payment_orders.length ? (
            <div className="mt-3 space-y-2">
              {payment_orders.slice(0, 4).map((order) => (
                <div key={`${order.provider}:${order.order_id}`} className="rounded-xl border border-[#22303c] bg-[#0b1218] px-3 py-2 text-xs">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="font-mono text-slate-800">{order.order_id}</p>
                    <span className={`badge ${paymentStatusTone(order.status)}`}>{paymentStatusLabel(order.status)}</span>
                  </div>
                  <p className="mt-1 text-slate-400">
                    {order.provider} · {order.plan_code || "-"} · {formatPaymentAmount(order)}
                  </p>
                  {order.last_event ? (
                    <p className="mt-1 text-slate-500">
                      Событие {order.last_event.event_type}: {order.last_event.processed_ok ? "обработано" : "нужно проверить"}
                    </p>
                  ) : (
                    <p className="mt-1 text-slate-500">Подтверждения от провайдера ещё нет.</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-2 text-xs text-slate-400">Оплат по этому аккаунту пока нет.</p>
          )}
        </div>
      </div>

      <div className={`${adminInsetPanelClass} mt-3`}>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-semibold text-slate-900">Токены и ссылки</p>
          <button className={adminButtonClass("ghost", "xs")} type="button" onClick={onReload} disabled={busy}>
            Обновить
          </button>
        </div>
        <div className="mt-3 space-y-2">
          <div className="flex items-start gap-2">
            <input value={String(user.subscription_url || "")} readOnly className={adminFieldClass} />
            <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => onCopyText(String(user.subscription_url || ""))}>
              Копировать URL
            </button>
          </div>
          <div className="flex items-start gap-2">
            <input value={String(user.subscription_token || "")} readOnly className={adminFieldClass} />
            <button className={adminButtonClass("secondary", "xs")} type="button" onClick={() => onCopyText(String(user.subscription_token || ""))}>
              Копировать токен
            </button>
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        <button className={tabButtonClass("overview")} type="button" onClick={() => setDetailTab("overview")}>
          Обзор
        </button>
        <button className={tabButtonClass("keys")} type="button" onClick={() => setDetailTab("keys")}>
          Ключи и лимиты
        </button>
        <button className={tabButtonClass("history")} type="button" onClick={() => setDetailTab("history")}>
          История ключей
        </button>
        <button className={tabButtonClass("audit")} type="button" onClick={() => setDetailTab("audit")}>
          Аудит
        </button>
      </div>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("reset_key")} disabled={busy}>
          Сбросить ключ
        </button>
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("rotate_link")} disabled={busy}>
          Обновить ссылку
        </button>
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("extend_1d")} disabled={busy}>
          Добавить 1 день
        </button>
        <button className={adminButtonClass("ghost", "xs")} type="button" onClick={() => onRunPreset("send_guide")} disabled={busy}>
          Отправить инструкцию
        </button>
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
