"use client";

import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import SubscriptionQrCard from "@/components/subscription-qr-card";
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
import { fetchPublicPlans, type PlanCatalogRow, type UserPaymentOrder } from "@/lib/api";
import { getTariffPlans, normalizePlanCode } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
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

function formatPaymentAmount(order: UserPaymentOrder): string {
  const currency = String(order.currency || "RUB").toUpperCase();
  try {
    return new Intl.NumberFormat("ru-RU", {
      style: "currency",
      currency,
      maximumFractionDigits: 0,
    }).format(Number(order.amount || 0));
  } catch {
    return `${Number(order.amount || 0).toLocaleString("ru-RU")} ${currency}`;
  }
}

function paymentStatusLabel(value?: string | null): string {
  const status = String(value || "").trim().toLowerCase();
  if (status === "paid") return "Оплачено";
  if (status === "failed") return "Не прошло";
  if (status === "cancelled") return "Отменено";
  if (status === "refunded") return "Возврат";
  if (status === "chargeback") return "Спор";
  if (status === "manual_review") return "Проверяем вручную";
  if (status === "pending_verification") return "Ждет проверки";
  if (status === "pending") return "В обработке";
  return "Создано";
}

function paymentStatusClass(value?: string | null): string {
  const status = String(value || "").trim().toLowerCase();
  if (status === "paid") return "bg-emerald-50 text-emerald-800 dark:bg-emerald-400/10 dark:text-emerald-200";
  if (["failed", "cancelled", "refunded", "chargeback"].includes(status)) {
    return "bg-rose-50 text-rose-800 dark:bg-rose-400/10 dark:text-rose-200";
  }
  if (["manual_review", "pending_verification"].includes(status)) {
    return "bg-amber-50 text-amber-800 dark:bg-amber-400/10 dark:text-amber-200";
  }
  return "bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-slate-200";
}

function nodePolicyLabel(value?: string | null): string {
  const normalized = String(value || "").trim().toLowerCase();
  if (normalized === "free_single_location" || normalized === "nl_only") return "NL-free";
  if (normalized === "managed_premium" || normalized === "paid_pool") return "Полный пул";
  return "По профилю";
}

export default function SubscriptionPage() {
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<PlanCatalogRow[]>(() => fallbackPlans());
  const [error, setError] = useState("");
  const [copyStatus, setCopyStatus] = useState("");
  const [manualAccessOpen, setManualAccessOpen] = useState(false);

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
      } catch (nextError) {
        if (!cancelled) {
          setPlans(fallbackPlans());
          setError(userFacingErrorMessage(nextError, "Не удалось обновить тарифы, показываем сохраненные варианты."));
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
  const subscriptionUrl = String(user?.subscription_url || dash?.subscription_url || "").trim();
  const manualAccessReady = Boolean(subscriptionUrl && (dash?.is_active || user?.is_active));
  const paymentOrders = (dash?.payment_orders || []).slice(0, 5);

  const copySubscriptionUrl = async () => {
    if (!manualAccessReady) {
      setCopyStatus("Ссылка появится после активации доступа.");
      return;
    }
    try {
      await navigator.clipboard.writeText(subscriptionUrl);
      setCopyStatus("Ссылка скопирована.");
    } catch {
      setCopyStatus("Не удалось скопировать автоматически. Выделите ссылку вручную.");
    }
  };

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
      title: "Проверить статус продления",
      body: "Покажем тарифы, текущую готовность оплаты и безопасный следующий шаг.",
      badge: "Статус оплаты",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/subscription/checkout/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Проверить статус продления
        </AppRouteLink>
      ),
    },
    {
      key: "redeem",
      title: "Применить ключ",
      body: "Если у вас уже есть подарок или оплаченный ключ, можно использовать его здесь.",
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
      title: paidMode ? "Полный режим уже активен" : "Полный режим — самый спокойный вариант",
      body: paidMode
        ? "Сейчас профиль работает без месячного лимита трафика."
        : "Если не хочется думать о месячных ограничениях, смотреть стоит в эту сторону.",
      badge: paidMode ? "Сейчас так" : "Вариант",
      tone: paidMode ? ("success" as const) : ("neutral" as const),
    },
    {
      key: "trial",
      title: trialMode ? "Пробный период уже идет" : "Пробный период показывает сервис в полном режиме",
      body: trialMode ? `Он действует до ${formatDate(dash?.expiry_at)}.` : "После него можно спокойно решить, нужен ли вам платный режим дальше.",
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
          : "Если срок закончился, отсюда проще всего вернуть доступ и продолжить тем же профилем."
      }
      actions={
        <>
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
            Проверить статус продления
          </AppRouteLink>
          <AppRouteLink href="/redeem/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            У меня есть ключ
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Текущий режим",
          value: resolvePlanLabel(dash, user),
          hint: dash?.is_active ? "Профиль уже активен." : "Если срок закончился, вернуть его можно отсюда.",
          tone: dash?.is_active ? "success" : "warning",
        },
        {
          label: "Срок",
          value: formatDate(dash?.expiry_at || user?.expiry_at),
          hint: trialMode ? "Сейчас действует пробный период." : "Это ближайшая важная дата по доступу.",
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
          hint: freeMode ? `В базовом режиме ориентир до ${freeLimitGb || 5} ГБ.` : "Лимит действует на весь профиль.",
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Сейчас по профилю"
        badge={dash?.is_active ? "Можно продлить спокойно" : "Нужен следующий шаг"}
        badgeTone={dash?.is_active ? "success" : "warning"}
        title={dash?.is_active ? "Выберите удобный способ продлить" : "Сначала верните срок действия"}
        description={
          dash?.is_active
            ? "Кабинет не пытается продавать лишнее. Показываем доступные варианты, честный статус продления и безопасный следующий шаг."
            : "Как только срок снова станет активным, устройства и история останутся на месте."
        }
        actions={
          <>
            <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
              Проверить статус продления
            </AppRouteLink>
            <AppRouteLink href="/redeem/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Применить ключ
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
            label: "Полный режим",
            value: paidMode ? "Активен" : "Можно включить",
            hint: paidMode ? "Без месячного лимита трафика." : "Подходит, если хочется меньше думать об ограничениях.",
            tone: paidMode ? "success" : "neutral",
          },
          {
            label: "Если оплата уже была",
            value: "Не искать обходы",
            hint: "Если статус не обновился, лучше сразу продолжить кейс в поддержке.",
            tone: "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <CabinetSection
          eyebrow="Варианты"
          title="Что можно выбрать"
          description="Показываем доступные варианты и честный статус продления, без маркетингового шума."
        >
          <CabinetCardGrid items={planCards} className="xl:grid-cols-2" />
          {error ? <p className="mt-4 text-sm text-amber-700 dark:text-amber-200">{error}</p> : null}
        </CabinetSection>

        <CabinetSection
          eyebrow="Восстановление"
          title="Ручное подключение только как запасной путь"
          description="Основной сценарий: откройте POKROV, войдите в тот же аккаунт и дайте приложению подтянуть профиль. QR и личная ссылка нужны только для совместимого клиента или восстановления."
          tone={manualAccessReady ? "info" : "warning"}
          actions={
            <AppRouteLink href="/downloads/" className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
              Загрузки
            </AppRouteLink>
          }
        >
          <div className="rounded-[1.3rem] border border-[color:var(--atlas-border)] bg-[var(--atlas-surface)] p-4">
            <p className="text-sm leading-6 text-[var(--atlas-text-soft)]">
              {manualAccessReady
                ? "Личная ссылка готова, но мы не показываем ее первой. Используйте ее только если приложение POKROV сейчас недоступно или поддержка попросила открыть ручной вариант."
                : "После оплаты или активации ключа запасной ручной вариант станет доступен здесь."}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setManualAccessOpen((value) => !value)}
                disabled={!manualAccessReady}
                className="outline-btn rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60"
              >
                {manualAccessOpen ? "Скрыть ручной вариант" : "Показать ручной вариант"}
              </button>
              {!manualAccessReady ? (
                <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                  Проверить статус продления
                </AppRouteLink>
              ) : null}
            </div>
          </div>

          {manualAccessOpen ? (
            <div className="mt-5 grid gap-5 lg:grid-cols-[240px_minmax(0,1fr)]">
              <div className="min-w-0">
                <SubscriptionQrCard value={subscriptionUrl} active={manualAccessReady} />
              </div>
              <div className="min-w-0">
                <p className="text-sm leading-6 text-[var(--atlas-text-soft)]">
                  Скопируйте ссылку или отсканируйте QR-код только на устройстве, которому доверяете.
                </p>
                <div className="mt-4 rounded-[1.1rem] border border-[color:var(--atlas-border)] bg-[var(--atlas-glass)] px-3 py-3">
                  <p className="break-all font-mono text-xs leading-6 text-[var(--atlas-text)]">{subscriptionUrl}</p>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <button
                    type="button"
                    onClick={() => void copySubscriptionUrl()}
                    disabled={!manualAccessReady}
                    className="btn-primary rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60"
                  >
                    Скопировать ссылку
                  </button>
                  <a href={subscriptionUrl} target="_blank" rel="noreferrer" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
                    Открыть ссылку
                  </a>
                </div>
                {copyStatus ? <p className="mt-3 text-sm font-semibold text-emerald-800 dark:text-emerald-300">{copyStatus}</p> : null}
              </div>
            </div>
          ) : null}
        </CabinetSection>

        <CabinetSection
          eyebrow="Что делать дальше"
          title="Три понятных сценария"
          description="Почти всегда нужен один из этих путей."
        >
          <CabinetCardGrid items={paymentCards} className="xl:grid-cols-1" />
        </CabinetSection>
      </div>

      <div id="payment-history" className="scroll-mt-28">
        <CabinetSection
          eyebrow="История"
          title="История оплат"
          description={
            paymentOrders.length
              ? "Показываем только ваши заказы из backend: сумму, статус и дату без служебных webhook-данных."
              : "Платежная история появится здесь после первого созданного заказа."
          }
          actions={
            <AppRouteLink href="/support/" className="outline-btn rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.12em]">
              Поддержка
            </AppRouteLink>
          }
          tone="info"
        >
          {paymentOrders.length ? (
            <div className="overflow-hidden rounded-[1.3rem] border border-[color:var(--atlas-border)] bg-white/72 dark:bg-white/[0.04]">
              <div className="grid grid-cols-[minmax(0,1fr)_auto] gap-3 border-b border-[color:var(--atlas-border)] px-4 py-3 text-xs font-semibold uppercase tracking-[0.12em] text-[var(--atlas-text-muted)]">
                <span>Заказ</span>
                <span>Статус</span>
              </div>
              {paymentOrders.map((order) => (
                <div key={`${order.provider}-${order.order_id}`} className="grid gap-3 border-b border-[color:var(--atlas-border)] px-4 py-4 last:border-b-0 md:grid-cols-[minmax(0,1fr)_auto]">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-[var(--atlas-text)]">
                      {formatPaymentAmount(order)} · {order.plan_code || "тариф"}
                    </p>
                    <p className="mt-1 truncate text-xs text-[var(--atlas-text-soft)]">
                      {order.provider} · {formatDate(order.paid_at || order.created_at)} · {order.order_id}
                    </p>
                  </div>
                  <span className={`h-fit rounded-full px-3 py-1 text-xs font-semibold ${paymentStatusClass(order.status)}`}>
                    {paymentStatusLabel(order.status)}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-[1.3rem] border border-dashed border-sky-200/80 bg-white/72 px-4 py-4 text-sm leading-6 text-slate-600 dark:border-sky-400/20 dark:bg-white/[0.04] dark:text-slate-300">
              <p className="font-semibold text-slate-950 dark:text-slate-50">Истории оплат пока нет.</p>
              <p className="mt-2">
                Мы не показываем декоративные строки и не придумываем квитанции. Если оплата уже была, а срок не обновился,
                откройте поддержку: оператор проверит платеж по безопасным данным и продолжит тот же кейс.
              </p>
            </div>
          )}
        </CabinetSection>
      </div>

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
