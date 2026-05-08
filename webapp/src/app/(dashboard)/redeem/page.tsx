"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { resolvePlanLabel } from "@/lib/access-policy";
import { fetchAccessKeyStatus, redeemAccessKey, redeemPromo, type AccessKeyStatusPayload } from "@/lib/api";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

function normalizeKey(value: string): string {
  return String(value || "")
    .trim()
    .replace(/[\u2010\u2011\u2012\u2013\u2014\u2212_]+/g, "-")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "")
    .toUpperCase();
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
  const [promoInput, setPromoInput] = useState("");
  const [lookupBusy, setLookupBusy] = useState(false);
  const [redeemBusy, setRedeemBusy] = useState(false);
  const [promoBusy, setPromoBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const lookup = async (rawKey?: string): Promise<AccessKeyStatusPayload | null> => {
    const key = normalizeKey(rawKey ?? keyInput);
    if (!key) {
      setError("Введите ключ, чтобы мы могли его проверить.");
      return null;
    }

    setLookupBusy(true);
    setError("");
    setMessage("");
    try {
      const nextStatus = await fetchAccessKeyStatus(key);
      setStatus(nextStatus);
      if (!nextStatus.exists) {
        setMessage("Такой ключ не найден. Проверьте, не потерялся ли символ.");
      } else if (nextStatus.redeemed) {
        setMessage("Этот ключ уже был использован. Если нужна помощь, лучше сразу открыть поддержку.");
      } else {
        setMessage("Ключ найден. Его можно применить к текущему профилю.");
      }
      return nextStatus;
    } catch (nextError) {
      setError(userFacingErrorMessage(nextError, "Не удалось проверить ключ."));
      return null;
    } finally {
      setLookupBusy(false);
    }
  };

  const onRedeem = async (): Promise<void> => {
    const currentKey = normalizeKey(keyInput);
    const nextStatus = status?.key === currentKey ? status : await lookup(currentKey);
    if (!nextStatus) return;
    if (!nextStatus.exists) {
      setError("Такой ключ не найден.");
      return;
    }
    if (nextStatus.redeemed) {
      setError("Ключ уже был использован. Для восстановления лучше открыть поддержку.");
      return;
    }

    setRedeemBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await redeemAccessKey(nextStatus.key);
      setStatus(payload.status);
      await refresh();
      setMessage(`Ключ ${payload.key} применен. Профиль уже обновлен.`);
    } catch (nextError) {
      setError(userFacingErrorMessage(nextError, "Не удалось применить ключ."));
    } finally {
      setRedeemBusy(false);
    }
  };

  const onRedeemPromo = async (): Promise<void> => {
    const code = normalizeKey(promoInput);
    if (!code) {
      setError("Введите промокод, чтобы мы могли его применить.");
      return;
    }

    setPromoBusy(true);
    setError("");
    setMessage("");
    try {
      const payload = await redeemPromo(code);
      await refresh();
      setPromoInput("");
      setMessage(`Промокод ${String(payload?.code || code)} применен.`);
    } catch (nextError) {
      setError(userFacingErrorMessage(nextError, "Не удалось применить промокод."));
    } finally {
      setPromoBusy(false);
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

  const facts = [
    {
      label: "Профиль",
      value: resolvePlanLabel(dash, user),
      hint: "Ключ применяется к текущему аккаунту.",
      tone: "neutral" as const,
    },
    {
      label: "Статус доступа",
      value: dash?.is_active ? "Активен" : "Нужно продление",
      hint: dash?.is_active ? "Ключ применится к текущему активному профилю." : "Если срок закончился, ключ поможет вернуть доступ.",
      tone: dash?.is_active ? ("success" as const) : ("warning" as const),
    },
    {
      label: "Проверка ключа",
      value: status ? (status.exists ? "Ключ найден" : "Не найден") : "Ждет проверки",
      hint: status?.redeemed ? "Этот ключ уже был использован." : "Сначала проверьте ключ, потом применяйте.",
      tone: status?.redeemed ? ("warning" as const) : status?.exists ? ("success" as const) : ("neutral" as const),
    },
    {
      label: "Что дальше",
      value: status?.redeemed ? "Открыть поддержку" : "Применить к профилю",
      hint: "Если ключ уже использован или потерян, лучше не гадать, а написать нам.",
      tone: "neutral" as const,
    },
  ];

  const statusItems = status
    ? [
        {
          key: "key",
          title: "Ключ",
          body: status.key,
          badge: status.exists ? "Найден" : "Не найден",
          tone: status.exists ? ("success" as const) : ("warning" as const),
        },
        {
          key: "plan",
          title: "Что даст этот ключ",
          body: status.plan?.label || status.kind || "Уточним после проверки",
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
      title: "Сначала проверьте ключ",
      body: "Так вы сразу увидите, существует ли он и не был ли уже использован раньше.",
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
      body: "Это самый безопасный путь, если ключ уже использован или выглядит не так, как ожидалось.",
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
      title="Применить ключ"
      description="Если у вас уже есть ключ оплаты или подарка, примените его здесь к текущему профилю."
      actions={
        <>
          <AppRouteLink href="/subscription/checkout/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Проверить статус ключа
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </>
      }
      metrics={facts}
    >
      <CabinetHero
        eyebrow="Что делать сейчас"
        badge={status?.exists && !status.redeemed ? "Ключ можно применить" : status?.redeemed ? "Нужна проверка" : "Сначала проверка"}
        badgeTone={status?.exists && !status.redeemed ? "success" : status?.redeemed ? "warning" : "neutral"}
        title={status?.exists && !status.redeemed ? "Ключ найден, примените его к профилю" : "Проверьте ключ перед применением"}
        description="Ключ применяется к текущему аккаунту POKROV. Новый профиль создавать не нужно, а личные ссылки и ручные параметры здесь не показываются."
        actions={
          <>
            <button
              type="button"
              disabled={lookupBusy}
              onClick={() => void lookup()}
              className="outline-btn rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60"
            >
              {lookupBusy ? "Проверяем..." : "Проверить ключ"}
            </button>
            <button
              type="button"
              disabled={redeemBusy}
              onClick={() => void onRedeem()}
              className="btn-primary rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60"
            >
              {redeemBusy ? "Применяем..." : "Применить"}
            </button>
          </>
        }
        details={[
          {
            label: "Профиль",
            value: resolvePlanLabel(dash, user),
            hint: "Ключ добавит срок к текущему аккаунту.",
            tone: dash?.is_active ? "success" : "neutral",
          },
          {
            label: "Проверка",
            value: status ? (status.exists ? "Найден" : "Не найден") : "Не запускалась",
            hint: status?.redeemed ? "Этот ключ уже был использован." : "Сначала проверьте, затем применяйте.",
            tone: status?.redeemed ? "warning" : status?.exists ? "success" : "neutral",
          },
          {
            label: "Если не сходится",
            value: "Поддержка",
            hint: "Один кейс быстрее ручных попыток.",
            tone: "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.04fr_0.96fr]">
        <CabinetSection
          eyebrow="Проверка"
          title="Проверить и применить"
          description="Лучше сначала проверить ключ, а потом уже применять его к профилю."
        >
          <label className="block text-xs font-semibold text-[var(--atlas-text-muted)]">
            Ключ
          </label>
          <div className="mt-2 flex flex-col gap-3 md:flex-row">
            <input
              value={keyInput}
              onChange={(event) => {
                setKeyInput(normalizeKey(event.target.value));
                setStatus(null);
                setMessage("");
                setError("");
              }}
              placeholder="Например: POKROV-XXXX-XXXX"
              className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
            />
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
        eyebrow="Промокод"
        title="Применить промокод"
        description="Если у вас промокод на дни или скидку, примените его отдельно от ключа доступа."
      >
        <label htmlFor="promo-code" className="block text-xs font-semibold text-[var(--atlas-text-muted)]">
          Промокод
        </label>
        <div className="mt-2 flex flex-col gap-3 md:flex-row">
          <input
            id="promo-code"
            value={promoInput}
            onChange={(event) => {
              setPromoInput(normalizeKey(event.target.value));
              setMessage("");
              setError("");
            }}
            placeholder="Например: WELCOME14"
            className="w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
          />
          <button
            type="button"
            disabled={promoBusy}
            onClick={() => void onRedeemPromo()}
            className="btn-primary rounded-2xl px-5 py-3 text-sm font-semibold disabled:opacity-60"
          >
            {promoBusy ? "Применяем..." : "Применить промокод"}
          </button>
        </div>
      </CabinetSection>

      <CabinetSection
        eyebrow="Статус"
        title="Что удалось узнать по ключу"
        description="После проверки или применения информация появится здесь."
      >
        <CabinetList items={statusItems} empty="Пока ничего не проверяли. Введите ключ, и здесь появится его статус." />
      </CabinetSection>
    </CabinetRoute>
  );
}
