"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { getDeviceLimit, getNextResetAt, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";

function icon(name: string) {
  return <span className="material-symbols-rounded text-[20px]">{name}</span>;
}

function formatDate(value?: string | null): string {
  if (!value) return "не задан";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "не задан";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function formatCount(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.round(Number(value))));
}

function formatGb(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "0 ГБ";
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 }).format(Math.max(0, Number(value)))} ГБ`;
}

export default function StatisticsPage() {
  const { user, dash } = usePortalSession();

  const deviceLimit = getDeviceLimit(dash, user);
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const activeUsersEstimate = dash?.connection_snapshot?.active_users_estimate ?? user?.connections?.active_users_estimate ?? 0;
  const activeNodes = dash?.connection_snapshot?.active_nodes ?? user?.connections?.active_nodes ?? 0;
  const knownNodes = dash?.connection_snapshot?.known_nodes ?? user?.connections?.known_nodes ?? user?.nodes?.length ?? 0;
  const trafficUsed = user?.traffic?.used_gb ?? dash?.used_gb ?? 0;
  const nextResetAt = getNextResetAt(dash, user);

  return (
    <main className="mx-auto w-full max-w-[840px] space-y-5">
      <CabinetStatus
        title="Статистика"
        meta={resolvePlanLabel(dash, user)}
        body="Безопасная сводка без личных ссылок, адресов точек доступа и технических параметров."
        tone={dash?.is_active ? "success" : "warning"}
        action={
          <AppRouteLink href="/support/" className="btn-primary w-full rounded-full px-5 py-3 text-center text-sm font-semibold sm:w-auto">
            Поддержка
          </AppRouteLink>
        }
      />

      <CabinetGroup title="Безопасная сводка">
        <CabinetRow icon={icon("verified_user")} label="Режим" hint={dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Дата уточняется"} value={resolvePlanLabel(dash, user)} href="/subscription/" />
        <CabinetRow icon={icon("speed")} label="Трафик" hint={resolveTrafficStatusText(dash, user)} value={formatGb(trafficUsed)} />
        <CabinetRow icon={icon("devices")} label="Устройства" hint="Связанные с профилем экраны" value={`${formatCount(deviceCount)} из ${formatCount(deviceLimit)}`} href="/devices/" />
        <CabinetRow icon={icon("wifi_tethering")} label="Подключения сейчас" hint="Живая активность по профилю" value={formatCount(activeConnections)} />
        <CabinetRow icon={icon("group")} label="Людей онлайн" hint="Ориентир, не список людей" value={formatCount(activeUsersEstimate)} />
        <CabinetRow icon={icon("hub")} label="Точки доступа" hint="Только счетчик готовности" value={`${formatCount(activeNodes)} из ${formatCount(knownNodes)}`} />
        <CabinetRow
          icon={icon("event_repeat")}
          label="Обновление лимита"
          hint="Для текущего режима"
          value={nextResetAt ? formatDate(nextResetAt) : "не нужно"}
        />
      </CabinetGroup>

      <CabinetGroup title="Действия">
        <CabinetRow icon={icon("support_agent")} label="Открыть поддержку" hint="Если цифры выглядят странно" href="/support/" />
        <CabinetRow icon={icon("payments")} label="Продлить доступ" hint="Срок и тарифы" href="/subscription/" />
        <CabinetRow icon={icon("download")} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
      </CabinetGroup>
    </main>
  );
}
