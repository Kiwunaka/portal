"use client";

import { useMemo, useState } from "react";
import { Ban, CalendarPlus, KeyRound, MessageSquareText, RefreshCw, Send, ShieldCheck, Trash2 } from "lucide-react";

import { ActionIntentDialog } from "@/components/ops/action-intent-dialog";
import { Badge, Button, Card, SectionTitle } from "@/components/ui";
import type { ActionIntentRequest, AdminActionResult } from "@/lib/admin-api/actions";
import type { AdminUserIdentity, AdminUserKey } from "@/lib/admin-api/users";

function userRequest(
  tgId: number,
  action: string,
  endpoint: string,
  payload: Record<string, unknown>,
): ActionIntentRequest {
  return {
    action,
    target: { type: "user", id: String(tgId) },
    payload,
    endpoint: `/api/admin/users/${encodeURIComponent(String(tgId))}${endpoint}`,
  };
}

export function UserActions({
  user,
  keys,
  onRefresh,
}: {
  user: AdminUserIdentity;
  keys: AdminUserKey[];
  onRefresh: () => void;
}) {
  const [request, setRequest] = useState<ActionIntentRequest | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [extendDays, setExtendDays] = useState("30");
  const [message, setMessage] = useState("");
  const [preset, setPreset] = useState("reset_key");
  const isBlocked = !user.isActive;

  const validExtendDays = useMemo(() => {
    const value = Number(extendDays);
    return Number.isInteger(value) && value >= 1 && value <= 3650 ? value : null;
  }, [extendDays]);

  function openAction(nextRequest: ActionIntentRequest) {
    setRequest(nextRequest);
    setDialogOpen(true);
  }

  function handleResult(result: AdminActionResult) {
    if (request?.action === "user.message" && result.status === "completed") setMessage("");
  }

  return (
    <>
      <Card className="min-h-0">
        <SectionTitle title="Действия пользователя" description="Каждое изменение сначала получает серверный предпросмотр. Повтор после неясного итога запрещён до обновления карточки." />

        <div className="grid gap-3 xl:grid-cols-2">
          <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
            <h3 className="text-sm font-semibold">Доступ и обслуживание</h3>
            <div className="mt-3 grid gap-2 sm:grid-cols-[110px_1fr]">
              <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
                Дней
                <input
                  aria-label="Продлить доступ на дней"
                  type="number"
                  min={1}
                  max={3650}
                  value={extendDays}
                  onChange={(event) => setExtendDays(event.target.value)}
                  className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
                />
              </label>
              <div className="flex flex-wrap items-end gap-2">
                <Button
                  tone="primary"
                  disabled={validExtendDays === null}
                  onClick={() => validExtendDays === null ? undefined : openAction(userRequest(user.tgId, "user.extend", "/manual/extend", { days: validExtendDays, delta_days: null, allow_deactivate: false }))}
                >
                  <CalendarPlus size={15} /> Продлить доступ
                </Button>
                <Button
                  tone={isBlocked ? "secondary" : "danger"}
                  onClick={() => openAction(userRequest(user.tgId, "user.block", "/manual/block", { blocked: !isBlocked }))}
                >
                  {isBlocked ? <ShieldCheck size={15} /> : <Ban size={15} />}
                  {isBlocked ? "Разблокировать" : "Заблокировать"}
                </Button>
              </div>
            </div>

            <div className="mt-4 border-t border-[color:var(--atlas-border)] pt-3">
              <label className="text-xs font-semibold text-[color:var(--atlas-text-soft)]">
                Готовый сценарий
                <select
                  aria-label="Готовый сценарий пользователя"
                  value={preset}
                  onChange={(event) => setPreset(event.target.value)}
                  className="mt-1 min-h-10 w-full rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] px-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
                >
                  <option value="reset_key">Сбросить ключи</option>
                  <option value="rotate_link">Перевыпустить ссылку подключения</option>
                  <option value="extend_1d">Продлить на один день</option>
                  <option value="send_guide">Отправить инструкцию</option>
                </select>
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                <Button tone="secondary" onClick={() => openAction(userRequest(user.tgId, "user.preset_run", "/presets/run", { preset }))}>
                  <RefreshCw size={15} /> Проверить и выполнить сценарий
                </Button>
                <Button tone="danger" onClick={() => openAction(userRequest(user.tgId, "user.regenerate_token", "/manual/regenerate-token", {}))}>
                  <KeyRound size={15} /> Обновить ссылку подключения
                </Button>
                {user.isManual ? (
                  <Button tone="danger" onClick={() => openAction(userRequest(user.tgId, "user.safe_delete", "/safe-delete", { confirm: true }))}>
                    <Trash2 size={15} /> Удалить тестового пользователя
                  </Button>
                ) : null}
              </div>
            </div>
          </div>

          <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
            <h3 className="flex items-center gap-2 text-sm font-semibold"><MessageSquareText size={16} /> Сообщение пользователю</h3>
            <p className="mt-1 text-xs leading-5 text-[color:var(--atlas-text-soft)]">Текст не сохраняется в намерении и аудите: там остаются только хэш и длина.</p>
            <label className="mt-3 block text-xs font-semibold text-[color:var(--atlas-text-soft)]">
              Текст сообщения
              <textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                rows={5}
                maxLength={4000}
                placeholder="Напишите понятное сообщение без секретов"
                className="mt-1 w-full resize-y rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-surface)] p-3 text-sm text-[color:var(--atlas-text)] outline-none focus:border-[color:var(--atlas-focus)]"
              />
            </label>
            <div className="mt-2 flex items-center justify-between gap-2">
              <span className="text-[11px] text-[color:var(--atlas-text-muted)]">{message.length} / 4000</span>
              <Button tone="primary" disabled={!message.trim()} onClick={() => openAction(userRequest(user.tgId, "user.message", "/message", { text: message.trim() }))}>
                <Send size={15} /> Подготовить отправку
              </Button>
            </div>
          </div>
        </div>

        <div className="mt-3 rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="text-sm font-semibold">Ключи по нодам</h3>
            <Badge tone={keys.length ? "info" : "neutral"}>{keys.length ? `${keys.length} ключей` : "Нет ключей"}</Badge>
          </div>
          {keys.length ? (
            <div className="mt-3 grid gap-2 lg:grid-cols-2">
              {keys.map((key) => (
                <div key={key.nodeCode} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-mono text-xs font-semibold">{key.nodeCode.toUpperCase()}</span>
                    <Badge tone={key.enabled === null ? "warning" : key.enabled ? "success" : "warning"}>{key.enabled === null ? "Нет данных панели" : key.enabled ? "Включён" : "Выключен"}</Badge>
                  </div>
                  {key.panelState === "ok" && key.enabled !== null ? <div className="mt-2 flex flex-wrap gap-2">
                    <Button tone="secondary" onClick={() => openAction(userRequest(user.tgId, "user.key_toggle", `/keys/${encodeURIComponent(key.nodeCode)}/toggle`, { node_code: key.nodeCode, enable: !key.enabled }))}>
                      {key.enabled ? "Выключить ключ" : "Включить ключ"}
                    </Button>
                    <Button tone="ghost" onClick={() => openAction(userRequest(user.tgId, "user.key_reset_traffic", `/keys/${encodeURIComponent(key.nodeCode)}/reset-traffic`, { node_code: key.nodeCode }))}>Сбросить трафик</Button>
                    <Button tone="ghost" onClick={() => openAction(userRequest(user.tgId, "user.key_resync_subid", `/keys/${encodeURIComponent(key.nodeCode)}/resync-subid`, { node_code: key.nodeCode }))}>Синхронизировать подписку</Button>
                  </div> : <p className="mt-2 text-xs text-[color:var(--atlas-text-muted)]">Действия с ключом недоступны, пока панель не вернёт его текущее состояние.</p>}
                </div>
              ))}
            </div>
          ) : <p className="mt-2 text-xs text-[color:var(--atlas-text-muted)]">Панель не вернула ключи пользователя.</p>}
        </div>
      </Card>

      <ActionIntentDialog
        open={dialogOpen}
        request={request}
        onOpenChange={(nextOpen) => {
          setDialogOpen(nextOpen);
          if (!nextOpen) setRequest(null);
        }}
        onKnownOutcome={onRefresh}
        onCheckState={onRefresh}
        onResult={handleResult}
      />
    </>
  );
}
