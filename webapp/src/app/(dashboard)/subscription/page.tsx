"use client";

import { useEffect, useState } from "react";

import AppRouteLink from "@/components/app-route-link";
import { icon } from "@/components/cabinet/icon";
import { CabinetGroup, CabinetRow, CabinetStatus } from "@/components/cabinet/surface";
import { Button } from "@/components/cabinet/ui";
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
  if (days > 0) parts.push(`${days} дней`);
  if (deviceLimit > 0) parts.push(`до ${deviceLimit} устройств`);
  return parts.join(" · ") || "срок уточняется";
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
    ? `Полный доступ до ${formatDate(dash?.expiry_at || user?.expiry_at)}.`
    : trialMode
      ? `Пробный период до ${formatDate(dash?.expiry_at || user?.expiry_at)}.`
      : freeMode
        ? `${freeLimitGb || 5} ГБ на 30 дней${nextResetAt ? `, сброс ${formatDate(nextResetAt)}` : ""}.`
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

  const statusTone = dash?.is_active ? (softMode ? "warning" : "success") : "warning";
  const statusBody = premiumMode
    ? "Можно продлить заранее: устройства и настройки останутся на месте."
    : dash?.is_active
      ? "Можно перейти на полный доступ без месячного лимита."
      : "Выберите срок или активируйте код.";

  return (
    <main className="cab-page">
      <CabinetStatus
        title="Продлить доступ"
        meta={`${resolvePlanLabel(dash, user)} · ${accessHint}`}
        body={statusBody}
        tone={statusTone}
        action={
          <Button href="/subscription/checkout/" className="w-full sm:w-auto">
            Оплатить
          </Button>
        }
      />

      <CabinetGroup title="Срок">
        {plans.slice(0, 4).map((plan) => {
          const normalizedCode = normalizePlanCode(plan.code);
          const isCurrent = Boolean(currentPaidPlanCode) && normalizedCode === currentPaidPlanCode;
          const amountRub = Number(plan.amount_rub || 0);
          return (
            <CabinetRow
              key={plan.code}
              icon={icon(isCurrent ? "check_circle" : "calendar_month")}
              label={plan.label}
              hint={planHint(plan)}
              value={`${amountRub} ₽`}
              action={
                isCurrent ? (
                  <span className="text-sm font-semibold text-[color:var(--atlas-primary)]">Действует</span>
                ) : (
                  <AppRouteLink
                    href={`/subscription/checkout/?plan=${encodeURIComponent(plan.code)}`}
                    className="cab-link"
                  >
                    Выбрать
                  </AppRouteLink>
                )
              }
            />
          );
        })}
      </CabinetGroup>
      {error ? <p className="px-1 text-sm text-[color:var(--atlas-status-warning-text)]">Часть тарифов не обновилась: {error}</p> : null}

      <CabinetGroup title="Действия">
        <CabinetRow icon={icon("key")} label="Активировать код" hint="Оплата, подарок или промокод" href="/redeem/" />
        <CabinetRow icon={icon("download")} label="Скачать приложение" hint="Android и Windows" href="/downloads/" />
        <CabinetRow icon={icon("support_agent")} label="Помощь" hint="Если оплата не обновилась" href="/support/" />
      </CabinetGroup>

      <section id="manual-setup" className="scroll-mt-24 space-y-2">
        <div className="flex items-center justify-between gap-3 px-1">
          <h2 className="cab-eyebrow">Ручная настройка</h2>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => setManualAccessOpen((value) => !value)}
            disabled={!manualAccessReady}
          >
            {manualAccessOpen ? "Скрыть" : "Показать"}
          </Button>
        </div>
        <div className="cab-panel">
          <CabinetRow
            icon={icon("qr_code_2")}
            label="Личная ссылка и QR"
            hint={manualAccessReady ? "Только для восстановления или совместимого клиента" : "Появится после активации"}
            value={manualAccessOpen ? "открыто" : "скрыто"}
          />
          {manualAccessOpen ? (
            <div className="space-y-5 border-t border-[color:var(--atlas-table-divider)] p-4">
              <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
                <SubscriptionQrCard value={subscriptionUrl} active={manualAccessReady} />
                <div className="min-w-0">
                  <p className="text-sm leading-6 text-[color:var(--atlas-text-soft)]">
                    Скопируйте ссылку только на устройстве, которому доверяете. Она открывает профиль подключения.
                  </p>
                  <div className="mt-4 rounded-[var(--pokrov-radius-control)] border border-[color:var(--atlas-border)] bg-[color:var(--atlas-canvas-alt)] px-3 py-3">
                    <p className="break-all font-mono text-xs leading-6 text-[color:var(--atlas-text)]">{subscriptionUrl}</p>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    <Button onClick={() => void copySubscriptionUrl()} disabled={!manualAccessReady}>
                      Скопировать ссылку
                    </Button>
                    <Button variant="secondary" href={subscriptionUrl} target="_blank" hardNavigate={false}>
                      Открыть ссылку
                    </Button>
                  </div>
                  {copyStatus ? <p className="mt-3 text-sm font-semibold text-[color:var(--atlas-primary)]">{copyStatus}</p> : null}
                </div>
              </div>

              <div>
                <p className="cab-eyebrow mb-2">Совместимые клиенты</p>
                <div className="cab-panel">
                  <CabinetRow label="Hiddify" value="Android и Windows" action={<a href="https://github.com/hiddify/hiddify-app/releases" target="_blank" rel="noreferrer" className="cab-link">Скачать</a>} />
                  <CabinetRow label="v2rayN" value="Windows" action={<a href="https://github.com/2dust/v2rayN/releases" target="_blank" rel="noreferrer" className="cab-link">Скачать</a>} />
                  <CabinetRow label="NekoBox" value="Android" action={<a href="https://github.com/MatsuriDayo/NekoBoxForAndroid/releases" target="_blank" rel="noreferrer" className="cab-link">Скачать</a>} />
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
