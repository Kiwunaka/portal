"use client";

import { useId, type ReactNode } from "react";
import { Activity, Radio, RefreshCw, ShieldAlert, UserRound } from "lucide-react";

import { Badge, Button, Card, SectionTitle, type Tone } from "@/components/ui";
import { EmptyState, ErrorState, LoadingState } from "@/components/ui/states";
import { OpsTooltip } from "@/components/ui/tooltip";
import type { AdminUserDetail, AdminUserInvestigation } from "@/lib/admin-api/users";
import { formatSourceAge } from "@/lib/ops-status/presentation";

import { UserActions } from "./user-actions";

export const USER_DETAIL_TABS = ["overview", "keys", "payments", "tickets", "risk", "audit", "investigation"] as const;
export type UserDetailTab = typeof USER_DETAIL_TABS[number];

const TAB_LABELS: Record<UserDetailTab, string> = {
  overview: "Обзор",
  keys: "Ключи",
  payments: "Платежи",
  tickets: "Тикеты",
  risk: "Риск и наблюдатель",
  audit: "Аудит",
  investigation: "Расследование",
};

function dateText(value: string | null): string {
  if (!value) return "Нет данных";
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) return "Нет данных";
  return new Date(parsed).toLocaleString("ru-RU", { dateStyle: "short", timeStyle: "short" });
}

function countText(value: number | null): string {
  return value === null ? "Нет данных" : new Intl.NumberFormat("ru-RU").format(value);
}

function numberText(value: number, suffix = ""): string {
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 2 }).format(value)}${suffix}`;
}

function statusLabel(value: string): string {
  const labels: Record<string, string> = {
    active: "Активен",
    inactive: "Неактивен",
    blocked: "Заблокирован",
    expired: "Истёк",
    manual: "Тестовый",
    manual_test: "Тестовый",
    open: "Открыт",
    in_progress: "В работе",
    closed: "Закрыт",
    paid: "Оплачен",
    pending: "Ожидает",
    created: "Создан",
    failed: "Ошибка",
    ok: "Норма",
    watch: "Наблюдение",
    suspicious: "Подозрение",
    low: "Низкий",
    medium: "Средний",
    high: "Высокий",
    critical: "Критический",
  };
  return labels[value.toLowerCase()] || "Неизвестно";
}

function tone(value: string): Tone {
  const normalized = value.toLowerCase();
  if (["blocked", "failed", "suspicious", "high", "critical"].includes(normalized)) return "danger";
  if (["expired", "watch", "medium", "pending", "created", "in_progress"].includes(normalized)) return "warning";
  if (["active", "ok", "paid", "closed", "low"].includes(normalized)) return "success";
  return "neutral";
}

function planLabel(value: string | null): string {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "paid") return "Платный";
  if (normalized === "free") return "Бесплатный";
  if (normalized === "manual") return "Ручной";
  return value || "Не указан";
}

function actionLabel(action: string): string {
  const labels: Record<string, string> = {
    admin_manual_extend: "Продление доступа",
    admin_manual_block: "Изменение блокировки",
    admin_manual_regen_token: "Замена токена подписки",
    admin_user_key_toggle: "Переключение ключа",
    admin_user_key_reset_traffic: "Сброс трафика ключа",
    admin_user_key_resync_subid: "Синхронизация подписки",
    admin_user_key_limits: "Изменение лимитов ключа",
    admin_user_message: "Сообщение пользователю",
    admin_user_preset_run: "Готовый сценарий",
    admin_user_loyalty_grant: "Награда лояльности",
  };
  return labels[action] || "Операционное действие";
}

function riskFactorLabel(key: string): string {
  const labels: Record<string, string> = {
    regen: "Частая замена ссылки",
    admin_key_ops: "Операции с ключами",
    multi_ip: "Много сетевых адресов",
    subid_mismatch: "Несовпадение подписки",
    observer_watch: "Наблюдатель: требуется внимание",
    observer_suspicious: "Наблюдатель: подозрение",
    anomalous_traffic: "Нетипичный трафик",
  };
  return labels[key] || "Сигнал риска";
}

function Metric({ label, value, explanation, source, sampledAt, threshold = null, icon }: {
  label: string;
  value: string;
  explanation: string;
  source: string;
  sampledAt: string | null;
  threshold?: string | null;
  icon?: ReactNode;
}) {
  const id = useId();
  return (
    <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs font-semibold text-[color:var(--atlas-text-soft)]">{icon}{label}</div>
          <div className="mt-2 break-words text-lg font-semibold text-[color:var(--atlas-text)]">{value}</div>
          <div className="mt-1 text-[11px] text-[color:var(--atlas-text-muted)]">{sampledAt ? formatSourceAge(sampledAt) : "Возраст неизвестен"}</div>
        </div>
        <OpsTooltip id={`${id}-metric`} content={explanation} source={source} sampledAt={sampledAt} threshold={threshold} />
      </div>
    </div>
  );
}

function DetailTable({ headers, rows, empty }: { headers: string[]; rows: ReactNode[][]; empty: string }) {
  if (!rows.length) return <EmptyState description={empty} className="min-h-24" />;
  return (
    <div className="ops-scrollbar overflow-auto rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)]">
      <table className="w-full min-w-[720px] border-collapse text-left text-xs">
        <thead className="bg-[color:var(--pokrov-table-header-bg)] text-[11px] text-[color:var(--atlas-text-soft)]">
          <tr>{headers.map((header) => <th key={header} className="border-b border-[color:var(--pokrov-table-divider)] px-3 py-2 font-semibold">{header}</th>)}</tr>
        </thead>
        <tbody>{rows.map((cells, rowIndex) => (
          <tr key={rowIndex} className="border-b border-[color:var(--pokrov-table-divider)] hover:bg-[color:var(--pokrov-table-row-hover-bg)]">
            {cells.map((cell, cellIndex) => <td key={cellIndex} className="px-3 py-2 align-middle">{cell}</td>)}
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

export function UserDetail({
  data,
  loadedAt,
  tab,
  onTabChange,
  investigation,
  investigationLoading,
  investigationError,
  onInvestigationRetry,
  onRefresh,
}: {
  data: AdminUserDetail;
  loadedAt: string | null;
  tab: UserDetailTab;
  onTabChange: (tab: UserDetailTab) => void;
  investigation: AdminUserInvestigation | null;
  investigationLoading: boolean;
  investigationError: string | null;
  onInvestigationRetry: () => void;
  onRefresh: () => void;
}) {
  const panelId = useId();
  const name = data.user.linkedTelegramUsername
    ? `@${data.user.linkedTelegramUsername}`
    : data.user.username && !data.user.username.toLowerCase().startsWith("app_")
      ? `@${data.user.username}`
      : data.user.displayName || data.user.deviceName || `Пользователь ${data.user.tgId}`;
  const panelWarning = data.summary.panelState === "partial"
    ? {
        title: "Снимок панели неполный",
        description: "Часть нод ответила, часть — нет. Общие показатели скрыты, чтобы неполные значения не выглядели как полные. Доступные строки ключей сохранены.",
      }
    : data.summary.panelState === "error" || data.summary.panelState === "missing"
      ? {
          title: "Панель не вернула состояние ключей",
          description: "Оперативные метрики помечены как «Нет данных», а не как нулевые. Сведения из базы пользователей и история остаются доступными.",
        }
      : null;

  return (
    <div className="space-y-3">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-[color:var(--atlas-text)]">Пользователь {data.user.tgId}</h2>
            <p className="mt-1 text-sm text-[color:var(--atlas-text-soft)]">{name}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone={tone(data.user.status)}>{statusLabel(data.user.status)}</Badge>
            <Badge tone="info">{planLabel(data.user.plan)}</Badge>
            <Badge tone={tone(data.observer.state)}>Наблюдатель: {statusLabel(data.observer.state)}</Badge>
          </div>
        </div>

        <div className="mt-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          <Metric label="Доступ до" value={dateText(data.user.expiryAt)} explanation="Срок действия доступа из основной записи пользователя." source="База пользователей" sampledAt={loadedAt} icon={<UserRound size={15} />} />
          <Metric label="Соединения сейчас" value={countText(data.summary.onlineConnectionsNow)} explanation="Оперативная оценка соединений панели; это не число уникальных людей." source="Панель · карточка пользователя" sampledAt={data.keys.map((key) => key.lastOnlineAt).filter(Boolean).sort().at(-1) || null} icon={<Radio size={15} />} />
          <Metric label="Ноды сейчас" value={data.summary.onlineNodeCodesNow === null ? "Нет данных" : data.summary.onlineNodeCodesNow.length ? data.summary.onlineNodeCodesNow.join(", ") : "Нет в оперативном снимке"} explanation="Ноды, где ключи пользователя были онлайн в текущем снимке." source="Панель · карточка пользователя" sampledAt={data.keys.map((key) => key.lastOnlineAt).filter(Boolean).sort().at(-1) || null} icon={<Activity size={15} />} />
          <Metric label="Риск" value={`${statusLabel(data.risk.level)} · ${data.risk.score}/100`} explanation="Серверная оценка факторов за указанное окно; это сигнал для разбора, а не автоматический приговор." source="Серверная оценка риска" sampledAt={data.risk.updatedAt} threshold="Высокий риск: от 60" icon={<ShieldAlert size={15} />} />
        </div>
      </Card>

      <Card className="p-0">
        <div role="tablist" aria-label="Разделы карточки пользователя" className="ops-scrollbar flex overflow-x-auto border-b border-[color:var(--atlas-border)] px-2 pt-2">
          {USER_DETAIL_TABS.map((item) => (
            <button
              key={item}
              id={`${panelId}-${item}-tab`}
              role="tab"
              type="button"
              aria-selected={tab === item}
              aria-controls={`${panelId}-${item}-panel`}
              onClick={() => onTabChange(item)}
              className={`min-h-10 shrink-0 rounded-t-[var(--pokrov-radius-control)] border-b-2 px-3 text-xs font-semibold ${tab === item ? "border-[color:var(--atlas-primary)] bg-[color:var(--pokrov-nav-active-bg)] text-[color:var(--atlas-text)]" : "border-transparent text-[color:var(--atlas-text-soft)] hover:text-[color:var(--atlas-text)]"}`}
            >
              {TAB_LABELS[item]}
            </button>
          ))}
        </div>

        <section id={`${panelId}-${tab}-panel`} role="tabpanel" aria-labelledby={`${panelId}-${tab}-tab`} className="p-[var(--pokrov-panel-padding)]">
          {tab === "overview" ? (
            <div className="space-y-4">
              {panelWarning ? (
                <ErrorState
                  title={panelWarning.title}
                  description={panelWarning.description}
                  action={<Button tone="secondary" onClick={onRefresh}><RefreshCw size={15} /> Повторить запрос панели</Button>}
                  className="min-h-0"
                />
              ) : null}
              <div className="grid gap-3 lg:grid-cols-2">
                <div>
                  <SectionTitle title="Основные сведения" description="Первый слой без токенов, ссылок подключения и исходных IP-адресов." />
                  <dl className="grid gap-2 text-xs sm:grid-cols-2">
                    {[
                      ["Telegram ID", String(data.user.tgId)],
                      ["Имя в Telegram", data.user.username ? `@${data.user.username}` : "Не указано"],
                      ["Привязанный Telegram", data.user.linkedTelegramUsername ? `@${data.user.linkedTelegramUsername}` : "Не привязан"],
                      ["Источник", data.user.origin === "app" ? "Приложение" : data.user.origin === "telegram" ? "Telegram" : data.user.origin === "manual_test" ? "Ручной тест" : "Не указан"],
                      ["Устройство", data.user.deviceName || "Не указано"],
                      ["ID установки", data.user.installId || "Не указан"],
                      ["Платформа", data.user.appPlatform || "Не указана"],
                      ["Последняя активность приложения", dateText(data.user.appLastSeenAt)],
                    ].map(([label, value]) => (
                      <div key={label} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3">
                        <dt className="text-[color:var(--atlas-text-muted)]">{label}</dt>
                        <dd className="mt-1 break-words font-semibold text-[color:var(--atlas-text)]">{value}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
                <div>
                  <SectionTitle title="Привязки нод" description="Без идентификатора клиента, адреса панели, идентификатора подписки и строк подключения." />
                  <div className="space-y-2">
                    {data.keys.length ? data.keys.map((key) => (
                      <div key={key.nodeCode} className="flex flex-wrap items-center justify-between gap-2 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-xs">
                        <div><span className="font-mono font-semibold">{key.nodeCode.toUpperCase()}</span><span className="ml-2 text-[color:var(--atlas-text-muted)]">{key.nodeName || "Название не указано"}</span></div>
                        <div className="flex gap-2"><Badge tone={key.exists === null ? "warning" : key.exists ? "success" : "neutral"}>{key.exists === null ? "Нет данных" : key.exists ? "Ключ есть" : "Ключа нет"}</Badge><Badge tone={key.online === null ? "warning" : key.online ? "success" : "neutral"}>{key.online === null ? "Нет данных" : key.online ? "Онлайн" : "Не онлайн"}</Badge></div>
                      </div>
                    )) : <EmptyState description="Панель не вернула привязки нод." className="min-h-24" />}
                  </div>
                </div>
              </div>
              <UserActions user={data.user} keys={data.keys} onRefresh={onRefresh} />
            </div>
          ) : null}

          {tab === "keys" ? (
            <div>
              <SectionTitle title="Ключи" description="Только безопасные операционные поля. Секреты подключения сервер в карточку не возвращает." />
              <DetailTable headers={["Нода", "Состояние", "Онлайн", "Соединения", "Трафик", "Подписка", "Источник"]} empty="Ключи не найдены или панель недоступна." rows={data.keys.map((key) => [
                <span key="node" className="font-mono font-semibold">{key.nodeCode.toUpperCase()}</span>,
                <Badge key="enabled" tone={key.enabled === null ? "warning" : key.enabled ? "success" : "warning"}>{key.enabled === null ? "Нет данных" : key.enabled ? "Включён" : "Выключен"}</Badge>,
                <Badge key="online" tone={key.online ? "success" : "neutral"}>{key.online === null ? "Нет данных" : key.online ? "Онлайн" : "Не онлайн"}</Badge>,
                countText(key.currentConnections),
                key.totalGb === null ? "Нет данных" : numberText(key.totalGb, " ГиБ"),
                <Badge key="sub" tone={key.subIdMatches === null ? "warning" : key.subIdMatches ? "success" : "danger"}>{key.subIdMatches === null ? "Нет данных" : key.subIdMatches ? "Синхронизирована" : "Не совпадает"}</Badge>,
                key.panelState === "error" ? "Панель не ответила" : key.lastOnlineAt ? formatSourceAge(key.lastOnlineAt) : "Возраст неизвестен",
              ])} />
            </div>
          ) : null}

          {tab === "payments" ? (
            <div>
              <SectionTitle title="Платежи" description="Заказы пользователя без исходного ответа провайдера и платёжных секретов." />
              <DetailTable headers={["Заказ", "Провайдер", "План", "Сумма", "Статус", "Создан"]} empty="Платежей пользователя нет." rows={data.payments.map((payment) => [
                payment.orderId || `#${payment.id}`,
                payment.provider,
                payment.planCode || "Не указан",
                `${numberText(payment.amount)} ${payment.currency}`,
                <Badge key="status" tone={tone(payment.status)}>{statusLabel(payment.status)}</Badge>,
                dateText(payment.createdAt),
              ])} />
            </div>
          ) : null}

          {tab === "tickets" ? (
            <div>
              <SectionTitle title="Тикеты пользователя" description="Для ответа откройте полную переписку в разделе «Тикеты»." />
              <DetailTable headers={["Тикет", "Тема", "Статус", "Последнее сообщение", "Обновлён"]} empty="У пользователя нет тикетов." rows={data.tickets.map((ticketItem) => [
                <a key="id" href={`/tickets?selected=${ticketItem.id}`} className="font-semibold text-[color:var(--atlas-primary)] hover:underline">#{ticketItem.id}</a>,
                ticketItem.subject,
                <Badge key="status" tone={tone(ticketItem.status)}>{statusLabel(ticketItem.status)}</Badge>,
                ticketItem.lastMessagePreview || "Нет сообщения",
                dateText(ticketItem.updatedAt),
              ])} />
            </div>
          ) : null}

          {tab === "risk" ? (
            <div className="space-y-4">
              <div className="grid gap-3 lg:grid-cols-2">
                <div>
                  <SectionTitle title="Оценка риска" description={`Окно: ${data.risk.windowDays} дней. Сырые сетевые адреса скрыты.`} />
                  <div className="rounded-[var(--pokrov-radius-card)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-4">
                    <div className="flex items-center justify-between gap-3"><span className="text-3xl font-semibold">{data.risk.score}/100</span><Badge tone={tone(data.risk.level)}>{statusLabel(data.risk.level)}</Badge></div>
                    <div className="mt-4 space-y-2">{data.risk.factors.length ? data.risk.factors.map((factor) => <div key={`${factor.key}-${factor.weight}`} className="flex justify-between gap-3 border-b border-[color:var(--atlas-border)] py-2 text-xs"><span>{riskFactorLabel(factor.key)}</span><span className="font-semibold">+{factor.weight}</span></div>) : <p className="text-xs text-[color:var(--atlas-text-muted)]">Активных факторов риска нет.</p>}</div>
                  </div>
                </div>
                <div>
                  <SectionTitle title="Наблюдатель" description="Сводные количества и ноды без исходных IP-адресов." />
                  <dl className="grid grid-cols-2 gap-2 text-xs">
                    {[
                      ["Адресов за 24 часа", data.observer.observedIpCount24h],
                      ["Нод за 24 часа", data.observer.observedNodeCount24h],
                      ["Пересечений за 24 часа", data.observer.overlapCount24h],
                      ["Адресов за 7 дней", data.observer.observedIpCount7d],
                    ].map(([label, value]) => <div key={String(label)} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3"><dt className="text-[color:var(--atlas-text-muted)]">{label}</dt><dd className="mt-1 text-lg font-semibold">{String(value)}</dd></div>)}
                  </dl>
                  <div className="mt-3 space-y-2">{data.observer.recentNodes.map((node) => <div key={`${node.nodeId}-${node.nodeCode}`} className="rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas)] p-3 text-xs"><span className="font-mono font-semibold">{node.nodeCode?.toUpperCase() || "Нода не указана"}</span><span className="ml-2 text-[color:var(--atlas-text-muted)]">{node.scoreIpCount} сетевых адресов · {dateText(node.lastSeenAt)}</span></div>)}</div>
                </div>
              </div>
            </div>
          ) : null}

          {tab === "audit" ? (
            <div className="space-y-4">
              <div>
                <SectionTitle title="История ключей" description="Без произвольных устаревших метаданных и секретных значений." />
                <DetailTable headers={["Время", "Действие", "Нода", "Оператор", "Источник"]} empty="История ключей пуста." rows={data.keyHistory.map((item) => [dateText(item.createdAt), actionLabel(item.action), item.nodeCode?.toUpperCase() || "—", item.actorTgId === null ? "Не указан" : String(item.actorTgId), item.source === "admin" ? "Админка" : item.source ? "Система" : "Не указан"])} />
              </div>
              <div>
                <SectionTitle title="Действия администраторов" />
                <DetailTable headers={["Время", "Действие", "Оператор"]} empty="Действий администраторов нет." rows={data.adminActions.map((item) => [dateText(item.createdAt), actionLabel(item.action), item.actorTgId === null ? "Не указан" : String(item.actorTgId)])} />
              </div>
            </div>
          ) : null}

          {tab === "investigation" ? (
            <div>
              <SectionTitle title="Расследование" description="Исходный IP-адрес загружается отдельным запросом с правами администратора только для выбранного пользователя и только при открытой вкладке." />
              {investigationLoading && !investigation ? <LoadingState title="Загружаем данные расследования" description="Общий список и остальные вкладки исходные IP-адреса не запрашивают." /> : null}
              {investigationError ? <ErrorState title="Данные расследования недоступны" description={investigationError} action={<Button tone="secondary" onClick={onInvestigationRetry}><RefreshCw size={15} /> Повторить</Button>} /> : null}
              {investigation ? (
                <DetailTable headers={["IP-адрес", "Нода", "Учитывается в риске", "Последний раз"]} empty="Исходные IP-адреса наблюдения для пользователя отсутствуют." rows={investigation.observer.recentIps.map((item) => [
                  <code key="ip" className="font-mono text-xs">{item.sourceIp}</code>,
                  item.nodeCode?.toUpperCase() || item.nodeName || "Не указана",
                  <Badge key="risk" tone={item.countsForSuspicion ? "warning" : "neutral"}>{item.countsForSuspicion ? "Да" : "Нет"}</Badge>,
                  dateText(item.lastSeenAt),
                ])} />
              ) : null}
            </div>
          ) : null}
        </section>
      </Card>
    </div>
  );
}
