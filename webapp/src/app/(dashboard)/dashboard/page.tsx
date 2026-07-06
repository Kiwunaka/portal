"use client";

import {
  CalendarCheck,
  Gauge,
  KeyRound,
  LifeBuoy,
  Lock,
  MonitorSmartphone,
  ShieldCheck,
  Smartphone,
  TriangleAlert,
  Wifi,
} from "lucide-react";

import AppRouteLink from "@/components/app-route-link";
import { StatusHero } from "@/components/cabinet/status-hero";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import { Meter } from "@/components/ui/meter";
import { ActionCard, ActionGrid, Tile, TileGrid } from "@/components/ui/tiles";
import {
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { getCopyText, getTariffPlan, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { formatDays } from "@/lib/ru-plural";

const TRIAL_DAYS = 5;

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
  const statusIcon = !isActive ? Lock : softMode ? TriangleAlert : ShieldCheck;

  const planDays = trialMode ? TRIAL_DAYS : getTariffPlan(normalizePlanCode(dash?.current_plan_code))?.duration_days || null;
  const runway =
    isActive && daysRemaining !== null && planDays
      ? { days: daysRemaining, value: Math.min(daysRemaining, planDays), max: planDays }
      : null;
  const runwayTone = daysRemaining !== null && daysRemaining <= 3 ? "danger" : daysRemaining !== null && daysRemaining <= 7 ? "warning" : "ok";

  const deviceRows = (user?.devices || []).slice(0, 2);

  return (
    <main className="mx-auto flex w-full max-w-[980px] flex-col gap-5">
      <StatusHero
        title={statusTitle}
        meta={statusMeta}
        body={statusBody}
        tone={statusTone}
        icon={statusIcon}
        action={
          <Button href={primaryHref} className="w-full sm:w-auto">
            {primaryLabel}
          </Button>
        }
      >
        {runway ? (
          <div className="flex flex-col gap-1.5">
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className="font-semibold text-ink">Осталось {formatDays(runway.days)}</span>
              <span className="text-ink-muted">план на {formatDays(runway.max)}</span>
            </div>
            <Meter value={runway.value} max={runway.max} tone={runwayTone} label="Оставшийся срок доступа" />
          </div>
        ) : null}
      </StatusHero>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Сводка</h2>
        <TileGrid>
          <Tile icon={Gauge} label="Трафик" value={dash?.traffic_policy?.kind === "unlimited" ? "Безлимит" : trafficText} tone="info" />
          <Tile
            icon={MonitorSmartphone}
            label="Устройства"
            value={`${formatCount(deviceCount)} из ${formatCount(deviceLimit)}`}
            hint="Подключенные"
            tone="neutral"
            href="/devices/"
          />
          <Tile
            icon={Wifi}
            label="Подключения"
            value={
              activeConnections > 0 ? (
                <span className="inline-flex items-center gap-2">
                  <span className="relative flex size-2" aria-hidden="true">
                    <span className="absolute inline-flex h-full w-full rounded-full bg-status-green opacity-60 motion-safe:animate-[ping_2.4s_cubic-bezier(0,0,0.2,1)_infinite]" />
                    <span className="relative inline-flex size-2 rounded-full bg-status-green" />
                  </span>
                  {formatCount(activeConnections)} активно
                </span>
              ) : (
                "нет активных"
              )
            }
            tone="success"
          />
          <Tile icon={CalendarCheck} label="Доступ до" value={formatDate(dash?.expiry_at)} tone="neutral" href="/subscription/" />
        </TileGrid>
      </section>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-muted uppercase">Быстрый доступ</h2>
        <ActionGrid>
          <ActionCard icon={KeyRound} title="Активировать код" hint="Оплата, подарок или промокод" href="/redeem/" />
          <ActionCard
            icon={LifeBuoy}
            title={getCopyText("webapp.dashboard.support_cta", "Помощь")}
            hint="Обращения и Telegram"
            href="/support/"
          />
        </ActionGrid>
      </section>

      {deviceRows.length ? (
        <GroupedSection
          title="Последние устройства"
          action={
            <AppRouteLink href="/devices/" className="text-sm font-semibold text-brand hover:text-brand-strong">
              Все
            </AppRouteLink>
          }
        >
          {deviceRows.map((device) => (
            <Row
              key={device.id}
              icon={device.platform?.toLowerCase().includes("win") ? MonitorSmartphone : Smartphone}
              label={deviceTitle(device.name, device.platform)}
              value={device.is_current ? "сейчас" : formatDateTime(device.last_seen_at)}
              href="/devices/"
            />
          ))}
        </GroupedSection>
      ) : null}
    </main>
  );
}
