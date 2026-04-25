"use client";

import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import {
  getAccessState,
  getDeviceLimit,
  getNextResetAt,
  getTrafficLimitGb,
  isFreeMonthlyState,
  isPaidUnlimitedState,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
  resolveTrafficStatusText,
} from "@/lib/access-policy";
import { fetchPublicPlans, type PlanCatalogRow } from "@/lib/api";
import { getTariffPlans, normalizePlanCode } from "@/lib/portal";
import { usePortalSession } from "@/lib/session";

function fallbackPlans(): PlanCatalogRow[] {
  return getTariffPlans()
    .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
    .map((plan) => ({
      code: plan.code,
      label: plan.label,
      amount_rub: Number(plan.amount_rub || 0),
      amount_stars: Number(plan.amount_stars || 0),
      days: Number(plan.duration_days || 0),
      device_limit: Number(plan.device_limit || 0),
      node_policy: plan.node_policy,
      badge: plan.badge || "",
      is_active: Boolean(plan.is_active),
      sort_order: Number(plan.sort_order || 0),
    }))
    .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));
}

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

function nodePolicyLabel(value?: string | null): string {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "free_single_location" || normalized === "nl_only") return "базовая локация";
  if (normalized === "managed_premium" || normalized === "paid_pool") return "без месячного лимита";
  return "по текущему доступу";
}

export default function SubscriptionPage() {
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<PlanCatalogRow[]>(() => fallbackPlans());
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const payload = await fetchPublicPlans();
        const rows = (payload.plans || [])
          .filter((plan) => Boolean(plan.is_active))
          .sort((a, b) => Number(a.sort_order || 0) - Number(b.sort_order || 0));

        if (!cancelled) {
          setPlans(rows.length ? rows : fallbackPlans());
          setError("");
        }
      } catch {
        if (!cancelled) {
          setPlans(fallbackPlans());
          setError("Не удалось обновить тарифы автоматически.");
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const softMode = isSoftModeState(accessState);
  const nextResetAt = getNextResetAt(dash, user);
  const deviceLimit = getDeviceLimit(dash, user);
  const freeLimitGb = getTrafficLimitGb(dash, user);
  const currentPlanCode = normalizePlanCode(dash?.current_plan_code || dash?.sub_type || "");

  const planCards = plans.slice(0, 4).map((plan) => {
    const normalizedCode = normalizePlanCode(plan.code);
    const isCurrent = Boolean(currentPlanCode) && normalizedCode === currentPlanCode;

    return {
      key: plan.code,
      title: `${plan.label} · ${Number(plan.amount_rub || 0)} ₽`,
      body: `${plan.days} дней · до ${plan.device_limit} устройств · ${nodePolicyLabel(plan.node_policy)}${plan.badge ? ` · ${plan.badge}` : ""}`,
      badge: isCurrent ? "Сейчас у вас" : plan.badge || "Доступно",
      tone: isCurrent ? ("success" as const) : plan.days >= 180 ? ("info" as const) : ("neutral" as const),
      action: isCurrent ? (
        <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">Уже действует</span>
      ) : (
        <AppRouteLink
          href={`/subscription/checkout/?plan=${encodeURIComponent(plan.code)}`}
          className="text-sm font-semibold text-emerald-800 dark:text-emerald-300"
        >
          Выбрать
        </AppRouteLink>
      ),
    };
  });

  const paymentCards = [
    {
      key: "checkout",
      title: "Перейти к оплате",
      body: "Самый прямой путь, если нужно продлить срок без лишних переходов.",
      badge: "Основной путь",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/subscription/checkout/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть оплату
        </AppRouteLink>
      ),
    },
    {
      key: "redeem",
      title: "Применить ключ доступа",
      body: "Если у вас уже есть подарочный или оплаченный ключ доступа, можно использовать его здесь.",
      badge: "Если ключ уже есть",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/redeem/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Применить ключ
        </AppRouteLink>
      ),
    },
    {
      key: "support",
      title: "Если после оплаты статус не обновился",
      body: "Не нужно искать скрытые экраны. Лучше сразу открыть поддержку и продолжить один кейс.",
      badge: "Человеческий путь",
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
      title: paidMode ? "Доступ без месячного лимита уже активен" : "Доступ без месячного лимита — самый спокойный вариант",
      body: paidMode
        ? "Сейчас аккаунт работает без месячного лимита трафика."
        : "Если не хочется думать о месячных ограничениях, смотреть стоит в эту сторону.",
      badge: paidMode ? "Сейчас так" : "Вариант",
      tone: paidMode ? ("success" as const) : ("neutral" as const),
    },
    {
      key: "trial",
      title: trialMode ? "Пробные 5 дней уже идут" : "Попробовать 5 дней можно в полном режиме",
      body: trialMode ? `Период действует до ${formatDate(dash?.expiry_at)}.` : "После него можно спокойно решить, нужен ли вам платный режим дальше.",
      badge: trialMode ? "Активен" : "Как это работает",
      tone: trialMode ? ("warning" as const) : ("neutral" as const),
    },
    {
      key: "free",
      title: freeMode ? "Базовый режим сейчас активен" : "Базовый режим остается запасным",
      body: freeMode
        ? `Сейчас ориентир до ${freeLimitGb || 5} ГБ и до ${deviceLimit} устройств.`
        : "Он подходит для спокойного повседневного использования и знакомства с сервисом.",
      badge: freeMode ? "Сейчас так" : "Запасной путь",
      tone: freeMode && !softMode ? ("info" as const) : softMode ? ("warning" as const) : ("neutral" as const),
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Тарифы и оплата"
      title={dash?.is_active ? "Продление и режимы" : "Вернуть доступ без лишних шагов"}
      description={
        dash?.is_active
          ? "Здесь только практичные вещи: текущий режим, понятные варианты продления и работа с ключом."
          : "Если срок закончился, отсюда проще всего вернуть доступ и продолжить с тем же аккаунтом."
      }
      actions={
        <>
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
            Перейти к оплате
          </AppRouteLink>
          <AppRouteLink href="/redeem/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            У меня есть ключ доступа
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Текущий режим",
          value: resolvePlanLabel(dash, user),
          hint: dash?.is_active ? "Доступ уже активен." : "Если срок закончился, вернуть его можно отсюда.",
          tone: dash?.is_active ? "success" : "warning",
        },
        {
          label: "Срок",
          value: formatDate(dash?.expiry_at || user?.expiry_at),
          hint: trialMode ? "Сейчас действуют пробные 5 дней." : "Это ближайшая важная дата по доступу.",
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
          value: `До ${deviceLimit}`,
          hint: freeMode ? `В базовом режиме ориентир до ${freeLimitGb || 5} ГБ.` : "Лимит действует на весь аккаунт.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Сейчас по доступу"
        badge={dash?.is_active ? "Можно продлить спокойно" : "Нужен следующий шаг"}
        badgeTone={dash?.is_active ? "success" : "warning"}
        title={dash?.is_active ? "Выберите удобный способ продлить" : "Сначала верните срок действия"}
        description={
          dash?.is_active
            ? "Показываем только рабочие варианты и самый прямой путь к оплате."
            : "Как только срок снова станет активным, устройства и история останутся на месте."
        }
        actions={
          <>
            <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
              Открыть оплату
            </AppRouteLink>
            <AppRouteLink href="/redeem/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Применить ключ доступа
            </AppRouteLink>
          </>
        }
        details={[
          {
            label: "План сейчас",
            value: resolvePlanLabel(dash, user),
            hint: dash?.expiry_at ? `До ${formatDate(dash.expiry_at)}` : "Дату уточним позже",
            tone: "neutral",
          },
          {
            label: "Без месячного лимита",
            value: paidMode ? "Активен" : "Можно включить",
            hint: paidMode ? "Без месячного лимита трафика." : "Подходит, если хочется меньше думать об ограничениях.",
            tone: paidMode ? "success" : "neutral",
          },
          {
            label: "Если оплата уже была",
            value: "Открыть поддержку",
            hint: "Если статус не обновился, лучше сразу продолжить кейс в поддержке.",
            tone: "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <CabinetSection
          eyebrow="Варианты"
          title="Что можно выбрать"
          description="Показываем только рабочие варианты продления, без маркетингового шума."
        >
          <CabinetCardGrid items={planCards} className="xl:grid-cols-2" />
          {error ? <p className="mt-4 text-sm text-amber-700 dark:text-amber-200">{error} Показываем сохраненные варианты.</p> : null}
        </CabinetSection>

        <CabinetSection
          eyebrow="Что делать дальше"
          title="Три понятных сценария"
          description="Почти всегда нужен один из этих путей."
        >
          <CabinetCardGrid items={paymentCards} className="xl:grid-cols-1" />
        </CabinetSection>
      </div>

      <CabinetSection
        eyebrow="История"
        title="История оплат"
        description="Платежная история появится здесь, когда backend отдаст безопасную пользовательскую выписку."
        actions={
          <AppRouteLink href="/support/" className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
            Поддержка
          </AppRouteLink>
        }
        tone="info"
      >
        <div className="rounded-[1.3rem] border border-dashed border-sky-200/80 bg-white/72 px-4 py-4 text-sm leading-6 text-slate-600 dark:border-sky-400/20 dark:bg-white/[0.04] dark:text-slate-300">
          <p className="font-semibold text-slate-950 dark:text-slate-50">История оплат пока не подключена.</p>
          <p className="mt-2">
            Мы не показываем декоративные строки и не придумываем квитанции. Если оплата уже была, а срок не обновился,
            откройте поддержку: оператор проверит платеж по безопасным данным и продолжит тот же кейс.
          </p>
        </div>
      </CabinetSection>

      <CabinetSection
        eyebrow="Коротко о режимах"
        title="Как на это смотреть"
        description="Если не хочется разбираться в терминах, этой короткой сводки обычно достаточно."
      >
        <CabinetCardGrid items={modeCards} />
      </CabinetSection>
    </CabinetRoute>
  );
}
