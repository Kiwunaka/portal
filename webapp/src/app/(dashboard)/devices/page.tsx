"use client";

import { useMemo } from "react";
import { CirclePlus, CreditCard, Download, Globe, LifeBuoy, MonitorSmartphone, Smartphone, Users, Wifi } from "lucide-react";

import { StatusHero } from "@/components/cabinet/status-hero";
import DevicePairingCard from "@/components/cabinet/device-pairing-card";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { Meter } from "@/components/ui/meter";
import { Tile, TileGrid } from "@/components/ui/tiles";
import { getAccessState, getDeviceLimit, getTrafficLimitGb, isFreeMonthlyState, isPaidUnlimitedState, isTrialPremiumState } from "@/lib/access-policy";
import { getCopyText } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { formatDevicesLimit } from "@/lib/ru-plural";

function formatDate(value?: string | null): string {
  if (!value) return "еще не появлялось";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "дату уточним";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function formatCount(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.round(Number(value))));
}

function deviceTitle(name?: string | null, platform?: string | null): string {
  const cleanName = String(name || "").trim();
  const cleanPlatform = String(platform || "").trim();
  if (cleanName && cleanPlatform) return `${cleanName} · ${cleanPlatform}`;
  return cleanName || cleanPlatform || "Устройство";
}

export default function DevicesPage() {
  const { user, dash } = usePortalSession();

  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const deviceLimit = getDeviceLimit(dash, user);
  const freeLimitGb = getTrafficLimitGb(dash, user);
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const activeUsersEstimate = dash?.connection_snapshot?.active_users_estimate ?? user?.connections?.active_users_estimate ?? 0;
  const activeNodes = dash?.connection_snapshot?.active_nodes ?? 0;
  const knownNodes = dash?.connection_snapshot?.known_nodes ?? user?.nodes?.length ?? 0;
  const knownAppDevices = user?.sync?.device_count ?? user?.devices?.length ?? 0;

  const devices = useMemo(() => user?.devices || [], [user?.devices]);
  const modeHint = paidMode
    ? "Полный доступ: больше запаса для устройств."
    : trialMode
      ? "Пробный период подходит для проверки основных устройств."
      : freeMode
        ? `Базовый режим: ${formatDevicesLimit(deviceLimit)} и около ${freeLimitGb || 5} ГБ в месяц.`
        : "Если срок закончился, сначала верните доступ.";

  const limitTone = deviceLimit > 0 && knownAppDevices >= deviceLimit ? "warning" : "ok";

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title={getCopyText("webapp.devices.title", "Устройства")}
        meta={`${formatCount(knownAppDevices)} из ${formatCount(deviceLimit)} в профиле`}
        body={getCopyText("webapp.devices.subtitle", "Проверьте, какие телефоны и компьютеры уже связаны. Новый экран начинается с загрузки приложения.")}
        tone={devices.length ? "success" : "neutral"}
        icon={MonitorSmartphone}
        action={
          <Button href="/downloads/" className="w-full sm:w-auto">
            Скачать
          </Button>
        }
      >
        {deviceLimit > 0 ? (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="font-semibold text-ink">Лимит устройств</span>
              <span className="text-ink-soft">
                {formatCount(knownAppDevices)} из {formatCount(deviceLimit)}
              </span>
            </div>
            <Meter value={knownAppDevices} max={deviceLimit} tone={limitTone} label="Использование лимита устройств" />
          </div>
        ) : null}
      </StatusHero>

      <DevicePairingCard />

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Сводка</h2>
        <TileGrid>
          <Tile icon={Wifi} label="Сессий в сети" value={formatCount(activeConnections)} hint="Общий счётчик, не ваши устройства" tone="success" />
          <Tile icon={MonitorSmartphone} label="Известных устройств" value={formatCount(knownAppDevices)} hint="Связаны с аккаунтом" tone="neutral" />
          <Tile icon={Globe} label="Точек доступа" value={`${formatCount(activeNodes)} из ${formatCount(knownNodes)}`} hint="Счетчик готовности" tone="info" />
          <Tile icon={Users} label="Людей онлайн" value={formatCount(activeUsersEstimate)} hint="Ориентир по сети" tone="neutral" />
        </TileGrid>
      </section>

      <GroupedSection title="Список">
        {devices.length ? (
          devices.map((device) => (
            <Row
              key={device.id}
              icon={device.platform === "windows" ? MonitorSmartphone : Smartphone}
              label={deviceTitle(device.name, device.platform)}
              hint={device.is_current ? "Это текущее устройство" : device.last_seen_at ? `Было в сети ${formatDate(device.last_seen_at)}` : "Появится после входа в приложение"}
              value={device.is_current ? "сейчас" : device.is_active ? "связано" : "нет активности"}
            />
          ))
        ) : (
          <Row icon={CirclePlus} label="Пока устройств нет" hint="Поставьте приложение и войдите в тот же аккаунт" href="/downloads/" />
        )}
      </GroupedSection>

      <GroupedSection title="Действия">
        <Row icon={Download} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
        <Row icon={CreditCard} label="Проверить доступ" hint={modeHint} href="/subscription/" />
        <Row icon={LifeBuoy} label="Поддержка" hint="Если устройство не появилось" href="/support/" />
      </GroupedSection>
    </main>
  );
}
