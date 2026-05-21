"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { StatusBadge } from "@/components/atlas";
import {
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { fetchNodeStatus, type NodeStatus } from "@/lib/api";
import { usePortalSession } from "@/lib/session";

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
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

function getDaysRemaining(expiryAt?: string | null): number | null {
  if (!expiryAt) return null;
  const expiry = new Date(expiryAt);
  if (Number.isNaN(expiry.getTime())) return null;
  const diff = expiry.getTime() - Date.now();
  return Math.max(0, Math.ceil(diff / (1000 * 60 * 60 * 24)));
}

/* ── Components ── */

function StatCard({ label, value, hint, tone = "neutral" }: { label: string; value: ReactNode; hint?: ReactNode; tone?: "success" | "warning" | "danger" | "neutral" }) {
  const toneClasses = {
    success: "border-emerald-200/50 bg-emerald-50/50 dark:bg-emerald-950/20 dark:border-emerald-800/40",
    warning: "border-amber-200/50 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800/40",
    danger: "border-rose-200/50 bg-rose-50/50 dark:bg-rose-950/20 dark:border-rose-800/40",
    neutral: "border-slate-200/50 bg-white/70 dark:bg-slate-900/40 dark:border-slate-700/40",
  };

  return (
    <div className={`bento-card ${toneClasses[tone]}`}>
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">{label}</p>
      <div className="stat-value-lg mt-1">{value}</div>
      {hint ? <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{hint}</div> : null}
    </div>
  );
}

function QuickAction({ icon, label, href, primary = false }: { icon: string; label: string; href: string; primary?: boolean }) {
  return (
    <AppRouteLink href={href} className={`quick-action-btn ${primary ? "primary" : ""}`}>
      <span className="material-symbols-rounded text-[20px]">{icon}</span>
      {label}
    </AppRouteLink>
  );
}

function AlertBanner({ tone, icon, title, children }: { tone: "success" | "warning" | "danger" | "info"; icon: string; title: string; children: ReactNode }) {
  return (
    <div className={`alert-card ${tone}`}>
      <span className="material-symbols-rounded text-[20px] shrink-0 mt-0.5">{icon}</span>
      <div>
        <p className="font-semibold">{title}</p>
        <div className="mt-0.5 opacity-90">{children}</div>
      </div>
    </div>
  );
}

/* ── Main Page ── */

export default function DashboardPage() {
  const { user, dash } = usePortalSession();
  const [nodes, setNodes] = useState<NodeStatus[]>([]);
  const [nodesError, setNodesError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    const load = async () => {
      try {
        const rows = await fetchNodeStatus({ signal: controller.signal });
        if (controller.signal.aborted) return;
        setNodes(rows);
        setNodesError("");
      } catch (error) {
        if (controller.signal.aborted || (error as { name?: string } | null)?.name === "AbortError") return;
        setNodesError(String((error as { message?: string })?.message || error || ""));
      }
    };
    void load();
    return () => controller.abort();
  }, []);

  const accessState = getAccessState(dash, user);
  const trialMode = isTrialPremiumState(accessState);
  const softMode = isSoftModeState(accessState);
  const nextResetAt = getNextResetAt(dash, user);
  const deviceLimit = getDeviceLimit(dash, user);
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const knownNodes = dash?.connection_snapshot?.known_nodes ?? user?.connections?.known_nodes ?? nodes.length;
  const healthyNodes = nodes.filter((node) => node.is_healthy).length;
  const daysRemaining = getDaysRemaining(dash?.expiry_at);

  /* ── Alerts ── */
  const alerts = useMemo(() => {
    const items: Array<ReactNode> = [];

    if (!dash?.is_active) {
      items.push(
        <AlertBanner key="inactive" tone="danger" icon="error" title="Доступ закончился">
          <AppRouteLink href="/subscription/checkout/" className="underline font-semibold">Продлите доступ</AppRouteLink>, чтобы снова подключаться в приложении POKROV.
        </AlertBanner>
      );
    } else if (trialMode) {
      items.push(
        <AlertBanner key="trial" tone="warning" icon="schedule" title="Пробный период">
          Осталось {daysRemaining ?? "—"} дней. Если всё подходит — <AppRouteLink href="/subscription/" className="underline font-semibold">выберите тариф</AppRouteLink> заранее.
        </AlertBanner>
      );
    } else if (softMode) {
      items.push(
        <AlertBanner key="soft" tone="warning" icon="speed" title="Трафик закончился">
          Скорость снижена. Полный доступ вернётся {nextResetAt ? formatDate(nextResetAt) : "скоро"}. <AppRouteLink href="/subscription/checkout/" className="underline font-semibold">Продлите сейчас</AppRouteLink>.
        </AlertBanner>
      );
    }

    if (dash?.is_active && activeConnections === 0) {
      items.push(
        <AlertBanner key="no-conn" tone="info" icon="info" title="Нет активного подключения">
          Откройте приложение POKROV и нажмите <strong>Подключить</strong>. <AppRouteLink href="/downloads/" className="underline font-semibold">Скачать приложение</AppRouteLink>
        </AlertBanner>
      );
    }

    if (nodesError) {
      items.push(
        <AlertBanner key="nodes" tone="info" icon="network_check" title="Статус сети обновим позже">
          Кабинет работает. Если подключение нестабильно — <AppRouteLink href="/support/" className="underline font-semibold">напишите в поддержку</AppRouteLink>.
        </AlertBanner>
      );
    } else if (knownNodes > 0 && healthyNodes < knownNodes) {
      items.push(
        <AlertBanner key="nodes-attention" tone="warning" icon="network_check" title="Часть серверов на обслуживании">
          Готовы {healthyNodes} из {knownNodes} серверов. Если заметили сбои — <AppRouteLink href="/support/" className="underline font-semibold">сообщите нам</AppRouteLink>.
        </AlertBanner>
      );
    }

    if (items.length === 0) {
      items.push(
        <AlertBanner key="all-good" tone="success" icon="check_circle" title="Доступ активен">
          Откройте приложение POKROV и нажмите <strong>Подключить</strong>, когда нужно включить его на устройстве.
        </AlertBanner>
      );
    }

    return items.slice(0, 3);
  }, [activeConnections, dash?.is_active, healthyNodes, knownNodes, daysRemaining, nextResetAt, nodesError, softMode, trialMode]);

  /* ── Device items ── */
  const deviceItems = (user?.devices || []).slice(0, 3).map((device) => ({
    key: device.id,
    title: deviceTitle(device.name, device.platform),
    body: device.is_current
      ? "Это устройство, с которого открыт кабинет"
      : device.last_seen_at
        ? `Было в сети ${formatDateTime(device.last_seen_at)}`
        : "Появится после первого входа в приложение",
    badge: device.is_current ? "Сейчас" : device.is_active ? "Активно" : "Не в сети",
    tone: device.is_current || device.is_active ? ("success" as const) : ("neutral" as const),
  }));

  /* ── Traffic calculation ── */
  const trafficText = resolveTrafficStatusText(dash, user);
  const trafficPercent = useMemo(() => {
    if (dash?.used_gb == null || dash?.total_gb == null) return null;
    const used = Number(dash.used_gb);
    const total = Number(dash.total_gb);
    if (!Number.isFinite(used) || !Number.isFinite(total) || total <= 0) return null;
    return Math.min(100, Math.round((used / total) * 100));
  }, [dash?.used_gb, dash?.total_gb]);

  return (
    <CabinetRoute
      eyebrow="Главная"
      title={dash?.is_active ? "Ваш доступ POKROV" : "Продлите доступ"}
      description={
        dash?.is_active
          ? "Здесь видно срок, устройства, трафик и следующий шаг. Само подключение включается в приложении."
          : "Доступ закончился. Продлите срок, чтобы снова подключаться в приложении POKROV."
      }
      actions={
        <>
          <AppRouteLink
            href={dash?.is_active ? "/downloads/" : "/subscription/checkout/"}
            className="btn-primary rounded-full px-5 py-3 text-sm font-semibold"
          >
            {dash?.is_active ? "Открыть приложение" : "Продлить доступ"}
          </AppRouteLink>
          <AppRouteLink href={dash?.is_active ? "/subscription/" : "/support/"} className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            {dash?.is_active ? "Продлить доступ" : "Поддержка"}
          </AppRouteLink>
        </>
      }
    >
      {/* ── Alerts ── */}
      <div className="grid gap-3">
        {alerts}
      </div>

      {/* ── Stats Bento ── */}
      <div className="bento-grid bento-grid-2 md:bento-grid-2 lg:grid-cols-4">
        <StatCard
          label="Тариф"
          value={
            <div className="flex items-center gap-2">
              {resolvePlanLabel(dash, user)}
              <StatusBadge tone={dash?.is_active ? "success" : "warning"}>{dash?.is_active ? "Активен" : "Закончился"}</StatusBadge>
            </div>
          }
          hint={dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : null}
          tone={dash?.is_active ? "success" : "warning"}
        />
        <StatCard
          label="Осталось дней"
          value={daysRemaining ?? "—"}
          hint={daysRemaining !== null && daysRemaining <= 5 ? "Срок скоро закончится" : null}
          tone={daysRemaining !== null && daysRemaining <= 5 ? "warning" : "neutral"}
        />
        <StatCard
          label="Трафик"
          value={trafficText}
          hint={trafficPercent !== null ? `${trafficPercent}% использовано` : null}
          tone={trafficPercent !== null && trafficPercent >= 90 ? "warning" : "neutral"}
        />
        <StatCard label="Устройства" value={`${formatCount(deviceCount)} / ${formatCount(deviceLimit)}`} />
      </div>

      {/* ── App Download Block ── */}
        <CabinetSection
          eyebrow="Следующий шаг"
        title="Откройте приложение и нажмите «Подключить»"
        description="Кабинет не заменяет приложение: он помогает скачать beta-сборку, проверить устройства, продлить доступ и открыть поддержку."
      >
        <div className="grid gap-6 lg:grid-cols-[0.82fr_1.18fr] items-start">
          <div className="rounded-[1.5rem] border border-emerald-200/60 bg-emerald-50/60 p-5 dark:border-emerald-800/40 dark:bg-emerald-950/20">
            <div className="flex items-center gap-3">
              <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-emerald-700 text-white">
                <span className="material-symbols-rounded text-[24px]">bolt</span>
              </span>
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Быстрый старт</p>
                <p className="mt-1 text-xs leading-5 text-slate-600 dark:text-slate-300">Откройте приложение и нажмите «Подключить».</p>
              </div>
            </div>
            <div className="mt-4 grid gap-2 text-sm text-slate-700 dark:text-slate-300">
              <div className="flex items-center gap-2">
                <span className="material-symbols-rounded text-[18px] text-emerald-700 dark:text-emerald-300">download</span>
                Скачать Android или Windows
              </div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-rounded text-[18px] text-emerald-700 dark:text-emerald-300">sync</span>
                Доступ подтянется автоматически
              </div>
              <div className="flex items-center gap-2">
                <span className="material-symbols-rounded text-[18px] text-emerald-700 dark:text-emerald-300">support_agent</span>
                Если что-то не так, поддержка рядом
              </div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <a
                href="https://pokrov.space/install/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 rounded-xl border border-slate-200/60 bg-white/80 p-4 hover:border-emerald-300 hover:bg-emerald-50/40 transition dark:bg-slate-900/40 dark:border-slate-700/40 dark:hover:border-emerald-700"
              >
                <span className="material-symbols-rounded text-[28px] text-emerald-700 dark:text-emerald-400">android</span>
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Android</p>
                  <p className="text-xs text-slate-500">APK через GitHub Releases</p>
                </div>
              </a>
              <a
                href="https://pokrov.space/install/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 rounded-xl border border-slate-200/60 bg-white/80 p-4 hover:border-emerald-300 hover:bg-emerald-50/40 transition dark:bg-slate-900/40 dark:border-slate-700/40 dark:hover:border-emerald-700"
              >
                <span className="material-symbols-rounded text-[28px] text-emerald-700 dark:text-emerald-400">desktop_windows</span>
                <div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-slate-100">Windows</p>
                  <p className="text-xs text-slate-500">Установщик и портативная</p>
                </div>
              </a>
            </div>
            <div className="rounded-xl border border-slate-200/60 bg-white/60 p-4 dark:bg-slate-900/30 dark:border-slate-700/30">
              <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                <strong>Как подключиться:</strong> установите приложение, продолжите текущий доступ и нажмите <strong>Подключить</strong>.
                Telegram остается запасным способом входа и восстановления, если приложение или кабинет не помогли.
              </p>
            </div>
          </div>
        </div>
      </CabinetSection>

      {/* ── Quick Actions ── */}
      <CabinetSection
        eyebrow="Быстрые действия"
        title="Что делать дальше"
        description="Сначала приложение, затем продление и поддержка, если они понадобятся."
      >
        <div className="quick-action-grid">
          <QuickAction icon="download" label="Скачать приложение" href="https://pokrov.space/install/" primary />
          <QuickAction icon="explore" label="Я запутался" href="/support/#quick-help" />
          <QuickAction icon="payments" label="Продлить доступ" href="/subscription/checkout/" />
          <QuickAction icon="devices" label="Мои устройства" href="/devices/" />
          <QuickAction icon="support_agent" label="Написать в поддержку" href="/support/" />
        </div>
      </CabinetSection>

      {/* ── Devices ── */}
      <CabinetSection
        eyebrow="Устройства"
        title="Что подключено"
        description="Устройства, привязанные к вашему аккаунту."
        actions={
          <AppRouteLink href="/devices/" className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
            Все устройства
          </AppRouteLink>
        }
      >
        <CabinetList items={deviceItems} empty="Устройства появятся после первого входа в приложение на Android или Windows." />
      </CabinetSection>
    </CabinetRoute>
  );
}
