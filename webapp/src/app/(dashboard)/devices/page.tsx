"use client";

import { useMemo } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { getAccessState, getDeviceLimit, getTrafficLimitGb, isFreeMonthlyState, isPaidUnlimitedState, isTrialPremiumState } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";

function formatDate(value?: string | null): string {
  if (!value) return "еще не появлялось";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "дату уточним";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

function formatCount(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.round(Number(value))));
}

function deviceTitle(name?: string | null, platform?: string | null): string {
  const cleanName = String(name || "").trim();
  const cleanPlatform = String(platform || "").trim();
  if (cleanName && cleanPlatform) return `${cleanName} · ${cleanPlatform}`;
  return cleanName || cleanPlatform || "Устройство";
}

export default function DevicesPage() {
  const { user, dash } = usePortalSession();

  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const deviceLimit = getDeviceLimit(dash, user);
  const freeLimitGb = getTrafficLimitGb(dash, user);
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const activeUsersEstimate = dash?.connection_snapshot?.active_users_estimate ?? user?.connections?.active_users_estimate ?? 0;
  const activeNodes = dash?.connection_snapshot?.active_nodes ?? 0;
  const knownNodes = dash?.connection_snapshot?.known_nodes ?? user?.nodes?.length ?? 0;
  const knownAppDevices = user?.sync?.device_count ?? user?.devices?.length ?? 0;

  const devices = useMemo(
    () =>
      (user?.devices || []).map((device) => ({
        key: device.id,
        title: deviceTitle(device.name, device.platform),
        body: device.is_current
          ? "Это текущее устройство."
          : device.last_seen_at
            ? `Последний раз в сети ${formatDate(device.last_seen_at)}.`
            : "Появится здесь после первого входа в приложение.",
        badge: device.is_current ? "Сейчас здесь" : device.is_active ? "Связано" : "Без активности",
        tone: device.is_current || device.is_active ? ("success" as const) : ("neutral" as const),
      })),
    [user?.devices],
  );

  const transferCards = [
    {
      key: "install",
      title: "Поставить приложение на новый экран",
      body: "Сначала просто откройте загрузки и поставьте нужную версию для Android или Windows.",
      badge: "Шаг 1",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/downloads/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Загрузки
        </AppRouteLink>
      ),
    },
    {
      key: "login",
      title: "Войти в тот же аккаунт",
      body: "Так профиль подтянется сам, без ручной раздачи скрытых данных.",
      badge: "Шаг 2",
      tone: "neutral" as const,
    },
    {
      key: "support",
      title: "Если что-то не появилось, открыть поддержку",
      body: "Один кейс лучше любого обходного пути. Так весь контекст уже будет рядом.",
      badge: "Шаг 3",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Поддержка
        </AppRouteLink>
      ),
    },
  ];

  const modeCards = [
    {
      key: "paid",
      title: paidMode ? "Сейчас полный режим" : "Полный режим дает больше запаса",
      body: paidMode
        ? "У профиля есть спокойный запас по устройствам и нет месячного лимита трафика."
        : "Если устройств становится больше и не хочется думать о лимитах, смотреть стоит туда.",
      badge: paidMode ? "Сейчас так" : "Если нужно",
      tone: paidMode ? ("success" as const) : ("neutral" as const),
    },
    {
      key: "trial",
      title: trialMode ? "Пробный период уже помогает проверить сервис на нескольких экранах" : "Пробный период подходит для проверки на нескольких экранах",
      body: trialMode
        ? "Это хороший момент, чтобы спокойно подключить свои основные устройства."
        : "Если он у вас активируется, используйте это время для спокойной проверки.",
      badge: trialMode ? "Активен" : "Как это работает",
      tone: trialMode ? ("warning" as const) : ("neutral" as const),
    },
    {
      key: "free",
      title: freeMode ? "В базовом режиме лимиты строже" : "Базовый режим остается запасным",
      body: freeMode
        ? `Сейчас ориентир до ${deviceLimit} устройств и около ${freeLimitGb || 5} ГБ в месяц.`
        : "Он подходит для спокойного повседневного использования, но может быть теснее по лимитам.",
      badge: freeMode ? "Сейчас так" : "Запасной путь",
      tone: freeMode ? ("info" as const) : ("neutral" as const),
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Устройства"
      title="Что уже связано с профилем"
      description="Здесь видно, какие устройства уже появились в кабинете и как спокойнее перенести доступ на новый экран."
      actions={
        <>
          <AppRouteLink href="/downloads/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
            Открыть загрузки
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Подключений сейчас",
          value: `${formatCount(activeConnections)} из ${formatCount(deviceLimit)}`,
          hint: "Это живые подключения по профилю прямо сейчас.",
          tone: "neutral",
        },
        {
          label: "Известных устройств",
          value: formatCount(knownAppDevices),
          hint: "То, что уже успело связаться с аккаунтом.",
          tone: "neutral",
        },
        {
          label: "Точек доступа",
          value: `${formatCount(activeNodes)} из ${formatCount(knownNodes)}`,
          hint: "Короткая сводка по текущему маршруту.",
          tone: "neutral",
        },
        {
          label: "Людей онлайн",
          value: formatCount(activeUsersEstimate),
          hint: "Это ориентир по живой активности сети.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Главное сейчас"
        badge={devices.length ? "Профиль уже связан с устройствами" : "Новый экран можно добавить"}
        badgeTone={devices.length ? "success" : "info"}
        title={devices.length ? "Сначала смотрим список, потом переносим доступ" : "Новый экран начинается с загрузки"}
        description={
          devices.length
            ? "Если хотите перенести доступ на новый экран, сначала проверьте, что уже связано с профилем. Так спокойнее не потерять лишнее."
            : "Когда в списке пока пусто, почти всегда достаточно просто поставить приложение и войти в тот же аккаунт."
        }
        actions={
          <>
            <AppRouteLink href="/downloads/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
              Скачать приложение
            </AppRouteLink>
            <AppRouteLink href="/subscription/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Проверить тариф
            </AppRouteLink>
          </>
        }
        details={[
          {
            label: "Лимит профиля",
            value: `До ${deviceLimit} устройств`,
            hint: "Лимит относится ко всему профилю, а не к одному экрану.",
            tone: "neutral",
          },
          {
            label: "Сейчас в кабинете",
            value: formatCount(knownAppDevices),
            hint: "Сколько устройств уже успели связаться с аккаунтом.",
            tone: devices.length ? "success" : "neutral",
          },
          {
            label: "Если нужно больше запаса",
            value: paidMode ? "Он уже есть" : "Смотреть в оплате",
            hint: paidMode ? "Полный режим уже активен." : "Полный режим обычно спокойнее, если устройств становится больше.",
            tone: paidMode ? "success" : "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <CabinetSection
          eyebrow="Список"
          title="Устройства в кабинете"
          description="Если переносите доступ на новый экран, сначала проверьте, появился ли он здесь."
        >
          <CabinetList items={devices} empty="Пока устройств нет. Обычно они появляются после первого входа в приложение на Android или Windows." />
        </CabinetSection>

        <CabinetSection
          eyebrow="Перенос"
          title="Как добавить еще одно устройство"
          description="Лучше идти коротким и безопасным путем, а не искать скрытые ссылки вручную."
        >
          <CabinetCardGrid items={transferCards} className="xl:grid-cols-1" />
        </CabinetSection>
      </div>

      <CabinetSection
        eyebrow="Лимиты"
        title="Что важно помнить"
        description="Если не хочется вникать глубоко, этих трех заметок обычно достаточно."
      >
        <CabinetCardGrid items={modeCards} />
      </CabinetSection>
    </CabinetRoute>
  );
}
