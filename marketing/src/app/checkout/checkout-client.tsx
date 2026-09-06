"use client";

import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Chip } from "../../components/ui/chip";
import { cn } from "../../components/utils";
import { MARKETING_CANONICAL_PATHS } from "../../lib/marketing-site";
import {
  useCheckoutController,
  OFFER_REASON_TEXT,
  type PaymentMethodChoice,
  RETURN_STATE_TEXT,
  config,
  describePromoContent,
  formatPlatformScope,
  formatPrice,
  formatServerDeadline,
  maskAccessKey,
  planBadgeLabel,
  planSupportingText,
} from "./use-checkout-controller";

const INPUT_CLASS =
  "min-h-11 w-full rounded-(--radius-control) border border-line bg-surface px-4 text-[0.9375rem] text-ink placeholder:text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-brand";

export function CheckoutLoadingFallback() {
  return (
    <div className="mx-auto flex max-w-3xl flex-col items-center gap-5 px-4 pt-12 pb-16 text-center sm:px-6 sm:pt-16">
      <Chip tone="neutral">Тарифы и код активации</Chip>
      <h1 className="font-display text-[2rem] leading-[1.1] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.5rem]">
        Выберите срок и проверьте сумму
      </h1>
      <p className="max-w-lg text-base leading-relaxed text-ink-soft">
        Подгружаем тарифы, условия доступа и действия для покупки или активации кода.
      </p>
      <div className="mt-4 grid w-full gap-4 sm:grid-cols-2">
        <Card>
          <p className="text-[0.9375rem] text-ink-soft">Готовим тарифы и сумму…</p>
        </Card>
        <Card>
          <p className="text-[0.9375rem] text-ink-soft">Проверяем доступные способы оплаты…</p>
        </Card>
      </div>
    </div>
  );
}

export default function CheckoutClient() {
  const {
    activeCheckoutTicket,
    infrastructureReady,
    paymentReturn,
    paymentReturnError,
    setPlanPickerOpen,
    planPickerOpen,
    activePlan,
    offerPreviewPending,
    previewMatchesPlan,
    activePlanTotal,
    availablePlans,
    selectedPlan,
    start99Eligibility,
    setSelectedPlan,
    catalog,
    activePlanMonthly,
    offerPreview,
    activePlanBase,
    buyerEmail,
    setBuyerEmail,
    setEmailError,
    emailError,
    paymentMethods,
    effectivePaymentMethod,
    setPaymentMethod,
    startPublicCheckout,
    checkoutBusy,
    recoveredReturnToken,
    checkoutReady,
    recoveringCheckout,
    offerQuote,
    setQuoteRefresh,
    checkoutStatusText,
    checkoutBlockedReasons,
    setInfrastructureRetry,
    promoCode,
    setPromoCode,
    offerMessage,
    keyInput,
    updateKeyInput,
    keyBusy,
    keyStatusText,
    keyStatus,
    redeemHref,
    marketingPromoIds,
  } = useCheckoutController();

  return (
    <div className="pb-16">
      <section className="mx-auto max-w-5xl px-4 pt-5 sm:px-6 sm:pt-9">
        <Card className="overflow-hidden p-0 shadow-medium">
          <div className="flex flex-col gap-4 border-b border-line bg-canvas-alt px-5 py-5 sm:flex-row sm:items-end sm:justify-between sm:px-8 sm:py-7">
            <div className="flex max-w-2xl flex-col items-start gap-2.5">
              <Chip tone="neutral">POKROV PREMIUM</Chip>
              <div>
                <h1 className="font-display text-[1.75rem] leading-[1.08] font-extrabold tracking-[-0.01em] text-ink sm:text-[2.25rem]">
                  Оформление доступа
                </h1>
                <p className="mt-2 text-[0.875rem] leading-relaxed text-ink-soft sm:text-[0.9375rem]">
                  {activeCheckoutTicket
                    ? "Один платёж, без автосписаний. Покупка привязана к вашему аккаунту."
                    : "Один платёж, без автосписаний. Код и чек придут на email."}
                </p>
              </div>
            </div>
            <Chip tone={infrastructureReady ? "brand" : "neutral"}>
              <span className={cn("size-1.5 rounded-full", infrastructureReady ? "bg-status-green" : "bg-ink-muted")} />
              {infrastructureReady ? "Оплата доступна" : "Оплата временно недоступна"}
            </Chip>
          </div>

          {paymentReturn || paymentReturnError ? (
            <div className="border-b border-line bg-surface px-5 py-4 sm:px-8" role="status" aria-live="polite">
              <p className={cn("text-[0.875rem] font-semibold", paymentReturn?.state === "paid" ? "text-status-green" : paymentReturn?.state === "manual_review" ? "text-brand-strong" : "text-ink") }>
                {paymentReturn ? RETURN_STATE_TEXT[paymentReturn.state] : paymentReturnError}
              </p>
              {paymentReturn?.state === "processing" ? (
                <p className="mt-1 text-[0.75rem] text-ink-soft">Проверяем подтверждение на сервере…</p>
              ) : null}
            </div>
          ) : null}

          <div className="grid lg:grid-cols-[1.08fr_0.92fr]">
            <div className="flex flex-col gap-5 border-b border-line px-5 py-6 sm:px-8 sm:py-8 lg:border-r lg:border-b-0">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[0.75rem] font-semibold tracking-[0.08em] text-brand-strong uppercase">Шаг 1</p>
                  <h2 className="font-display text-[1.25rem] font-bold text-ink">Выберите срок</h2>
                </div>
                <span className="text-[0.75rem] text-ink-muted">Безлимитный трафик</span>
              </div>

              <div className="relative">
                <button
                  type="button"
                  onClick={() => setPlanPickerOpen((value) => !value)}
                  aria-expanded={planPickerOpen}
                  aria-controls="checkout-plan-picker"
                  className="flex min-h-11 w-full items-center justify-between gap-4 rounded-(--radius-control) border border-brand bg-brand-soft px-4 py-4 text-left shadow-soft transition-[border-color,background-color,box-shadow] duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand"
                >
                  <span className="flex min-w-0 flex-col gap-1">
                    <span className="flex flex-wrap items-center gap-2">
                      <strong className="text-[1rem] font-semibold text-ink">{activePlan.label}</strong>
                      {planBadgeLabel(activePlan) ? (
                        <span className="rounded-full bg-surface px-2 py-0.5 text-[0.6875rem] font-semibold text-brand-strong">
                          {planBadgeLabel(activePlan)}
                        </span>
                      ) : null}
                    </span>
                    <span className="text-[0.75rem] text-ink-soft">{planSupportingText(activePlan)}</span>
                  </span>
                  <span className="flex shrink-0 items-center gap-2">
                    <strong className="text-[1.25rem] text-ink">{offerPreviewPending || !previewMatchesPlan ? "—" : `${activePlanTotal} ₽`}</strong>
                    <span aria-hidden="true" className={cn("text-[0.75rem] text-brand-strong transition-transform duration-200", planPickerOpen ? "rotate-180" : "")}>▼</span>
                  </span>
                </button>

                {planPickerOpen ? (
                  <div id="checkout-plan-picker" className="mt-2 grid grid-cols-2 gap-2 rounded-(--radius-control) border border-line bg-surface p-2 shadow-medium sm:grid-cols-3">
                    {availablePlans.map((plan) => {
                      const selected = selectedPlan === plan.code;
                      const disabled = plan.code === "start_99" && start99Eligibility === "ineligible";
                      return (
                        <button
                          key={plan.code}
                          type="button"
                          onClick={() => {
                            if (disabled) return;
                            setSelectedPlan(plan.code);
                            setPlanPickerOpen(false);
                          }}
                          disabled={disabled}
                          aria-pressed={selected}
                          className={cn(
                            "flex min-h-20 flex-col justify-between gap-2 rounded-(--radius-control) border px-3 py-2.5 text-left transition-[border-color,background-color] duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
                            disabled
                              ? "cursor-not-allowed border-line bg-canvas-alt opacity-60"
                              : selected
                                ? "border-brand bg-brand-soft"
                                : "border-line bg-surface hover:border-line-strong",
                          )}
                        >
                          <span className="flex w-full items-start justify-between gap-1">
                            <strong className="text-[0.8125rem] font-semibold text-ink">{plan.label}</strong>
                            {disabled ? (
                              <span className="text-[0.625rem] font-semibold text-ink-muted">Уже использован</span>
                            ) : planBadgeLabel(plan, true) ? (
                              <span className="text-[0.625rem] font-semibold text-brand-strong">{planBadgeLabel(plan, true)}</span>
                            ) : null}
                          </span>
                          <strong className="text-[0.9375rem] text-ink">{formatPrice(plan.amount_rub)}</strong>
                        </button>
                      );
                    })}
                  </div>
                ) : null}
              </div>

              <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
                Сменить срок — нажмите на карточку. Приветственные 99 ₽ доступны один раз.
              </p>
            </div>

            <div className="flex flex-col gap-5 px-5 py-6 sm:px-8 sm:py-8">
              <div className="flex items-end justify-between gap-4 border-b border-line pb-4">
                <div>
                  <p className="text-[0.75rem] font-semibold tracking-[0.08em] text-brand-strong uppercase">Шаг 2</p>
                  <h2 className="font-display text-[1.25rem] font-bold text-ink">Оплата</h2>
                  <p className="mt-1 text-[0.75rem] text-ink-soft">
                    {activePlan.days} дней · {formatPlatformScope(catalog?.public_surface_policy?.public_platform_scope)}
                  </p>
                </div>
                <div className="text-right">
                  <strong className="block font-display text-[1.75rem] leading-none text-brand">{offerPreviewPending || !previewMatchesPlan ? "—" : `${activePlanTotal} ₽`}</strong>
                  {activePlanMonthly > 0 ? <span className="mt-1 block text-[0.75rem] text-ink-soft">≈ {activePlanMonthly} ₽/мес</span> : null}
                  {offerPreview?.valid && activePlanTotal < activePlanBase ? <span className="mt-1 block text-[0.75rem] text-ink-soft">было {activePlanBase} ₽</span> : null}
                </div>
              </div>

              {infrastructureReady && !activeCheckoutTicket ? (
                <label className="flex flex-col gap-2 text-[0.875rem] font-medium text-ink" htmlFor="checkout-buyer-email">
                  Email для чека и кода
                  <input
                    id="checkout-buyer-email"
                    type="email"
                    name="email"
                    autoComplete="email"
                    inputMode="email"
                    value={buyerEmail}
                    onChange={(event) => {
                      setBuyerEmail(event.target.value);
                      setEmailError("");
                    }}
                    placeholder="email@example.com"
                    className={cn(INPUT_CLASS, "scroll-mt-24", emailError ? "border-status-red" : "")}
                    aria-invalid={Boolean(emailError)}
                    aria-describedby={emailError ? "checkout-email-error" : undefined}
                    aria-errormessage={emailError ? "checkout-email-error" : undefined}
                    required
                  />
                  {emailError ? (
                    <span id="checkout-email-error" role="alert" className="text-[0.8125rem] font-normal text-status-red">
                      {emailError}
                    </span>
                  ) : null}
                </label>
              ) : null}

              {infrastructureReady ? (
                <div className="flex flex-col gap-2">
                  <span className="text-[0.875rem] font-medium text-ink">Способ оплаты</span>
                  <div className="grid grid-cols-2 gap-2">
                    {paymentMethods.map((option) => {
                      const selected = option.code === effectivePaymentMethod;
                      return (
                        <button
                          key={option.code}
                          type="button"
                          onClick={() => setPaymentMethod(option.code as PaymentMethodChoice)}
                          disabled={!option.available}
                          className={cn(
                            "min-h-11 rounded-(--radius-control) border px-3 py-2 text-left transition-[border-color,background-color] duration-200 ease-(--ease-apple) focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
                            !option.available
                              ? "cursor-not-allowed border-line bg-canvas-alt opacity-55"
                              : selected
                                ? "border-brand bg-brand-soft"
                                : "border-line bg-surface hover:border-line-strong",
                          )}
                          aria-pressed={selected}
                        >
                          <span className="block text-[0.875rem] font-semibold text-ink">{option.label}</span>
                          <span className="block text-[0.6875rem] text-ink-soft">{option.available ? option.hint : "Временно недоступно"}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              {infrastructureReady ? (
                <Button onClick={() => void startPublicCheckout(performance.now())} disabled={checkoutBusy || Boolean(recoveredReturnToken) || (!checkoutReady && !recoveringCheckout)} size="lg" className="w-full">
                  {recoveringCheckout ? "Проверить заказ" : offerPreviewPending ? "Проверяем сумму…" : previewMatchesPlan ? `Оплатить ${activePlanTotal} ₽` : "Оплата недоступна"}
                </Button>
              ) : (
                <span aria-disabled="true" className="inline-flex min-h-11 w-full items-center justify-center rounded-full bg-canvas-alt px-6 text-[0.9375rem] font-semibold text-ink-muted">
                  Оплата временно недоступна
                </span>
              )}

              <p className="-mt-2 text-center text-[0.75rem] leading-relaxed text-ink-soft">
                {activeCheckoutTicket
                  ? "Разовая оплата · без автосписаний · доступ в аккаунт"
                  : "Разовая оплата · без автосписаний · код на email"}
              </p>

              {previewMatchesPlan && formatServerDeadline(offerPreview?.hold_expires_at) ? (
                <p className="-mt-2 text-center text-[0.75rem] leading-relaxed text-ink-soft">
                  Расчёт действителен до {formatServerDeadline(offerPreview?.hold_expires_at)}.
                </p>
              ) : null}
              {offerPreview?.terms_url ? (
                <a href={offerPreview.terms_url} target="_blank" rel="noreferrer" className="-mt-2 text-center text-[0.75rem] font-semibold text-brand-strong underline-offset-4 hover:underline">
                  Условия предложения
                </a>
              ) : null}

              {infrastructureReady && !offerPreviewPending && !previewMatchesPlan ? (
                <div className="flex flex-col gap-2" role="status">
                  <p className="text-[0.8125rem] text-ink-soft">
                    {offerQuote?.expired && offerPreview?.valid
                      ? "Срок подтверждённой суммы истёк. Проверьте условия ещё раз."
                      : OFFER_REASON_TEXT[offerPreview?.reason_code || ""] || "Не удалось подтвердить сумму. Проверьте условия ещё раз."}
                  </p>
                  <Button variant="secondary" onClick={() => setQuoteRefresh((current) => current + 1)}>
                    Проверить сумму
                  </Button>
                </div>
              ) : null}

              {checkoutStatusText ? (
                <p role="alert" className="rounded-(--radius-control) bg-canvas-alt px-4 py-3 text-[0.875rem] text-ink">
                  {checkoutStatusText}
                </p>
              ) : null}

              {!infrastructureReady ? (
                <div className="flex flex-col gap-3">
                  <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
                    {checkoutBlockedReasons.length
                      ? "Оплата временно недоступна. Начните с приложения или напишите в поддержку — подскажем следующий шаг."
                      : "Проверяем доступность оплаты. Если кнопка не появится, начните с приложения или напишите в поддержку."}
                  </p>
                  <Button variant="secondary" onClick={() => setInfrastructureRetry((value) => value + 1)}>
                    Проверить доступность оплаты
                  </Button>
                  <div className="grid grid-cols-2 gap-2">
                    <Button href={MARKETING_CANONICAL_PATHS.install} variant="secondary" className="w-full">
                      Скачать
                    </Button>
                    <Button href={config.botUrl} variant="secondary" target="_blank" rel="noreferrer" className="w-full">
                      Поддержка
                    </Button>
                  </div>
                </div>
              ) : null}

              <div className="flex flex-col divide-y divide-line border-y border-line">
                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Есть промокод?</summary>
                  <label className="mt-3 flex flex-col gap-2 text-[0.8125rem] text-ink-soft" htmlFor="checkout-promo-code">
                    Введите код — итог проверит сервер перед созданием платежа
                    <input
                      id="checkout-promo-code"
                      value={promoCode}
                      onChange={(event) => setPromoCode(event.target.value.toUpperCase().trim())}
                      placeholder="Например: POKROV10"
                      className={INPUT_CLASS}
                    />
                    <span>
                      {promoCode
                        ? offerPreviewPending
                          ? "Проверяем код и сумму на сервере…"
                          : offerMessage
                        : ""}
                    </span>
                  </label>
                </details>

                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Что входит в доступ?</summary>
                  <ul className="mt-3 mb-0 flex list-none flex-col gap-2 p-0 text-[0.8125rem] leading-relaxed text-ink-soft">
                    <li>Безлимитный трафик без пакетов гигабайтов.</li>
                    <li>Android + Windows, до {activePlan.device_limit} устройств.</li>
                    <li>Поддержка поможет с оплатой и активацией.</li>
                  </ul>
                </details>

                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Уже есть код активации?</summary>
                  <div className="mt-3 flex flex-col gap-3">
                    <label className="sr-only" htmlFor="checkout-access-key">Код активации</label>
                    <input
                      id="checkout-access-key"
                      value={keyInput}
                      onChange={(event) => updateKeyInput(event.target.value)}
                      placeholder="POKROV-XXXX-XXXX"
                      className={INPUT_CLASS}
                    />
                    {keyBusy ? <p className="text-[0.8125rem] text-ink-soft">Проверяем статус кода…</p> : null}
                    {keyStatusText ? <p role="alert" className="text-[0.8125rem] text-status-red">{keyStatusText}</p> : null}
                    {keyStatus ? (
                      <p className="text-[0.8125rem] leading-relaxed text-ink-soft">
                        {maskAccessKey(keyStatus.key)} · {keyStatus.plan?.label || `${keyStatus.days} дней`} · {keyStatus.redeemed ? "уже активирован" : "готов к активации"}
                      </p>
                    ) : null}
                    <Button href={redeemHref} variant="secondary" target="_blank" rel="noreferrer" className="w-full">
                      Активировать код
                    </Button>
                  </div>
                </details>

                <details className="group py-3">
                  <summary className="cursor-pointer text-[0.875rem] font-semibold text-ink">Перед оплатой — важное</summary>
                  <ul className="mt-3 mb-0 flex list-none flex-col gap-2 p-0 text-[0.8125rem] leading-relaxed text-ink-soft">
                    <li>99 ₽ доступны один раз — для первой успешной оплаты.</li>
                    {marketingPromoIds.map((contentId) => {
                      const content = describePromoContent(contentId);
                      return (
                        <li key={contentId}>
                          <strong className="text-ink">{content.title}</strong>: {content.body}
                        </li>
                      );
                    })}
                  </ul>
                  <a href={config.webappUrl} target="_blank" rel="noreferrer" className="mt-3 inline-flex text-[0.8125rem] font-semibold text-brand-strong underline-offset-4 hover:underline">
                    Открыть кабинет
                  </a>
                </details>
              </div>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
