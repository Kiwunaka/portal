"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ChevronDown, CircleCheck, Download, KeyRound, LifeBuoy, QrCode, ShieldCheck, TriangleAlert } from "lucide-react";

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
  resolveSubscriptionPresentation,
} from "@/lib/access-policy";
import { fetchPublicPlans, trackEvent, type PlanCatalogRow, type PromoSlotAssignmentPayload } from "@/lib/api";
import { getCabinetFallbackPlans, resolveCabinetPlans } from "@/lib/cabinet-plans";
import { normalizePlanCode } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { formatDays, formatDevicesLimit } from "@/lib/ru-plural";
import { subscriptionUrlForFormat } from "@/lib/subscription-format";

const ROW_ACTION_CLASS =
  "inline-flex min-h-12 items-center rounded-control px-2 text-sm font-semibold text-brand transition-colors hover:text-brand-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand";

function fallbackPlans(): PlanCatalogRow[] {
  return getCabinetFallbackPlans();
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

function formatDeadline(value?: string | null): string {
  if (!value) return "срок уточняется";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "срок уточняется";
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed);
}

const COMMERCIAL_LINEAGE_KEYS = [
  "pilot_id",
  "pilot_revision",
  "pilot_contract_sha256",
  "commercial_revision",
  "campaign_id",
  "offer_id",
  "creative_id",
  "variant",
  "assignment_id",
  "impression_id",
  "click_id",
] as const;

function commercialLineage(slot: PromoSlotAssignmentPayload): Record<string, string> | null {
  const entries = COMMERCIAL_LINEAGE_KEYS.map((key) => [key, String(slot[key] || "").trim()] as const);
  if (entries.some(([, value]) => !value)) return null;
  return Object.fromEntries(entries);
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
  name: "Happ";
  platforms: string;
  formatLabel: "format=happ";
  subscriptionUrl: string;
  downloadUrl: string;
  testId: "happ-subscription-url";
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
          className={ROW_ACTION_CLASS}
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
        const rows = resolveCabinetPlans(payload.plans);

        if (!cancelled) {
          setPlans(rows);
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
  const subscriptionPresentation = resolveSubscriptionPresentation(accessState);
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
  let happSubscriptionUrl: string | null = null;
  if (manualAccessVisible) {
    try {
      happSubscriptionUrl = subscriptionUrlForFormat(subscriptionUrl, "happ");
    } catch {
      happSubscriptionUrl = null;
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

  const visiblePlans = plans;
  const featuredCode = visiblePlans.length
    ? visiblePlans.reduce((best, plan) => (Number(plan.days || 0) > Number(best.days || 0) ? plan : best), visiblePlans[0]).code
    : "";
  const winbackSlot = dash?.promo_slots?.slots.find(
    (slot) => slot.enabled && slot.content_id === "winback_offer" && slot.slot_id === "webapp.subscription.contextual",
  ) || null;
  const winbackLineage = winbackSlot ? commercialLineage(winbackSlot) : null;

  useEffect(() => {
    if (!winbackSlot || !winbackLineage) return;
    const impressionId = String(winbackSlot.impression_id || "");
    const storageKey = `pokrov:promo-impression:${impressionId}`;
    try {
      if (window.sessionStorage.getItem(storageKey)) return;
      window.sessionStorage.setItem(storageKey, "1");
    } catch {
      // Telemetry is advisory; rendering and checkout must keep working.
    }
    void trackEvent("promo_impression", "webapp", winbackLineage);
  }, [winbackLineage, winbackSlot]);

  return (
    <main className="mx-auto flex w-full max-w-[860px] flex-col gap-5">
      <StatusHero
        title={subscriptionPresentation.title}
        meta={`${resolvePlanLabel(dash, user)} · ${accessHint}`}
        body={statusBody}
        tone={statusTone}
        icon={dash?.is_active ? ShieldCheck : TriangleAlert}
        action={
          <Button href="/subscription/checkout/" className="w-full sm:w-auto">
            {subscriptionPresentation.actionLabel}
          </Button>
        }
      />

      {winbackSlot ? (
        <section
          data-testid="winback-offer"
          className="rounded-card border border-ok-line bg-ok-bg p-4 shadow-soft"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone="success">{winbackSlot.badge_label || "Персональное предложение"}</Badge>
                <span className="text-xs text-ink-soft">до {formatDeadline(winbackSlot.ends_at)}</span>
              </div>
              <h2 className="mt-2 text-lg font-bold tracking-tight text-ink">{winbackSlot.title}</h2>
              {winbackSlot.body ? <p className="mt-1 text-sm leading-6 text-ink-soft">{winbackSlot.body}</p> : null}
              {typeof winbackSlot.final_price_rub === "number" ? (
                <p className="mt-2 text-sm font-semibold text-ink">
                  {typeof winbackSlot.base_price_rub === "number" ? <s className="mr-2 text-ink-muted">{winbackSlot.base_price_rub} ₽</s> : null}
                  {winbackSlot.final_price_rub} ₽
                  {typeof winbackSlot.remaining_quota_lower_bound === "number" ? ` · доступно не более ${winbackSlot.remaining_quota_lower_bound}` : ""}
                </p>
              ) : null}
              {winbackSlot.terms_url ? (
                <a href={winbackSlot.terms_url} target="_blank" rel="noreferrer" className="mt-2 inline-flex text-xs font-semibold text-brand-strong underline-offset-4 hover:underline">
                  Условия предложения
                </a>
              ) : null}
            </div>
            {winbackSlot.cta_href ? (
              <Button
                href={winbackSlot.cta_href}
                hardNavigate
                className="w-full shrink-0 sm:w-auto"
                onClick={() => {
                  if (winbackLineage) void trackEvent("promo_click", "webapp", winbackLineage);
                }}
              >
                {winbackSlot.cta_label || "Вернуться"}
              </Button>
            ) : null}
          </div>
          <p className="mt-3 text-xs leading-5 text-ink-muted">Без автосписаний. Итоговую сумму и доступность сервер повторно проверит перед оплатой.</p>
        </section>
      ) : null}

      <section className="flex flex-col gap-2.5">
        <details className="group overflow-hidden rounded-card border border-line bg-surface shadow-soft">
          <summary className="flex min-h-14 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-left outline-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-inset">
            <span className="min-w-0">
              <span className="block text-sm font-semibold text-ink">Все тарифы</span>
              <span className="mt-0.5 block text-xs text-ink-soft">6 сроков · от 99 ₽ · без автосписаний</span>
            </span>
            <ChevronDown className="shrink-0 text-ink-muted transition-transform group-open:rotate-180 motion-reduce:transition-none" size={18} strokeWidth={2} aria-hidden="true" />
          </summary>
          <div className="border-t border-line p-3">
            <div data-testid="subscription-plan-grid" className="grid grid-cols-2 gap-3 lg:grid-cols-3">
          {visiblePlans.map((plan) => {
            const normalizedCode = normalizePlanCode(plan.code);
            const isCurrent = Boolean(currentPaidPlanCode) && normalizedCode === currentPaidPlanCode;
            const isFeatured = !isCurrent && plan.code === featuredCode;
            const amountRub = Number(plan.amount_rub || 0);
            const days = Number(plan.days || 0);
            return (
              <article
                key={plan.code}
                data-plan-code={plan.code}
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
          </div>
        </details>
      </section>
      {error ? <p className="px-1 text-sm text-warn-text">Часть тарифов не обновилась: {error}</p> : null}

      <GroupedSection title="Действия">
        <Row icon={KeyRound} label="Активировать код" hint="Оплата, подарок или промокод" href="/redeem/" />
        <Row icon={Download} label="Скачать приложение" hint="APK для Android · EXE для Windows" href="/downloads/" />
        <Row icon={LifeBuoy} label="Помощь" hint="Если оплата не обновилась" href="/support/" />
      </GroupedSection>

      <section id="manual-setup" className="scroll-mt-24 space-y-2">
        <div className="flex items-center justify-between gap-3 px-1">
          <h2 className="text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Apple: ручное подключение</h2>
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
            label="Личный ключ и QR"
            hint={manualAccessReady ? "Для iPhone, iPad и Mac" : "Появится после активации"}
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
                    Используйте ключ только в совместимом Apple-приложении. На Android установите APK POKROV, на Windows — EXE.
                  </p>
                  <div className="mt-4 rounded-control border border-line bg-canvas-alt px-3 py-3">
                    <p className="font-mono text-xs leading-6 break-all text-ink">{subscriptionUrl}</p>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <CopyButton
                      text={subscriptionUrl}
                      label="Скопировать ключ"
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
                <p className="mb-2 text-xs font-bold tracking-[0.08em] text-ink-soft uppercase">Совместимые Apple-клиенты</p>
                <GroupedSection>
                  <Row
                    label="Hiddify"
                    value="Apple"
                    hint="Если доступен в вашем App Store"
                    action={
                      <a href="https://github.com/hiddify/hiddify-app/releases" target="_blank" rel="noreferrer" className={ROW_ACTION_CLASS}>
                        Скачать
                      </a>
                    }
                  />
                  {happSubscriptionUrl ? (
                    <CompatibleClientImport
                      name="Happ"
                      platforms="iPhone, iPad и Mac"
                      formatLabel="format=happ"
                      subscriptionUrl={happSubscriptionUrl}
                      downloadUrl="https://www.happ.su/main/"
                      testId="happ-subscription-url"
                    />
                  ) : (
                    <div className="p-4 text-sm leading-6 text-danger-text">
                      Не удалось безопасно подготовить ссылку для Happ.
                    </div>
                  )}
                  <Row label="Другие Apple-клиенты" value="Streisand · V2Box · Shadowrocket" href="/guides/" />
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
