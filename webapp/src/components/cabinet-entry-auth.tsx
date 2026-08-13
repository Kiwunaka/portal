"use client";

import { Eye, EyeOff } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import { cn, FOCUS_RING } from "@/components/utils";
import { finishEmailRecovery, getEmailAuthStatus, loginByEmail, registerByEmail, setWebSessionToken, startEmailRecovery, verifyEmailToken, type EmailAuthStatusResult } from "@/lib/api";
import { isEmailAuthPublicReady } from "@/lib/email-auth-readiness";
import { getCopyText } from "@/lib/portal";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { useEffect, useRef, useState, type FormEvent } from "react";

export type EmailMode = "login" | "register" | "verify" | "recover";

export const EMAIL_MODE_COPY: Record<EmailMode, { title: string; subtitle: string }> = {
  login: {
    title: "Вход в аккаунт",
    subtitle: "Войдите по email или через Telegram, чтобы продолжить в кабинете.",
  },
  register: {
    title: "Создать аккаунт",
    subtitle: "Зарегистрируйтесь по email, чтобы сохранить доступ в одном профиле.",
  },
  verify: {
    title: "Подтвердить email",
    subtitle: "Введите код из письма, чтобы завершить регистрацию и открыть кабинет.",
  },
  recover: {
    title: "Восстановить доступ",
    subtitle: "Получите код по email и задайте новый пароль.",
  },
};

const EMAIL_MODE_LABELS: Record<EmailMode, string> = {
  login: "Вход",
  register: "Регистрация",
  verify: "Подтверждение",
  recover: "Восстановление",
};
const EMAIL_MODES = new Set(Object.keys(EMAIL_MODE_LABELS));
const PASSWORD_HINT = "Минимум 10 символов. Не используйте пароль от почты или Telegram.";

function externalPageUrl(siteUrl: string, pathname: "/offer/" | "/privacy/"): string {
  try {
    return new URL(pathname, siteUrl).href;
  } catch {
    return pathname;
  }
}

export default function CabinetEntryAuth({
  siteUrl,
  onModeChange,
}: {
  siteUrl: string;
  onModeChange?: (mode: EmailMode) => void;
}) {
  const { webLoginBusy, webLoginError } = usePortalSession();
  const reduceMotion = useReducedMotion();
  const passwordRef = useRef<HTMLInputElement | null>(null);
  const newPasswordRef = useRef<HTMLInputElement | null>(null);
  const [emailMode, setEmailMode] = useState<EmailMode>("login");
  const [emailBusy, setEmailBusy] = useState(false);
  const [emailMessage, setEmailMessage] = useState("");
  const [emailError, setEmailError] = useState("");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [verifyToken, setVerifyToken] = useState("");
  const [recoveryToken, setRecoveryToken] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [emailAuthStatus, setEmailAuthStatus] = useState<EmailAuthStatusResult | null>(null);
  const [emailAuthChecked, setEmailAuthChecked] = useState(false);

  useEffect(() => {
    onModeChange?.(emailMode);
  }, [emailMode, onModeChange]);

  useEffect(() => {
    let cancelled = false;

    getEmailAuthStatus()
      .then((payload) => {
        if (!cancelled) setEmailAuthStatus(payload);
      })
      .catch(() => {
        if (!cancelled) setEmailAuthStatus(null);
      })
      .finally(() => {
        if (!cancelled) setEmailAuthChecked(true);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const url = new URL(window.location.href);
    const nextVerifyToken = String(url.searchParams.get("email_token") || url.searchParams.get("verify_token") || "").trim();
    const nextRecoveryToken = String(url.searchParams.get("email_reset_token") || url.searchParams.get("reset_token") || "").trim();
    const nextEmailMode = String(url.searchParams.get("email_mode") || "").trim();
    let shouldReplaceUrl = Boolean(nextVerifyToken || nextRecoveryToken);
    if (!nextVerifyToken && !nextRecoveryToken && EMAIL_MODES.has(nextEmailMode)) {
      setEmailMode(nextEmailMode as EmailMode);
      shouldReplaceUrl = true;
    }
    if (!shouldReplaceUrl) return;

    if (nextVerifyToken) {
      setVerifyToken(nextVerifyToken);
      setRecoveryToken("");
      setEmailMode("verify");
      setEmailMessage("Код подтверждения уже подставлен. Нажмите «Подтвердить».");
    } else if (nextRecoveryToken) {
      setRecoveryToken(nextRecoveryToken);
      setVerifyToken("");
      setEmailMode("recover");
      setEmailMessage("Код восстановления уже подставлен. Введите новый пароль.");
    }
    setEmailError("");

    for (const key of ["email_token", "verify_token", "email_reset_token", "reset_token", "email_mode"]) {
      url.searchParams.delete(key);
    }
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}` || "/");
  }, []);

  const clearSensitiveInputs = (): void => {
    if (passwordRef.current) passwordRef.current.value = "";
    if (newPasswordRef.current) newPasswordRef.current.value = "";
  };

  const setMode = (mode: EmailMode): void => {
    setEmailMode(mode);
    setEmailError("");
    setEmailMessage("");
    clearSensitiveInputs();
    if (mode === "verify") setRecoveryToken("");
    if (mode === "recover") setVerifyToken("");
  };

  const completeEmailLogin = (nextToken?: string | null): void => {
    if (!nextToken) {
      setEmailError("Не получилось завершить вход по email. Попробуйте ещё раз.");
      return;
    }
    clearSensitiveInputs();
    setWebSessionToken(nextToken);
    if (typeof window !== "undefined") {
      window.location.replace("/dashboard/");
    }
  };

  const runEmailAction = async (action: () => Promise<void>): Promise<void> => {
    setEmailBusy(true);
    setEmailError("");
    setEmailMessage("");
    try {
      await action();
    } catch (error) {
      setEmailError(userFacingErrorMessage(error, "Не удалось выполнить действие. Попробуйте позже или напишите в поддержку."));
    } finally {
      setEmailBusy(false);
    }
  };

  const submitLogin = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const payload = await loginByEmail({ email, password: passwordRef.current?.value || "" });
      completeEmailLogin(payload.token);
    });
    clearSensitiveInputs();
  };

  const submitRegister = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const payload = await registerByEmail({
        email,
        password: passwordRef.current?.value || "",
        display_name: displayName || undefined,
      });
      setEmailMessage(
        payload?.delivery?.status === "sent"
          ? "Письмо отправлено. Проверьте почту."
          : "Аккаунт создан. Введите код из письма.",
      );
      setVerifyToken("");
      setRecoveryToken("");
      setEmailMode("verify");
    });
    clearSensitiveInputs();
  };

  const submitVerify = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const token = String(verifyToken || "").trim();
      if (!token) {
        setEmailError("Введите код подтверждения из письма.");
        return;
      }
      const payload = await verifyEmailToken({ token });
      completeEmailLogin(payload.token);
    });
  };

  const submitRecovery = async (event: FormEvent<HTMLFormElement>): Promise<void> => {
    event.preventDefault();
    await runEmailAction(async () => {
      const token = String(recoveryToken || "").trim();
      if (!token) {
        await startEmailRecovery({ email });
        setEmailMessage("Письмо для восстановления отправлено.");
        return;
      }
      const nextPassword = String(newPasswordRef.current?.value || "").trim();
      if (!nextPassword) {
        setEmailError("Введите новый пароль.");
        return;
      }
      const payload = await finishEmailRecovery({ token, password: nextPassword });
      completeEmailLogin(payload.token);
    });
    clearSensitiveInputs();
  };

  // Aligned with the UI kit (ui/input.tsx, ui/button.tsx): control radius
  // token, kit FOCUS_RING focus-visible pattern, pressed scale feedback with
  // motion-reduce guards.
  const inputClass = cn(
    "w-full rounded-control border border-line bg-surface px-4 py-3 text-sm text-ink placeholder:text-ink-muted transition-colors duration-200 hover:border-line-strong motion-reduce:transition-none",
    FOCUS_RING,
  );
  const passwordInputClass = cn(inputClass, "pr-12");
  const primaryButtonClass = cn(
    "w-full rounded-control bg-brand px-5 py-4 text-sm font-semibold text-brand-contrast transition-[background-color,transform] duration-200 hover:bg-brand-strong active:scale-[0.97] disabled:opacity-60 motion-reduce:transition-none motion-reduce:active:scale-100",
    FOCUS_RING,
  );
  const secondaryButtonClass = cn(
    "w-full rounded-control border border-line bg-surface px-5 py-3 text-sm font-semibold text-ink transition-[background-color,transform] duration-200 hover:bg-canvas-alt active:scale-[0.97] motion-reduce:transition-none motion-reduce:active:scale-100",
    FOCUS_RING,
  );
  const passwordToggleClass = cn(
    "absolute top-1/2 right-3 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-full text-ink-soft transition-colors duration-200 hover:bg-canvas-alt hover:text-ink motion-reduce:transition-none",
    FOCUS_RING,
  );
  const legalLinkClass = "text-ink-soft underline-offset-4 transition hover:text-ink hover:underline";
  const emailAuthReady = isEmailAuthPublicReady(emailAuthStatus);

  const passwordField = (
    <div>
      <label className="mb-2 block text-sm font-medium text-ink-soft">Пароль</label>
      <div className="relative">
        <input
          ref={passwordRef}
          className={passwordInputClass}
          type={showPassword ? "text" : "password"}
          autoComplete={emailMode === "login" ? "current-password" : "new-password"}
          placeholder="Пароль"
          minLength={emailMode === "register" ? 10 : undefined}
          required
        />
        <button
          type="button"
          aria-label={showPassword ? "Скрыть пароль" : "Показать пароль"}
          onClick={() => setShowPassword((value) => !value)}
          className={passwordToggleClass}
        >
          {showPassword ? <EyeOff className="h-5 w-5" strokeWidth={1.75} /> : <Eye className="h-5 w-5" strokeWidth={1.75} />}
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      {emailAuthReady ? (
        <div>
          <div className="grid grid-cols-2 rounded-[1.5rem] bg-canvas-alt p-1 shadow-inner">
            {(["login", "register"] as const).map((mode) => {
              const active = emailMode === mode;
              return (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setMode(mode)}
                  aria-pressed={active}
                  className={cn(
                    "relative min-h-12 rounded-[1.25rem] px-4 text-sm font-semibold transition-colors duration-200 motion-reduce:transition-none",
                    active ? "text-brand" : "text-ink-soft hover:text-ink",
                    FOCUS_RING,
                  )}
                >
                  {active ? (
                    /* Same sliding-thumb pattern as the sidebar nav pill in cabinet-shell.tsx. */
                    <motion.span
                      layoutId="entry-auth-mode-thumb"
                      aria-hidden="true"
                      className="absolute inset-0 rounded-[1.25rem] bg-surface shadow-sm"
                      transition={reduceMotion ? { duration: 0 } : { type: "spring", stiffness: 480, damping: 40 }}
                    />
                  ) : null}
                  <span className="relative z-10">{EMAIL_MODE_LABELS[mode]}</span>
                </button>
              );
            })}
          </div>

          <div className="mt-6">
            {emailMode === "login" ? (
              <form className="space-y-4" onSubmit={submitLogin}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-ink-soft">Email</label>
                  <input
                    className={inputClass}
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    type="email"
                    autoComplete="email"
                    placeholder="name@example.com"
                    required
                  />
                </div>
                {passwordField}
                <button type="submit" disabled={emailBusy} className={primaryButtonClass}>
                  {emailBusy ? "Входим..." : "Войти"}
                </button>
                <button
                  type="button"
                  onClick={() => setMode("recover")}
                  className={cn(secondaryButtonClass, "text-ink-soft")}
                >
                  Забыли пароль?
                </button>
              </form>
            ) : null}

            {emailMode === "register" ? (
              <form className="space-y-4" onSubmit={submitRegister}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-ink-soft">Email</label>
                  <input
                    className={inputClass}
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    type="email"
                    autoComplete="email"
                    placeholder="name@example.com"
                    required
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-ink-soft">Имя</label>
                  <input
                    className={inputClass}
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    autoComplete="name"
                    placeholder="Как к вам обращаться"
                  />
                </div>
                {passwordField}
                <p className="text-xs leading-5 text-ink-soft">{PASSWORD_HINT}</p>
                <p className="text-xs leading-5 text-ink-soft">
                  Уже начали в приложении? Откройте кабинет из приложения и добавьте email там, чтобы доступ остался в одном профиле.
                </p>
                <button type="submit" disabled={emailBusy} className={primaryButtonClass}>
                  {emailBusy ? "Создаем..." : "Зарегистрироваться"}
                </button>
              </form>
            ) : null}

            {emailMode === "verify" ? (
              <form className="space-y-4" onSubmit={submitVerify}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-ink-soft">Код из письма</label>
                  <input
                    className={inputClass}
                    value={verifyToken}
                    onChange={(event) => setVerifyToken(event.target.value)}
                    autoComplete="one-time-code"
                    placeholder="Код подтверждения"
                    required
                  />
                </div>
                <button type="submit" disabled={emailBusy} className={primaryButtonClass}>
                  {emailBusy ? "Проверяем..." : "Подтвердить"}
                </button>
                <button type="button" onClick={() => setMode("login")} className={secondaryButtonClass}>
                  Вернуться ко входу
                </button>
              </form>
            ) : null}

            {emailMode === "recover" ? (
              <form className="space-y-4" onSubmit={submitRecovery}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-ink-soft">Email</label>
                  <input
                    className={inputClass}
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    type="email"
                    autoComplete="email"
                    placeholder="name@example.com"
                    required={!recoveryToken}
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-ink-soft">Код из письма для восстановления</label>
                  <input
                    className={inputClass}
                    value={recoveryToken}
                    onChange={(event) => setRecoveryToken(event.target.value)}
                    autoComplete="one-time-code"
                    placeholder="Заполните, когда письмо придет"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-ink-soft">Новый пароль</label>
                  <div className="relative">
                    <input
                      ref={newPasswordRef}
                      className={passwordInputClass}
                      type={showNewPassword ? "text" : "password"}
                      autoComplete="new-password"
                      placeholder="Минимум 10 символов"
                      minLength={10}
                      required={Boolean(recoveryToken)}
                    />
                    <button
                      type="button"
                      aria-label={showNewPassword ? "Скрыть пароль" : "Показать пароль"}
                      onClick={() => setShowNewPassword((value) => !value)}
                      className={passwordToggleClass}
                    >
                      {showNewPassword ? <EyeOff className="h-5 w-5" strokeWidth={1.75} /> : <Eye className="h-5 w-5" strokeWidth={1.75} />}
                    </button>
                  </div>
                </div>
                <button type="submit" disabled={emailBusy} className={primaryButtonClass}>
                  {emailBusy ? "Отправляем..." : recoveryToken ? "Сбросить пароль и войти" : "Отправить письмо"}
                </button>
                <button type="button" onClick={() => setMode("login")} className={secondaryButtonClass}>
                  Вернуться ко входу
                </button>
              </form>
            ) : null}
          </div>
        </div>
      ) : (
        <div className="rounded-2xl border border-info-line bg-info-bg px-4 py-3 text-sm leading-6 text-info-text">
          {emailAuthChecked
            ? "Email-вход временно недоступен. Войдите через Telegram, а если нужна помощь с доступом, напишите в поддержку."
            : "Проверяем доступность входа по email..."}
        </div>
      )}

      {emailMessage ? (
        <div className="rounded-2xl border border-ok-line bg-ok-bg px-4 py-3 text-sm leading-6 text-ok-text">
          {emailMessage}
        </div>
      ) : null}
      {emailError ? (
        <div className="rounded-2xl border border-danger-line bg-danger-bg px-4 py-3 text-sm leading-6 text-danger-text">
          {emailError}
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-line" />
        <span className="text-xs font-semibold uppercase tracking-[0.16em] text-ink-soft">или</span>
        <div className="h-px flex-1 bg-line" />
      </div>

      <TelegramLoginWidget
        buttonClassName={cn(secondaryButtonClass, "text-ink")}
        buttonLabel={getCopyText("webapp.entry.primary_cta", "Войти через Telegram")}
        busyLabel="Открываем Telegram..."
        showHint={false}
      />

      {webLoginError ? (
        <div className="rounded-2xl border border-danger-line bg-danger-bg px-4 py-3 text-sm leading-6 text-danger-text">
          {webLoginError}
        </div>
      ) : null}
      {webLoginBusy ? (
        <p className="text-xs leading-5 text-ink-soft">
          Подтвердите вход в Telegram и вернитесь сюда. Кабинет откроется автоматически.
        </p>
      ) : null}

      <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 pt-2 text-xs">
        <AppRouteLink href={externalPageUrl(siteUrl, "/privacy/")} target="_blank" hardNavigate={false} className={legalLinkClass}>
          Политика конфиденциальности
        </AppRouteLink>
        <AppRouteLink href={externalPageUrl(siteUrl, "/offer/")} target="_blank" hardNavigate={false} className={legalLinkClass}>
          Пользовательское соглашение
        </AppRouteLink>
      </div>
    </div>
  );
}
