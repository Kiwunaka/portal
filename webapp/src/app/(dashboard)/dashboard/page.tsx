"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetList, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import {
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { fetchNodeStatus, type NodeStatus } from "@/lib/api";
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

function formatCount(value?: number | null): string {
  if (value == null || !Number.isFinite(Number(value))) return "0";
  return new Intl.NumberFormat("ru-RU").format(Math.max(0, Math.round(Number(value))));
}

function formatLocationReadiness(ready: number, total: number): string {
  if (!Number.isFinite(total) || total <= 0) return "Проверим позже";
  return `${formatCount(ready)} из ${formatCount(total)}`;
}

function locationReadinessTone(ready: number, total: number): "success" | "warning" | "neutral" {
  if (!Number.isFinite(total) || total <= 0) return "neutral";
  return ready < total ? "warning" : "success";
}

function deviceTitle(name?: string | null, platform?: string | null): string {
  const cleanName = String(name || "").trim();
  const cleanPlatform = String(platform || "").trim();
  if (cleanName && cleanPlatform) return `${cleanName} · ${cleanPlatform}`;
  return cleanName || cleanPlatform || "Устройство";
}

function routeLabel(dash: unknown, user: unknown): string {
  const dashboard = dash as { location_matrix?: { locations?: Array<{ label?: string | null }> } | null; hidden_transport_matrix?: { logical_location_count?: number | null } | null } | null;
  const profile = user as { location_matrix?: { locations?: Array<{ label?: string | null }> } | null; hidden_transport_matrix?: { logical_location_count?: number | null } | null } | null;
  const locations = dashboard?.location_matrix?.locations || profile?.location_matrix?.locations || [];
  const firstLabel = locations.find((item) => String(item.label || "").trim())?.label;
  const count = dashboard?.hidden_transport_matrix?.logical_location_count ?? profile?.hidden_transport_matrix?.logical_location_count ?? locations.length;

  if (firstLabel && count <= 1) return firstLabel;
  if (count > 1) return `${formatCount(count)} локации`;
  return "Автоматически";
}

export default function DashboardPage() {
  const { user, dash } = usePortalSession();
  const [nodes, setNodes] = useState<NodeStatus[]>([]);
  const [nodesError, setNodesError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      try {
        const rows = await fetchNodeStatus({ signal: controller.signal });
        if (controller.signal.aborted) return;
        setNodes(rows);
        setNodesError("");
      } catch (error) {
        if (controller.signal.aborted || (error as { name?: string } | null)?.name === "AbortError") return;
        setNodesError("node_status_unavailable");
      }
    };

    void load();
    return () => controller.abort();
  }, []);

  const accessState = getAccessState(dash, user);
  const trialMode = isTrialPremiumState(accessState);
  const softMode = isSoftModeState(accessState);
  const nextResetAt = getNextResetAt(dash, user);
  const deviceLimit = getDeviceLimit(dash, user);
  const deviceCount = user?.sync?.device_count ?? user?.devices?.length ?? 0;
  const activeConnections = dash?.connection_snapshot?.active_connections ?? dash?.active_sessions ?? 0;
  const activeNodes = dash?.connection_snapshot?.active_nodes ?? user?.connections?.active_nodes ?? 0;
  const knownNodes = dash?.connection_snapshot?.known_nodes ?? user?.connections?.known_nodes ?? nodes.length;
  const healthyNodes = nodes.filter((node) => node.is_healthy).length;
  const routeSummary = routeLabel(dash, user);

  const attentionItems = (() => {
    const items: Array<{
      key: string;
      title: string;
      body: string;
      tone: "success" | "warning" | "danger" | "info" | "neutral";
      badge?: string;
      action?: ReactNode;
    }> = [];

    if (!dash?.is_active) {
      items.push({
        key: "inactive",
        title: "Доступу нужно продление",
        body: "Профиль и устройства останутся теми же. Нужно только вернуть срок действия.",
        tone: "danger",
        badge: "Сейчас важно",
        action: (
          <AppRouteLink href="/subscription/checkout/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Продлить
          </AppRouteLink>
        ),
      });
    } else if (trialMode) {
      items.push({
        key: "trial",
        title: "Сейчас идет пробный период",
        body: `Он действует до ${formatDate(dash.expiry_at)}. Если сервис подходит, можно выбрать продление заранее.`,
        tone: "warning",
        badge: "Можно заранее",
        action: (
          <AppRouteLink href="/subscription/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Посмотреть варианты
          </AppRouteLink>
        ),
      });
    } else if (softMode) {
      items.push({
        key: "soft",
        title: "Сейчас режим с ограничениями",
        body: nextResetAt
          ? `Доступ без месячного лимита вернется после сброса ${formatDate(nextResetAt)}. Если не хочется ждать, откройте оплату.`
          : "Если не хочется ждать следующего цикла, можно сразу открыть оплату.",
        tone: "warning",
        badge: "Стоит проверить",
        action: (
          <AppRouteLink href="/subscription/checkout/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Вернуть доступ без лимита
          </AppRouteLink>
        ),
      });
    }

    if (dash?.is_active && activeConnections === 0) {
      items.push({
        key: "no-connections",
        title: "Сейчас нет активного подключения",
        body: "Обычно это значит, что приложение просто не открыто на устройстве. Сам доступ при этом может быть в порядке.",
        tone: "neutral",
        badge: "На заметку",
        action: (
          <AppRouteLink href="/downloads/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Открыть загрузки
          </AppRouteLink>
        ),
      });
    }

    if (nodesError) {
      items.push({
        key: "nodes-error",
        title: "Статус сети обновим позже",
        body: "Кабинет продолжает работать. Если само подключение ведет себя неровно, лучше сразу открыть поддержку.",
        tone: "info",
        badge: "Проверка позже",
        action: (
          <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Поддержка
          </AppRouteLink>
        ),
      });
    } else if (knownNodes > 0 && healthyNodes < knownNodes) {
      items.push({
        key: "nodes-attention",
        title: "Часть локаций требует внимания",
        body: `Сейчас готовы ${healthyNodes} из ${knownNodes}. Если это уже заметно по качеству доступа, лучше написать нам.`,
        tone: "warning",
        badge: "Стоит проверить",
        action: (
          <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Сообщить
          </AppRouteLink>
        ),
      });
    }

    if (!items.length) {
      items.push({
        key: "all-good",
        title: "Сейчас все спокойно",
        body: "Статус ровный. Кабинет нужен только чтобы иногда проверить детали и быстро перейти дальше.",
        tone: "success",
        badge: "Все в порядке",
        action: (
          <AppRouteLink href="/devices/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
            Проверить устройства
          </AppRouteLink>
        ),
      });
    }

    return items.slice(0, 4);
  })();

  const nextSteps = [
    {
      key: "downloads",
      title: dash?.is_active ? "Открыть приложение" : "Вернуть доступ",
      body: dash?.is_active
        ? "Если хотите подключиться на новом экране, начните с загрузок."
        : "Сначала верните срок действия, потом продолжайте тем же профилем.",
      badge: "Шаг 1",
      tone: dash?.is_active ? ("neutral" as const) : ("warning" as const),
      action: (
        <AppRouteLink
          href={dash?.is_active ? "/downloads/" : "/subscription/checkout/"}
          className="text-sm font-semibold text-emerald-800 dark:text-emerald-300"
        >
          {dash?.is_active ? "Загрузки" : "Продлить"}
        </AppRouteLink>
      ),
    },
    {
      key: "subscription",
      title: "Проверить тариф и срок",
      body: "Там видны режим, дата окончания и понятные варианты продления без лишних переходов.",
      badge: "Шаг 2",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/subscription/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Тарифы и оплата
        </AppRouteLink>
      ),
    },
    {
      key: "support",
      title: "Если что-то не так, продолжить один кейс",
      body: "Так не теряется история и не нужно заново объяснять всю ситуацию.",
      badge: "Шаг 3",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Поддержка
        </AppRouteLink>
      ),
    },
  ];

  const deviceItems = (user?.devices || []).slice(0, 3).map((device) => ({
    key: device.id,
    title: deviceTitle(device.name, device.platform),
    body: device.is_current
      ? "Это устройство, с которого кабинет открыт сейчас."
      : device.last_seen_at
        ? `Последний раз было в сети ${formatDate(device.last_seen_at)}.`
        : "Появится здесь после первого входа в приложение.",
    badge: device.is_current ? "Сейчас здесь" : device.is_active ? "Связано" : "Без активности",
    tone: device.is_current || device.is_active ? ("success" as const) : ("neutral" as const),
  }));

  const utilityCards = [
    {
      key: "network",
      title: "Сеть сейчас",
      body: nodesError
        ? "Статус сети подтянем позже. Если проблема видна в приложении, лучше сразу открыть поддержку."
        : knownNodes > 0
          ? `${formatLocationReadiness(healthyNodes || activeNodes, knownNodes)} локаций сейчас выглядят готовыми.`
          : "Сводка по локациям появится после обновления телеметрии.",
      badge: nodesError || knownNodes <= 0 ? "Проверка позже" : `${formatCount(healthyNodes || activeNodes)}/${formatCount(knownNodes)}`,
      tone: nodesError ? ("info" as const) : locationReadinessTone(healthyNodes || activeNodes, knownNodes),
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
      key: "support",
      title: "Поддержка",
      body: "Если вопрос уже был, удобнее продолжать один кейс и не терять контекст.",
      badge: "Если понадобится",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/support/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Перейти
        </AppRouteLink>
      ),
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Главная"
      title={dash?.is_active ? "Статус и следующий шаг" : "Доступу нужно внимание"}
      description={
        dash?.is_active
          ? "Здесь только главное: что сейчас с доступом, что стоит проверить и куда идти дальше."
          : "Сначала верните спокойный рабочий статус, потом продолжайте тем же профилем."
      }
      actions={
        <>
          <AppRouteLink
            href={dash?.is_active ? "/downloads/" : "/subscription/checkout/"}
            className="btn-primary rounded-full px-5 py-3 text-sm font-semibold"
          >
            {dash?.is_active ? "Загрузки" : "Вернуть доступ"}
          </AppRouteLink>
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Поддержка
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Статус",
          value: dash?.is_active ? "Доступ активен" : "Нужно продление",
          hint: dash?.is_active ? "Профиль уже работает." : "Возвращается из раздела оплаты.",
          tone: dash?.is_active ? "success" : "warning",
        },
        {
          label: "План",
          value: resolvePlanLabel(dash, user),
          hint: dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Дату уточним после синхронизации",
          tone: "neutral",
        },
        {
          label: "Трафик",
          value: resolveTrafficStatusText(dash, user),
          hint: nextResetAt ? `Следующий сброс ${formatDate(nextResetAt)}` : "Без отдельного сброса",
          tone: softMode ? "warning" : "neutral",
        },
        {
          label: "Устройства",
          value: `${formatCount(deviceCount)} из ${formatCount(deviceLimit)}`,
          hint: "Сколько экранов уже связано с профилем.",
          tone: "neutral",
        },
        {
          label: "Маршрут",
          value: routeSummary,
          hint: "Приложение выбирает рабочий путь без ручных настроек.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Что происходит"
        badge={dash?.is_active ? "Кабинет в спокойном режиме" : "Нужен следующий шаг"}
        badgeTone={dash?.is_active ? "success" : "warning"}
        title={attentionItems[0]?.title || "Все спокойно"}
        description={attentionItems[0]?.body || "Если что-то изменится, это сразу появится здесь."}
        actions={
          <>
            {attentionItems[0]?.action}
            <AppRouteLink href="/devices/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Устройства
            </AppRouteLink>
          </>
        }
        details={[
          {
            label: "Активных подключений",
            value: formatCount(activeConnections),
            hint: activeConnections > 0 ? "Есть активное подключение по профилю." : "Если нужен доступ сейчас, откройте приложение.",
            tone: activeConnections > 0 ? "success" : "neutral",
          },
          {
            label: "Маршрут",
            value: routeSummary,
            hint: "Показываем понятную сводку, без технических деталей.",
            tone: "neutral",
          },
          {
            label: "Локации",
            value: nodesError ? "Проверим позже" : formatLocationReadiness(healthyNodes || activeNodes, knownNodes),
            hint: nodesError || knownNodes <= 0 ? "Если доступ ведет себя неровно, напишите нам." : "Короткая сводка по доступным направлениям.",
            tone: nodesError ? "info" : locationReadinessTone(healthyNodes || activeNodes, knownNodes),
          },
        ]}
        footer={
          <div className="grid gap-3 md:grid-cols-3">
            {nextSteps.map((item) => (
              <div key={item.key} className="rounded-[1.2rem] border border-slate-200/80 bg-slate-50/85 px-4 py-4 dark:border-white/10 dark:bg-white/[0.04]">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">{item.badge}</p>
                <h3 className="mt-2 text-sm font-semibold text-slate-950 dark:text-slate-50">{item.title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{item.body}</p>
                <div className="mt-4">{item.action}</div>
              </div>
            ))}
          </div>
        }
      />

      <div className="grid gap-6 xl:grid-cols-[1.06fr_0.94fr]">
        <CabinetSection
          eyebrow="Что требует внимания"
          title="Только важное"
          description="Если что-то поменялось, вы увидите это здесь. Если всё спокойно, это тоже сразу видно."
        >
          <CabinetList items={attentionItems.slice(1)} empty="Прямо сейчас ничего дополнительного проверять не нужно." />
        </CabinetSection>

        <CabinetSection
          eyebrow="Ваши устройства"
          title="Что уже связано с профилем"
          description="Удобно проверить перед переносом доступа на новый экран."
          actions={
            <AppRouteLink href="/devices/" className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
              Все устройства
            </AppRouteLink>
          }
        >
          <CabinetList items={deviceItems} empty="Устройства появятся здесь после первого входа в приложение на Android или Windows." />
        </CabinetSection>
      </div>

      <CabinetSection
        eyebrow="Полезное рядом"
        title="Быстрые разделы"
        description="Ниже только те места, куда чаще всего действительно стоит перейти."
      >
        <CabinetCardGrid items={utilityCards} />
      </CabinetSection>
    </CabinetRoute>
  );
}
