"use client";

import { useEffect, useMemo, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { getDeviceLimit, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import { checkChannelSubscriberStatus, claimChannelBonus, getEmailAuthStatus } from "@/lib/api";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";

function formatDate(value?: string | null): string {
  if (!value) return "Уточним позже";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Уточним позже";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function profileLabel(username?: string | null, tgId?: number | null): string {
  if (username) return `@${username}`;
  if (tgId) return `ID ${tgId}`;
  return "Аккаунт POKROV";
}

type BonusCheckState = {
  checked: boolean;
  subscriber: boolean;
  alreadyClaimed: boolean;
  linkRequired: boolean;
  bonusDays: number;
  message: string;
};

const isEmailPublicReady = (payload: Awaited<ReturnType<typeof getEmailAuthStatus>>): boolean =>
  Boolean(
    payload.enabled &&
      payload.public_enabled &&
      payload.delivery_configured &&
      payload.delivery_secret_configured &&
      !payload.debug_echo,
  );

export default function SettingsPage() {
  const { user, dash } = usePortalSession();
  const [bonusCheck, setBonusCheck] = useState<BonusCheckState | null>(null);
  const [bonusMessage, setBonusMessage] = useState("");
  const [bonusError, setBonusError] = useState("");
  const [bonusBusy, setBonusBusy] = useState<"check" | "claim" | "">("");
  const [emailReady, setEmailReady] = useState(false);

  const linked = user?.linked_identities || dash?.linked_identities || null;
  const telegramName = linked?.telegram?.username ? `@${linked.telegram.username}` : profileLabel(user?.username, user?.tg_id);
  const linkedEmail = linked?.email?.email || "";
  const deviceLimit = getDeviceLimit(dash, user);
  const channelLink = user?.channel?.link || "";
  const supportLink = user?.support?.link || "/support/";
  const channelBonusDays = bonusCheck?.bonusDays || user?.bonuses?.channel_bonus?.premium_days || 10;
  const channelBonusClaimedAt = user?.bonuses?.channel_bonus?.claimed_at || null;
  const channelBonusReady = Boolean(user?.bonuses?.channel_bonus?.can_claim);
  const canClaimBonus = !channelBonusClaimedAt && (channelBonusReady || Boolean(bonusCheck?.subscriber && !bonusCheck.alreadyClaimed));

  useEffect(() => {
    let cancelled = false;
    void getEmailAuthStatus()
      .then((payload) => {
        if (!cancelled) setEmailReady(isEmailPublicReady(payload));
      })
      .catch(() => {
        if (!cancelled) setEmailReady(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const linkedItems = [
    {
      key: "telegram",
      title: "Telegram",
      body: "Используется для входа в браузере, бонуса и восстановления доступа через поддержку.",
      badge: telegramName,
      tone: "success" as const,
      action: (
        <AppRouteLink href={supportLink} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Поддержка
        </AppRouteLink>
      ),
    },
    {
      key: "email",
      title: "Email",
      body: linkedEmail
        ? "Email уже привязан к аккаунту."
        : emailReady
          ? "Email-вход включен на экране входа."
          : "Email-вход скрыт, пока доставка писем недоступна.",
      badge: linkedEmail || (emailReady ? "Доступен" : "Недоступен"),
      tone: linkedEmail ? ("info" as const) : ("neutral" as const),
      action: emailReady ? (
        <span className="text-sm font-semibold text-slate-500 dark:text-slate-400">На экране входа</span>
      ) : undefined,
    },
    {
      key: "access",
      title: "Статус доступа",
      body: dash?.is_active
        ? "Профиль готов для приложений, продления и поддержки."
        : "Доступ можно вернуть через раздел оплаты.",
      badge: dash?.is_active ? "Активен" : "Нужно продление",
      tone: dash?.is_active ? ("success" as const) : ("warning" as const),
      action: (
        <AppRouteLink href="/subscription/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Тарифы и оплата
        </AppRouteLink>
      ),
    },
  ];

  const quickActions = [
    {
      key: "devices",
      title: "Проверить устройства",
      body: "Полезно перед переносом доступа на новый экран.",
      badge: "Устройства",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/devices/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Перейти
        </AppRouteLink>
      ),
    },
    {
      key: "downloads",
      title: "Открыть загрузки",
      body: "Android и Windows бета-ссылки лежат в отдельном разделе кабинета.",
      badge: "Загрузки",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/downloads/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Перейти
        </AppRouteLink>
      ),
    },
    {
      key: "support",
      title: "Продолжить поддержку",
      body: "Если вопрос уже был, лучше держать его в одном кейсе.",
      badge: "Поддержка",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть
        </AppRouteLink>
      ),
    },
  ];

  const bonusStatusText = useMemo(() => {
    if (bonusMessage) return bonusMessage;
    if (channelBonusClaimedAt) return `Бонус уже добавлен ${formatDate(channelBonusClaimedAt)}.`;
    if (bonusCheck?.message) return bonusCheck.message;
    if (channelBonusReady) return `Можно забрать +${channelBonusDays} дней после проверки подписки.`;
    return "Подпишитесь на канал, проверьте статус и заберите бонус, если аккаунт подходит.";
  }, [bonusCheck?.message, bonusMessage, channelBonusClaimedAt, channelBonusDays, channelBonusReady]);

  const onCheckBonus = async (): Promise<void> => {
    setBonusBusy("check");
    setBonusError("");
    setBonusMessage("");
    try {
      const payload = await checkChannelSubscriberStatus();
      const subscriber = Boolean(payload.subscriber);
      const alreadyClaimed = Boolean(payload.already_claimed);
      setBonusCheck({
        checked: true,
        subscriber,
        alreadyClaimed,
        linkRequired: Boolean(payload.link_required),
        bonusDays: Number(payload.bonus_days || channelBonusDays || 10),
        message: alreadyClaimed
          ? "Бонус уже был добавлен раньше."
          : subscriber
            ? "Подписка подтверждена. Теперь можно забрать бонус."
            : "Подписка пока не подтверждена. Откройте канал и попробуйте еще раз.",
      });
    } catch (error) {
      setBonusError(
        userFacingErrorMessage(
          error,
          "Не удалось проверить подписку. Откройте канал и попробуйте позже или напишите в поддержку.",
        ),
      );
    } finally {
      setBonusBusy("");
    }
  };

  const onClaimBonus = async (): Promise<void> => {
    setBonusBusy("claim");
    setBonusError("");
    setBonusMessage("");
    try {
      const payload = await claimChannelBonus();
      const days = Number(payload.premium_days || channelBonusDays || 10);
      setBonusMessage(payload.already_claimed ? "Бонус уже был добавлен раньше." : `Бонус +${days} дней добавлен.`);
    } catch (error) {
      setBonusError(userFacingErrorMessage(error, "Не удалось добавить бонус. Попробуйте позже или напишите в поддержку."));
    } finally {
      setBonusBusy("");
    }
  };

  return (
    <CabinetRoute
      eyebrow="Настройки"
      title="Настройки и бонусы"
      description="Аккаунт, связанные каналы и понятные действия без личных ссылок, технических адресов и ручных профилей."
      actions={
        <>
          <AppRouteLink href="/subscription/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
            Тарифы и оплата
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Профиль",
          value: profileLabel(user?.username, user?.tg_id),
          hint: "Это тот же аккаунт, который используют ваши устройства.",
          tone: "neutral",
        },
        {
          label: "Текущий режим",
          value: resolvePlanLabel(dash, user),
          hint: resolveTrafficStatusText(dash, user),
          tone: dash?.is_active ? "success" : "warning",
        },
        {
          label: "Срок",
          value: formatDate(dash?.expiry_at || user?.expiry_at),
          hint: dash?.is_active ? "Доступ уже активен." : "Если срок закончился, верните его в разделе оплаты.",
          tone: dash?.is_active ? "neutral" : "warning",
        },
        {
          label: "Устройства",
          value: `До ${deviceLimit}`,
          hint: "Лимит относится ко всему профилю.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Главное по аккаунту"
        badge={dash?.is_active ? "Профиль в порядке" : "Профилю нужен следующий шаг"}
        badgeTone={dash?.is_active ? "success" : "warning"}
        title={profileLabel(user?.username, user?.tg_id)}
        description={
          dash?.is_active
            ? "Здесь удобно проверить связки, забрать Telegram-бонус и быстро перейти к нужному разделу."
            : "Если срок закончился, здесь видно, через какие разделы быстрее вернуть рабочий статус."
        }
        details={[
          {
            label: "Telegram",
            value: telegramName,
            hint: "Основной рабочий канал входа в браузере.",
            tone: "success",
          },
          {
            label: "Email",
            value: linkedEmail || (emailReady ? "Доступен" : "Недоступен"),
            hint: linkedEmail ? "Связка уже есть." : emailReady ? "Email-вход включен на экране входа." : "Пока доставка писем недоступна, этот вход скрыт.",
            tone: linkedEmail ? "info" : "neutral",
          },
          {
            label: "Если нужен следующий шаг",
            value: dash?.is_active ? "Проверить устройства" : "Проверить статус продления",
            hint: dash?.is_active ? "Полезно перед переносом доступа." : "Покажем доступный следующий шаг, если срок закончился.",
            tone: "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <CabinetSection
          eyebrow="Связки"
          title="Что уже привязано"
          description="Только каналы, которые реально помогают зайти, продлить доступ или продолжить поддержку."
        >
          <CabinetList items={linkedItems} />
        </CabinetSection>

        <CabinetSection
          eyebrow="Полезное рядом"
          title="Быстрые действия"
          description="Если нужна следующая понятная точка, вот самые частые действия."
        >
          <CabinetCardGrid items={quickActions} className="xl:grid-cols-1" />
        </CabinetSection>
      </div>

      <CabinetSection
        eyebrow="Telegram-бонус"
        title="Проверить канал и забрать +10 дней"
        description="Бонус добавляется только после явной проверки и отдельного нажатия. Если что-то не сходится, поддержку лучше открыть отсюда."
      >
        <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
          <div className="rounded-[1.3rem] border border-emerald-200/70 bg-emerald-50/85 p-4 dark:border-emerald-400/25 dark:bg-emerald-400/10">
            <p className="text-sm font-semibold text-slate-950 dark:text-slate-50">{bonusStatusText}</p>
            {bonusError ? <p className="mt-3 text-sm leading-6 text-rose-700 dark:text-rose-200">{bonusError}</p> : null}
            <div className="mt-4 flex flex-wrap gap-3">
              {channelLink ? (
                <AppRouteLink href={channelLink} target="_blank" hardNavigate={false} className="outline-btn rounded-full px-4 py-2 text-sm font-semibold">
                  Открыть канал
                </AppRouteLink>
              ) : null}
              <button
                type="button"
                onClick={() => void onCheckBonus()}
                disabled={bonusBusy !== ""}
                className="outline-btn rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-60"
              >
                {bonusBusy === "check" ? "Проверяем..." : "Проверить подписку"}
              </button>
              <button
                type="button"
                onClick={() => void onClaimBonus()}
                disabled={bonusBusy !== "" || Boolean(channelBonusClaimedAt) || (!canClaimBonus && !bonusCheck?.subscriber)}
                className="btn-primary rounded-full px-4 py-2 text-sm font-semibold disabled:opacity-60"
              >
                {bonusBusy === "claim" ? "Добавляем..." : `Забрать +${channelBonusDays} дней`}
              </button>
            </div>
          </div>

          <CabinetCardGrid
            className="lg:grid-cols-1"
            items={[
              {
                key: "bonus-rules",
                title: "Как это работает",
                body: "Сначала проверяем подписку на официальный канал. Затем отдельной кнопкой добавляем дни к текущему профилю.",
                badge: "+10 дней",
                tone: "neutral" as const,
              },
              {
                key: "bonus-support",
                title: "Если бонус не сработал",
                body: "Откройте поддержку. Достаточно написать, что проверка канала не прошла.",
                badge: "Поможем",
                tone: "neutral" as const,
                action: (
                  <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                    Поддержка
                  </AppRouteLink>
                ),
              },
            ]}
          />
        </div>
      </CabinetSection>
    </CabinetRoute>
  );
}
