"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { CabinetThemeControl } from "@/components/cabinet/theme-control";
import { getDeviceLimit, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
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

function channelStatusLabel(subscriber?: boolean): string {
  return subscriber ? "Подписка подтверждена" : "Можно подключить позже";
}

export default function ProfilePage() {
  const { user, dash } = usePortalSession();

  const linked = user?.linked_identities || dash?.linked_identities || null;
  const telegramName = linked?.telegram?.username ? `@${linked.telegram.username}` : profileLabel(user?.username, user?.tg_id);
  const linkedEmail = linked?.email?.email || "";
  const deviceLimit = getDeviceLimit(dash, user);
  const planLabel = resolvePlanLabel(dash, user);
  const referralLink = user?.referral?.link || "";
  const supportLink = user?.support?.link || "/support/";
  const channelLink = user?.channel?.link || "";
  const channelBonusDays = user?.bonuses?.channel_bonus?.premium_days || 0;
  const channelBonusClaimedAt = user?.bonuses?.channel_bonus?.claimed_at || null;
  const channelBonusReady = Boolean(user?.bonuses?.channel_bonus?.can_claim);

  const linkedItems = [
    {
      key: "telegram",
      title: "Telegram",
      body: "Сейчас это основной рабочий способ подтвердить аккаунт в браузере, забрать бонус и восстановить доступ через поддержку.",
      badge: telegramName,
      tone: "success" as const,
      action: (
        <AppRouteLink href={supportLink} target={supportLink.startsWith("http") ? "_blank" : undefined} hardNavigate={false} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Поддержка
        </AppRouteLink>
      ),
    },
    {
      key: "email",
      title: "Email",
      body: linkedEmail ? "Email уже привязан к аккаунту." : "Email-вход еще не открыт. Мы честно держим этот сценарий выключенным, пока он не готов.",
      badge: linkedEmail || "Скоро подключим",
      tone: linkedEmail ? ("info" as const) : ("neutral" as const),
    },
    {
      key: "access",
      title: "Статус доступа",
      body: dash?.is_active
        ? "Аккаунт готов для приложений, продления и поддержки без нового старта."
        : "Доступ можно вернуть в пару шагов через раздел оплаты.",
      badge: planLabel,
      tone: dash?.is_active ? ("success" as const) : ("warning" as const),
      action: (
        <AppRouteLink href="/subscription/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть оплату
        </AppRouteLink>
      ),
    },
  ];

  const quickActions = [
    {
      key: "support",
      title: "Продолжить кейс поддержки",
      body: "Если вопрос уже был, удобнее продолжать тот же кейс и не терять контекст.",
      badge: "Поддержка",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть
        </AppRouteLink>
      ),
    },
    {
      key: "devices",
      title: "Проверить устройства",
      body: "Перед переносом доступа на новый экран удобно посмотреть, что уже связано с профилем.",
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
      body: "Приложения и инструкции лежат в одном разделе, без поиска по старым сообщениям.",
      badge: "Загрузки",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/downloads/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Перейти
        </AppRouteLink>
      ),
    },
  ];

  const bonusCards = [
    {
      key: "channel-state",
      title: "Telegram-канал",
      body: channelBonusClaimedAt
        ? `Бонус уже был подтвержден ${formatDate(channelBonusClaimedAt)}.`
        : channelBonusReady
          ? `Можно забрать бонус +${channelBonusDays || 10} дней.`
          : "Подписку можно подключить позже, если она вам нужна.",
      badge: channelStatusLabel(user?.channel?.subscriber),
      tone: channelBonusClaimedAt ? ("success" as const) : channelBonusReady ? ("info" as const) : ("neutral" as const),
      action: channelLink ? (
        <AppRouteLink href={channelLink} target="_blank" hardNavigate={false} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть канал
        </AppRouteLink>
      ) : null,
    },
    {
      key: "referral-link",
      title: referralLink ? "Личная ссылка готова" : "Личная ссылка уточняется",
      body: referralLink ? "Ссылка не показывается на первом экране целиком. Откройте ее отдельной кнопкой, когда нужно поделиться." : "Когда ссылка появится, ее можно будет использовать как есть.",
      badge: `+${user?.referral?.bonus_days || 10} дней`,
      tone: referralLink ? ("success" as const) : ("neutral" as const),
      action: referralLink ? (
        <AppRouteLink href={referralLink} target="_blank" hardNavigate={false} className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть
        </AppRouteLink>
      ) : null,
    },
    {
      key: "referral-count",
      title: "Сколько уже сработало",
      body: `Подтверждено приглашений: ${user?.bonuses?.referral_count || 0}.`,
      badge: user?.referral?.code ? "Код готов" : "Код уточняется",
      tone: "neutral" as const,
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Аккаунт"
      title="Вход, тема и связанные каналы"
      description="Здесь собраны только практичные вещи: кто вы, какой режим действует сейчас и через какие каналы удобно продолжать доступ."
      metrics={[
        {
          label: "Аккаунт",
          value: profileLabel(user?.username, user?.tg_id),
          hint: "Это тот же аккаунт, который используют ваши устройства.",
          tone: "neutral",
        },
        {
          label: "Текущий режим",
          value: planLabel,
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
          hint: "Лимит относится ко всему профилю, а не к одному экрану.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Главное по аккаунту"
        badge={dash?.is_active ? "Аккаунт в порядке" : "Аккаунту нужен следующий шаг"}
        badgeTone={dash?.is_active ? "success" : "warning"}
        title={profileLabel(user?.username, user?.tg_id)}
        description={
          dash?.is_active
            ? "Аккаунт уже готов для приложений, продления и поддержки. Здесь удобно проверить связки и быстро перейти дальше."
            : "Если срок закончился, здесь видно, через какие каналы и разделы быстрее вернуть рабочий статус."
        }
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
        details={[
          {
            label: "Telegram",
            value: telegramName,
            hint: "Основной рабочий канал входа в браузере.",
            tone: "success",
          },
          {
            label: "Email",
            value: linkedEmail || "Скоро подключим",
            hint: linkedEmail ? "Связка уже есть." : "Пока честно держим этот вход выключенным.",
            tone: linkedEmail ? "info" : "neutral",
          },
          {
            label: "Если нужен следующий шаг",
            value: dash?.is_active ? "Проверить устройства" : "Открыть оплату",
            hint: dash?.is_active ? "Полезно перед переносом доступа на новый экран." : "Это самый прямой путь, если срок закончился.",
            tone: "neutral",
          },
        ]}
      />

      <section id="settings" aria-label="Настройки кабинета">
        <CabinetSection
          eyebrow="Настройки"
          title="Тема кабинета"
          description="Выберите системную, светлую или темную тему. Выбор сохранится для этого браузера."
        >
          <CabinetThemeControl />
        </CabinetSection>
      </section>

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
        eyebrow="Бонусы и ссылки"
        title="Что еще есть у аккаунта"
        description="Дополнительные вещи под рукой, если они вам нужны. Длинные личные ссылки открываются отдельным действием."
      >
        <CabinetCardGrid items={bonusCards} />
      </CabinetSection>
    </CabinetRoute>
  );
}
