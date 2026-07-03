"use client";

import AppRouteLink from "@/components/app-route-link";
import { icon } from "@/components/cabinet/icon";
import {
  CabinetActionCard,
  CabinetActionGrid,
  CabinetGroup,
  CabinetRow,
  CabinetStatus,
  CabinetTile,
  CabinetTiles,
} from "@/components/cabinet/surface";
import { Button } from "@/components/cabinet/ui";
import { useCountUp } from "@/components/cabinet/use-count-up";
import {
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { getCopyText } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";

function formatDate(value?: string | null): string {
  if (!value) return "уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "уточняется";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function formatDateTime(value?: string | null): string {
  if (!value) return "недавно";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "недавно";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function formatCount(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.round(Number(value))));
}

function getDaysRemaining(expiryAt?: string | null): number | null {
  if (!expiryAt) return null;
  const expiry = new Date(expiryAt);
  if (Number.isNaN(expiry.getTime())) return null;
  const diff = expiry.getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

function deviceTitle(name?: string | null, platform?: string | null): string {
  const cleanName = String(name || "").trim();
  const cleanPlatform = String(platform || "").trim();
  if (cleanName && cleanPlatform) return `${cleanName} · ${cleanPlatform}`;
  return cleanName || cleanPlatform || "Устройство";
}

export default function DashboardPage() {
  const { user, dash } = usePortalSession();
  const accessState = getAccessState(dash, user);
  const trialMode = isTrialPremiumState(accessState);
  const softMode = isSoftModeState(accessState);
  const nextResetAt = getNextResetAt(dash, user);
  const daysRemaining = getDaysRemaining(dash?.expiry_at);
  const planLabel = resolvePlanLabel(dash, user);
  const trafficText = resolveTrafficStatusText(dash, user);
  const deviceLimit = getDeviceLimit(dash, user);
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const isActive = Boolean(dash?.is_active);
  const animatedDeviceCount = useCountUp(Math.max(0, Math.round(Number(deviceCount) || 0)));
  const animatedConnections = useCountUp(Math.max(0, Math.round(Number(activeConnections) || 0)));

  const statusTone = !isActive ? "warning" : softMode ? "warning" : "success";
  const statusTitle = !isActive ? "Доступ закончился" : softMode ? "Скорость ограничена" : "Доступ активен";
  const statusMeta = isActive ? `${planLabel} · до ${formatDate(dash?.expiry_at)}` : "Продление вернет доступ в этом аккаунте";
  const statusBody = !isActive
    ? "Продлите срок и снова подключайтесь в приложении."
    : softMode
      ? `Лимит обновится ${nextResetAt ? formatDate(nextResetAt) : "после обновления профиля"}.`
      : trialMode
        ? `Пробный период работает${daysRemaining !== null ? `, осталось ${formatCount(daysRemaining)} дн.` : "."}`
        : "Откройте приложение и нажмите Подключить.";
  const primaryHref = isActive ? "/downloads/" : "/subscription/checkout/";
  const primaryLabel = isActive ? "Скачать приложение" : "Продлить";
  const emblemName = !isActive ? "lock" : softMode ? "warning" : "verified_user";

  const deviceRows = (user?.devices || []).slice(0, 2);

  return (
    <main className="cab-page cab-page--wide">
      <CabinetStatus
        title={statusTitle}
        meta={statusMeta}
        body={statusBody}
        tone={statusTone}
        emblem={icon(emblemName, "h-7 w-7")}
        action={
          <Button href={primaryHref} className="w-full sm:w-auto">
            {primaryLabel}
          </Button>
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Сводка</h2>
        <CabinetTiles>
          <CabinetTile icon={icon("speed")} label="Трафик" value={dash?.traffic_policy?.kind === "unlimited" ? "Безлимит" : trafficText} tone="info" />
          <CabinetTile
            icon={icon("devices")}
            label="Устройства"
            value={`${formatCount(animatedDeviceCount)} из ${formatCount(deviceLimit)}`}
            hint="Подключенные"
            tone="neutral"
            href="/devices/"
          />
          <CabinetTile
            icon={icon("wifi_tethering")}
            label="Подключения"
            value={
              activeConnections > 0 ? (
                <span className="inline-flex items-center gap-2">
                  <span className="status-dot status-dot-online" aria-hidden="true" />
                  {formatCount(animatedConnections)} активно
                </span>
              ) : (
                "нет активных"
              )
            }
            tone="success"
          />
          <CabinetTile icon={icon("event_available")} label="Доступ до" value={formatDate(dash?.expiry_at)} tone="neutral" href="/subscription/" />
        </CabinetTiles>
      </section>

      <section className="flex flex-col gap-2.5">
        <h2 className="cab-eyebrow px-1">Быстрый доступ</h2>
        <CabinetActionGrid>
          <CabinetActionCard icon={icon("key")} title="Активировать код" hint="Оплата, подарок или промокод" href="/redeem/" />
          <CabinetActionCard icon={icon("support_agent")} title={getCopyText("webapp.dashboard.support_cta", "Помощь")} hint="Обращения и Telegram" href="/support/" />
        </CabinetActionGrid>
      </section>

      {deviceRows.length ? (
        <CabinetGroup title="Последние устройства" action={<AppRouteLink href="/devices/" className="cab-link">Все</AppRouteLink>}>
          {deviceRows.map((device) => (
            <CabinetRow
              key={device.id}
              icon={icon(device.platform?.toLowerCase().includes("win") ? "desktop_windows" : "smartphone")}
              label={deviceTitle(device.name, device.platform)}
              value={device.is_current ? "сейчас" : formatDateTime(device.last_seen_at)}
              href="/devices/"
            />
          ))}
        </CabinetGroup>
      ) : null}
    </main>
  );
}
