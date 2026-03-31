"use client";

import AppRouteLink from "@/components/app-route-link";
import SubscriptionQrCard from "@/components/subscription-qr-card";
import { fetchNodeStatus, type NodeStatus } from "@/lib/api";
import { getCopyText } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import { useEffect, useMemo, useState } from "react";

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

export default function DashboardPage() {
  const { user, dash } = usePortalSession();
  const [nodes, setNodes] = useState<NodeStatus[]>([]);
  const [nodesError, setNodesError] = useState("");
  const [nodesLoading, setNodesLoading] = useState(false);
  const [keyVisible, setKeyVisible] = useState(false);
  const [qrVisible, setQrVisible] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "ok" | "fail">("idle");

  const connectionKey = String(dash?.subscription_url || "").trim();
  const isTrialLike = ["FREE", "TRIAL", "BONUS"].includes(String(dash?.sub_type || "").toUpperCase()) || String(dash?.current_plan_code || "") === "trial";
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

  const nextStepTitle = dash?.is_active
    ? isTrialLike
      ? "🚀 Тест запущен! Самое время открыть YouTube, TikTok или любимые сайты и проверить скорость. Спойлер: скорее всего, вам понравится."
      : "✨ Всё работает как надо. Пользуйтесь свободным интернетом, а статистика, настройки и продление всегда под рукой."
    : "⏸ Ваш профиль ожидает продления. Верните безлимитный интернет в пару кликов!";

  const nextStepBody = dash?.is_active
    ? isTrialLike
      ? "Откройте приложение, проверьте YouTube, TikTok, сайты и привычные сценарии. Если всё устраивает, следующий шаг — апгрейд на платный тариф."
      : "Здесь уже собраны ключ, QR, приложения и кнопка продления. Ничего дополнительно искать не нужно."
    : "Если платежный шлюз временно перегружен, мы предложим комфортно оплатить через Telegram.";

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
              {dash?.is_active ? "online" : "pending"}
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
            <p>Ваш тариф: {dash?.current_plan_code || dash?.sub_type || "—"}</p>
            <p>До окончания: {fmtDate(dash?.expiry_at)}</p>
            <p>Лимит устройств: {dash?.device_limit ?? "—"}</p>
            <p>Подключений сейчас: {dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? "—"}</p>
            <p>Активные серверы: {connectionPointsLabel}</p>
          </div>
          {nodesLoading && !nodes.length ? <p className="mt-3 text-xs text-slate-500">Проверяем точки подключения...</p> : null}
          {nodesError ? <p className="mt-3 text-xs text-rose-500">{nodesError}</p> : null}
        </article>
      </section>

      {isTrialLike ? (
        <section className="glass-card p-6">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-300">trial-first</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Вы в бонусном периоде! Наслаждайтесь высокой скоростью, а после выберите удобный тариф.</h2>
          <p className="mt-3 max-w-3xl text-sm text-slate-600 dark:text-slate-300">
            Проверьте сервис на своих устройствах и в привычных сценариях. Если всё устраивает, переходите в тарифы и продлевайте без повторной настройки.
          </p>
        </section>
      ) : null}

      <section className="glass-card p-7">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">ключ и QR</p>
            <h2 className="mt-2 font-display text-3xl font-bold">Показать, скопировать или открыть по QR</h2>
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
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Ваша премиум-ссылка</p>
            <p className="mt-3 break-all font-mono text-xs leading-6 text-slate-700 dark:text-slate-200">
              {maskKey(connectionKey, keyVisible)}
            </p>
            <p className="mt-3 text-xs text-slate-500">Используйте эту ссылку только на своих устройствах.</p>
            {copyState === "ok" ? <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-300">Ссылка скопирована.</p> : null}
            {copyState === "fail" ? <p className="mt-2 text-xs text-rose-500">Ой, ссылка не скопировалась. Попробуйте еще раз.</p> : null}
          </article>

          <article className="rounded-2xl border border-white/45 bg-white/65 p-4 dark:border-white/10 dark:bg-white/5">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">Умный Умный QR-код доступа доступа</p>
            <SubscriptionQrCard value={connectionKey} active={qrVisible} />
          </article>
        </div>
      </section>
    </main>
  );
}
