"use client";

import AppRouteLink from "@/components/app-route-link";
import TelegramLoginWidget from "@/components/telegram-login-widget";
import {
  finishEmailRecovery,
  getEmailAuthStatus,
  loginByEmail,
  registerByEmail,
  setWebSessionToken,
  startEmailRecovery,
  verifyEmailToken,
} from "@/lib/api";
import { isEmailAuthPublicReady } from "@/lib/email-auth-readiness";
import { userFacingErrorMessage } from "@/lib/public-error-messages";
import { usePortalSession } from "@/lib/session";
import { useEffect, useRef, useState, type FormEvent } from "react";

type EmailMode = "login" | "register" | "verify" | "recover";

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

export default function CabinetEntryAuth({ siteUrl }: { siteUrl: string }) {
  const { webLoginBusy, webLoginError } = usePortalSession();
  const passwordRef = useRef<HTMLInputElement | null>(null);
  const newPasswordRef = useRef<HTMLInputElement | null>(null);
  const [emailReady, setEmailReady] = useState(false);
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

  useEffect(() => {
    let cancelled = false;
    void getEmailAuthStatus()
      .then((payload) => {
        if (!cancelled) setEmailReady(isEmailAuthPublicReady(payload));
      })
      .catch(() => {
        if (!cancelled) setEmailReady(false);
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
      setEmailError("Не получен токен email-сессии.");
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

  const inputClass =
    "w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none transition focus:border-rose-400 dark:border-white/10 dark:bg-white/[0.04]";
  const passwordInputClass = `${inputClass} pr-12`;
  const legalLinkClass = "text-slate-500 underline-offset-4 transition hover:text-slate-950 hover:underline dark:text-slate-400 dark:hover:text-slate-100";

  const passwordField = (
    <div>
      <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Пароль</label>
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
          className="absolute right-3 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-slate-100"
        >
          <span className="material-symbols-rounded text-[20px]">{showPassword ? "visibility_off" : "visibility"}</span>
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-5">
      <div>
        <div className="grid grid-cols-2 rounded-[1.5rem] bg-slate-100 p-1 shadow-inner dark:bg-white/[0.05]">
          {(["login", "register"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              onClick={() => setMode(mode)}
              className={`min-h-12 rounded-[1.25rem] px-4 text-sm font-semibold transition ${
                emailMode === mode
                  ? "bg-white text-rose-600 shadow-sm dark:bg-white/[0.10] dark:text-rose-200"
                  : "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100"
              }`}
            >
              {EMAIL_MODE_LABELS[mode]}
            </button>
          ))}
        </div>

        {emailReady ? (
          <div className="mt-6">
            {emailMode === "login" ? (
              <form className="space-y-4" onSubmit={submitLogin}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Email</label>
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
                <button type="submit" disabled={emailBusy} className="btn-primary w-full rounded-2xl px-5 py-4 text-sm font-semibold disabled:opacity-60">
                  {emailBusy ? "Входим..." : "Войти"}
                </button>
                <button
                  type="button"
                  onClick={() => setMode("recover")}
                  className="outline-btn w-full rounded-2xl px-5 py-3 text-sm font-semibold text-slate-600 dark:text-slate-300"
                >
                  Забыли пароль?
                </button>
              </form>
            ) : null}

            {emailMode === "register" ? (
              <form className="space-y-4" onSubmit={submitRegister}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Email</label>
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
                  <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Имя</label>
                  <input
                    className={inputClass}
                    value={displayName}
                    onChange={(event) => setDisplayName(event.target.value)}
                    autoComplete="name"
                    placeholder="Как к вам обращаться"
                  />
                </div>
                {passwordField}
                <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">{PASSWORD_HINT}</p>
                <button type="submit" disabled={emailBusy} className="btn-primary w-full rounded-2xl px-5 py-4 text-sm font-semibold disabled:opacity-60">
                  {emailBusy ? "Создаем..." : "Зарегистрироваться"}
                </button>
              </form>
            ) : null}

            {emailMode === "verify" ? (
              <form className="space-y-4" onSubmit={submitVerify}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Код из письма</label>
                  <input
                    className={inputClass}
                    value={verifyToken}
                    onChange={(event) => setVerifyToken(event.target.value)}
                    autoComplete="one-time-code"
                    placeholder="Код подтверждения"
                    required
                  />
                </div>
                <button type="submit" disabled={emailBusy} className="btn-primary w-full rounded-2xl px-5 py-4 text-sm font-semibold disabled:opacity-60">
                  {emailBusy ? "Проверяем..." : "Подтвердить"}
                </button>
                <button type="button" onClick={() => setMode("login")} className="outline-btn w-full rounded-2xl px-5 py-3 text-sm font-semibold">
                  Вернуться ко входу
                </button>
              </form>
            ) : null}

            {emailMode === "recover" ? (
              <form className="space-y-4" onSubmit={submitRecovery}>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Email</label>
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
                  <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Код восстановления</label>
                  <input
                    className={inputClass}
                    value={recoveryToken}
                    onChange={(event) => setRecoveryToken(event.target.value)}
                    autoComplete="one-time-code"
                    placeholder="Заполните, когда письмо придет"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-slate-600 dark:text-slate-300">Новый пароль</label>
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
                      className="absolute right-3 top-1/2 grid h-9 w-9 -translate-y-1/2 place-items-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-slate-100"
                    >
                      <span className="material-symbols-rounded text-[20px]">{showNewPassword ? "visibility_off" : "visibility"}</span>
                    </button>
                  </div>
                </div>
                <button type="submit" disabled={emailBusy} className="btn-primary w-full rounded-2xl px-5 py-4 text-sm font-semibold disabled:opacity-60">
                  {emailBusy ? "Отправляем..." : recoveryToken ? "Сбросить пароль и войти" : "Отправить письмо"}
                </button>
                <button type="button" onClick={() => setMode("login")} className="outline-btn w-full rounded-2xl px-5 py-3 text-sm font-semibold">
                  Вернуться ко входу
                </button>
              </form>
            ) : null}
          </div>
        ) : (
          <div className="mt-6 rounded-2xl border border-amber-200/70 bg-amber-50/80 px-4 py-3 text-sm leading-6 text-amber-900 dark:border-amber-400/25 dark:bg-amber-400/10 dark:text-amber-100">
            Email-вход пока проверяется. Самый быстрый путь сейчас — войти через Telegram.
          </div>
        )}
      </div>

      {emailMessage ? (
        <div className="rounded-2xl border border-emerald-300/40 bg-emerald-50/80 px-4 py-3 text-sm leading-6 text-emerald-900 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-200">
          {emailMessage}
        </div>
      ) : null}
      {emailError ? (
        <div className="rounded-2xl border border-rose-300/40 bg-rose-50/80 px-4 py-3 text-sm leading-6 text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
          {emailError}
        </div>
      ) : null}

      <div className="flex items-center gap-3">
        <div className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
        <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">или</span>
        <div className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
      </div>

      <TelegramLoginWidget
        buttonClassName="outline-btn w-full rounded-2xl px-5 py-3 text-sm font-semibold"
        buttonLabel="Войти через Telegram"
        busyLabel="Открываем Telegram..."
        showHint={false}
      />

      {webLoginError ? (
        <div className="rounded-2xl border border-rose-300/40 bg-rose-50/80 px-4 py-3 text-sm leading-6 text-rose-700 dark:border-rose-400/20 dark:bg-rose-400/10 dark:text-rose-200">
          {webLoginError}
        </div>
      ) : null}
      {webLoginBusy ? (
        <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">
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
