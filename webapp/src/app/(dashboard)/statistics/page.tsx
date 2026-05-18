"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { getDeviceLimit, getNextResetAt, resolvePlanLabel, resolveTrafficStatusText } from "@/lib/access-policy";
import { usePortalSession } from "@/lib/session";

function formatDate(value?: string | null): string {
  if (!value) return "не задан";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "не задан";
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

function formatGb(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "0 ГБ";
  return `${new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 1 }).format(Math.max(0, Number(value)))} ГБ`;
}

export default function StatisticsPage() {
  const { user, dash } = usePortalSession();

  const deviceLimit = getDeviceLimit(dash, user);
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const activeUsersEstimate = dash?.connection_snapshot?.active_users_estimate ?? user?.connections?.active_users_estimate ?? 0;
  const activeNodes = dash?.connection_snapshot?.active_nodes ?? user?.connections?.active_nodes ?? 0;
  const knownNodes = dash?.connection_snapshot?.known_nodes ?? user?.connections?.known_nodes ?? user?.nodes?.length ?? 0;
  const trafficUsed = user?.traffic?.used_gb ?? dash?.used_gb ?? 0;
  const nextResetAt = getNextResetAt(dash, user);

  const visibilityItems = [
    {
      key: "traffic",
      title: "Трафик",
      body: `Использовано примерно ${formatGb(trafficUsed)}. ${resolveTrafficStatusText(dash, user)}.`,
      badge: "Сводка",
      tone: "neutral" as const,
    },
    {
      key: "devices",
      title: "Устройства",
      body: `${formatCount(deviceCount)} из ${formatCount(deviceLimit)} уже связаны с профилем.`,
      badge: "Профиль",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/devices/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть
        </AppRouteLink>
      ),
    },
    {
      key: "connections",
      title: "Живая активность",
      body: `${formatCount(activeConnections)} подключений сейчас. Оценка людей онлайн: ${formatCount(activeUsersEstimate)}.`,
      badge: "Сейчас",
      tone: activeConnections > 0 ? ("success" as const) : ("neutral" as const),
    },
    {
      key: "reset",
      title: "Следующее обновление лимита",
      body: nextResetAt ? `Ближайший сброс: ${formatDate(nextResetAt)}.` : "Для вашего текущего режима отдельный сброс может не понадобиться.",
      badge: "Лимиты",
      tone: "neutral" as const,
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Статистика"
      title="Статистика без лишних деталей"
      description="Здесь только безопасные сводки: срок, трафик, устройства и живая активность. Личные ссылки, адреса узлов и технические параметры не показываем."
      actions={
        <>
          <AppRouteLink href="/subscription/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Тарифы и оплата
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Режим",
          value: resolvePlanLabel(dash, user),
          hint: dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Дата уточняется",
          tone: dash?.is_active ? "success" : "warning",
        },
        {
          label: "Трафик",
          value: formatGb(trafficUsed),
          hint: resolveTrafficStatusText(dash, user),
          tone: "neutral",
        },
        {
          label: "Устройства",
          value: `${formatCount(deviceCount)} из ${formatCount(deviceLimit)}`,
          hint: "Связанные с вашим профилем экраны.",
          tone: "neutral",
        },
        {
          label: "Людей онлайн",
          value: formatCount(activeUsersEstimate),
          hint: "Ориентир по текущей активности, не список людей.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Короткая картина"
        badge={dash?.is_active ? "Доступ активен" : "Нужно действие"}
        badgeTone={dash?.is_active ? "success" : "warning"}
        title={dash?.is_active ? "Все важное видно без технических деталей" : "Сначала верните срок действия"}
        description={
          dash?.is_active
            ? "Если что-то выглядит странно, можно сразу открыть поддержку: ей хватит безопасного контекста из кабинета."
            : "После продления эта страница снова покажет свежую сводку по профилю."
        }
        actions={
          <>
            <AppRouteLink href="/support/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
              Открыть поддержку
            </AppRouteLink>
            <AppRouteLink href="/downloads/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Загрузки
            </AppRouteLink>
          </>
        }
        details={[
          {
            label: "Подключений сейчас",
            value: formatCount(activeConnections),
            hint: activeConnections > 0 ? "Приложение сейчас где-то открыто." : "Если нужен доступ, откройте приложение.",
            tone: activeConnections > 0 ? "success" : "neutral",
          },
          {
            label: "Точки доступа",
            value: `${formatCount(activeNodes)} из ${formatCount(knownNodes)}`,
            hint: "Показываем только счетчик готовности, без адресов и портов.",
            tone: "neutral",
          },
          {
            label: "Следующее действие",
            value: dash?.is_active ? "Наблюдать" : "Продлить",
            hint: dash?.is_active ? "Если проблем нет, делать ничего не нужно." : "Продление не меняет ваш профиль.",
            tone: dash?.is_active ? "success" : "warning",
          },
        ]}
      />

      <CabinetSection
        eyebrow="Сводки"
        title="Что можно проверить"
        description="Эти данные помогают понять состояние профиля, не раскрывая личные ссылки или сетевые подробности."
      >
        <CabinetCardGrid items={visibilityItems} />
      </CabinetSection>
    </CabinetRoute>
  );
}
