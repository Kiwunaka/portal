"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { CircleCheck, Download, KeyRound, LifeBuoy, QrCode, ShieldCheck, TriangleAlert } from "lucide-react";

import CopyButton from "@/components/cabinet/copy-button";
import { StatusHero } from "@/components/cabinet/status-hero";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { GroupedSection, Row } from "@/components/ui/grouped";
import SubscriptionQrCard from "@/components/subscription-qr-card";
import { cn } from "@/components/utils";
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
import { getCopyText, getTariffPlans, normalizePlanCode } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { formatDays, formatDevicesLimit } from "@/lib/ru-plural";
import { subscriptionUrlForFormat } from "@/lib/subscription-format";

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
  if (!value) return "уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "уточняется";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
  }).format(parsed);
}

function planHint(plan: PlanCatalogRow): string {
  const days = Number(plan.days || 0);
  const deviceLimit = Number(plan.device_limit || 0);
  const parts = [];
  if (days > 0) parts.push(formatDays(days));
  if (deviceLimit > 0) parts.push(formatDevicesLimit(deviceLimit));
  return parts.join(" · ") || "срок уточняется";
}

function CompatibleClientImport({
  name,
  platforms,
  formatLabel,
  subscriptionUrl,
  downloadUrl,
  testId,
}: {
  name: "Karing" | "Happ";
  platforms: string;
  formatLabel: "format=smart" | "format=happ";
  subscriptionUrl: string;
  downloadUrl: string;
  testId: "karing-subscription-url" | "happ-subscription-url";
}) {
  return (
    <div className="p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-semibold text-ink">{name}</p>
            <Badge tone="neutral">Запасной</Badge>
          </div>
          <p className="mt-1 text-xs leading-5 text-ink-soft">{platforms} · {formatLabel}</p>
        </div>
        <a
          href={downloadUrl}
          target="_blank"
          rel="noreferrer"
          className="text-sm font-semibold text-brand hover:text-brand-strong"
        >
          Скачать
        </a>
      </div>

      <div className="mt-4 grid gap-4 sm:grid-cols-[132px_minmax(0,1fr)] sm:items-start">
        <div
          data-testid={`${testId}-qr`}
          className="[&>div]:!mt-0 [&>div]:!size-32 [&>img]:!mt-0 [&>img]:!size-32"
        >
          <SubscriptionQrCard value={subscriptionUrl} active={Boolean(subscriptionUrl)} />
        </div>
        <div className="min-w-0">
          <p className="text-xs leading-5 text-ink-soft">
            Импортируйте эту ссылку как подписку. Не отправляйте её в чат или сторонний сайт.
          </p>
          <div className="mt-2 rounded-control border border-line bg-canvas-alt px-3 py-2.5">
            <p data-testid={testId} className="font-mono text-xs leading-5 break-all text-ink">
              {subscriptionUrl}
            </p>
          </div>
          <CopyButton
            text={subscriptionUrl}
            label={`Скопировать для ${name}`}
            copiedLabel="Скопировано"
            toastMessage={`Ссылка для ${name} скопирована`}
            variant="secondary"
            size="sm"
            disabled={!subscriptionUrl}
            className="mt-3"
          />
        </div>
      </div>
    </div>
  );
}

export default function SubscriptionPage() {
  const { user, dash } = usePortalSession();
  const reduceMotion = useReducedMotion();
  const [plans, setPlans] = useState<PlanCatalogRow[]>(() => fallbackPlans());
  const [error, setError] = useState("");
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
          setError(userFacingErrorMessage(nextError, "Проверьте соединение и обновите страницу."));
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
  const freeLimitGb = getTrafficLimitGb(dash, user);
  const currentPlanCode = normalizePlanCode(dash?.current_plan_code || dash?.sub_type || "");
  const currentPaidPlanCode = paidMode ? currentPlanCode : "";
  const subscriptionUrl = String(user?.subscription_url || dash?.subscription_url || "").trim();
  const manualAccessReady = Boolean(subscriptionUrl && (dash?.is_active || user?.is_active));
  const manualAccessVisible = manualAccessOpen && manualAccessReady;
  let compatibleClientUrls: { karing: string; happ: string } | null = null;
  if (manualAccessVisible) {
    try {
      compatibleClientUrls = {
        karing: subscriptionUrlForFormat(subscriptionUrl, "smart"),
        happ: subscriptionUrlForFormat(subscriptionUrl, "happ"),
      };
    } catch {
      compatibleClientUrls = null;
    }
  }

  useEffect(() => {
    if (typeof window === "undefined") return;
    const openManualSetupFromHash = () => {
      if (window.location.hash === "#manual-setup") {
        setManualAccessOpen(manualAccessReady);
      }
    };
    openManualSetupFromHash();
    window.addEventListener("hashchange", openManualSetupFromHash);
    return () => window.removeEventListener("hashchange", openManualSetupFromHash);
  }, [manualAccessReady]);
  const premiumMode = paidMode || trialMode;
  const accessHint = paidMode
    ? `Полный доступ до ${formatDate(dash?.expiry_at || user?.expiry_at)}.`
    : trialMode
      ? `Пробный период до ${formatDate(dash?.expiry_at || user?.expiry_at)}.`
      : freeMode
        ? `${freeLimitGb || 5} ГБ на 30 дней${nextResetAt ? `, сброс ${formatDate(nextResetAt)}` : ""}.`
        : "Продлите срок, чтобы снова подключаться в приложении.";

  const statusTone = dash?.is_active ? (softMode ? "warning" : "success") : "warning";
  const statusBody = premiumMode
    ? "Можно продлить заранее: устройства и настройки останутся на месте."
    : dash?.is_active
      ? "Можно перейти на полный доступ без месячного лимита."
      : "Выберите срок или активируйте код.";

  const visiblePlans = plans.slice(0, 4);
  const featuredCode = visiblePlans.length
    ? visiblePlans.reduce((best, plan) => (Number(plan.days || 0) > Number(best.days || 0) ? plan : best), visiblePlans[0]).code
    : "";

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title={getCopyText("webapp.subscription.title", "Продлить доступ")}
        meta={`${resolvePlanLabel(dash, user)} · ${accessHint}`}
        body={statusBody}
        tone={statusTone}
        icon={dash?.is_active ? ShieldCheck : TriangleAlert}
        action={
          <Button href="/subscription/checkout/" className="w-full sm:w-auto">
            Оплатить
          </Button>
        }
      />

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Срок</h2>
        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {visiblePlans.map((plan) => {
            const normalizedCode = normalizePlanCode(plan.code);
            const isCurrent = Boolean(currentPaidPlanCode) && normalizedCode === currentPaidPlanCode;
            const isFeatured = !isCurrent && plan.code === featuredCode;
            const amountRub = Number(plan.amount_rub || 0);
            const days = Number(plan.days || 0);
            return (
              <article
                key={plan.code}
                className={cn(
                  "flex flex-col gap-2 rounded-card border bg-surface p-4 shadow-soft",
                  isFeatured ? "border-brand shadow-medium" : "border-line",
                  isCurrent && "border-ok-line bg-ok-bg/40",
                )}
              >
                <span
                  className={cn(
                    "inline-flex w-fit items-center rounded-full border px-2 py-0.5 text-[11px] font-bold uppercase",
                    isFeatured ? "border-ok-line bg-ok-bg text-ok-text" : "border-neutral-line bg-neutral-bg text-neutral-text",
                  )}
                >
                  {plan.badge || (isFeatured ? "выгодно" : "срок")}
                </span>
                <h3 className="text-sm font-semibold text-ink">{plan.label}</h3>
                <div className="text-xl leading-none font-bold text-ink">
                  {amountRub} ₽{days > 0 ? <span className="text-sm font-medium text-ink-soft"> / {days} дн.</span> : null}
                </div>
                <p className="flex-1 text-xs leading-5 text-ink-soft">{planHint(plan)}</p>
                {isCurrent ? (
                  <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-ok-text">
                    <CircleCheck size={18} strokeWidth={2} aria-hidden="true" />
                    Действует сейчас
                  </span>
                ) : (
                  <Button
                    href={`/subscription/checkout/?plan=${encodeURIComponent(plan.code)}`}
                    variant={isFeatured ? "primary" : "secondary"}
                    size="sm"
                    block
                  >
                    Выбрать
                  </Button>
                )}
              </article>
            );
          })}
        </div>
      </section>
      {error ? <p className="px-1 text-sm text-warn-text">Часть тарифов не обновилась: {error}</p> : null}

      <GroupedSection title="Действия">
        <Row icon={KeyRound} label="Активировать код" hint="Оплата, подарок или промокод" href="/redeem/" />
        <Row icon={Download} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
        <Row icon={LifeBuoy} label="Помощь" hint="Если оплата не обновилась" href="/support/" />
      </GroupedSection>

      <section id="manual-setup" className="scroll-mt-24 space-y-2">
        <div className="flex items-center justify-between gap-3 px-1">
          <h2 className="text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Ручная настройка</h2>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setManualAccessOpen((value) => !value)}
            disabled={!manualAccessReady}
          >
            {manualAccessVisible ? "Скрыть" : "Показать"}
          </Button>
        </div>
        <div className="overflow-hidden rounded-card border border-line bg-surface shadow-soft">
          <Row
            icon={QrCode}
            label="Личная ссылка и QR"
            hint={manualAccessReady ? "Только для восстановления или совместимого клиента" : "Появится после активации"}
            value={manualAccessVisible ? "открыто" : "скрыто"}
          />
          <AnimatePresence initial={false}>
            {manualAccessVisible ? (
              <motion.div
                initial={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
                animate={reduceMotion ? { opacity: 1 } : { height: "auto", opacity: 1 }}
                exit={reduceMotion ? { opacity: 0 } : { height: 0, opacity: 0 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                className="overflow-hidden"
              >
                <div className="space-y-5 border-t border-line p-4">
              <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
                <SubscriptionQrCard value={subscriptionUrl} active={manualAccessReady} />
                <div className="min-w-0">
                  <p className="text-sm leading-6 text-ink-soft">
                    Скопируйте ссылку только на устройстве, которому доверяете. Она открывает профиль подключения.
                  </p>
                  <div className="mt-4 rounded-control border border-line bg-canvas-alt px-3 py-3">
                    <p className="font-mono text-xs leading-6 break-all text-ink">{subscriptionUrl}</p>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <CopyButton
                      text={subscriptionUrl}
                      label="Скопировать ссылку"
                      copiedLabel="Скопировано"
                      toastMessage="Ссылка скопирована"
                      disabled={!manualAccessReady}
                    />
                    <Button variant="secondary" href={subscriptionUrl} hardNavigate>
                      Открыть ссылку
                    </Button>
                  </div>
                </div>
              </div>

              <div>
                <p className="mb-2 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Совместимые клиенты</p>
                <GroupedSection>
                  <Row
                    label="Hiddify"
                    value="Android и Windows"
                    hint="Проверенный fallback"
                    action={
                      <a href="https://github.com/hiddify/hiddify-app/releases" target="_blank" rel="noreferrer" className="text-sm font-semibold text-brand hover:text-brand-strong">
                        Скачать
                      </a>
                    }
                  />
                  {compatibleClientUrls ? (
                    <>
                      <CompatibleClientImport
                        name="Karing"
                        platforms="Android, Windows и macOS"
                        formatLabel="format=smart"
                        subscriptionUrl={compatibleClientUrls.karing}
                        downloadUrl="https://github.com/KaringX/karing/releases/latest"
                        testId="karing-subscription-url"
                      />
                      <CompatibleClientImport
                        name="Happ"
                        platforms="Android, Windows, macOS и iOS"
                        formatLabel="format=happ"
                        subscriptionUrl={compatibleClientUrls.happ}
                        downloadUrl="https://www.happ.su/main/"
                        testId="happ-subscription-url"
                      />
                    </>
                  ) : (
                    <div className="p-4 text-sm leading-6 text-danger-text">
                      Не удалось безопасно подготовить ссылки для Karing и Happ.
                    </div>
                  )}
                  <Row
                    label="v2rayN"
                    value="Windows"
                    action={
                      <a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noreferrer" className="text-sm font-semibold text-brand hover:text-brand-strong">
                        Скачать
                      </a>
                    }
                  />
                  <Row
                    label="NekoBox"
                    value="Android"
                    action={
                      <a href="https://github.com/MatsuriDayo/NekoBoxForAndroid/releases" target="_blank" rel="noreferrer" className="text-sm font-semibold text-brand hover:text-brand-strong">
                        Скачать
                      </a>
                    }
                  />
                </GroupedSection>
              </div>
                </div>
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      </section>
    </main>
  );
}
