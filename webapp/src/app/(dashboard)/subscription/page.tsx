"use client";

import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import SubscriptionQrCard from "@/components/subscription-qr-card";
import {
  getAccessState,
  getNextResetAt,
  getTrafficLimitGb,
  isFreeMonthlyState,
  isPaidUnlimitedState,
  isSoftModeState,
  isTrialPremiumState,
  resolvePlanLabel,
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
  if (normalized === "free_single_location" || normalized === "nl_only") return "Базовый узел";
  if (normalized === "managed_premium" || normalized === "paid_pool") return "Полный пул";
  return "По профилю";
}

const manualStepCards = [
  {
    key: "copy",
    title: "Скопируйте личную ссылку",
    body: "Это ссылка подключения для совместимого клиента. Она не привязывает Telegram и не заменяет код активации.",
    badge: "1",
    tone: "neutral" as const,
  },
  {
    key: "client",
    title: "Установите клиент",
    body: "Для Android проще начать с Hiddify или NekoBox. Для Windows обычно подходят Hiddify или v2rayN.",
    badge: "2",
    tone: "neutral" as const,
  },
  {
    key: "import",
    title: "Импортируйте ссылку",
    body: "Нажмите плюс, выберите импорт из буфера или subscription URL, вставьте ссылку и обновите профиль.",
    badge: "3",
    tone: "neutral" as const,
  },
  {
    key: "connect",
    title: "Выберите профиль и подключитесь",
    body: "Если клиент попросит режим, выбирайте автоматический профиль из подписки. Ручные параметры вводить не нужно.",
    badge: "4",
    tone: "neutral" as const,
  },
];

const manualClientCards = [
  {
    key: "hiddify",
    title: "Hiddify",
    body: "Android и Windows. Удобный импорт ссылки, подходит для sing-box/Xray-профилей.",
    badge: "Проще всего",
    tone: "success" as const,
    action: (
      <a href="https://github.com/hiddify/hiddify-app/releases" target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
        Скачать
      </a>
    ),
  },
  {
    key: "v2rayn",
    title: "v2rayN",
    body: "Windows. Подходит, если нужен привычный настольный клиент с подписками.",
    badge: "Windows",
    tone: "neutral" as const,
    action: (
      <a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
        Скачать
      </a>
    ),
  },
  {
    key: "nekobox",
    title: "NekoBox",
    body: "Android. Подходит для импорта ссылки и профилей на базе sing-box/Xray.",
    badge: "Android",
    tone: "neutral" as const,
    action: (
      <a href="https://github.com/MatsuriDayo/NekoBoxForAndroid/releases" target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
        Скачать
      </a>
    ),
  },
  {
    key: "sfa",
    title: "sing-box for Android",
    body: "Android. Ближе к чистому sing-box, если нужен минимальный клиент без лишней оболочки.",
    badge: "SFA",
    tone: "neutral" as const,
    action: (
      <a href="https://sing-box.sagernet.org/clients/android/" target="_blank" rel="noreferrer" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
        Открыть
      </a>
    ),
  },
];

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
          setError(String((nextError as { message?: string })?.message || nextError || ""));
        }
      }
    };

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const openManualSetupFromHash = () => {
      if (window.location.hash === "#manual-setup") {
        setManualAccessOpen(true);
      }
    };
    openManualSetupFromHash();
    window.addEventListener("hashchange", openManualSetupFromHash);
    return () => window.removeEventListener("hashchange", openManualSetupFromHash);
  }, []);

  const accessState = getAccessState(dash, user);
  const paidMode = isPaidUnlimitedState(accessState);
  const trialMode = isTrialPremiumState(accessState);
  const freeMode = isFreeMonthlyState(accessState);
  const softMode = isSoftModeState(accessState);
  const nextResetAt = getNextResetAt(dash, user);
  const freeLimitGb = getTrafficLimitGb(dash, user);
  const currentPlanCode = normalizePlanCode(dash?.current_plan_code || dash?.sub_type || "");
  const currentPaidPlanCode = paidMode ? currentPlanCode : "";
  const subscriptionUrl = String(user?.subscription_url || dash?.subscription_url || "").trim();
  const manualAccessReady = Boolean(subscriptionUrl && (dash?.is_active || user?.is_active));
  const premiumMode = paidMode || trialMode;
  const accessHint = paidMode
    ? "Полный доступ действует до указанной даты."
    : trialMode
      ? "Сейчас идет бесплатный полный доступ."
      : freeMode
        ? `Доступно ${freeLimitGb || 5} ГБ на ${nextResetAt ? `период до ${formatDate(nextResetAt)}` : "30 дней"} для 1 устройства.`
        : "Продлите срок, чтобы снова подключаться в приложении.";

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
    const isCurrent = Boolean(currentPaidPlanCode) && normalizedCode === currentPaidPlanCode;
    const amountRub = Number(plan.amount_rub || 0);
    const days = Number(plan.days || 0);
    const deviceLimit = Number(plan.device_limit || 0);

    return {
      key: plan.code,
      title: `${amountRub} ₽`,
      body: `${plan.label} · ${days} дней · до ${deviceLimit} устройств · ${nodePolicyLabel(plan.node_policy)}`,
      badge: isCurrent ? "Действует" : plan.badge || "Тариф",
      tone: isCurrent ? ("success" as const) : days >= 180 ? ("info" as const) : ("neutral" as const),
      action: isCurrent ? (
        <span className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">Действует сейчас</span>
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
      title: "Продлить доступ",
      body: "Выберите срок, проверьте сумму, устройства и платформы до оплаты.",
      badge: "Основной способ",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/subscription/checkout/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Открыть оплату
        </AppRouteLink>
      ),
    },
    {
      key: "redeem",
      title: "Активировать код",
      body: "Если у вас уже есть подарочный или оплаченный код, примените его в этом разделе.",
      badge: "Если код уже есть",
      tone: "neutral" as const,
      action: (
        <AppRouteLink href="/redeem/" className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
          Активировать код
        </AppRouteLink>
      ),
    },
    {
      key: "support",
      title: "Если после оплаты статус не обновился",
      body: "Откройте поддержку и продолжите один кейс. Оператор проверит оплату по безопасным данным.",
      badge: "Поддержка",
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
      title: paidMode ? "Премиум активен" : "Премиум для основного использования",
      body: paidMode
        ? `Доступ действует до ${formatDate(dash?.expiry_at)}. После окончания срока останется базовый режим.`
        : "Если не хочется думать о месячном лимите, продлите полный доступ от 99 ₽.",
      badge: paidMode ? "Сейчас так" : "Вариант",
      tone: paidMode ? ("success" as const) : ("neutral" as const),
    },
    {
      key: "trial",
      title: trialMode ? "Пробный период уже идет" : "Пробный период показывает POKROV в полном доступе",
      body: trialMode ? `Он действует до ${formatDate(dash?.expiry_at)}.` : "После него можно решить, нужен ли платный срок дальше.",
      badge: trialMode ? "Активен" : "Как это работает",
      tone: trialMode ? ("warning" as const) : ("neutral" as const),
    },
    {
      key: "free",
      title: freeMode ? "Базовый режим сейчас активен" : "Базовый режим остается запасным",
      body: freeMode
        ? `Сейчас доступно ${freeLimitGb || 5} ГБ на 30 дней для 1 устройства.`
        : "После окончания полного доступа остается запасной режим: 5 ГБ на 30 дней для 1 устройства.",
      badge: freeMode ? "Сейчас так" : "Запасной путь",
      tone: freeMode && !softMode ? ("info" as const) : softMode ? ("warning" as const) : ("neutral" as const),
    },
  ];

  return (
    <CabinetRoute
      eyebrow="Тарифы и оплата"
      title={dash?.is_active ? "Выберите срок продления" : "Вернуть доступ"}
      description={
        dash?.is_active
          ? "Цены, срок и лимит устройств показаны сразу. Текущий статус ниже."
          : "Сначала выберите срок, затем продолжайте тем же профилем."
      }
      actions={
        <>
          <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
            Открыть оплату
          </AppRouteLink>
          <AppRouteLink href="/redeem/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            У меня есть код
          </AppRouteLink>
          <AppRouteLink href="#manual-setup" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            Ключ / QR
          </AppRouteLink>
        </>
      }
    >
      <CabinetSection
        eyebrow="Варианты"
        title="Сроки видно сразу"
        description="Цена, срок и лимит устройств показаны в карточках до оплаты."
      >
        <CabinetCardGrid items={planCards} className="xl:grid-cols-4" />
        {error ? <p className="mt-4 text-sm text-amber-700 dark:text-amber-200">Часть данных не обновилась автоматически: {error}</p> : null}
      </CabinetSection>

      <CabinetHero
        eyebrow="Сейчас по профилю"
        badge={dash?.is_active ? "Можно продлить" : "Нужно действие"}
        badgeTone={dash?.is_active ? "success" : "warning"}
        title={premiumMode ? "Полный доступ можно продлить заранее" : dash?.is_active ? "Базовый режим можно заменить полным доступом" : "Сначала верните срок действия"}
        description={
          premiumMode
            ? "Если POKROV подходит, продлите срок до окончания доступа: устройства и история останутся на месте."
            : dash?.is_active
              ? "Базовый режим остается запасным, но полный доступ дает больше устройств и убирает месячный лимит."
            : "Как только срок снова станет активным, устройства и история останутся на месте."
        }
        actions={
          <>
            <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
              Открыть оплату
            </AppRouteLink>
            <AppRouteLink href="/redeem/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Активировать код
            </AppRouteLink>
          </>
        }
        details={[
          {
            label: "План сейчас",
            value: resolvePlanLabel(dash, user),
            hint: paidMode || trialMode ? `Полный доступ до ${formatDate(dash?.expiry_at || user?.expiry_at)}` : accessHint,
            tone: "neutral",
          },
          {
            label: "Полный режим",
            value: paidMode ? "Активен" : "Можно включить",
            hint: paidMode ? "Без месячного лимита трафика." : "До 5 устройств и полный пул доступных узлов.",
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

      <div id="manual-setup" className="scroll-mt-24 grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <CabinetSection
          eyebrow="Ручной вариант"
          title="Если приложения POKROV пока нет под рукой"
          description="Личная ссылка нужна только для совместимых клиентов и восстановления. Это не код активации и не способ привязать Telegram."
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
                ? "Инструкции можно читать сразу. Саму ссылку показываем отдельно, чтобы ее случайно не скопировали на чужое устройство."
                : "После оплаты или активации кода здесь появится личная ссылка и QR-код."}
            </p>
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setManualAccessOpen((value) => !value)}
                disabled={!manualAccessReady}
                className="outline-btn rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60"
              >
                {manualAccessOpen ? "Скрыть ссылку" : "Показать ссылку и QR"}
              </button>
              {!manualAccessReady ? (
                <AppRouteLink href="/subscription/checkout/" className="btn-primary rounded-full px-5 py-3 text-sm font-semibold">
                  Открыть оплату
                </AppRouteLink>
              ) : null}
            </div>
          </div>

          <div className="mt-5">
            <CabinetCardGrid items={manualStepCards} className="xl:grid-cols-2" />
          </div>

          <div className="mt-5">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-[var(--atlas-text-muted)]">
              Совместимые клиенты
            </p>
            <CabinetCardGrid items={manualClientCards} className="xl:grid-cols-1" />
          </div>

          {manualAccessOpen ? (
            <div className="mt-5 grid gap-5 lg:grid-cols-[240px_minmax(0,1fr)]">
              <div className="min-w-0">
                <SubscriptionQrCard value={subscriptionUrl} active={manualAccessReady} />
              </div>
              <div className="min-w-0">
                <p className="text-sm leading-6 text-[var(--atlas-text-soft)]">
                  Скопируйте ссылку или отсканируйте QR-код только на устройстве, которому доверяете. Ссылка дает доступ к профилю подключения.
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
          title="Три рабочих действия"
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
            Мы не показываем фальшивые строки и не придумываем квитанции. Если оплата уже была, а срок не обновился,
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
