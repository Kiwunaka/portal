"use client";

import AppRouteLink from "@/components/app-route-link";
import { fetchNodeStatus } from "@/lib/api";
import { getPortalPublicConfig } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useMemo, useState } from "react";

const config = getPortalPublicConfig(process.env as Record<string, string | undefined>);

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ru-RU");
}

function formatGb(value?: number | null): string {
  if (!Number.isFinite(Number(value))) return "0 ГБ";
  return `${Number(value || 0).toLocaleString("ru-RU", { maximumFractionDigits: 1 })} ГБ`;
}

function isTrialLike(subType?: string | null): boolean {
  const value = String(subType || "").toUpperCase();
  return value.includes("TRIAL") || value.includes("FREE");
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

  const trialMode = isTrialLike(dash?.sub_type || dash?.current_plan_code || user?.sub_type);

  const usageCards = useMemo(
    () => [
      {
        label: "Статус",
        value: dash?.is_active ? "Активен" : "Требует продления",
        hint: dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Срок не указан",
      },
      {
        label: "Использовано",
        value: formatGb(dash?.used_gb),
        hint: `Осталось ${formatGb(dash?.remaining_gb)}`,
      },
      {
        label: "Устройства",
        value: String(dash?.active_sessions ?? 0),
        hint: `Лимит устройств ${dash?.device_limit ?? user?.limits?.device_limit ?? 1}`,
      },
      {
        label: "Точки подключения",
        value: nodeHealth.total ? `${nodeHealth.healthy}/${nodeHealth.total}` : String((user?.nodes || []).length || 0),
        hint: nodeHealth.updatedAt ? `Обновлено ${formatDate(nodeHealth.updatedAt)}` : "Показываем текущее состояние профиля",
      },
    ],
    [dash, nodeHealth, user?.limits?.device_limit, user?.nodes],
  );

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-slate-500">usage snapshot</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Сводка по использованию</h1>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
          Здесь мы показываем только реальные данные профиля: срок доступа, трафик, устройства и состояние точек подключения.
        </p>
      </section>

      <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
        {usageCards.map((card) => (
          <article key={card.label} className="glass-card p-5">
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
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-orange-500">trial / free</p>
              <h2 className="mt-2 font-display text-2xl font-semibold">Хотите больше трафика и устройств?</h2>
              <p className="mt-2 max-w-2xl text-sm text-slate-600 dark:text-slate-300">
                Тест и базовый доступ созданы, чтобы быстро проверить скорость и запуск. Для постоянного использования без жёстких ограничений лучше сразу перейти к тарифам.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <AppRouteLink href="/dashboard/subscription" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
                Смотреть тарифы
              </AppRouteLink>
              <AppRouteLink href={config.botUrl} target="_blank" hardNavigate={false} className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
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
              Тариф: <span className="font-semibold text-slate-900 dark:text-white">{dash?.current_plan_code || dash?.sub_type || "—"}</span>
            </p>
            <p>Ссылка доступа: {user?.subscription_url ? "готова" : "пока недоступна"}</p>
            <p>Объём профиля: {formatGb(dash?.total_gb)}</p>
            <p>Скорость: {dash?.speed_limit_mbps ? `${dash.speed_limit_mbps} Мбит/с` : "по текущей политике профиля"}</p>
            <p>Семейные слоты: {dash?.family_slots ?? user?.family_slots ?? 0}</p>
          </div>
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Что делать, если цифры не сходятся</h2>
          <ul className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <li>Обновите страницу после смены тарифа или нового подключения.</li>
            <li>Если точек подключения стало меньше ожидаемого, откройте поддержку или Telegram-бот.</li>
            <li>Если нужен апгрейд по устройствам и трафику, переходите в раздел подписки.</li>
          </ul>
          <div className="mt-4 flex flex-wrap gap-2">
            <AppRouteLink href="/dashboard/subscription" className="outline-btn rounded-xl px-4 py-2 text-sm font-semibold">
              Раздел подписки
            </AppRouteLink>
            <AppRouteLink href={config.supportTelegramUrl} target="_blank" hardNavigate={false} className="btn-primary rounded-xl px-4 py-2 text-sm font-semibold">
              Написать в поддержку
            </AppRouteLink>
          </div>
          {nodesError ? <p className="mt-3 text-xs text-amber-600 dark:text-amber-300">Не удалось обновить статус точек подключения: {nodesError}</p> : null}
        </article>
      </section>
    </main>
  );
}
