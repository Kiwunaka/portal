"use client";

import { CalendarSync, CreditCard, Download, Gauge, Globe, LifeBuoy, MonitorSmartphone, ShieldCheck, TriangleAlert, Users, Wifi } from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { Tile, TileGrid } from "@/components/ui/tiles";
import { getDeviceLimit, getNextResetAt, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import { getCopyText } from "@/lib/portal";
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
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title={getCopyText("webapp.statistics.title", "Статистика")}
        meta={resolvePlanLabel(dash, user)}
        body={getCopyText("webapp.statistics.subtitle", "Безопасная сводка без личных ссылок, адресов точек доступа и технических параметров.")}
        tone={dash?.is_active ? "success" : "warning"}
        icon={dash?.is_active ? ShieldCheck : TriangleAlert}
        action={
          <Button variant="secondary" href="/support/" className="w-full sm:w-auto">
            Поддержка
          </Button>
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Безопасная сводка</h2>
        <TileGrid>
          <Tile icon={ShieldCheck} label="Режим" value={resolvePlanLabel(dash, user)} hint={dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Дата уточняется"} tone="success" href="/subscription/" />
          <Tile icon={Gauge} label="Трафик" value={formatGb(trafficUsed)} hint={resolveTrafficStatusText(dash, user)} tone="info" />
          <Tile icon={MonitorSmartphone} label="Устройства" value={`${formatCount(deviceCount)} из ${formatCount(deviceLimit)}`} hint="Связанные экраны" tone="neutral" href="/devices/" />
          <Tile icon={Wifi} label="Подключения сейчас" value={formatCount(activeConnections)} hint="Живая активность" tone="success" />
          <Tile icon={Users} label="Людей онлайн" value={formatCount(activeUsersEstimate)} hint="Ориентир, не список" tone="neutral" />
          <Tile icon={Globe} label="Точки доступа" value={`${formatCount(activeNodes)} из ${formatCount(knownNodes)}`} hint="Счетчик готовности" tone="info" />
          <Tile icon={CalendarSync} label="Обновление лимита" value={nextResetAt ? formatDate(nextResetAt) : "не нужно"} hint="Для текущего режима" tone="neutral" />
        </TileGrid>
      </section>

      <GroupedSection title="Действия">
        <Row icon={LifeBuoy} label="Открыть поддержку" hint="Если цифры выглядят странно" href="/support/" />
        <Row icon={CreditCard} label="Продлить доступ" hint="Срок и тарифы" href="/subscription/" />
        <Row icon={Download} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
      </GroupedSection>
    </main>
  );
}
