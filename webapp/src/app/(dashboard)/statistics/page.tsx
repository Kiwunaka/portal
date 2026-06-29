"use client";

import { icon } from "@/components/cabinet/icon";
import { CabinetGroup, CabinetRow, CabinetStatus, CabinetTile, CabinetTiles } from "@/components/cabinet/surface";
import { Button } from "@/components/cabinet/ui";
import { getDeviceLimit, getNextResetAt, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";

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
    <main className="cab-page">
      <CabinetStatus
        title="Статистика"
        meta={resolvePlanLabel(dash, user)}
        body="Безопасная сводка без личных ссылок, адресов точек доступа и технических параметров."
        tone={dash?.is_active ? "success" : "warning"}
        emblem={icon(dash?.is_active ? "verified_user" : "warning", "h-7 w-7")}
        action={
          <Button variant="secondary" href="/support/" className="w-full sm:w-auto">
            Поддержка
          </Button>
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Безопасная сводка</h2>
        <CabinetTiles>
          <CabinetTile icon={icon("verified_user")} label="Режим" value={resolvePlanLabel(dash, user)} hint={dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Дата уточняется"} tone="success" href="/subscription/" />
          <CabinetTile icon={icon("speed")} label="Трафик" value={formatGb(trafficUsed)} hint={resolveTrafficStatusText(dash, user)} tone="info" />
          <CabinetTile icon={icon("devices")} label="Устройства" value={`${formatCount(deviceCount)} из ${formatCount(deviceLimit)}`} hint="Связанные экраны" tone="neutral" href="/devices/" />
          <CabinetTile icon={icon("wifi_tethering")} label="Подключения сейчас" value={formatCount(activeConnections)} hint="Живая активность" tone="success" />
          <CabinetTile icon={icon("group")} label="Людей онлайн" value={formatCount(activeUsersEstimate)} hint="Ориентир, не список" tone="neutral" />
          <CabinetTile icon={icon("hub")} label="Точки доступа" value={`${formatCount(activeNodes)} из ${formatCount(knownNodes)}`} hint="Счетчик готовности" tone="info" />
          <CabinetTile icon={icon("event_repeat")} label="Обновление лимита" value={nextResetAt ? formatDate(nextResetAt) : "не нужно"} hint="Для текущего режима" tone="neutral" />
        </CabinetTiles>
      </section>

      <CabinetGroup title="Действия">
        <CabinetRow icon={icon("support_agent")} label="Открыть поддержку" hint="Если цифры выглядят странно" href="/support/" />
        <CabinetRow icon={icon("payments")} label="Продлить доступ" hint="Срок и тарифы" href="/subscription/" />
        <CabinetRow icon={icon("download")} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
      </CabinetGroup>
    </main>
  );
}
