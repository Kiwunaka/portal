"use client";

import AppRouteLink from "@/components/app-route-link";
import { getAccessState, resolvePlanLabel } from "@/lib/access-policy";
import { fetchAccessKeyStatus, redeemAccessKey, type AccessKeyStatusPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

function normalizeKey(value: string): string {
  return String(value || "").trim().toUpperCase();
}

function formatDate(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ru-RU");
}

export default function RedeemPage() {
  const searchParams = useSearchParams();
  const { user, dash, refresh } = usePortalSession();
  const [keyInput, setKeyInput] = useState(() => normalizeKey(searchParams.get("key") || ""));
  const [status, setStatus] = useState<AccessKeyStatusPayload | null>(null);
  const [lookupBusy, setLookupBusy] = useState(false);
  const [redeemBusy, setRedeemBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const lookup = async (rawKey?: string): Promise<AccessKeyStatusPayload | null> => {
    const key = normalizeKey(rawKey ?? keyInput);
    if (!key) {
      setError("Введите activation key, чтобы проверить его статус.");
      return null;
    }

    setLookupBusy(true);
    setError("");
    setMessage("");
    try {
      const nextStatus = await fetchAccessKeyStatus(key);
      setStatus(nextStatus);
      if (!nextStatus.exists) {
        setMessage("Ключ не найден. Проверьте написание или откройте support/recovery.");
      } else if (nextStatus.redeemed) {
        setMessage("Этот ключ уже был погашен. Для восстановления откройте support.");
      } else {
        setMessage("Ключ найден и готов к redeem в текущем app-first аккаунте.");
      }
      return nextStatus;
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось проверить ключ."));
      return null;
    } finally {
      setLookupBusy(false);
    }
  };

  const onRedeem = async (): Promise<void> => {
    const nextStatus = status || (await lookup());
    if (!nextStatus) return;
    if (!nextStatus.exists) {
      setError("Такой ключ не найден.");
      return;
    }
    if (nextStatus.redeemed) {
      setError("Ключ уже погашен. Для manual recovery используйте support.");
      return;
    }

    setRedeemBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await redeemAccessKey(nextStatus.key);
      setStatus(payload.status);
      await refresh();
      setMessage(
        `Ключ ${payload.key} погашен. План ${payload.plan?.label || payload.status.plan?.label || "managed premium"} уже применён к текущему аккаунту.`,
      );
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось погасить ключ."));
    } finally {
      setRedeemBusy(false);
    }
  };

  useEffect(() => {
    const nextKey = normalizeKey(searchParams.get("key") || "");
    if (!nextKey) return;
    setKeyInput(nextKey);
    void lookup(nextKey);
    // searchParams is stable enough for this route and we intentionally want to react to URL changes only
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return (
    <main className="space-y-6">
      <section className="glass-card p-7">
        <p className="font-mono text-xs uppercase tracking-[0.18em] text-emerald-500">redeem activation key</p>
        <h1 className="mt-2 font-display text-4xl font-bold">Ключ привязывает paid access к app-first аккаунту</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-600 dark:text-slate-300">
          В новой коммерческой модели покупка и выдача разделены: сначала пользователь получает activation key,
          затем погашает его здесь или в приложении, после чего managed premium обновляется без raw subscription link
          в обычном UX.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Купить ключ
          </AppRouteLink>
          <AppRouteLink href="/subscription/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Назад в доступ
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-xl px-6 py-3 text-sm font-semibold uppercase tracking-[0.12em]">
            Нужен recovery path
          </AppRouteLink>
        </div>
      </section>

      <section className="grid gap-5 lg:grid-cols-[1.1fr,0.9fr]">
        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Проверить и погасить ключ</h2>
          <label className="mt-4 block text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
            Activation key
          </label>
          <div className="mt-2 flex flex-col gap-3 md:flex-row">
            <input
              value={keyInput}
              onChange={(event) => setKeyInput(normalizeKey(event.target.value))}
              placeholder="Например: POKROV-XXXX-XXXX"
              className="w-full rounded-2xl border border-white/45 bg-white/65 px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/5"
            />
            <button
              type="button"
              onClick={() => void lookup()}
              disabled={lookupBusy}
              className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
            >
              {lookupBusy ? "Проверяем..." : "Проверить"}
            </button>
            <button
              type="button"
              onClick={() => void onRedeem()}
              disabled={redeemBusy}
              className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
            >
              {redeemBusy ? "Погашаем..." : "Redeem"}
            </button>
          </div>

          {message ? (
            <div className="mt-4 rounded-2xl border border-emerald-300/35 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-900 dark:text-emerald-200">
              {message}
            </div>
          ) : null}
          {error ? (
            <div className="mt-4 rounded-2xl border border-rose-300/35 bg-rose-500/10 px-4 py-3 text-sm text-rose-700 dark:text-rose-200">
              {error}
            </div>
          ) : null}

          <div className="mt-5 rounded-2xl border border-white/40 bg-white/55 p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
            <p>Текущий профиль: <strong>{resolvePlanLabel(dash, user)}</strong></p>
            <p>Состояние доступа: <strong>{getAccessState(dash, user) || "free_monthly"}</strong></p>
            <p>
              Если ключ уже использован или потерян, normal path не покажет старую raw ссылку. Восстановление идёт
              через support или Telegram continuation.
            </p>
          </div>
        </article>

        <article className="glass-card p-6">
          <h2 className="font-display text-2xl font-semibold">Статус ключа</h2>
          {status ? (
            <div className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-300">
              <p>Ключ: <strong>{status.key}</strong></p>
              <p>Найден: <strong>{status.exists ? "да" : "нет"}</strong></p>
              <p>Погашен: <strong>{status.redeemed ? "да" : "нет"}</strong></p>
              <p>План: <strong>{status.plan?.label || status.kind || "—"}</strong></p>
              <p>Лимит устройств: <strong>{status.device_limit || 1}</strong></p>
              <p>Node policy: <strong>{status.node_policy || "managed_premium"}</strong></p>
              <p>Выдан: <strong>{formatDate(status.issued_at)}</strong></p>
              <p>Погашен: <strong>{formatDate(status.redeemed_at)}</strong></p>
            </div>
          ) : (
            <p className="mt-4 text-sm text-slate-500">
              Введите ключ и проверьте его перед redeem. Это безопаснее, чем показывать ручные ссылки или legacy delivery.
            </p>
          )}

          <div className="mt-5 rounded-2xl border border-white/40 bg-white/55 p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
            <p>Site email signup даёт только Free Monthly.</p>
            <p>5-дневный premium trial стартует в приложении и не зависит от этого web-маршрута.</p>
            <p>Telegram нужен как recovery/link path, support fallback и бонус +10 дней, а не как primary commerce story.</p>
          </div>
        </article>
      </section>
    </main>
  );
}
