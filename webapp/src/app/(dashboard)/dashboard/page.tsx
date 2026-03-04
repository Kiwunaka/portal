"use client";

import { fetchNodeStatus, type NodeStatus } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

type ComparisonRow = {
  metric: string;
  start: string;
  pro: string;
  ultra: string;
};

const COMPARISON_ROWS: ComparisonRow[] = [
  { metric: "Устройства", start: "1", pro: "До 5", ultra: "До 5" },
  { metric: "Страны", start: "NL", pro: "Польша, Нидерланды, США, Италия", ultra: "Полный пул + приоритет" },
  { metric: "Трафик", start: "Безлимит*", pro: "Безлимит*", ultra: "Безлимит*" },
  { metric: "Маршрутизация", start: "Базовый защищенный маршрут", pro: "Полный маршрут ежедневно", ultra: "Маршрут + приоритетная обработка" },
  { metric: "Скоростной профиль", start: "Базовый", pro: "Высокий (типично 90-95%)", ultra: "Максимальный на близком узле" },
  { metric: "Поддержка", start: "Стандартная", pro: "Быстрый Telegram-ответ", ultra: "Приоритет 24/7" },
];

function planColumn(planCode: string | null | undefined): "start" | "pro" | "ultra" {
  const code = String(planCode || "").trim().toLowerCase();
  if (code === "start_99") return "start";
  if (code === "1_month" || code === "3_months") return "pro";
  return "ultra";
}

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
  const [keyVisible, setKeyVisible] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "ok" | "fail">("idle");

  const connectionKey = String(dash?.subscription_url || "").trim();
  const activeColumn = planColumn(dash?.current_plan_code || dash?.sub_type || "");

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
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
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const healthyNodes = useMemo(() => nodes.filter((node) => node.is_healthy).length, [nodes]);
  const qrUrl = useMemo(() => {
    if (!connectionKey) return "";
    return `https://api.qrserver.com/v1/create-qr-code/?size=220x220&data=${encodeURIComponent(connectionKey)}`;
  }, [connectionKey]);

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

  return (
    <main className="space-y-6">
      <section className="grid gap-5 xl:grid-cols-3">
        <article className="glass-card xl:col-span-2 p-7">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Текущий статус</p>
              <h1 className="mt-2 font-display text-4xl font-bold text-emerald-600">{dash?.is_active ? "АКТИВЕН" : "ТРЕБУЕТ ПРОДЛЕНИЯ"}</h1>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {dash?.is_active
                  ? "Доступ активен. Профиль и ключ подключения готовы к работе."
                  : "Доступ требует продления. После оплаты статус обновится автоматически."}
              </p>
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] ${dash?.is_active ? "bg-emerald-500 text-white" : "bg-amber-400 text-slate-900"}`}>
              {dash?.is_active ? "online" : "pending"}
            </span>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/subscription/checkout/" className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Открыть оплату
            </Link>
            <Link href="/support/" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Поддержка
            </Link>
            <Link href="/dashboard/downloads/" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Скачать клиент
            </Link>
          </div>
        </article>

        <article className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Параметры</p>
          <div className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <p>Пользователь: {user?.username ? `@${user.username}` : `ID ${user?.tg_id}`}</p>
            <p>Тариф: {dash?.sub_type || "—"}</p>
            <p>План: {dash?.current_plan_code || "—"}</p>
            <p>До окончания: {fmtDate(dash?.expiry_at)}</p>
            <p>Лимит устройств: {dash?.device_limit ?? "—"}</p>
            <p>Сессии: {dash?.active_sessions ?? "—"}</p>
            <p>Узлы online: {nodes.length ? `${healthyNodes}/${nodes.length}` : "—"}</p>
          </div>
          {nodesError ? <p className="mt-3 text-xs text-rose-500">{nodesError}</p> : null}
        </article>
      </section>

      <section className="glass-card p-7">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Ключ подключения</p>
            <h2 className="mt-2 font-display text-3xl font-bold">Mask + Reveal + Copy + QR</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={() => setKeyVisible((prev) => !prev)} className="outline-btn rounded-xl px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
              {keyVisible ? "Скрыть" : "Показать"}
            </button>
            <button type="button" onClick={() => void onCopyKey()} className="btn-primary rounded-xl px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]" disabled={!connectionKey}>
              Скопировать
            </button>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[1.4fr,0.9fr]">
          <article className="rounded-2xl border border-white/45 bg-white/65 p-4 dark:border-white/10 dark:bg-white/5">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">URL подключения</p>
            <p className="mt-3 break-all font-mono text-xs leading-6 text-slate-700 dark:text-slate-200">
              {maskKey(connectionKey, keyVisible)}
            </p>
            <p className="mt-3 text-xs text-slate-500">
              Этот ключ используется в клиентах iOS/Android/Desktop. Передавайте его только своим устройствам.
            </p>
            {copyState === "ok" ? <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-300">Ключ скопирован.</p> : null}
            {copyState === "fail" ? <p className="mt-2 text-xs text-rose-500">Не удалось скопировать ключ.</p> : null}
          </article>

          <article className="rounded-2xl border border-white/45 bg-white/65 p-4 dark:border-white/10 dark:bg-white/5">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">QR-код</p>
            {qrUrl ? (
              <Image
                src={qrUrl}
                alt="QR key"
                width={220}
                height={220}
                unoptimized
                className="mt-3 h-[220px] w-[220px] max-w-full rounded-xl border border-white/45 bg-white p-2"
              />
            ) : (
              <p className="mt-3 text-sm text-slate-500">Ключ недоступен</p>
            )}
          </article>
        </div>
      </section>

      <section className="glass-card p-7">
        <div className="mb-4">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">Наглядное сравнение тарифов</p>
          <h2 className="mt-2 font-display text-3xl font-bold">Что выбрать и почему</h2>
        </div>

        <div className="overflow-x-auto rounded-xl border border-white/45 dark:border-white/10">
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="bg-white/55 dark:bg-white/5">
              <tr>
                <th className="px-4 py-3">Параметр</th>
                <th className={`px-4 py-3 ${activeColumn === "start" ? "text-violet-600 dark:text-violet-300" : ""}`}>Start</th>
                <th className={`px-4 py-3 ${activeColumn === "pro" ? "text-violet-600 dark:text-violet-300" : ""}`}>Pro</th>
                <th className={`px-4 py-3 ${activeColumn === "ultra" ? "text-violet-600 dark:text-violet-300" : ""}`}>Ultra</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.metric} className="border-t border-white/40 dark:border-white/10">
                  <td className="px-4 py-3 font-semibold">{row.metric}</td>
                  <td className={`px-4 py-3 ${activeColumn === "start" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.start}</td>
                  <td className={`px-4 py-3 ${activeColumn === "pro" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.pro}</td>
                  <td className={`px-4 py-3 ${activeColumn === "ultra" ? "font-semibold text-violet-600 dark:text-violet-300" : ""}`}>{row.ultra}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">
          Почему часть медиасервисов может идти напрямую: в отдельных сценариях это снижает задержку и помогает стабильнее
          воспроизводить видео. Защищенный канал для основного трафика сохраняется по правилам тарифа.
          Безлимит* относится к объёму трафика, а фактическая скорость зависит от вашей сети и текущей нагрузки.
        </p>
      </section>
    </main>
  );
}
