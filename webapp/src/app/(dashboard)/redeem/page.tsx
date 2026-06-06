"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { resolvePlanLabel } from "@/lib/access-policy";
import { fetchAccessKeyStatus, redeemAccessKey, type AccessKeyStatusPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

function icon(name: string) {
  return <span className="material-symbols-rounded text-[20px]">{name}</span>;
}

function normalizeKey(value: string): string {
  return String(value || "").trim().toUpperCase();
}

function looksLikeConnectionLink(value: string): boolean {
  const normalized = String(value || "").trim().toLowerCase();
  return (
    normalized.startsWith("http://") ||
    normalized.startsWith("https://") ||
    normalized.includes("connect.pokrov.space") ||
    normalized.includes("/s8kx2mp7qr4wt/")
  );
}

const CONNECTION_LINK_ERROR =
  "Это ссылка подключения, а не код активации. Ее нужно вставлять в совместимый клиент, а код оплаты или подарка вводится здесь.";

function formatDate(value?: string | null): string {
  if (!value) return "не использован";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "не задан";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
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
    const rawValue = rawKey ?? keyInput;
    if (looksLikeConnectionLink(rawValue)) {
      setStatus(null);
      setMessage("");
      setError(CONNECTION_LINK_ERROR);
      return null;
    }
    const key = normalizeKey(rawValue);
    if (!key) {
      setError("Введите код, чтобы мы могли его проверить.");
      return null;
    }

    setLookupBusy(true);
    setError("");
    setMessage("");
    try {
      const nextStatus = await fetchAccessKeyStatus(key);
      setStatus(nextStatus);
      if (!nextStatus.exists) {
        setMessage("Такой код не найден. Проверьте, не потерялся ли символ.");
      } else if (nextStatus.redeemed) {
        setMessage("Этот код уже был использован. Нужна помощь? Откройте поддержку.");
      } else {
        setMessage("Код найден. Его можно активировать в текущем профиле.");
      }
      return nextStatus;
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось проверить код."));
      return null;
    } finally {
      setLookupBusy(false);
    }
  };

  const onRedeem = async (): Promise<void> => {
    const nextStatus = status || (await lookup());
    if (!nextStatus) return;
    if (!nextStatus.exists) {
      setError("Такой код не найден.");
      return;
    }
    if (nextStatus.redeemed) {
      setError("Код уже был использован. Для восстановления лучше открыть поддержку.");
      return;
    }

    setRedeemBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await redeemAccessKey(nextStatus.key);
      setStatus(payload.status);
      await refresh();
      setMessage(`Код ${payload.key} активирован. Профиль уже обновлен.`);
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось активировать код."));
    } finally {
      setRedeemBusy(false);
    }
  };

  useEffect(() => {
    const nextKey = normalizeKey(searchParams.get("key") || "");
    if (!nextKey) return;
    setKeyInput(nextKey);
    void lookup(nextKey);
    // searchParams is stable enough here and we only react to URL changes
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  return (
    <main className="mx-auto w-full max-w-[840px] space-y-5">
      <CabinetStatus
        title="Активировать код"
        meta={resolvePlanLabel(dash, user)}
        body="Введите код оплаты, подарка или промокод. Личная ссылка подключения сюда не подходит."
        tone={status?.exists && !status.redeemed ? "success" : status?.redeemed ? "warning" : "neutral"}
        action={
          <AppRouteLink href="/subscription/checkout/" className="outline-btn w-full rounded-full px-5 py-3 text-center text-sm font-semibold sm:w-auto">
            Купить доступ
          </AppRouteLink>
        }
      />

      <CabinetGroup title="Код">
        <div className="space-y-3 p-4">
          <input
            value={keyInput}
            onChange={(event) => setKeyInput(normalizeKey(event.target.value))}
            placeholder="Код активации"
            className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
          />
          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              disabled={lookupBusy}
              onClick={() => void lookup()}
              className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
            >
              {lookupBusy ? "Проверяем..." : "Проверить"}
            </button>
            <button
              type="button"
              disabled={redeemBusy}
              onClick={() => void onRedeem()}
              className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
            >
              {redeemBusy ? "Активируем..." : "Активировать"}
            </button>
          </div>
          <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
            Если у вас длинная ссылка `connect.pokrov.space`, откройте ручную настройку в разделе доступа.
          </p>
        </div>
      </CabinetGroup>

      {message ? (
        <p className="rounded-2xl border border-emerald-300/40 bg-emerald-50/80 px-4 py-3 text-sm leading-6 text-emerald-900 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-200">
          {message}
        </p>
      ) : null}
      {error ? (
        <p className="rounded-2xl border border-rose-300/40 bg-rose-50/80 px-4 py-3 text-sm leading-6 text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
          {error}
        </p>
      ) : null}

      <CabinetGroup title="Статус">
        {status ? (
          <>
            <CabinetRow icon={icon(status.exists ? "check_circle" : "help")} label="Проверка" hint={status.exists ? "Код найден" : "Код не найден"} value={status.exists ? "найден" : "не найден"} />
            <CabinetRow icon={icon("workspace_premium")} label="Что дает" hint={status.plan?.label || status.kind || "Уточним после проверки"} value={`до ${status.device_limit || 1} устройств`} />
            <CabinetRow icon={icon("event_available")} label="Использован" hint="По данным кабинета" value={formatDate(status.redeemed_at)} />
          </>
        ) : (
          <CabinetRow icon={icon("search")} label="Ждет проверки" hint="Введите код и нажмите Проверить" value="не запускалась" />
        )}
      </CabinetGroup>

      <CabinetGroup title="Что дальше">
        <CabinetRow icon={icon("payments")} label="Купить доступ" hint="Если кода еще нет" href="/subscription/checkout/" />
        <CabinetRow icon={icon("support_agent")} label="Поддержка" hint="Если код уже использован или не найден" href="/support/" />
        <CabinetRow icon={icon("qr_code_2")} label="Ручная ссылка" hint="Только для совместимого клиента" href="/subscription/#manual-setup" />
      </CabinetGroup>
    </main>
  );
}
