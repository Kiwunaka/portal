"use client";

import { useMemo } from "react";

import { icon } from "@/components/cabinet/icon";
import { CabinetGroup, CabinetRow, CabinetStatus, CabinetTile, CabinetTiles } from "@/components/cabinet/surface";
import { Button } from "@/components/cabinet/ui";
import { getAccessState, getDeviceLimit, getTrafficLimitGb, isFreeMonthlyState, isPaidUnlimitedState, isTrialPremiumState } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";

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
        ? `Базовый режим: до ${deviceLimit} устройств и около ${freeLimitGb || 5} ГБ в месяц.`
        : "Если срок закончился, сначала верните доступ.";

  return (
    <main className="cab-page">
      <CabinetStatus
        title="Устройства"
        meta={`${formatCount(knownAppDevices)} из ${formatCount(deviceLimit)} в профиле`}
        body="Проверьте, какие телефоны и компьютеры уже связаны. Новый экран начинается с загрузки приложения."
        tone={devices.length ? "success" : "neutral"}
        emblem={icon("devices", "h-7 w-7")}
        action={
          <Button href="/downloads/" className="w-full sm:w-auto">
            Скачать
          </Button>
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Сводка</h2>
        <CabinetTiles>
          <CabinetTile icon={icon("wifi_tethering")} label="Подключений сейчас" value={`${formatCount(activeConnections)} из ${formatCount(deviceLimit)}`} hint="Живые подключения" tone="success" />
          <CabinetTile icon={icon("devices")} label="Известных устройств" value={formatCount(knownAppDevices)} hint="Связаны с аккаунтом" tone="neutral" />
          <CabinetTile icon={icon("hub")} label="Точек доступа" value={`${formatCount(activeNodes)} из ${formatCount(knownNodes)}`} hint="Счетчик готовности" tone="info" />
          <CabinetTile icon={icon("group")} label="Людей онлайн" value={formatCount(activeUsersEstimate)} hint="Ориентир по сети" tone="neutral" />
        </CabinetTiles>
      </section>

      <CabinetGroup title="Список">
        {devices.length ? (
          devices.map((device) => (
            <CabinetRow
              key={device.id}
              icon={icon(device.platform === "windows" ? "desktop_windows" : "smartphone")}
              label={deviceTitle(device.name, device.platform)}
              hint={device.is_current ? "Это текущее устройство" : device.last_seen_at ? `Было в сети ${formatDate(device.last_seen_at)}` : "Появится после входа в приложение"}
              value={device.is_current ? "сейчас" : device.is_active ? "связано" : "нет активности"}
            />
          ))
        ) : (
          <CabinetRow icon={icon("add_circle")} label="Пока устройств нет" hint="Поставьте приложение и войдите в тот же аккаунт" href="/downloads/" />
        )}
      </CabinetGroup>

      <CabinetGroup title="Действия">
        <CabinetRow icon={icon("download")} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
        <CabinetRow icon={icon("payments")} label="Проверить доступ" hint={modeHint} href="/subscription/" />
        <CabinetRow icon={icon("support_agent")} label="Поддержка" hint="Если устройство не появилось" href="/support/" />
      </CabinetGroup>
    </main>
  );
}
