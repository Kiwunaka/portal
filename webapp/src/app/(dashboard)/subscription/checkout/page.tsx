"use client";

import AppRouteLink from "@/components/app-route-link";
import { CabinetCardGrid, CabinetHero, CabinetRoute, CabinetSection } from "@/components/cabinet/surface";
import { resolvePlanLabel } from "@/lib/access-policy";
import { createRubCheckoutOrder, fetchPublicCatalog, getRubPaymentProviders, type RubPaymentProvidersResult } from "@/lib/api";
import {
  getPricingPreviewDiscountPercent,
  getTariffPlans,
  normalizePlanCode,
} from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

type DisplayPlan = {
  code: string;
  label: string;
  badge?: string;
  days: number;
  amountRub: number;
  deviceLimit: number;
  note: string;
};

const CHECKOUT_BLOCKED_PUBLIC_TEXT =
  "Оплата пока закрыта: мы включим продление после финальной проверки Lava.top и доставки ключей на email.";
const CHECKOUT_START_PUBLIC_ERROR =
  "Не удалось открыть оплату. Проверьте статус чуть позже или напишите в поддержку.";

const SHARED_PLANS: DisplayPlan[] = getTariffPlans()
  .slice()
  .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
  .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
  .map((plan) => ({
    code: plan.code,
    label: plan.label,
    badge: plan.badge || undefined,
    days: Number(plan.duration_days || 0),
    amountRub: Number(plan.amount_rub || 0),
    deviceLimit: Number(plan.device_limit || 1),
    note: plan.cabinet_note || plan.marketing_note || plan.label,
  }));

function normalizePromo(raw: string): string {
  return String(raw || "").trim().toUpperCase();
}

function formatDuration(days: number): string {
  if (days >= 365) return `${Math.round(days / 30)} мес.`;
  if (days > 90) return `${Math.round(days / 30)} мес.`;
  return `${days} дней`;
}

export default function CheckoutPage() {
  const searchParams = useSearchParams();
  const { user, dash } = usePortalSession();
  const [plans, setPlans] = useState<DisplayPlan[]>(SHARED_PLANS);
  const [promoInput, setPromoInput] = useState(() => normalizePromo(searchParams.get("promo") || ""));
  const [catalogError, setCatalogError] = useState("");
  const [selectedCode, setSelectedCode] = useState(() => normalizePlanCode(searchParams.get("plan"), "1_month"));
  const [providerCode, setProviderCode] = useState("");
  const [providerState, setProviderState] = useState<RubPaymentProvidersResult | null>(null);
  const [checkoutBusy, setCheckoutBusy] = useState(false);
  const [checkoutError, setCheckoutError] = useState("");

  useEffect(() => {
    setSelectedCode(normalizePlanCode(searchParams.get("plan"), "1_month"));
    setPromoInput(normalizePromo(searchParams.get("promo") || ""));
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const payload = await fetchPublicCatalog();
        const nextPlans = (payload.plans || [])
          .filter((plan) => Boolean(plan.is_active) && Number(plan.amount_rub || 0) > 0)
          .sort((left, right) => Number(left.sort_order || 0) - Number(right.sort_order || 0))
          .map((plan) => ({
            code: plan.code,
            label: plan.label,
            badge: plan.badge || undefined,
            days: Number(plan.days || 0),
            amountRub: Number(plan.amount_rub || 0),
            deviceLimit: Number(plan.device_limit || 1),
            note: plan.label,
          }));

        if (!cancelled) {
          setPlans(nextPlans.length ? nextPlans : SHARED_PLANS);
          setCatalogError("");
        }
      } catch (nextError) {
        if (!cancelled) {
          setPlans(SHARED_PLANS);
          setCatalogError(userFacingErrorMessage(nextError, "Показываем сохраненные варианты тарифов."));
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    void getRubPaymentProviders()
      .then((payload) => {
        if (!cancelled) {
          setProviderState(payload);
          setProviderCode(payload.ok && !payload.blocked ? String(payload.providers?.[0]?.code || "") : "");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setProviderState(null);
          setProviderCode("");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const activePlan = useMemo(
    () => plans.find((plan) => plan.code === selectedCode) || plans[0] || SHARED_PLANS[0],
    [plans, selectedCode],
  );
  const promoCode = normalizePromo(promoInput);
  const discountPercent = getPricingPreviewDiscountPercent(promoCode);
  const discountAmount = Math.round((Number(activePlan?.amountRub || 0) * discountPercent) / 100);
  const totalAmount = Math.max(0, Number(activePlan?.amountRub || 0) - discountAmount);
  const checkoutReady = Boolean(providerCode && providerState?.ok && !providerState?.blocked);
  const paymentBlockedText = CHECKOUT_BLOCKED_PUBLIC_TEXT;
  const checkoutPrimaryText = checkoutReady
    ? checkoutBusy
      ? "Открываем оплату..."
      : "Перейти к оплате"
    : "Проверить статус оплаты";
  const checkoutRouteTitle = checkoutReady ? "Продлить доступ" : "Оплата временно недоступна";
  const checkoutRouteDescription = checkoutReady
    ? "Выберите срок, проверьте сумму и перейдите на защищенную страницу оплаты. После оплаты ключ можно применить в приложении или в кабинете."
    : "Платежный маршрут закрыт, пока Lava.top и email-доставка ключей не пройдут проверку. Можно проверить тариф, ключ или написать в поддержку.";
  const checkoutHeroBadge = checkoutReady ? "Продолжение из кабинета" : "Ожидает проверки";
  const checkoutHeroBadgeTone = checkoutReady ? "success" : "warning";
  const checkoutHeroTitle = checkoutReady
    ? "Покупка проходит на платежной странице POKROV"
    : "Платежная касса закрыта до проверки запуска";
  const checkoutHeroDescription = checkoutReady
    ? "Кабинет помогает выбрать срок и возвращает вас к текущему профилю. Личные ссылки и ручные настройки здесь не показываются."
    : "Кабинет показывает выбранный срок и статус оплаты, но не создает заказ, пока запуск Lava.top, webhook и доставка ключей не подтверждены.";
  const checkoutAmountLabel = checkoutReady ? "К оплате" : "Сумма";
  const checkoutAmountHint = checkoutReady
    ? "Итог перед переходом на страницу оплаты."
    : "Ориентир до включения платежного маршрута.";
  const checkoutSummaryTitle = checkoutReady ? "Проверьте перед оплатой" : "Проверьте план и статус оплаты";
  const checkoutSummaryDescription = checkoutReady
    ? "Сумма и срок видны до перехода на платежную страницу."
    : "Сумма и срок показаны для ориентира. Переход к оплате включится только после зеленой проверки запуска.";

  const startCheckout = async (): Promise<void> => {
    if (!activePlan?.code || !checkoutReady || !providerCode) return;
    setCheckoutBusy(true);
    setCheckoutError("");
    try {
      const order = await createRubCheckoutOrder({
        provider: providerCode,
        plan_code: activePlan.code,
        source: "site",
        promo_code: discountPercent > 0 ? promoCode : undefined,
        currency: "RUB",
      });
      const paymentUrl = String(order.payment_url || "").trim();
      if (!paymentUrl) {
        throw new Error(CHECKOUT_START_PUBLIC_ERROR);
      }
      window.location.assign(paymentUrl);
    } catch {
      setCheckoutError(CHECKOUT_START_PUBLIC_ERROR);
    } finally {
      setCheckoutBusy(false);
    }
  };

  const selectedPlanCards = plans.map((plan) => {
    const selected = plan.code === activePlan?.code;
    return {
      key: plan.code,
      title: `${plan.label} · ${plan.amountRub} ₽`,
      body: `${formatDuration(plan.days)} · до ${plan.deviceLimit} устройств. ${plan.note}`,
      badge: selected ? "Выбрано" : plan.badge || "Вариант",
      tone: selected ? ("success" as const) : plan.days >= 180 ? ("info" as const) : ("neutral" as const),
      action: (
        <button
          type="button"
          onClick={() => setSelectedCode(plan.code)}
          className="text-sm font-semibold text-emerald-800 dark:text-emerald-300"
        >
          {selected ? "Оставить" : "Выбрать"}
        </button>
      ),
    };
  });

  return (
    <CabinetRoute
      eyebrow="Продление"
      title={checkoutRouteTitle}
      description={checkoutRouteDescription}
      actions={
        <>
          <button type="button" onClick={startCheckout} disabled={!checkoutReady || checkoutBusy} className="btn-primary rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60">
            {checkoutPrimaryText}
          </button>
          <AppRouteLink href="/redeem/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
            У меня уже есть ключ
          </AppRouteLink>
        </>
      }
      metrics={[
        {
          label: "Сейчас у вас",
          value: resolvePlanLabel(dash, user),
          hint: "Продление останется на текущем профиле.",
          tone: dash?.is_active ? "success" : "warning",
        },
        {
          label: "Выбранный срок",
          value: activePlan?.label || "1 месяц",
          hint: `${activePlan?.days || 30} дней · до ${activePlan?.deviceLimit || 1} устройств.`,
          tone: "neutral",
        },
        {
          label: "Скидка",
          value: discountPercent > 0 ? `${discountPercent}%` : "Нет",
          hint: discountPercent > 0 ? "Промокод применен к сумме." : "Можно оставить поле пустым.",
          tone: discountPercent > 0 ? "success" : "neutral",
        },
        {
          label: checkoutAmountLabel,
          value: `${totalAmount} ₽`,
          hint: checkoutAmountHint,
          tone: "neutral",
        },
      ]}
    >
      <CabinetHero
        eyebrow="Без второй витрины"
        badge={checkoutHeroBadge}
        badgeTone={checkoutHeroBadgeTone}
        title={checkoutHeroTitle}
        description={checkoutHeroDescription}
        actions={
          <>
            <button type="button" onClick={startCheckout} disabled={!checkoutReady || checkoutBusy} className="btn-primary rounded-full px-5 py-3 text-sm font-semibold disabled:opacity-60">
              {checkoutPrimaryText}
            </button>
            <AppRouteLink href="/subscription/" className="outline-btn rounded-full px-5 py-3 text-sm font-semibold">
              Назад к тарифам
            </AppRouteLink>
          </>
        }
        details={[
          {
            label: "Профиль",
            value: resolvePlanLabel(dash, user),
            hint: "Продление не создает новый аккаунт.",
            tone: "neutral",
          },
          {
            label: "Ключ после оплаты",
            value: "Применяется отдельно",
            hint: "Если ключ уже есть, используйте раздел применения ключа.",
            tone: "neutral",
          },
          {
            label: "Если оплата не обновилась",
            value: "Откройте поддержку",
            hint: "Мы проверим платеж и продолжим один кейс.",
            tone: "neutral",
          },
        ]}
      />

      <div className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
        <CabinetSection
          eyebrow="Срок"
          title="Выберите вариант"
          description="Берите тот срок, который нужен сейчас. Остальное можно изменить при следующем продлении."
        >
          <CabinetCardGrid items={selectedPlanCards} className="xl:grid-cols-2" />
          {catalogError ? (
            <p className="mt-4 text-sm text-amber-700 dark:text-amber-200">
              Каталог не обновился автоматически. {catalogError}
            </p>
          ) : null}
        </CabinetSection>

        <CabinetSection
          eyebrow="Итог"
          title={checkoutSummaryTitle}
          description={checkoutSummaryDescription}
        >
          <label className="block text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
            Промокод
          </label>
          <input
            value={promoInput}
            onChange={(event) => setPromoInput(event.target.value)}
            placeholder="Например: POKROV10"
            className="mt-2 w-full rounded-2xl border border-slate-200/80 bg-white px-4 py-3 text-sm outline-none transition focus:border-emerald-400 dark:border-white/10 dark:bg-white/[0.04]"
          />

          <div className="mt-4 rounded-[1.3rem] border border-slate-200/80 bg-slate-50/90 p-4 text-sm leading-6 text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-200">
            <p>
              Базовая цена: <strong>{activePlan?.amountRub} ₽</strong>
            </p>
            <p>
              Скидка: <strong>{discountAmount > 0 ? `${discountAmount} ₽` : "нет"}</strong>
            </p>
            <p className="mt-2 text-base font-semibold text-slate-950 dark:text-white">{checkoutAmountLabel}: {totalAmount} ₽</p>
          </div>

          <div className="mt-5 grid gap-3">
            <button type="button" onClick={startCheckout} disabled={!checkoutReady || checkoutBusy} className="btn-primary block rounded-2xl py-3 text-center text-sm font-semibold disabled:opacity-60">
              {checkoutPrimaryText}
            </button>
            <AppRouteLink href="/redeem/" className="outline-btn block rounded-2xl py-3 text-center text-sm font-semibold">
              Применить уже полученный ключ
            </AppRouteLink>
          </div>

          {checkoutError ? <p className="mt-4 text-sm text-rose-700 dark:text-rose-200">{checkoutError}</p> : null}
          {!checkoutReady ? (
            <p className="mt-4 text-sm text-amber-700 dark:text-amber-200">
              {paymentBlockedText}
            </p>
          ) : null}

          <div className="mt-5 rounded-[1.3rem] border border-slate-200/80 bg-white/72 px-4 py-4 text-sm leading-6 text-slate-600 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300">
            <p>Пробный период начинается в приложении на первом подходящем устройстве.</p>
            <p className="mt-2">Telegram остается для бонуса, восстановления и поддержки, если браузерный сценарий недоступен.</p>
          </div>
        </CabinetSection>
      </div>
    </CabinetRoute>
  );
}
