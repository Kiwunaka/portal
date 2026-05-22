"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { resolvePlanLabel } from "@/lib/access-policy";
import { fetchAccessKeyStatus, redeemAccessKey, type AccessKeyStatusPayload } from "@/lib/api";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

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

  const facts = [
    {
      label: "Профиль",
      value: resolvePlanLabel(dash, user),
      hint: "Код активируется в текущем аккаунте.",
      tone: "neutral" as const,
    },
    {
      label: "Статус доступа",
      value: dash?.is_active ? "Активен" : "Нужно продление",
      hint: dash?.is_active ? "Код добавится к текущему активному профилю." : "Если срок закончился, код поможет вернуть доступ.",
      tone: dash?.is_active ? ("success" as const) : ("warning" as const),
    },
    {
      label: "Проверка кода",
      value: status ? (status.exists ? "Код найден" : "Не найден") : "Ждет проверки",
      hint: status?.redeemed ? "Этот код уже был использован." : "Сначала проверьте код, потом активируйте.",
      tone: status?.redeemed ? ("warning" as const) : status?.exists ? ("success" as const) : ("neutral" as const),
    },
    {
      label: "Что дальше",
      value: status?.redeemed ? "Открыть поддержку" : "Активировать в профиле",
      hint: "Если код уже использован или потерян, лучше не гадать, а написать нам.",
      tone: "neutral" as const,
    },
  ];

  const statusItems = status
    ? [
        {
          key: "key",
          title: "Код",
          body: status.key,
          badge: status.exists ? "Найден" : "Не найден",
          tone: status.exists ? ("success" as const) : ("warning" as const),
        },
        {
          key: "plan",
          title: "Что даст этот код",
          body: status.plan?.label || status.kind || "Уточним после проверки",
          badge: `До ${status.device_limit || 1} устройств`,
          tone: "neutral" as const,
        },
        {
          key: "dates",
          title: "Когда был выдан и использован",
          body: `Выдан: ${formatDate(status.issued_at)}. Использован: ${formatDate(status.redeemed_at)}.`,
          badge: status.redeemed ? "Уже использован" : "Готов к активации",
          tone: status.redeemed ? ("warning" as const) : ("info" as const),
        },
      ]
    : [];

  const helpItems = [
    {
      key: "check",
      title: "Сначала проверьте код",
      body: "Так вы сразу увидите, существует ли он и не был ли уже использован раньше.",
      badge: "Шаг 1",
      tone: "neutral" as const,
    },
    {
      key: "redeem",
      title: "Если код найден, активируйте его",
      body: "После этого профиль подтянется автоматически. Новый аккаунт создавать не нужно.",
      badge: "Шаг 2",
      tone: "neutral" as const,
    },
    {
      key: "support",
      title: "Если что-то не совпало, откройте поддержку",
      body: "Это самый безопасный путь, если код уже использован или выглядит не так, как ожидалось.",
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
      title="Активировать код"
      description="Здесь вводится только код оплаты или подарка. Личная ссылка подключения сюда не подходит."
      actions={
        <>
          <AppRouteLink href="/subscription/checkout/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Купить доступ
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
        badge={status?.exists && !status.redeemed ? "Код можно активировать" : status?.redeemed ? "Нужна проверка" : "Сначала проверка"}
        badgeTone={status?.exists && !status.redeemed ? "success" : status?.redeemed ? "warning" : "neutral"}
        title={status?.exists && !status.redeemed ? "Код найден, активируйте его в профиле" : "Проверьте код перед активацией"}
        description="Код активируется в текущем аккаунте POKROV. Если у вас длинная ссылка или токен подключения, используйте раздел тарифов и ручной вариант."
        actions={
          <>
            <button
              type="button"
              disabled={lookupBusy}
              onClick={() => void lookup()}
              className="outline-btn rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60"
            >
              {lookupBusy ? "Проверяем..." : "Проверить код"}
            </button>
            <button
              type="button"
              disabled={redeemBusy}
              onClick={() => void onRedeem()}
              className="btn-primary rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60"
            >
              {redeemBusy ? "Активируем..." : "Активировать"}
            </button>
          </>
        }
        details={[
          {
            label: "Профиль",
            value: resolvePlanLabel(dash, user),
            hint: "Код добавит срок к текущему аккаунту.",
            tone: dash?.is_active ? "success" : "neutral",
          },
          {
            label: "Проверка",
            value: status ? (status.exists ? "Найден" : "Не найден") : "Не запускалась",
            hint: status?.redeemed ? "Этот код уже был использован." : "Сначала проверьте, затем активируйте.",
            tone: status?.redeemed ? "warning" : status?.exists ? "success" : "neutral",
          },
          {
            label: "Если не сходится",
            value: "Поддержка",
            hint: "Одно обращение быстрее ручных попыток.",
            tone: "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.04fr_0.96fr]">
        <CabinetSection
          eyebrow="Проверка"
          title="Проверить и активировать"
          description="Лучше сначала проверить код, а потом уже активировать его в профиле."
        >
          <label className="block text-xs font-semibold text-[var(--atlas-text-muted)]">
            Код
          </label>
          <div className="mt-2 flex flex-col gap-3 md:flex-row">
            <input
              value={keyInput}
              onChange={(event) => setKeyInput(normalizeKey(event.target.value))}
              placeholder="Код активации или подарка"
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
              {redeemBusy ? "Активируем..." : "Активировать"}
            </button>
          </div>
          <p className="mt-3 text-xs leading-5 text-[var(--atlas-text-muted)]">
            Длинная ссылка вида connect.pokrov.space сюда не подходит. Это ссылка подключения для совместимого клиента.
          </p>

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
          title="Если код не проходит"
          description="Обычно дальше нужен один из этих трех шагов."
        >
          <CabinetCardGrid items={helpItems} className="xl:grid-cols-1" />
        </CabinetSection>
      </div>

      <CabinetSection
        eyebrow="Статус"
        title="Что удалось узнать по коду"
        description="После проверки или активации информация появится здесь."
      >
        <CabinetList items={statusItems} empty="Пока ничего не проверяли. Введите код, и здесь появится его статус." />
      </CabinetSection>
    </CabinetRoute>
  );
}
