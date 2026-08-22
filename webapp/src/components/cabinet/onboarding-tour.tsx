"use client";

import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  AtSign,
  Download,
  MonitorSmartphone,
  Send,
  ShieldCheck,
  Smartphone,
  UserRound,
  Wifi,
} from "lucide-react";

import PokrovMark from "@/components/pokrov-mark";
import { StepArt, type StepArtKind } from "@/components/cabinet/instructions";
import { Button } from "@/components/ui/button";
import { cn } from "@/components/utils";
import type { AccountExperienceNextStep, OnboardingCompletionStatus } from "@/lib/api";

const EASE = [0.22, 1, 0.36, 1] as const;
type TourStepId = "welcome" | "download" | "login" | "connect";
const STEP_ORDER: TourStepId[] = ["welcome", "download", "login", "connect"];

type OnboardingTourProps = {
  open: boolean;
  nextStep: AccountExperienceNextStep;
  saving?: boolean;
  error?: string;
  onClose: (status: OnboardingCompletionStatus) => Promise<boolean>;
};

function initialStepFor(nextStep: AccountExperienceNextStep): number {
  return nextStep === "connect" ? STEP_ORDER.indexOf("connect") : 0;
}

function WelcomeHero() {
  return (
    <div className="relative mx-auto grid size-[88px] place-items-center" aria-hidden="true">
      <span className="absolute inset-0 rounded-[28px] ring-2 ring-ok-line motion-safe:animate-[heroPulse_3.2s_ease-out_infinite]" />
      <span className="relative grid size-full place-items-center rounded-[28px] bg-brand-soft ring-1 ring-line">
        <PokrovMark className="h-12 w-12" label={undefined} />
      </span>
    </div>
  );
}

function FeatureRow({
  icon: Icon,
  title,
  hint,
}: {
  icon: typeof ShieldCheck;
  title: string;
  hint: string;
}) {
  return (
    <span className="flex items-center gap-3.5 text-left">
      <span className="grid size-10 shrink-0 place-items-center rounded-[12px] bg-brand-soft text-brand">
        <Icon size={19} strokeWidth={2} aria-hidden="true" />
      </span>
      <span className="min-w-0">
        <span className="block text-sm font-semibold text-ink">{title}</span>
        <span className="mt-0.5 block text-[13px] leading-5 text-ink-soft">{hint}</span>
      </span>
    </span>
  );
}

function PlatformRow({ icon: Icon, label, hint }: { icon: typeof Smartphone; label: string; hint: string }) {
  return (
    <li className="flex min-h-[52px] items-center gap-3 px-4 py-2.5 text-left">
      <span className="grid size-9 shrink-0 place-items-center rounded-[10px] bg-brand-soft text-brand">
        <Icon size={18} strokeWidth={2} aria-hidden="true" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold text-ink">{label}</span>
        <span className="mt-0.5 block text-[13px] leading-5 text-ink-muted">{hint}</span>
      </span>
    </li>
  );
}

function StepArtBadge({ kind }: { kind: StepArtKind }) {
  return (
    <span className="mx-auto grid size-[88px] place-items-center rounded-[28px] bg-canvas-alt ring-1 ring-line" aria-hidden="true">
      <StepArt kind={kind} />
    </span>
  );
}

function StepDots({ index }: { index: number }) {
  return (
    <div className="flex items-center gap-1.5" aria-hidden="true">
      {STEP_ORDER.map((step, dotIndex) => (
        <span
          key={step}
          className={cn(
            "h-1.5 rounded-full transition-all duration-300 ease-apple motion-reduce:transition-none",
            dotIndex === index ? "w-5 bg-brand" : "w-1.5 bg-line-strong",
          )}
        />
      ))}
    </div>
  );
}

export function OnboardingTour({ open, nextStep, saving = false, error = "", onClose }: OnboardingTourProps) {
  const router = useRouter();
  const reduceMotion = useReducedMotion();
  const titleId = useId();
  const panelRef = useRef<HTMLDivElement | null>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);
  const [stepIndex, setStepIndex] = useState(() => initialStepFor(nextStep));
  const [direction, setDirection] = useState(1);

  const stepId = STEP_ORDER[stepIndex];
  const isLastStep = stepIndex === STEP_ORDER.length - 1;
  const skip = useCallback(() => void onClose("skipped"), [onClose]);
  const finish = useCallback(() => void onClose("completed"), [onClose]);
  const finishAndOpenDownloads = useCallback(async () => {
    if (await onClose("completed")) router.push("/downloads/");
  }, [onClose, router]);

  useEffect(() => {
    if (!open || typeof document === "undefined") return;
    restoreFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    document.body.classList.add("modal-open");
    const focusTimer = window.setTimeout(() => panelRef.current?.focus(), 30);
    return () => {
      document.body.classList.remove("modal-open");
      window.clearTimeout(focusTimer);
      const restoreTarget = restoreFocusRef.current;
      restoreFocusRef.current = null;
      if (restoreTarget?.isConnected) {
        window.requestAnimationFrame(() => restoreTarget.focus());
      }
    };
  }, [open]);

  useEffect(() => {
    if (!open || typeof window === "undefined") return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !saving) {
        event.preventDefault();
        skip();
        return;
      }
      if (event.key !== "Tab") return;
      const panel = panelRef.current;
      if (!panel) return;
      const focusable = Array.from(
        panel.querySelectorAll<HTMLElement>("a[href], button:not([disabled]), [tabindex]:not([tabindex='-1'])"),
      ).filter((element) => element.offsetParent !== null || element === document.activeElement);
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey && (active === first || active === panel)) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, saving, skip]);

  const variants = useMemo(
    () => ({
      enter: (dir: number) => (reduceMotion ? { opacity: 0 } : { opacity: 0, x: dir > 0 ? 32 : -32 }),
      center: { opacity: 1, x: 0 },
      exit: (dir: number) => (reduceMotion ? { opacity: 0 } : { opacity: 0, x: dir > 0 ? -32 : 32 }),
    }),
    [reduceMotion],
  );

  const goNext = () => {
    setDirection(1);
    setStepIndex((value) => Math.min(value + 1, STEP_ORDER.length - 1));
  };
  const goBack = () => {
    setDirection(-1);
    setStepIndex((value) => Math.max(value - 1, 0));
  };

  return (
    <AnimatePresence>
      {open ? (
        <motion.div
          className="fixed inset-0 z-[70] flex items-end justify-center sm:items-center sm:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduceMotion ? 0 : 0.22 }}
        >
          <button
            type="button"
            aria-label="Закрыть подсказки"
            tabIndex={-1}
            disabled={saving}
            onClick={skip}
            className="absolute inset-0 cursor-default bg-[rgba(18,26,22,0.42)] backdrop-blur-[10px]"
          />
          <motion.div
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            tabIndex={-1}
            data-testid="onboarding-tour"
            initial={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 40, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={reduceMotion ? { opacity: 0 } : { opacity: 0, y: 28, scale: 0.98 }}
            transition={{ duration: reduceMotion ? 0 : 0.38, ease: EASE }}
            className="relative flex max-h-[92dvh] w-full flex-col overflow-hidden rounded-t-[28px] border border-line bg-surface pb-[max(env(safe-area-inset-bottom),1.25rem)] shadow-strong outline-none sm:max-w-[440px] sm:rounded-modal sm:pb-6"
          >
            <div className="flex justify-center pt-2.5 sm:hidden" aria-hidden="true">
              <span className="h-1 w-9 rounded-full bg-line-strong" />
            </div>
            <header className="flex items-center justify-between gap-3 px-5 pt-3 sm:px-6 sm:pt-5">
              <StepDots index={stepIndex} />
              <span className="sr-only" aria-live="polite">Шаг {stepIndex + 1} из {STEP_ORDER.length}</span>
              {!isLastStep ? (
                <Button variant="ghost" size="sm" onClick={skip} disabled={saving} className="-mr-2">Пропустить</Button>
              ) : <span className="min-h-9" aria-hidden="true" />}
            </header>

            <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-5 pt-4 pb-2 sm:px-6">
              <AnimatePresence mode="wait" custom={direction} initial={false}>
                <motion.section
                  key={stepId}
                  custom={direction}
                  variants={variants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{ duration: reduceMotion ? 0 : 0.32, ease: EASE }}
                  className="flex flex-col items-center gap-5 text-center"
                >
                  {stepId === "welcome" ? (
                    <>
                      <WelcomeHero />
                      <div>
                        <h2 id={titleId} className="font-display text-[1.55rem] leading-tight font-bold tracking-[-0.02em] text-ink">Добро пожаловать в POKROV</h2>
                        <p className="mx-auto mt-2 max-w-[34ch] text-sm leading-6 text-ink-soft">Три коротких шага — и защита работает на вашем устройстве.</p>
                      </div>
                      <ul className="m-0 flex w-full list-none flex-col gap-3.5 p-0 pt-1">
                        <li><FeatureRow icon={Download} title="Приложение POKROV" hint="Официальные сборки для Android и Windows" /></li>
                        <li><FeatureRow icon={UserRound} title="Один аккаунт" hint="Кабинет и приложение используют один доступ" /></li>
                        <li><FeatureRow icon={Wifi} title="Одна кнопка" hint="Подключение запускается одним нажатием" /></li>
                      </ul>
                    </>
                  ) : null}
                  {stepId === "download" ? (
                    <>
                      <StepArtBadge kind="download" />
                      <div>
                        <p className="text-xs font-semibold tracking-[0.14em] text-ink-muted uppercase">1 из 3</p>
                        <h2 id={titleId} className="mt-1.5 font-display text-[1.45rem] leading-tight font-bold tracking-[-0.02em] text-ink">Скачайте приложение</h2>
                        <p className="mx-auto mt-2 max-w-[36ch] text-sm leading-6 text-ink-soft">Берите сборки только из раздела «Загрузки» кабинета. Там указаны версия, размер и SHA-256; неполный релиз скрывается.</p>
                      </div>
                      <ul className="m-0 w-full list-none divide-y divide-line overflow-hidden rounded-card border border-line bg-surface p-0 text-left shadow-soft">
                        <PlatformRow icon={Smartphone} label="Android" hint="APK · версия и SHA-256" />
                        <PlatformRow icon={MonitorSmartphone} label="Windows" hint="EXE · версия и SHA-256" />
                      </ul>
                    </>
                  ) : null}
                  {stepId === "login" ? (
                    <>
                      <StepArtBadge kind="login" />
                      <div>
                        <p className="text-xs font-semibold tracking-[0.14em] text-ink-muted uppercase">2 из 3</p>
                        <h2 id={titleId} className="mt-1.5 font-display text-[1.45rem] leading-tight font-bold tracking-[-0.02em] text-ink">Войдите в тот же аккаунт</h2>
                        <p className="mx-auto mt-2 max-w-[36ch] text-sm leading-6 text-ink-soft">Используйте тот же email или связанный Telegram. Доступ и устройства подтянутся с сервера.</p>
                      </div>
                      <div className="flex flex-wrap items-center justify-center gap-2.5">
                        <span className="inline-flex items-center gap-2 rounded-full border border-line bg-canvas-alt px-3.5 py-1.5 text-[13px] font-semibold text-ink"><AtSign size={15} aria-hidden="true" className="text-brand" />Email</span>
                        <span className="text-xs font-semibold text-ink-muted">или</span>
                        <span className="inline-flex items-center gap-2 rounded-full border border-line bg-canvas-alt px-3.5 py-1.5 text-[13px] font-semibold text-ink"><Send size={15} aria-hidden="true" className="text-brand" />Telegram</span>
                      </div>
                    </>
                  ) : null}
                  {stepId === "connect" ? (
                    <>
                      <StepArtBadge kind="connect" />
                      <div>
                        <p className="text-xs font-semibold tracking-[0.14em] text-ink-muted uppercase">3 из 3</p>
                        <h2 id={titleId} className="mt-1.5 font-display text-[1.45rem] leading-tight font-bold tracking-[-0.02em] text-ink">Нажмите «Подключить»</h2>
                        <p className="mx-auto mt-2 max-w-[36ch] text-sm leading-6 text-ink-soft">Первый запуск может запросить системное разрешение VPN. После подключения сервер подтвердит статус в кабинете.</p>
                      </div>
                      <p className="inline-flex items-center gap-2 rounded-full border border-ok-line bg-ok-bg px-3.5 py-1.5 text-[13px] font-semibold text-ok-text"><ShieldCheck size={15} aria-hidden="true" />Готово — остальное сделает POKROV</p>
                    </>
                  ) : null}
                </motion.section>
              </AnimatePresence>
            </div>

            <footer className="flex flex-col gap-2.5 px-5 pt-3 sm:px-6">
              {error ? <p role="alert" className="text-sm font-medium text-danger-text">{error}</p> : null}
              <div className="flex items-center gap-2.5">
                {isLastStep ? (
                  <>
                    <Button variant="secondary" onClick={finish} loading={saving}>Готово</Button>
                    <Button onClick={() => void finishAndOpenDownloads()} loading={saving} className="flex-1">Открыть загрузки</Button>
                  </>
                ) : (
                  <>
                    {stepIndex > 0 ? <Button variant="secondary" onClick={goBack}>Назад</Button> : null}
                    <Button onClick={goNext} className="flex-1">Дальше</Button>
                  </>
                )}
              </div>
            </footer>
          </motion.div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
