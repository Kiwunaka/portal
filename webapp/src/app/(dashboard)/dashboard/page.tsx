"use client";

import AppRouteLink from "@/components/app-route-link";
import SubscriptionQrCard from "@/components/subscription-qr-card";
import {
  formatTrafficGb,
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  getTrafficLimitGb,
  isFreeMonthlyState,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { fetchNodeStatus, type NodeStatus } from "@/lib/api";
import { getCopyText } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useMemo, useState } from "react";

const ACTIVE_USERS_LABEL = "Пользователей по IP сейчас";
const ACTIVE_USERS_HINT = "Оценка по живым IP, но не выше уникальных IP за 24 часа. Не точное число людей.";

function fmtDate(value?: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString("ru-RU");
}

function maskKey(value: string, shown: boolean): string {
  if (shown) return value;
  if (!value) return "—";
  if (value.length < 16) return "••••••••";
  return `${value.slice(0, 8)}••••••••••••${value.slice(-8)}`;
}

function fmtMetricCount(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "—";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.round(Number(value))));
}

export default function DashboardPage() {
  const { user, dash } = usePortalSession();
  const [nodes, setNodes] = useState<NodeStatus[]>([]);
  const [nodesError, setNodesError] = useState("");
  const [nodesLoading, setNodesLoading] = useState(false);
  const [keyVisible, setKeyVisible] = useState(false);
  const [qrVisible, setQrVisible] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "ok" | "fail">("idle");

  const connectionKey = String(dash?.subscription_url || "").trim();
  const accessState = getAccessState(dash, user);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const softMode = isSoftModeState(accessState);
  const primaryHref = dash?.is_active ? "/dashboard/downloads/" : "/subscription/checkout/";
  const primaryLabel = dash?.is_active
    ? "Мои приложения"
    : getCopyText("webapp.dashboard.primary_cta", "Продлить доступ");

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(() => {
      const load = async () => {
        setNodesLoading(true);
        try {
          const rows = await fetchNodeStatus();
          if (!cancelled) {
            setNodes(rows);
            setNodesError("");
          }
        } catch (error) {
          if (!cancelled) {
            setNodesError(String((error as { message?: string })?.message || error || ""));
          }
        } finally {
          if (!cancelled) {
            setNodesLoading(false);
          }
        }
      };
      void load();
    }, 900);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

  const healthyNodes = useMemo(() => nodes.filter((node) => node.is_healthy).length, [nodes]);
  const plannedNodes = user?.nodes?.length || 0;
  const connectionPointsLabel = nodes.length ? `${healthyNodes}/${nodes.length}` : plannedNodes ? `${plannedNodes}` : "—";
  const deviceLimit = getDeviceLimit(dash, user);
  const activeConnectionsNow = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? null;
  const activeUsersEstimate = dash?.connection_snapshot?.active_users_estimate ?? user?.connections?.active_users_estimate ?? null;
  const freeLimitGb = getTrafficLimitGb(dash, user);
  const nextResetAt = getNextResetAt(dash, user);

  const onCopyKey = async (): Promise<void> => {
    if (!connectionKey) return;
    try {
      await navigator.clipboard.writeText(connectionKey);
      setCopyState("ok");
    } catch {
      setCopyState("fail");
    }
    window.setTimeout(() => setCopyState("idle"), 1800);
  };

  const nextStepTitle = !dash?.is_active
    ? "Профиль ждёт продления"
    : trialMode
      ? "Премиум-период уже активен"
      : softMode
        ? "Мягкий режим до следующего сброса"
        : freeMode
          ? "Бесплатный режим с месячной квотой"
          : "Безлимитный доступ активен";

  const nextStepBody = !dash?.is_active
    ? "Верните полный доступ в пару кликов."
    : trialMode
      ? "Сейчас можно спокойно проверить сервис. После премиум-периода профиль автоматически перейдёт в бесплатный режим 5 ГБ в месяц."
      : softMode
        ? "Месячная квота бесплатного тарифа уже исчерпана, поэтому профиль работает в мягком режиме до следующего сброса."
        : freeMode
          ? `Профиль находится в бесплатном режиме: ${freeLimitGb ? formatTrafficGb(freeLimitGb) : "месячная квота"} и до ${deviceLimit} устройства.`
          : "Пользуйтесь свободным интернетом: здесь уже собраны ключ, QR, приложения и быстрый доступ к продлению.";

  return (
    <main className="space-y-6">
      <section className="grid gap-5 xl:grid-cols-3">
        <article className="glass-card p-7 xl:col-span-2">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">текущий статус</p>
              <h1 className="mt-2 font-display text-4xl font-bold text-emerald-600">
                {dash?.is_active ? "АКТИВЕН" : "ТРЕБУЕТ ДЕЙСТВИЯ"}
              </h1>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{nextStepBody}</p>
            </div>
            <span
              className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] ${
                dash?.is_active ? "bg-emerald-500 text-white" : "bg-amber-400 text-slate-900"
              }`}
            >
              {dash?.is_active ? "активен" : "ожидание"}
            </span>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <AppRouteLink href={primaryHref} className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              {primaryLabel}
            </AppRouteLink>
            <AppRouteLink href="/subscription/" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Перейти к тарифам
            </AppRouteLink>
            <AppRouteLink href="/support/" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              {getCopyText("webapp.dashboard.support_cta", "Служба заботы")}
            </AppRouteLink>
          </div>
        </article>

        <article className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">что делать дальше</p>
          <h2 className="mt-3 font-display text-2xl font-bold">{nextStepTitle}</h2>
          <div className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <p>Тариф: {resolvePlanLabel(dash, user)}</p>
            <p>До окончания: {fmtDate(dash?.expiry_at)}</p>
            <p>Трафик: {resolveTrafficStatusText(dash, user)}</p>
            {freeMode && nextResetAt ? <p>Следующий сброс: {fmtDate(nextResetAt)}</p> : null}
            <p>Лимит устройств: {deviceLimit}</p>
            <p>Активные серверы: {connectionPointsLabel}</p>
          </div>
          <div className="mt-4 grid gap-2">
            <div className="rounded-xl bg-white/70 p-3 dark:bg-white/10">
              <p className="text-xs text-slate-500">Подключений сейчас</p>
              <p className="mt-1 text-2xl font-semibold">{fmtMetricCount(activeConnectionsNow)}</p>
              <p className="mt-1 text-[11px] text-slate-500">Живые соединения на нодах POKROV.</p>
            </div>
            <div className="rounded-xl border border-emerald-200/60 bg-emerald-50/80 p-3 dark:border-emerald-500/30 dark:bg-emerald-500/10">
              <p className="text-xs text-emerald-700 dark:text-emerald-300">{ACTIVE_USERS_LABEL}</p>
              <p className="mt-1 text-2xl font-semibold text-emerald-700 dark:text-emerald-200">{fmtMetricCount(activeUsersEstimate)}</p>
              <p className="mt-1 text-[11px] text-emerald-700/80 dark:text-emerald-200/80">{ACTIVE_USERS_HINT}</p>
            </div>
          </div>
          {nodesLoading && !nodes.length ? <p className="mt-3 text-xs text-slate-500">Проверяем точки подключения...</p> : null}
          {nodesError ? <p className="mt-3 text-xs text-rose-500">{nodesError}</p> : null}
        </article>
      </section>

      {trialMode ? (
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-300">премиум-период</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Сейчас у вас премиум без лимита трафика</h2>
          <p className="mt-3 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
            Проверьте сервис на своих устройствах и в привычных сценариях. После этого можно перейти на paid без повторной настройки.
          </p>
        </section>
      ) : null}

      <section className="glass-card p-7">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">ссылка подключения и QR</p>
            <h2 className="mt-2 font-display text-3xl font-bold">Показать ссылку подключения или открыть QR</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setKeyVisible((prev) => !prev)}
              className="outline-btn rounded-xl px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]"
            >
              {keyVisible ? "Скрыть" : "Показать"}
            </button>
            <button
              type="button"
              onClick={() => setQrVisible((prev) => !prev)}
              className="outline-btn rounded-xl px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]"
            >
              {qrVisible ? "Скрыть QR" : "Показать QR"}
            </button>
            <button
              type="button"
              onClick={() => void onCopyKey()}
              className="btn-primary rounded-xl px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]"
              disabled={!connectionKey}
            >
              Скопировать
            </button>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[1.4fr,0.9fr]">
          <article className="rounded-2xl border border-white/45 bg-white/65 p-4 dark:border-white/10 dark:bg-white/5">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Ссылка подключения</p>
            <p className="mt-3 break-all font-mono text-xs leading-6 text-slate-700 dark:text-slate-200">
              {maskKey(connectionKey, keyVisible)}
            </p>
            <p className="mt-3 text-xs text-slate-500">Используйте эту ссылку только на своих устройствах.</p>
            {copyState === "ok" ? <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-300">Ссылка скопирована.</p> : null}
            {copyState === "fail" ? <p className="mt-2 text-xs text-rose-500">Ссылка не скопировалась. Попробуйте ещё раз.</p> : null}
          </article>

          <article className="rounded-2xl border border-white/45 bg-white/65 p-4 dark:border-white/10 dark:bg-white/5">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">QR для подключения</p>
            <SubscriptionQrCard value={connectionKey} active={qrVisible} />
          </article>
        </div>
      </section>
    </main>
  );
}
