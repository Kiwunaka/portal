"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { resolvePlanLabel } from "@/lib/access-policy";
import { fetchAccessKeyStatus, redeemAccessKey, type AccessKeyStatusPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";

function normalizeKey(value: string): string {
  return String(value || "").trim().toUpperCase();
}

function maskAccessKey(value?: string | null): string {
  const key = String(value || "").trim();
  if (!key) return "Ключ не введен";
  if (key.length <= 8) return "Ключ скрыт";
  return `${key.slice(0, 6)}...${key.slice(-4)}`;
}

function formatDate(value?: string | null): string {
  if (!value) return "Уточним по мере обновления";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Уточним по мере обновления";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
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
    const key = normalizeKey(rawKey ?? keyInput);
    if (!key) {
      setError("Введите ключ доступа, чтобы мы могли его проверить.");
      return null;
    }

    setLookupBusy(true);
    setError("");
    setMessage("");
    try {
      const nextStatus = await fetchAccessKeyStatus(key);
      setStatus(nextStatus);
      if (!nextStatus.exists) {
        setMessage("Такой ключ доступа не найден. Проверьте, не потерялся ли символ.");
      } else if (nextStatus.redeemed) {
        setMessage("Этот ключ доступа уже был использован. Если нужна помощь, лучше открыть поддержку.");
      } else {
        setMessage("Ключ доступа найден. Его можно применить к текущему профилю.");
      }
      return nextStatus;
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось проверить ключ доступа."));
      return null;
    } finally {
      setLookupBusy(false);
    }
  };

  const onRedeem = async (): Promise<void> => {
    const nextStatus = status || (await lookup());
    if (!nextStatus) return;
    if (!nextStatus.exists) {
      setError("Такой ключ доступа не найден.");
      return;
    }
    if (nextStatus.redeemed) {
      setError("Ключ доступа уже был использован. Для восстановления лучше открыть поддержку.");
      return;
    }

    setRedeemBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await redeemAccessKey(nextStatus.key);
      setStatus(payload.status);
      await refresh();
      setMessage("Ключ доступа применен. Профиль уже обновлен.");
    } catch (nextError) {
      setError(String((nextError as { message?: string })?.message || nextError || "Не удалось применить ключ доступа."));
    } finally {
      setRedeemBusy(false);
    }
  };

  useEffect(() => {
    const nextKey = normalizeKey(searchParams.get("key") || "");
    if (!nextKey) return;
    setKeyInput(nextKey);
    void lookup(nextKey);
    // searchParams is stable enough here and we only react to URL changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  const facts = [
    {
      label: "Профиль",
      value: resolvePlanLabel(dash, user),
      hint: "Ключ доступа применяется к текущему аккаунту.",
      tone: "neutral" as const,
    },
    {
      label: "Статус доступа",
      value: dash?.is_active ? "Активен" : "Нужно продление",
      hint: dash?.is_active ? "Профиль уже готов к работе." : "Ключ доступа или продление вернут рабочий статус.",
      tone: dash?.is_active ? ("success" as const) : ("warning" as const),
    },
    {
      label: "Проверка ключа",
      value: status ? (status.exists ? "Ключ найден" : "Не найден") : "Ждет проверки",
      hint: status?.redeemed ? "Этот ключ доступа уже был использован." : "Сначала проверьте ключ, потом применяйте.",
      tone: status?.redeemed ? ("warning" as const) : status?.exists ? ("success" as const) : ("neutral" as const),
    },
    {
      label: "Что дальше",
      value: status?.redeemed ? "Открыть поддержку" : "Применить к профилю",
      hint: "Если ключ потерян или уже использован, лучше не гадать, а написать нам.",
      tone: "neutral" as const,
    },
  ];

  const statusItems = status
    ? [
        {
          key: "key",
          title: "Ключ доступа",
          body: maskAccessKey(status.key),
          badge: status.exists ? "Найден" : "Не найден",
          tone: status.exists ? ("success" as const) : ("warning" as const),
        },
        {
          key: "plan",
          title: "Что даст этот ключ",
          body: status.plan?.label || "Доступ по ключу",
          badge: `До ${status.device_limit || 1} устройств`,
          tone: "neutral" as const,
        },
        {
          key: "dates",
          title: "Когда был выдан и использован",
          body: `Выдан: ${formatDate(status.issued_at)}. Использован: ${formatDate(status.redeemed_at)}.`,
          badge: status.redeemed ? "Уже использован" : "Готов к применению",
          tone: status.redeemed ? ("warning" as const) : ("info" as const),
        },
      ]
    : [];

  const helpItems = [
    {
      key: "check",
      title: "Сначала проверьте ключ доступа",
      body: "Так вы сразу увидите, существует ли он и не был ли использован раньше.",
      badge: "Шаг 1",
      tone: "neutral" as const,
    },
    {
      key: "redeem",
      title: "Если ключ найден, примените его",
      body: "После этого профиль подтянется автоматически. Новый аккаунт создавать не нужно.",
      badge: "Шаг 2",
      tone: "neutral" as const,
    },
    {
      key: "support",
      title: "Если что-то не совпало, откройте поддержку",
      body: "Это самый спокойный путь, если ключ уже использован или выглядит не так, как ожидалось.",
      badge: "Шаг 3",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Поддержка
        </AppRouteLink>
      ),
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Тарифы и оплата"
      title="Применить ключ доступа"
      description="Если у вас уже есть ключ доступа, примените его здесь к текущему профилю. Новый аккаунт создавать не нужно."
      actions={
        <>
          <AppRouteLink href="/subscription/checkout/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Купить ключ доступа
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </>
      }
      metrics={facts}
    >
      <div className="grid gap-6 xl:grid-cols-[1.04fr_0.96fr]">
        <CabinetSection
          eyebrow="Проверка"
          title="Проверить и применить"
          description="Лучше сначала проверить ключ доступа, а потом уже применять его к профилю."
        >
          <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            Ключ доступа
          </label>
          <div className="mt-2 flex flex-col gap-3 md:flex-row">
            <input
              value={keyInput}
              onChange={(event) => setKeyInput(normalizeKey(event.target.value))}
              placeholder="Например: POKROV-XXXX-XXXX"
              className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
            />
            <button
              type="button"
              disabled={lookupBusy}
              onClick={() => void lookup()}
              className="outline-btn rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
            >
              {lookupBusy ? "Проверяем..." : "Проверить"}
            </button>
            <button
              type="button"
              disabled={redeemBusy}
              onClick={() => void onRedeem()}
              className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold uppercase tracking-[0.12em] disabled:opacity-60"
            >
              {redeemBusy ? "Применяем..." : "Применить"}
            </button>
          </div>

          {message ? (
            <div className="mt-4 rounded-2xl border border-emerald-300/40 bg-emerald-50/80 px-4 py-3 text-sm leading-6 text-emerald-900 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-200">
              {message}
            </div>
          ) : null}
          {error ? (
            <div className="mt-4 rounded-2xl border border-rose-300/40 bg-rose-50/80 px-4 py-3 text-sm leading-6 text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
              {error}
            </div>
          ) : null}
        </CabinetSection>

        <CabinetSection
          eyebrow="Подсказка"
          title="Если ключ не проходит"
          description="Обычно дальше нужен один из этих трех шагов."
        >
          <CabinetCardGrid items={helpItems} className="xl:grid-cols-1" />
        </CabinetSection>
      </div>

      <CabinetSection
        eyebrow="Статус"
        title="Что удалось узнать по ключу"
        description="После проверки или применения информация появится здесь. Сам ключ скрываем на первом слое."
      >
        <CabinetList items={statusItems} empty="Пока ничего не проверяли. Введите ключ доступа, и здесь появится его статус." />
      </CabinetSection>
    </CabinetRoute>
  );
}
