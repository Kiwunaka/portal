"use client";

import { fetchNodeStatus, type NodeStatus } from "@/lib/api";
import SubscriptionQrCard from "@/components/subscription-qr-card";
import { getCopyText } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";
import Link from "next/link";
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
  const [keyVisible, setKeyVisible] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "ok" | "fail">("idle");

  const connectionKey = String(dash?.subscription_url || "").trim();

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
        <article className="glass-card p-7 xl:col-span-2">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">текущий статус</p>
              <h1 className="mt-2 font-display text-4xl font-bold text-emerald-600">{dash?.is_active ? "АКТИВЕН" : "ТРЕБУЕТ ПРОДЛЕНИЯ"}</h1>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
                {dash?.is_active ? "Доступ активен, ссылка подключения готова к работе." : "После оплаты статус обновится автоматически."}
              </p>
            </div>
            <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] ${dash?.is_active ? "bg-emerald-500 text-white" : "bg-amber-400 text-slate-900"}`}>
              {dash?.is_active ? "online" : "pending"}
            </span>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/subscription/checkout/" className="btn-primary rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              {getCopyText("webapp.dashboard.primary_cta", "Открыть оплату")}
            </Link>
            <Link href="/support/" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              {getCopyText("webapp.dashboard.support_cta", "Поддержка")}
            </Link>
            <Link href="/dashboard/downloads/" className="outline-btn rounded-xl px-5 py-2.5 text-sm font-semibold uppercase tracking-[0.12em]">
              Скачать приложения
            </Link>
          </div>
        </article>

        <article className="glass-card p-7">
          <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">профиль</p>
          <div className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            <p>Пользователь: {user?.username ? `@${user.username}` : `ID ${user?.tg_id}`}</p>
            <p>План: {dash?.current_plan_code || dash?.sub_type || "—"}</p>
            <p>До окончания: {fmtDate(dash?.expiry_at)}</p>
            <p>Лимит устройств: {dash?.device_limit ?? "—"}</p>
            <p>Сессии: {dash?.active_sessions ?? "—"}</p>
            <p>Точки подключения online: {nodes.length ? `${healthyNodes}/${nodes.length}` : "—"}</p>
          </div>
          {nodesError ? <p className="mt-3 text-xs text-rose-500">{nodesError}</p> : null}
        </article>
      </section>

      <section className="glass-card p-7">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.16em] text-slate-500">ссылка доступа</p>
            <h2 className="mt-2 font-display text-3xl font-bold">Показать, скопировать или открыть по QR</h2>
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
            <p className="mt-3 break-all font-mono text-xs leading-6 text-slate-700 dark:text-slate-200">{maskKey(connectionKey, keyVisible)}</p>
            <p className="mt-3 text-xs text-slate-500">Передавайте эту ссылку только своим устройствам.</p>
            {copyState === "ok" ? <p className="mt-2 text-xs text-emerald-600 dark:text-emerald-300">Ссылка скопирована.</p> : null}
            {copyState === "fail" ? <p className="mt-2 text-xs text-rose-500">Не удалось скопировать ссылку.</p> : null}
          </article>

          <article className="rounded-2xl border border-white/45 bg-white/65 p-4 dark:border-white/10 dark:bg-white/5">
            <p className="text-xs uppercase tracking-[0.14em] text-slate-500">QR-код</p>
            <SubscriptionQrCard value={connectionKey} />
          </article>
        </div>
      </section>
    </main>
  );
}
