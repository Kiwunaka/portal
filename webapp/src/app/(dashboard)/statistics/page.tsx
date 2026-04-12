"use client";

import AppRouteLink from "@/components/app-route-link";
import {
  formatTrafficGb,
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  getTrafficLimitGb,
  getTrafficRemainingGb,
  isFreeMonthlyState,
  isPaidUnlimitedState,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { fetchNodeStatus } from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);
const ACTIVE_USERS_LABEL = "Пользователей по IP сейчас";
const ACTIVE_USERS_HINT = "Оценка по живым IP, но не выше уникальных IP за 24 часа. Не точное число людей.";

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ru-RU");
}

function formatCount(value: number): string {
  if (!Number.isFinite(value)) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.round(value)));
}

export default function StatisticsPage() {
  const { user, dash } = usePortalSession();
  const [nodeHealth, setNodeHealth] = useState<{ total: number; healthy: number; updatedAt: string }>({
    total: 0,
    healthy: 0,
    updatedAt: "",
  });
  const [nodesError, setNodesError] = useState("");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      try {
        const rows = await fetchNodeStatus();
        if (cancelled) return;
        const healthy = rows.filter((row) => row.is_healthy).length;
        const updatedAt = rows.find((row) => row.updated_at)?.updated_at || "";
        setNodeHealth({ total: rows.length, healthy, updatedAt });
        setNodesError("");
      } catch (error) {
        if (!cancelled) {
          setNodesError(String((error as { message?: string })?.message || error || ""));
        }
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const accessState = getAccessState(dash, user);
  const trialMode = isTrialPremiumState(accessState);
  const paidMode = isPaidUnlimitedState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const softMode = isSoftModeState(accessState);
  const limitGb = getTrafficLimitGb(dash, user);
  const remainingGb = getTrafficRemainingGb(dash, user);
  const nextResetAt = getNextResetAt(dash, user);
  const usedGb = Number(dash?.used_gb || user?.traffic?.used_gb || 0);
  const deviceLimit = getDeviceLimit(dash, user);
  const activeUsersEstimate = Math.max(0, Number(dash?.connection_snapshot?.active_users_estimate ?? user?.connections?.active_users_estimate ?? 0));

  const trafficCard = useMemo(() => {
    if (paidMode || trialMode) {
      return {
        label: "Трафик",
        value: "Безлимитный",
        hint: `Использовано ${formatTrafficGb(usedGb)}`,
      };
    }
    if (softMode) {
      return {
        label: "Трафик",
        value: "Мягкий режим",
        hint: nextResetAt ? `До сброса ${formatDate(nextResetAt)}` : "До следующего месячного сброса",
      };
    }
    if (freeMode && limitGb != null) {
      return {
        label: "Трафик",
        value: `${formatTrafficGb(usedGb)} из ${formatTrafficGb(limitGb)}`,
        hint: nextResetAt ? `Сброс ${formatDate(nextResetAt)}` : "Месячный лимит бесплатного тарифа",
      };
    }
    return {
      label: "Использовано",
      value: formatTrafficGb(usedGb),
      hint: `Осталось ${formatTrafficGb(remainingGb)}`,
    };
  }, [freeMode, limitGb, nextResetAt, paidMode, remainingGb, softMode, trialMode, usedGb]);

  const usageCards = useMemo<Array<{ label: string; value: string; hint: string; tone?: "emerald" }>>(
    () => [
      {
        label: "Статус",
        value: dash?.is_active ? "Активен" : "Требует продления",
        hint: dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Срок не указан",
      },
      trafficCard,
      {
        label: "Подключения",
        value: `${dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0} / ${deviceLimit}`,
        hint:
          dash?.active_sessions_source === "panel_ip_count"
            ? "Живой счётчик по runtime-нодам POKROV"
            : "Резервный счётчик по активности на нодах",
      },
      {
        label: ACTIVE_USERS_LABEL,
        value: formatCount(activeUsersEstimate),
        hint: ACTIVE_USERS_HINT,
        tone: "emerald",
      },
      {
        label: "Точки подключения",
        value: nodeHealth.total ? `${nodeHealth.healthy}/${nodeHealth.total}` : String((user?.nodes || []).length || 0),
        hint: nodeHealth.updatedAt ? `Обновлено ${formatDate(nodeHealth.updatedAt)}` : "Показываем текущее состояние профиля",
      },
    ],
    [activeUsersEstimate, dash, deviceLimit, nodeHealth, trafficCard, user?.nodes],
  );

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">сводка</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Сводка по использованию</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Здесь видно трафик, состояние доступа и живые подключения. Метрики собираются по runtime-нодам POKROV, а не
          только по приложению.
        </p>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">
        {usageCards.map((card) => (
          <article
            key={card.label}
            className={
              card.tone === "emerald"
                ? "glass-card border border-emerald-200/60 bg-emerald-50/80 p-5 dark:border-emerald-500/30 dark:bg-emerald-500/10"
                : "glass-card p-5"
            }
          >
            <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">{card.label}</p>
            <p className="mt-3 font-display text-4xl font-bold">{card.value}</p>
            <p className="mt-2 text-xs text-slate-500">{card.hint}</p>
          </article>
        ))}
      </section>

      {trialMode ? (
        <section className="glass-card p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-orange-500">премиум-период</p>
              <h2 className="mt-2 font-display text-2xl font-semibold">Сейчас у вас премиум без лимита трафика</h2>
              <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-300">
                Это стартовый или бонусный премиум-период. После него профиль автоматически перейдёт в бесплатный режим
                на 5 ГБ в месяц, поэтому тариф можно выбрать заранее.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <AppRouteLink href="/subscription" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                Перейти к тарифам
              </AppRouteLink>
              <AppRouteLink
                href={config.botUrl}
                target="_blank"
                hardNavigate={false}
                className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold"
              >
                Продолжить в Telegram
              </AppRouteLink>
            </div>
          </div>
        </section>
      ) : null}

      <section className="grid gap-5 lg:grid-cols-[1.1fr,0.9fr]">
        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Что доступно сейчас</h2>
          <div className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
            <p>
              Тариф: <span className="font-semibold text-slate-900 dark:text-white">{resolvePlanLabel(dash, user)}</span>
            </p>
            <p>Ссылка подключения: {user?.subscription_url ? "готова" : "пока недоступна"}</p>
            <p>Трафик: {resolveTrafficStatusText(dash, user)}</p>
            {freeMode && nextResetAt ? <p>Следующий сброс: {formatDate(nextResetAt)}</p> : null}
            <p>Устройства: до {deviceLimit}</p>
            <p>Скорость: {softMode ? "ограничена до следующего сброса" : dash?.speed_limit_mbps ? `${dash.speed_limit_mbps} Мбит/с` : "по текущей политике профиля"}</p>
            <p>Семейные слоты: {dash?.family_slots ?? user?.family_slots ?? 0}</p>
          </div>
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Как читать эти данные</h2>
          <ul className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <li>Paid отображается как безлимитный трафик и до 5 устройств.</li>
            <li>Free Monthly показывает расход из 5 ГБ и дату следующего месячного сброса.</li>
            <li>Soft mode означает, что месячная квота исчерпана и профиль работает с ограничением до сброса.</li>
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            <AppRouteLink href="/subscription" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
              Раздел подписки
            </AppRouteLink>
            <AppRouteLink
              href={config.supportTelegramUrl}
              target="_blank"
              hardNavigate={false}
              className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold"
            >
              Написать в службу заботы
            </AppRouteLink>
          </div>
          {nodesError ? <p className="mt-3 text-xs text-amber-600 dark:text-amber-300">Не удалось обновить статус точек подключения: {nodesError}</p> : null}
        </article>
      </section>
    </main>
  );
}
